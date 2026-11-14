"""Analysis of a run of option1b.py (throwaway, no model). Reads the run dir and, for the same documents, the option 1 run and the owner's marks.
usage: python3 -I analyze_option1b.py RUN1B_DIR RUN1_DIR MARKS.json [MARKS.json ...]
Prints: per document accepted/refused and the refusal reasons; how entities of option 1 fare in 1b (kept, dropped, new);
what the 1b rules would have decided on every ALREADY MARKED item that 1b proposes again (the real test: rules that
refuse invented/wrong marked items are a gain, rules that refuse right marked items are a cost); the accepted entities at the other limits
of `max_ungrounded` (read off the stored counts, no re-run; the pre-set limit is 0, nothing is tuned on the marks)."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import norm

run1b, run1 = Path(sys.argv[1]), Path(sys.argv[2])
marks = {}
for f in sys.argv[3:]:
    for m in json.loads(Path(f).read_text())["items"]:
        marks[(m["doc"], m["kind"], tuple(norm(k) for k in m["key"]))] = m["decision"]


def key(doc, p, kind):
    return (doc, kind, (norm(p["name"]),) if kind == "entity" else (norm(p["source"]), norm(p["target"])))


def category(reason):
    for start, name in (("quote is not a passage", "quote not in document"), ("name not in", "name not in document"),
                        ("quote does not contain", "quote lacks name/ends"), ("quote is not one whole", "not one whole sentence"),
                        ("entity has no description", "no description"), ("description uses", "description not grounded"),
                        ("model step failed", "model step failed")):
        if reason.startswith(start):
            return name
    return reason[:40]


docs = sorted(p.stem for p in run1b.glob("*.json"))
tot = Counter()
verdict = {}  # key -> "accepted" | reason category, for every proposal of 1b
ungr = []     # (accepted at limit 0?, reason category, ungrounded) of entities
print(f"{'document':32} {'chunks':>6} {'accepted':>8} {'refused':>7} {'s':>6}")
for d in docs:
    r = json.loads((run1b / f"{d}.json").read_text())
    print(f"{d:32} {r['chunks']:>6} {len(r['accepted']):>8} {len(r['refused']):>7} {r.get('seconds', 0):>6}")
    for a in r["accepted"]:
        verdict[key(d, a, a["kind"])] = "accepted"
        tot["accepted " + a["kind"]] += 1
        if a["kind"] == "entity":
            ungr.append(("accepted", a.get("ungrounded", 0)))
    for x in r["refused"]:
        item = x["item"]
        if "kind" not in item:
            tot["model step failed"] += 1
            continue
        c = category(x["reason"])
        verdict[key(d, item, item["kind"])] = c
        tot["refused: " + c] += 1
        if item["kind"] == "entity" and c == "description not grounded":
            ungr.append(("ungrounded", item.get("ungrounded", 99)))
print()
for k, v in sorted(tot.items()):
    print(f"  {k}: {v}")

print("\nentities of option 1 in option 1b:")
st = Counter()
for d in docs:
    f = run1 / f"{d}.json"
    if not f.exists():
        continue
    for a in json.loads(f.read_text())["accepted"]:
        if a["kind"] == "entity":
            st[verdict.get(key(d, a, "entity"), "not proposed again")] += 1
for k, v in st.most_common():
    print(f"  {k}: {v}")

print("\nowner's marks on items that 1b proposes again (rules of 1b on marked items):")
cross = defaultdict(Counter)
unseen = Counter()
for k, dec in marks.items():
    if k[0] not in docs:
        continue
    if k in verdict:
        cross[dec]["accepted" if verdict[k] == "accepted" else "refused: " + verdict[k]] += 1
    else:
        unseen[dec] += 1
for dec in ("right", "trivial", "wrong", "invented"):
    if cross[dec] or unseen[dec]:
        print(f"  marked {dec}: {dict(cross[dec])}" + (f"; not proposed by 1b: {unseen[dec]}" if unseen[dec] else ""))

print("\naccepted entities at other limits of max_ungrounded (pre-set limit: 0):")
base = sum(1 for s, _ in ungr if s == "accepted")
for L in (0, 1, 2, 3):
    print(f"  limit {L}: {base + sum(1 for s, u in ungr if s == 'ungrounded' and u <= L)} entities")
