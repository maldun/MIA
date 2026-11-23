"""Builds the marking page of an NFR-23 sample (plan: specs/mia/goals/G-V4.BUILDER/nfr23-sample-plan.md, section 4).
Sample A: definitions and facts (option_df.py, light model); sample B: entities and relations (option1.py, full model).
Draw: seed 20261123, per document in file-name order shuffle the accepted proposals and take up to the per-document
counts, top up from the rest (pooled, shuffled) to 120, show in one random order. The page is the one of
make_marking.py; the tally shows the NFR-23 rule. Answers are saved as nfr23-<a|b>-marks.json for score_marks.py.
usage: python3 -I make_marking_nfr23.py A|B RUNDIR OUT.html"""
import html, json, random, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SEED, TARGET = 20261123, 120
SAMPLES = {"A": dict(per_doc={"definition": 5, "fact": 5}, prefix="DF", title="definitions and stated facts", model="gemma4:12b-it-qat"),
           "B": dict(per_doc={"entity": 6, "relation": 4}, prefix="IR", title="items and relations", model="gemma4:26b")}


def draw(runs, per_doc, rng, target=TARGET):
    """runs: [(doc, [accepted proposals])] in file-name order. Returns [(doc, proposal)]: per document up to the per-kind
    counts, then topped up from the rest to `target`, then shuffled into one order."""
    picked, rest = [], []
    for doc, accepted in runs:
        pool = list(accepted)
        rng.shuffle(pool)
        taken = {kind: 0 for kind in per_doc}
        for p in pool:
            if taken.get(p["kind"], 99) < per_doc.get(p["kind"], 0):
                taken[p["kind"]] += 1
                picked.append((doc, p))
            else:
                rest.append((doc, p))
    rng.shuffle(rest)
    picked += rest[:max(0, target - len(picked))]
    rng.shuffle(picked)
    return picked


def head(p):
    return {"entity": lambda: p["name"], "relation": lambda: f"{p['source']}  —  {p['target']}  [{p['relation']}]",
            "definition": lambda: f"{p['term']}: {p['definition']}", "fact": lambda: p["statement"]}[p["kind"]]()


def names(p):
    return {"entity": [p.get("name", "")], "relation": [p.get("source", ""), p.get("target", "")],
            "definition": [p.get("term", "")], "fact": []}[p["kind"]]


def context(doc_text, quote):
    q = " ".join(quote.split()).casefold()
    for para in re.split(r"\n\s*\n", doc_text):
        p = " ".join(para.split())
        if q[:60] in p.casefold():
            return p
    return ""


def mark(text, words):
    t = html.escape(text)
    for n in sorted({n for n in words if len(n) > 2}, key=len, reverse=True):
        t = re.sub("(?i)(" + re.escape(html.escape(n)) + ")", r"<mark>\1</mark>", t)
    return t


TALLY = """function tally(){const d=cards.map(c=>(c.querySelector('input[type=radio]:checked')||{}).value).filter(Boolean),n=d.length;
 const r=d.filter(x=>x==='right').length,k=d.filter(x=>x==='invented').length;
 document.getElementById('count').textContent+=' | right '+r+', invented '+k+' | NFR-23: at least 120 marked, at most 4 invented and at least 91 right'+
  (n>=120?(k<=4&&r>=91?' -> met':' -> not met'):' (not decided before 120)');}
document.addEventListener('input',()=>{store();tally();});store();tally();"""


def page(sample, items, n_docs):
    s = SAMPLES[sample]
    tpl = re.search(r'PAGE = """(.*?)"""\n', (HERE / "make_marking.py").read_text(), re.S).group(1)
    tpl = (tpl.replace("Spike C: mark the extracted items", f"NFR-23 sample {sample}: mark the proposed {s['title']}")
           .replace("(LightRAG, gemma4:12b-it-qat, num_ctx 8192)", f"(own builder, {s['model']}, num_ctx 8192; the model's quote is shown on each card)")
           .replace("document.addEventListener('input',store);store();", TALLY)
           .replace("mia-spike-c-marking", f"mia-nfr23-{sample.lower()}-marking")
           .replace("spike-c-marks.json", f"nfr23-{sample.lower()}-marks.json"))
    cards = ['<p class="miss"><label>Important things the texts say that are missing (optional, name the document): '
             '<input data-doc="all" class="missing" placeholder="short note or empty"></label></p>']
    for it in items:
        cards.append(f"""<section class="card" data-id="{it['id']}">
<h3>{it['id']} · {html.escape(it['doc'])} · {it['kind']}: {html.escape(it['head'])}</h3>
<p class="desc">Model's quote: “{html.escape(it['quote'])}”</p>
<details><summary>Source passage</summary><div class='src'>{it['source']}</div></details>
<p class="opts"><label><input type="radio" name="d-{it['id']}" value="right"> right</label>
<label><input type="radio" name="d-{it['id']}" value="trivial"> right but useless</label>
<label><input type="radio" name="d-{it['id']}" value="wrong"> wrong (text says otherwise)</label>
<label><input type="radio" name="d-{it['id']}" value="invented"> invented (not in the text)</label></p>
<input class="note" placeholder="comment (optional)"></section>""")
    meta = [dict(id=i["id"], doc=i["doc"], kind=i["kind"], key=i["key"]) for i in items]
    return (tpl.replace("__N__", str(len(items))).replace("__D__", str(n_docs))
            .replace("__CARDS__", "\n".join(cards)).replace("__META__", json.dumps(meta)))


def main(argv):
    sample, run, out = argv[1], Path(argv[2]), Path(argv[3])
    s = SAMPLES[sample]
    texts = {p.stem: p.read_text() for d in ("docs", "docs-n6") for p in sorted((HERE / d).glob("*.txt"))}
    runs = [(f.stem, json.loads(f.read_text())["accepted"]) for f in sorted(run.glob("*.json"))]
    drawn = draw(runs, s["per_doc"], random.Random(SEED))
    items = [dict(id=f"{s['prefix']}{n:03d}", doc=doc, kind=p["kind"], key=names(p), head=head(p), quote=p["quote"],
                  source=mark(context(texts[doc], p["quote"]) or p["quote"], names(p)))
             for n, (doc, p) in enumerate(drawn, start=1)]
    out.write_text(page(sample, items, len(runs)))
    short = "" if len(items) >= TARGET else f" (SHORT of {TARGET}: NFR-23 cannot be decided on this sample)"
    print(f"sample {sample}: {len(items)} cards from {len(runs)} documents{short} -> {out}")


if __name__ == "__main__":
    main(sys.argv)
