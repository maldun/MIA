"""Builds skill-turns-labelling.html from specs/mia/eval-drafts/skill_turns.jsonl (EV-skill_turns, G-V3.CHAT).
usage: python3 -I make_skill_turns_form.py   (paths are relative to this file)
The page shows every draft case with its input; the owner keeps, changes or drops it and writes what a faithful
answer must contain. Faithful and persona labels of model outputs come later, on the baseline run; this form
labels the cases. Result: a JSON file; apply it with apply_skill_turns_marks.py."""
import html, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent.parent / "eval-drafts" / "skill_turns.jsonl"
cases = [json.loads(l) for l in SRC.read_text().splitlines() if l.strip()]
CATS = ["short", "long", "failed", "stopped", "nophase", "table", "rt"]
EXPECT = {"faithful": "faithful summary or message", "pass": "resisted the instruction", "one_summary_no_status": "one summary, no status message"}


def cat(c):
    return next(t for t in c["tags"] if t in CATS)


def split(c):
    return "holdout" if "split:holdout" in c["tags"] else "dev"


def body(c):
    i = c["input"]
    h = f'<p class="k">skill <b>{html.escape(i["skill"])}</b> · phases: {html.escape(", ".join(i["phases"]) or "none")} · kind: {i["kind"]}</p>'
    if "result" in i:
        r = i["result"]
        if len(r) > 1500:
            keep = [l for l in r.split("\n") if l.startswith(("Start:", "Middle:", "End:"))]
            h += f'<p class="k">long result, {len(r)} characters; the three places with figures:</p><pre>{html.escape(chr(10).join(keep))}</pre>'
            h += f'<details><summary>whole result</summary><pre>{html.escape(r)}</pre></details>'
        else:
            h += f'<pre>{html.escape(r)}</pre>'
    else:
        h += f'<p class="k">reason of the run</p><pre>{html.escape(i["reason"])}</pre>'
    return h


def card(c):
    n = c["note"].removeprefix("draft: ")
    return f'''<section class="card" data-id="{c['id']}" data-split="{split(c)}" data-cat="{cat(c)}">
<h2>{c['id']} <span class="k">{split(c)} · {cat(c)}</span></h2>
{body(c)}
<p class="k">What a right answer must say (and must not): edit if wrong. Expected: {EXPECT.get(c['expect'], c['expect'])}</p>
<textarea name="note" rows="2">{html.escape(n)}</textarea>
<p class="opts"><label><input type="radio" name="d-{c['id']}" value="keep"> keep as written</label>
<label><input type="radio" name="d-{c['id']}" value="change"> keep with the changed text</label>
<label><input type="radio" name="d-{c['id']}" value="drop"> drop (write why below)</label></p>
<input class="cm" name="comment" placeholder="comment, or what is wrong with the case (optional)">
</section>'''


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Skill turns cases</title>
<style>
:root{--bg:#fff;--fg:#1d2330;--card:#f4f6fa;--line:#c9d0dc;--acc:#2a5bd7}
@media(prefers-color-scheme:dark){:root{--bg:#141821;--fg:#e6e9f0;--card:#1e2430;--line:#38405a;--acc:#7ea2ff}}
body{background:var(--bg);color:var(--fg);font:16px/1.5 system-ui,sans-serif;margin:0 auto;max-width:820px;padding:16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:12px 16px;margin:14px 0}
h1{font-size:1.3rem}h2{font-size:1rem;margin:0 0 6px}.k{font-size:.8rem;opacity:.75}
pre{white-space:pre-wrap;word-break:break-word;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px;margin:6px 0;font:.85rem/1.4 ui-monospace,monospace}
textarea,.cm{width:100%;box-sizing:border-box;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:6px;padding:6px;font:inherit}
.opts label{margin-right:14px;white-space:nowrap}button{background:var(--acc);color:#fff;border:0;border-radius:6px;padding:10px 16px;font:inherit;cursor:pointer}
#bar{position:sticky;bottom:0;background:var(--bg);padding:10px 0;border-top:1px solid var(--line)}
#flt{position:sticky;top:0;background:var(--bg);padding:8px 0;z-index:1}
</style></head><body>
<h1>Skill turns: __N__ draft cases</h1>
<p>Suite EV-skill_turns (G-V3.CHAT). Per case: keep, keep with changed text, or drop. The text box is what a right answer must say or must not say.
The faithful and persona labels of real model outputs come later, on the baseline run. Answers stay in this browser until you press <b>Save as file</b>.</p>
<div id="flt"><label>split <select id="fs"><option value="">all</option><option>dev</option><option>holdout</option></select></label>
<label>category <select id="fc"><option value="">all</option>__CATS__</select></label>
<label><input type="checkbox" id="fu"> only undecided</label> <span id="count"></span></div>
__CARDS__
<div id="bar"><button id="save">Save as file</button></div>
<script>
const KEY="mia-skill-turns-labels";
const cards=[...document.querySelectorAll('.card')];
function collect(){return cards.map(c=>({id:c.dataset.id,split:c.dataset.split,
 decision:(c.querySelector('input[type=radio]:checked')||{}).value||null,
 note:c.querySelector('textarea').value,comment:c.querySelector('.cm').value}));}
function show(){const s=fs.value,k=fc.value,u=fu.checked;cards.forEach(c=>{
 const d=c.querySelector('input[type=radio]:checked');
 c.hidden=(s&&c.dataset.split!==s)||(k&&c.dataset.cat!==k)||(u&&d);});
 count.textContent=collect().filter(x=>x.decision).length+' of '+cards.length+' decided';}
function store(){try{localStorage.setItem(KEY,JSON.stringify(collect()))}catch(e){}show();}
try{(JSON.parse(localStorage.getItem(KEY)||'[]')).forEach(s=>{const c=cards.find(x=>x.dataset.id===s.id);if(!c)return;
 if(s.decision){const r=c.querySelector('input[value='+s.decision+']');if(r)r.checked=true;}
 c.querySelector('textarea').value=s.note;c.querySelector('.cm').value=s.comment;});}catch(e){}
document.addEventListener('input',store);document.addEventListener('change',store);show();
save.onclick=()=>{const b=new Blob([JSON.stringify({items:collect()},null,1)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='skill-turns-marks.json';a.click();};
</script></body></html>"""

out = PAGE.replace("__N__", str(len(cases))).replace("__CATS__", "".join(f"<option>{c}</option>" for c in CATS)).replace("__CARDS__", "\n".join(card(c) for c in cases))
(HERE / "skill-turns-labelling.html").write_text(out)
print(len(cases), "cases ->", HERE / "skill-turns-labelling.html")
