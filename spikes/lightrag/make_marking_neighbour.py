"""Marking page for the neighbour rule (FR-42 candidate): 20 relations that option1.py refused for 'quote does not contain
both ends' but whose ends both occur in the quote and its two neighbouring sentences, fixed seed. Shown: the relation, the
model's quote and the three-sentence window. Same page and answer format as make_marking_n6.py.
usage: python3 -I make_marking_neighbour.py DOCS_DIR OUT.html RUNDIR:DOCSDIR... (rundirs of option1.py)"""
import html, json, random, re, sys
from pathlib import Path

out = Path(sys.argv[1]); pairs = [a.split(':') for a in sys.argv[2:]]; N = 20
sys.path.insert(0, str(Path(__file__).resolve().parent))
from option1 import split_sentences
from checks import norm, relation_in_source
rng = random.Random(20261108)  # seed fixed before the draw (n6-sample-plan.md, neighbour rule)
TALLY = """function tally(){const d=cards.map(c=>(c.querySelector('input[type=radio]:checked')||{}).value).filter(Boolean),n=d.length;
 const r=d.filter(x=>x==='right').length,k=d.filter(x=>x==='invented').length;let t='';
 if(n>=10){const p=r/n,s=Math.sqrt(p*(1-p)/n),z=1.645,q=k/n,up=(q+z*z/(2*n)+z*Math.sqrt(q*(1-q)/n+z*z/(4*n*n)))/(1+z*z/n);
  const okR=p-s>=0.68,okI=up<=0.05,bad=p+s<0.68||(k/n-Math.sqrt(q*(1-q)/n))>0.05;
  t=' | right '+(100*p).toFixed(0)+' % (1 sigma: '+(100*(p-s)).toFixed(0)+' to '+(100*(p+s)).toFixed(0)+' %), invented '+k+' (95 % upper bound '+(100*up).toFixed(1)+' %)'+
   ' | rule: at most 5 % invented; right at least 68 %';}
 document.getElementById('count').textContent+=t;}
document.addEventListener('input',()=>{store();tally();});store();tally();"""

here = Path(__file__).resolve().parent
PAGE = re.search(r'PAGE = """(.*?)"""\n', (here / "make_marking.py").read_text(), re.S).group(1)
PAGE = (PAGE.replace("Spike C: mark the extracted items", "N-6 neighbour rule: mark the relations the strict rule refused")
        .replace("(LightRAG, gemma4:12b-it-qat, num_ctx 8192)", "(own builder, gemma4:12b-it-qat, num_ctx 8192; the model's quote is shown on each card)")
        .replace("document.addEventListener('input',store);store();", TALLY)
        .replace("mia-spike-c-marking", "mia-n6-neighbour-marking").replace("spike-c-marks.json", "n6-neighbour-marks.json"))



def mark(text, names):
    t = html.escape(text)
    for n in sorted({n for n in names if len(n) > 2}, key=len, reverse=True):
        t = re.sub("(?i)(" + re.escape(html.escape(n)) + ")", r"<mark>\1</mark>", t)
    return t


cand = []
for run, docs in pairs:
    for f in sorted(Path(run).glob("*.json")):
        sents = list(split_sentences((Path(docs) / f"{f.stem}.txt").read_text()))
        ns = [norm(x) for x in sents]
        for r in json.loads(f.read_text())["refused"]:
            it = r["item"]
            if r["reason"] != "quote does not contain both ends":
                continue
            q = norm(it["quote"])
            i = next((k for k, x in enumerate(ns) if q in x or x in q), None)
            if i is None:
                continue
            win = " ".join(sents[max(0, i - 1): i + 2])
            if relation_in_source(it["source"], it["target"], [win]):
                cand.append((f.stem, it, win))
print(len(cand), "candidates; drawing", N)
cand.sort(key=lambda c: (c[0], c[1]["source"], c[1]["relation"], c[1]["target"]))  # stable order before the seeded draw
items = []
for d, it, win in rng.sample(cand, N):
    names = [it["source"], it["target"]]
    items.append(dict(id=f"R{len(items) + 1:03d}", doc=d, kind="relation", key=names,
                      head=f"{it['source']}  \u2014  {it['target']}  [{it['relation']}]", quote=it["quote"], source=mark(win, names)))
cards = ['<p class="miss"><label>Notes (optional): <input data-doc="all" class="missing" placeholder="short note or empty"></label></p>']
for it in items:
    cards.append(f"""<section class="card" data-id="{it['id']}">
<h3>{it['id']} \u00b7 {html.escape(it['doc'])} \u00b7 relation: {html.escape(it['head'])}</h3>
<p class="desc">Model's quote: \u201c{html.escape(it['quote'])}\u201d (the strict rule refused it: the quote lacks one end)</p>
<details open><summary>Quote with its neighbouring sentences</summary><div class='src'>{it['source']}</div></details>
<p class="opts"><label><input type="radio" name="d-{it['id']}" value="right"> right</label>
<label><input type="radio" name="d-{it['id']}" value="trivial"> right but useless</label>
<label><input type="radio" name="d-{it['id']}" value="wrong"> wrong (text says otherwise)</label>
<label><input type="radio" name="d-{it['id']}" value="invented"> invented (not in the text)</label></p>
<input class="note" placeholder="comment (optional)"></section>""")
meta = [dict(id=i["id"], doc=i["doc"], kind=i["kind"], key=i["key"]) for i in items]
out.write_text(PAGE.replace("__N__", str(len(items))).replace("__D__", str(len({i["doc"] for i in items})))
               .replace("__CARDS__", "\n".join(cards)).replace("__META__", json.dumps(meta)))
print(len(items), "items ->", out)
