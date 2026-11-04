"""Builds the marking page of spike C: a sample of the items LightRAG extracted, each with its source passage.
usage: <venv>/bin/python make_marking.py RUNDIR OUT.html [items_per_doc=20]
RUNDIR holds rep1/<doc>/ rep2/ rep3/ (working dirs of run_spike.py). Sampling is fixed (seed 1) and uses rep1;
the other repeats only supply a stability number that is stored in the answer file, not shown."""
import html, json, random, re, sys
from pathlib import Path
import networkx as nx

run, out = Path(sys.argv[1]), Path(sys.argv[2])
per_doc = int(sys.argv[3]) if len(sys.argv) > 3 else 20
rng = random.Random(1)


def load(rep, doc):
    d = run / rep / doc
    g = d / "graph_chunk_entity_relation.graphml"
    if not g.exists():
        return None, {}
    chunks = json.loads((d / "kv_store_text_chunks.json").read_text())
    return nx.read_graphml(g), {k: v["content"] for k, v in chunks.items()}


def mark(text, names):
    t = html.escape(text)
    for n in sorted({n for n in names if len(n) > 2}, key=len, reverse=True):
        t = re.sub("(?i)(" + re.escape(html.escape(n)) + ")", r"<mark>\1</mark>", t)
    return t


docs = sorted(p.name for p in (run / "rep1").iterdir() if p.is_dir())
items = []
for doc in docs:
    G, chunks = load("rep1", doc)
    others = [load(r, doc)[0] for r in ("rep2", "rep3")]
    cand = [("entity", n, d) for n, d in G.nodes(data=True)] + [("relation", (a, b), d) for a, b, d in G.edges(data=True)]
    rng.shuffle(cand)
    nodes = [c for c in cand if c[0] == "entity"][:max(per_doc * 6 // 10, 1)]
    rels = [c for c in cand if c[0] == "relation"][:per_doc - len(nodes)]
    for kind, key, d in nodes + rels:
        names = [key] if kind == "entity" else list(key)
        src = [chunks[c] for c in d.get("source_id", "").split("<SEP>") if c in chunks]
        if kind == "entity":
            stab = sum(1 for o in others if o is not None and key in o)
            head, body = f"{key}  ({d.get('entity_type', '')})", d.get("description", "")
        else:
            stab = sum(1 for o in others if o is not None and (o.has_edge(*key) or o.has_edge(key[1], key[0])))
            head, body = f"{key[0]}  —  {key[1]}  [{d.get('keywords', '')}]", d.get("description", "")
        items.append(dict(id=f"I{len(items) + 1:03d}", doc=doc, kind=kind, key=list(names), stable=stab,
                          head=head, body=body, source=[mark(s, names) for s in src]))

cards = []
last = None
for it in items:
    if it["doc"] != last:
        last = it["doc"]
        cards.append(f'<h2 class="doc">{html.escape(last)}</h2><p class="miss"><label>Important things the text says that are missing from the items: '
                     f'<input data-doc="{html.escape(last)}" class="missing" placeholder="short note or empty"></label></p>')
    src = "".join(f"<div class='src'>{s}</div>" for s in it["source"]) or "<div class='src'>(no source passage found)</div>"
    cards.append(f"""<section class="card" data-id="{it['id']}">
<h3>{it['id']} · {it['kind']}: {html.escape(it['head'])}</h3>
<p class="desc">{html.escape(it['body'])}</p>
<details><summary>Source passage</summary>{src}</details>
<p class="opts"><label><input type="radio" name="d-{it['id']}" value="right"> right</label>
<label><input type="radio" name="d-{it['id']}" value="trivial"> right but useless</label>
<label><input type="radio" name="d-{it['id']}" value="wrong"> wrong (text says otherwise)</label>
<label><input type="radio" name="d-{it['id']}" value="invented"> invented (not in the text)</label></p>
<input class="note" placeholder="comment (optional)"></section>""")

meta = [dict(id=i["id"], doc=i["doc"], kind=i["kind"], key=i["key"], stable=i["stable"]) for i in items]
PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Spike C: mark the extracted items</title>
<style>
:root{--bg:#fff;--fg:#1d2330;--card:#f4f6fa;--line:#c9d0dc;--acc:#2a5bd7;--mark:#ffe58a}
@media(prefers-color-scheme:dark){:root{--bg:#141821;--fg:#e6e9f0;--card:#1e2430;--line:#38405a;--acc:#7ea2ff;--mark:#6b5a00}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:800px;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:8px 16px;margin:10px 0}
h1{font-size:1.3rem}h2.doc{font-size:1.1rem;margin-top:28px;border-bottom:1px solid var(--line)}h3{font-size:.95rem;margin:6px 0}
.desc{margin:4px 0}.src{max-height:11em;overflow:auto;white-space:pre-wrap;font-size:.85rem;padding:6px;border-left:3px solid var(--line);margin:6px 0}
mark{background:var(--mark);color:inherit}.opts label{margin-right:12px;white-space:nowrap}
.note,.missing{width:100%;box-sizing:border-box;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:6px;font:inherit}
button{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:10px 16px;font:inherit;cursor:pointer}
#bar{position:sticky;bottom:0;background:var(--bg);padding:10px 0;border-top:1px solid var(--line)}
</style></head><body>
<h1>Spike C: mark the extracted items</h1>
<p>__N__ items sampled from __D__ documents (LightRAG, gemma4:12b-it-qat, num_ctx 8192). Open <b>Source passage</b>; the item's names are highlighted.
<b>right</b> = the text supports it. <b>right but useless</b> = true but not worth keeping in a context graph. <b>wrong</b> = the text says something else.
<b>invented</b> = the text does not say it. Per document, note anything important that is missing. Answers stay in this browser until you press <b>Save as file</b>.</p>
__CARDS__
<div id="bar"><button id="save">Save as file</button> <span id="count"></span></div>
<script>
const META=__META__, KEY="mia-spike-c-marking";
const cards=[...document.querySelectorAll('.card')], miss=[...document.querySelectorAll('.missing')];
function collect(){return {items:cards.map(c=>({...META.find(m=>m.id===c.dataset.id),
  decision:(c.querySelector('input[type=radio]:checked')||{}).value||null,comment:c.querySelector('.note').value})),
  missing:miss.map(m=>({doc:m.dataset.doc,note:m.value}))};}
function store(){const s=collect();try{localStorage.setItem(KEY,JSON.stringify(s))}catch(e){}
 document.getElementById('count').textContent=s.items.filter(x=>x.decision).length+' of '+cards.length+' marked';}
try{const s=JSON.parse(localStorage.getItem(KEY)||'null');if(s){s.items.forEach(x=>{const c=cards.find(k=>k.dataset.id===x.id);if(!c)return;
 c.querySelector('.note').value=x.comment||'';if(x.decision){const r=c.querySelector('input[value='+x.decision+']');if(r)r.checked=true;}});
 s.missing.forEach(x=>{const m=miss.find(k=>k.dataset.doc===x.doc);if(m)m.value=x.note;});}}catch(e){}
document.addEventListener('input',store);store();
document.getElementById('save').onclick=()=>{const a=document.createElement('a');
 a.href=URL.createObjectURL(new Blob([JSON.stringify(collect(),null,1)],{type:'application/json'}));a.download='spike-c-marks.json';a.click();};
</script></body></html>"""
out.write_text(PAGE.replace("__N__", str(len(items))).replace("__D__", str(len(docs)))
               .replace("__CARDS__", "\n".join(cards)).replace("__META__", json.dumps(meta)))
print(len(items), "items,", len(docs), "documents ->", out)
