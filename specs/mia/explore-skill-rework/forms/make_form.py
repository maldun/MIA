"""Builds example-cases.html from the quality-notion table of the HLS: the rows still "to be confirmed" (and the empty one).
usage: python3 -I make_form.py   (run from anywhere; paths are relative to this file)"""
import html, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
HLS = (HERE.parent.parent / "high-level-spec.md").read_text()
sec = HLS[HLS.index("### Quality notion"):HLS.index("### Model and hardware envelope")]
cases = []
for line in sec.split("\n"):
    if not line.startswith("| ") or line.startswith("| Kind") or line.startswith("|---"):
        continue
    cells = [c.strip() for c in line.strip().strip("|").split("|")]
    if len(cells) < 4:
        continue
    if "to be confirmed" in cells[3] or "missing" in cells[2]:
        cases.append(dict(id=f"EX-{len(cases) + 1:02d}", kind=cells[0], input=cells[1], right=cells[2], note=cells[3]))


def md(t):
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", html.escape(t))


cards = "\n".join(f"""<section class="card" data-id="{c['id']}">
<h2>{c['id']} · {md(c['kind'])}</h2>
<p><span class="k">Input / situation</span><br>{md(c['input'])}</p>
<p><span class="k">What a right result looks like (edit if wrong)</span></p>
<textarea name="right" rows="3">{html.escape(c['right'])}</textarea>
<p class="opts"><label><input type="radio" name="d-{c['id']}" value="ok"> ok as written</label>
<label><input type="radio" name="d-{c['id']}" value="change"> change (see text above)</label>
<label><input type="radio" name="d-{c['id']}" value="drop"> drop this case</label></p>
<input class="note" name="comment" placeholder="comment (optional)">
</section>""" for c in cases)

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Example cases to confirm</title>
<style>
:root{--bg:#fff;--fg:#1d2330;--card:#f4f6fa;--line:#c9d0dc;--acc:#2a5bd7}
@media(prefers-color-scheme:dark){:root{--bg:#141821;--fg:#e6e9f0;--card:#1e2430;--line:#38405a;--acc:#7ea2ff}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:760px;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:14px 0}
h1{font-size:1.3rem}h2{font-size:1rem;margin:0 0 6px}.k{font-size:.8rem;opacity:.7}
textarea,.note{width:100%;box-sizing:border-box;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:6px;font:inherit}
.opts label{margin-right:14px;white-space:nowrap}button{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:10px 16px;font:inherit;cursor:pointer}
#bar{position:sticky;bottom:0;background:var(--bg);padding:10px 0;border-top:1px solid var(--line)}
</style></head><body>
<h1>Example cases to confirm</h1>
<p>__N__ cases from the quality notion (HLS section 4). Pick one option per case, edit the right-result text where it is wrong.
Your answers stay in this browser until you press <b>Save as file</b>; hand the file back to the agent.</p>
__CARDS__
<div id="bar"><button id="save">Save as file</button> <span id="count"></span></div>
<script>
const KEY="mia-example-cases";
const cards=[...document.querySelectorAll('.card')];
function collect(){return cards.map(c=>({id:c.dataset.id,
 decision:(c.querySelector('input[type=radio]:checked')||{}).value||null,
 right:c.querySelector('textarea').value,comment:c.querySelector('.note').value}));}
function store(){try{localStorage.setItem(KEY,JSON.stringify(collect()))}catch(e){}
 const done=collect().filter(x=>x.decision).length;document.getElementById('count').textContent=done+' of '+cards.length+' decided';}
try{(JSON.parse(localStorage.getItem(KEY)||'[]')).forEach(s=>{const c=cards.find(x=>x.dataset.id===s.id);if(!c)return;
 c.querySelector('textarea').value=s.right;c.querySelector('.note').value=s.comment||'';
 if(s.decision){const r=c.querySelector('input[value='+s.decision+']');if(r)r.checked=true;}})}catch(e){}
document.addEventListener('input',store);store();
document.getElementById('save').onclick=()=>{const a=document.createElement('a');
 a.href=URL.createObjectURL(new Blob([JSON.stringify(collect(),null,1)],{type:'application/json'}));
 a.download='example-cases-answers.json';a.click();};
</script></body></html>"""
out = HERE / "example-cases.html"
out.write_text(PAGE.replace("__N__", str(len(cases))).replace("__CARDS__", cards))
(HERE / "example-cases-source.json").write_text(json.dumps(cases, indent=1))
print(len(cases), "cases ->", out)
