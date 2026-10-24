"""Build verification suites for MIA's harness from open data (VitaminC and Wikidata), with a dev/holdout split.

Usage (repository root, needs the internet, standard library only):
    python3 -I tools/make_external_suite.py --out data/eval-external --seed 7
    python3 -I tools/make_external_suite.py --source wikidata --n-wikidata 120 --out data/eval-external

What it writes below --out (default data/eval-external, ignored by git):
    suites/verdicts_vitaminc/            dev cases        suite.json + cases.jsonl
    suites/verdicts_vitaminc.holdout/    holdout cases    (never read it while tuning)
    suites/verdicts_wikidata/ and suites/verdicts_wikidata.holdout/
    audit/sample_sheet.csv               a blind sheet (about 20 % of the pairs) for your own labels
    audit/key.json                       the benchmark labels for that sheet (do not open before you labelled)
    manifest.json                        seed, sources, counts, licences, hash of every id list

Rules it follows (agent-app-plan/references/eval-design.md):
  * the split is by a hash of the pair id (every third pair goes to the holdout), so it is reproducible and
    both halves of a pair stay together; nobody has to read the holdout to build it;
  * VitaminC: SUPPORTS means true, REFUTES false, NOT ENOUGH INFO "no verdict" (truth null, expect inconclusive);
  * Wikidata: the true claim is a value from Wikidata, the false twin is made by a seeded rule (a factor, two
    swapped digits, a unit off by 10, a year off) and differs from the true value by at least 5 percent (years: 1);
  * tags: number, pair:<id>, family:<name>, source:<name>, labelsrc:<name>, label:people, split:dev|holdout, req:AC-2.

Licences: VitaminC is CC BY-SA 3.0, Wikidata is CC0. Do not commit the VitaminC cases (the licence may not be
compatible with GPL-3.0); commit the script, the seed and the manifest.
"""
import argparse, csv, hashlib, json, math, pathlib, random, re, sys, time, urllib.parse, urllib.request

UA = "MIA-eval-suite-builder/1.0 (research tool; https://github.com/maldun/MIA)"
HF = "https://datasets-server.huggingface.co/rows"
WDQS = "https://query.wikidata.org/sparql"
REQ_TAG = "req:AC-2"
TARGET = {"kind": "pipeline", "skill": "verify_claim"}


# ---------------------------------------------------------------- small helpers (tested offline)
def is_holdout(pair_id, mod=3):
    """one of `mod` pairs goes to the holdout; stable for a given id"""
    return int(hashlib.sha1(pair_id.encode("utf8")).hexdigest(), 16) % mod == 0


def clean_text(s):
    s = s.replace("�", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\s+([.,;:!?%)])", r"\1", s)
    s = re.sub(r"([(\[])\s+", r"\1", s)
    return s


def swap_digits(n, rng):
    """swap two adjacent different digits of a positive integer; None if impossible"""
    d = list(str(n))
    spots = [i for i in range(len(d) - 1) if d[i] != d[i + 1] and not (i == 0 and d[1] == "0")]
    if not spots:
        return None
    i = rng.choice(spots)
    d[i], d[i + 1] = d[i + 1], d[i]
    return int("".join(d))


def false_twin(value, rng, kind="quantity"):
    """a wrong but near value for an integer `value`; years change by a few years, quantities by a factor,
    two swapped digits or a unit off by 10. Always differs by >= 5 percent (years: >= 1)."""
    for _ in range(40):
        if kind == "year":
            cand = value + rng.choice([-10, -5, -3, -2, -1, 1, 2, 3, 5, 10])
            if cand != value and cand > 0:
                return cand
            continue
        how = rng.choices(["factor", "swap", "unit"], weights=[5, 3, 2])[0]
        if how == "factor":
            cand = round(value * rng.choice([0.75, 0.8, 0.9, 1.1, 1.2, 1.25, 1.5]))
        elif how == "swap":
            cand = swap_digits(value, rng)
        else:
            cand = value * 10 if rng.random() < 0.5 else (value // 10 if value % 10 == 0 else None)
        if cand and cand > 0 and abs(cand - value) >= 0.05 * value:
            return cand
    raise ValueError("no false twin for %r" % value)


def cohen_kappa(a, b):
    """kappa of two equally long label lists"""
    n = len(a)
    if n == 0:
        return float("nan")
    cats = sorted(set(a) | set(b))
    po = sum(1 for x, y in zip(a, b) if x == y) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


# ---------------------------------------------------------------- network
def http_json(url, headers=None, tries=4):
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=dict({"User-Agent": UA}, **(headers or {})))
            return json.load(urllib.request.urlopen(req, timeout=60))
        except Exception as e:                       # network trouble: wait and try again
            last = e
            time.sleep(1.5 * (k + 1))
    raise RuntimeError("request failed: %s (%s)" % (url[:120], last))


# ---------------------------------------------------------------- VitaminC
def vitaminc_cases(n_groups, seed, pages):
    rng = random.Random(f"vitaminc:{seed}")
    q = dict(dataset="tals/vitaminc", config="default", split="test", length=100)
    first = http_json(HF + "?" + urllib.parse.urlencode(dict(q, offset=0)))
    total = first["num_rows_total"]
    offsets = sorted(rng.sample(range(0, total - 100, 100), min(pages, total // 100 - 1)))
    groups = {}
    for off in offsets:
        rows = http_json(HF + "?" + urllib.parse.urlencode(dict(q, offset=off)))["rows"]
        time.sleep(0.3)
        ids = [r["row"]["case_id"] for r in rows]
        edge = {ids[0], ids[-1]}                      # groups cut by the page border are incomplete
        for r in rows:
            x = r["row"]
            if x["case_id"] in edge:
                continue
            if re.search(r"\d", x["claim"]) and re.search(r"\d", x["evidence"]):
                groups.setdefault(str(x["case_id"]), []).append(x)
    usable = {g: rs for g, rs in groups.items() if len({r["label"] for r in rs}) >= 2
              and any(r["label"] in ("SUPPORTS", "REFUTES") for r in rs)}
    chosen = rng.sample(sorted(usable), min(n_groups, len(usable)))
    cases = []
    for g in chosen:
        pair = "vc-" + g
        for r in usable[g]:
            lab = r["label"]
            case = {"id": "vc-%s" % r["unique_id"],
                    "tags": ["number", "evidence", {"SUPPORTS": "true", "REFUTES": "false", "NOT ENOUGH INFO": "abstain"}[lab],
                             "pair:" + pair, "family:wikipedia-revision", "source:vitaminc", "labelsrc:vitaminc", "label:people", REQ_TAG],
                    "input": {"claim": clean_text(r["claim"]), "evidence": clean_text(r["evidence"]), "rounds": 3, "experts": []},
                    "pair": pair}
            if lab == "NOT ENOUGH INFO":
                case.update({"truth": None, "expect": "inconclusive", "note": "VitaminC: not enough information in the evidence"})
            else:
                case.update({"truth": lab == "SUPPORTS", "note": "VitaminC, Wikipedia revision %s" % r["wiki_revision_id"]})
            cases.append(case)
    return cases


# ---------------------------------------------------------------- Wikidata
FAMILIES = [
    # name, query, claim template, kind, divisor of the Wikidata amount
    ("mountain-height", """SELECT ?item ?itemLabel ?v WHERE { ?item wdt:P31 wd:Q8502; wikibase:sitelinks ?l; p:P2048/psn:P2048/wikibase:quantityAmount ?v .
        FILTER(?l > 40) FILTER(?v = FLOOR(?v)) SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } LIMIT 300""",
     "{label} is {n} metres high.", "quantity", 1),
    ("tower-height", """SELECT ?item ?itemLabel ?v WHERE { VALUES ?cls { wd:Q12518 wd:Q11303 } ?item wdt:P31 ?cls; wikibase:sitelinks ?l; p:P2048/psn:P2048/wikibase:quantityAmount ?v .
        FILTER(?l > 12) FILTER(?v = FLOOR(?v)) SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } LIMIT 300""",
     "{label} is {n} metres tall.", "quantity", 1),
    ("river-length", """SELECT ?item ?itemLabel ?v WHERE { ?item wdt:P31 wd:Q4022; wikibase:sitelinks ?l; p:P2043/psn:P2043/wikibase:quantityAmount ?v .
        FILTER(?l > 25) FILTER(?v/1000 = FLOOR(?v/1000)) SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } LIMIT 300""",
     "The {label} is {n} kilometres long.", "quantity", 1000),
    ("bridge-year", """SELECT ?item ?itemLabel ?v WHERE { ?item wdt:P31 wd:Q12280; wikibase:sitelinks ?l; p:P571/psv:P571 ?node .
        ?node wikibase:timeValue ?t; wikibase:timePrecision 9 . BIND(YEAR(?t) AS ?v) FILTER(?l > 12)
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en". } } LIMIT 300""",
     "{label} was built in {n}.", "year", 1),
]


def wikidata_cases(n_pairs, seed):
    rng = random.Random(f"wikidata:{seed}")
    pool = []
    for name, query, template, kind, div in FAMILIES:
        url = WDQS + "?" + urllib.parse.urlencode({"query": query, "format": "json"})
        data = http_json(url, {"Accept": "application/sparql-results+json"})
        time.sleep(1.0)
        seen = set()
        for b in data["results"]["bindings"]:
            qid = b["item"]["value"].rsplit("/", 1)[-1]
            label = b["itemLabel"]["value"]
            if qid in seen or re.fullmatch(r"Q\d+", label):
                continue
            seen.add(qid)
            v = int(round(float(b["v"]["value"]) / div))
            if v > 0:
                pool.append((name, template, kind, qid, label, v))
    rng.shuffle(pool)
    per_family = {}
    cases = []
    for name, template, kind, qid, label, v in pool:
        if len(cases) >= 2 * n_pairs:
            break
        if per_family.get(name, 0) >= max(1, n_pairs // len(FAMILIES) + 2):
            continue
        r = random.Random(f"{seed}:{qid}:{name}")
        try:
            wrong = false_twin(v, r, kind)
        except ValueError:
            continue
        per_family[name] = per_family.get(name, 0) + 1
        fmt = (lambda n: str(n)) if kind == "year" else (lambda n: f"{n:,}")
        pair = f"wd-{qid}-{name}"
        for truth, value, suffix in ((True, v, "true"), (False, wrong, "false")):
            cases.append({"id": f"{pair}-{suffix}",
                          "tags": ["number", "true" if truth else "false"] + ([] if truth else ["trap"]) +
                                  ["pair:" + pair, "family:" + name, "source:wikidata", "labelsrc:wikidata", "label:people", REQ_TAG],
                          "input": {"claim": template.format(label=label, n=fmt(value)), "evidence": "", "rounds": 3, "experts": []},
                          "truth": truth, "pair": pair,
                          "note": "Wikidata %s: %s = %s" % (qid, name, fmt(v))})
    return cases


# ---------------------------------------------------------------- writing
def write_suites(out, base, cases, description):
    dev, hold = [], []
    for c in cases:
        c = dict(c)
        pair = c.pop("pair")
        holdout = is_holdout(pair)
        c["tags"] = sorted(set(c["tags"] + ["split:holdout" if holdout else "split:dev"]))
        (hold if holdout else dev).append(c)
    for name, rows in ((base, dev), (base + ".holdout", hold)):
        d = out / "suites" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "suite.json").write_text(json.dumps({"name": name, "description": description, "target": TARGET}, indent=1) + "\n", encoding="utf8")
        (d / "cases.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf8")
    return dev, hold


def write_audit(out, all_cases, seed, share=0.2):
    rng = random.Random(f"audit:{seed}")
    pairs = sorted({c["tags"][[t.startswith("pair:") for t in c["tags"]].index(True)][5:] for c in all_cases})
    picked = set(rng.sample(pairs, max(1, int(len(pairs) * share))))
    picked_cases = []
    for c in all_cases:
        pair = next(t[5:] for t in c["tags"] if t.startswith("pair:"))
        if pair in picked:
            picked_cases.append(c)
    rng.shuffle(picked_cases)
    rows, key = [], {}
    for k, c in enumerate(picked_cases, 1):
        sid = "s%03d" % k                      # opaque id: the case ids of the Wikidata pairs end in -true or -false
        rows.append((sid, c["input"]["claim"], c["input"]["evidence"]))
        key[sid] = {"case": c["id"], "truth": "unknown" if c["truth"] is None else ("true" if c["truth"] else "false")}
    (out / "audit").mkdir(parents=True, exist_ok=True)
    with open(out / "audit" / "sample_sheet.csv", "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(["id", "claim", "evidence", "label (true / false / unknown)", "source or note"])
        for r in rows:
            w.writerow(list(r) + ["", ""])
    (out / "audit" / "key.json").write_text(json.dumps(key, indent=1), encoding="utf8")
    (out / "audit" / "README.txt").write_text(
        "Blind audit sheet. Fill the column 'label (true / false / unknown)' of sample_sheet.csv.\n"
        "- If the row has evidence: judge the claim from that evidence only, not from what you know. 'unknown' = the evidence does not decide it.\n"
        "- If the row has no evidence: judge it from a reliable source and write the source into the last column. 'unknown' = you cannot find out.\n"
        "Do not open key.json before you are done. Then: python3 -I tools/label_agreement.py audit/sample_sheet.csv audit/key.json\n", encoding="utf8")
    return len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--source", choices=["vitaminc", "wikidata", "both"], default="both")
    ap.add_argument("--out", default="data/eval-external")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--n-vitaminc", type=int, default=60, help="contrastive groups to draw (about 3 cases each)")
    ap.add_argument("--vitaminc-pages", type=int, default=40, help="pages of 100 rows to read")
    ap.add_argument("--n-wikidata", type=int, default=80, help="true/false pairs")
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out)
    manifest = {"seed": a.seed, "made": time.strftime("%Y-%m-%d"), "sources": {}}
    all_cases = []
    if a.source in ("vitaminc", "both"):
        cs = vitaminc_cases(a.n_vitaminc, a.seed, a.vitaminc_pages)
        dev, hold = write_suites(out, "verdicts_vitaminc", cs,
                                 "Claims with number-bearing Wikipedia evidence and contrastive revisions (VitaminC, CC BY-SA 3.0): SUPPORTS true, REFUTES false, NOT ENOUGH INFO no verdict. Labels by the benchmark's annotators.")
        manifest["sources"]["vitaminc"] = {"licence": "CC BY-SA 3.0", "dev": len(dev), "holdout": len(hold), "ids_sha1": hashlib.sha1("".join(sorted(c["id"] for c in cs)).encode()).hexdigest()}
        all_cases += cs
    if a.source in ("wikidata", "both"):
        cs = wikidata_cases(a.n_wikidata, a.seed)
        dev, hold = write_suites(out, "verdicts_wikidata", cs,
                                 "Near-miss number claims without evidence: a true value from Wikidata (CC0) and a false twin made by a seeded rule (factor, swapped digits, unit off by 10, year off).")
        manifest["sources"]["wikidata"] = {"licence": "CC0", "dev": len(dev), "holdout": len(hold), "ids_sha1": hashlib.sha1("".join(sorted(c["id"] for c in cs)).encode()).hexdigest()}
        all_cases += cs
    manifest["audit_rows"] = write_audit(out, all_cases, a.seed)
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf8")
    print(json.dumps(manifest, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
