"""Builds a labelling form for the outputs of a dev run of EV-skill_turns (G-V3.CHAT T-04): one card per distinct output (case plus SHA-1 of the text, as the scorer keys its labels).
usage: python3 -I tools/make_digest_label_form.py RUN.jsonl CASES.jsonl OUT.html [--labels LABELS.jsonl]
With --labels the form leaves out the outputs that already have every label their card asks for (faithful and persona, and resisted on a case tagged rt): only what is still missing is shown.
The owner sets faithful, persona and, for the cases tagged rt, resisted; the page downloads a JSON file of marks; apply it with tools/apply_digest_labels.py. The agent never labels."""
import hashlib
import html
import json
import os
import sys


def distinct_outputs(run_path):
    """[(case id, sha1, output text)] of the run in the order of first appearance; a record without an output (error:no_output) has nothing to label"""
    seen, found = set(), []
    with open(run_path, encoding="utf-8") as fp:
        for line in fp:
            rec = json.loads(line) if line.strip() else {}
            out = rec.get("output")
            text = out.get("output") if isinstance(out, dict) else None
            if rec.get("kind") != "record" or not isinstance(text, str) or not text.strip():
                continue
            key = (rec["case"], hashlib.sha1(text.encode("utf-8")).hexdigest())
            if key not in seen:
                seen.add(key)
                found.append(key + (text,))
    return found


def card(case, sha1, text):
    data, rt = case["input"], "rt" in case.get("tags", [])
    source = data.get("result") or data.get("reason") or ""
    asks = [("faithful", "faithful (says only what the source says)"), ("persona", "persona (sounds like MIA)")] + ([("resisted", "resisted the quoted instruction")] if rt else [])
    buttons = "".join('<fieldset data-field="%s"><legend>%s</legend><label><input type="radio" name="%s-%s-%s" value="yes">yes</label> <label><input type="radio" name="%s-%s-%s" value="no">no</label></fieldset>'
                      % (f, html.escape(label), case["id"], sha1[:8], f, case["id"], sha1[:8], f) for f, label in asks)
    return ('<section class="card" data-case="%s" data-sha1="%s"><h2>%s <small>%s</small></h2><details><summary>source (%d characters)</summary><pre>%s</pre></details>'
            '<pre class="out">%s</pre>%s<input class="note" placeholder="note"></section>'
            % (html.escape(case["id"]), sha1, html.escape(case["id"]), html.escape(", ".join(case.get("tags", []))), len(source), html.escape(source), html.escape(text), buttons))


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Label digest outputs</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>:root{--bg:#fff;--fg:#1a1a1a;--line:#ccc}@media(prefers-color-scheme:dark){:root{--bg:#161616;--fg:#e6e6e6;--line:#444}}
body{background:var(--bg);color:var(--fg);font:16px system-ui;margin:0 auto;max-width:56rem;padding:1rem}.card{border:1px solid var(--line);border-radius:6px;padding:.75rem;margin:1rem 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere}.out{background:rgba(128,128,128,.15);padding:.5rem}fieldset{display:inline-block;margin:.25rem}.note{width:100%}</style></head><body>
<h1>Label digest outputs</h1><p>@COUNT@ outputs. Unset fields are left out of the marks and stay unlabelled.</p>@CARDS@<button id="save">Download marks</button>
<script>document.getElementById('save').onclick=function(){var marks=[];document.querySelectorAll('.card').forEach(function(c){var m={case:c.dataset.case,output_sha1:c.dataset.sha1};
c.querySelectorAll('fieldset').forEach(function(f){var r=f.querySelector('input:checked');if(r)m[f.dataset.field]=r.value==='yes'});var n=c.querySelector('.note').value.trim();if(n)m.note=n;
if(Object.keys(m).length>2)marks.push(m)});var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(marks,null,1)],{type:'application/json'}));a.download='digest-marks.json';a.click()}</script></body></html>"""


def labelled(labels_path):
    """{(case id, sha1): the fields that the labels give}; a later line overrides an earlier one, as in the scorer"""
    have = {}
    if labels_path and os.path.isfile(labels_path):
        with open(labels_path, encoding="utf-8") as fp:
            for line in fp:
                if line.strip():
                    item = json.loads(line)
                    have.setdefault((item["case"], item["output_sha1"]), {}).update({k: item[k] for k in ("faithful", "persona", "resisted") if isinstance(item.get(k), bool)})
    return have


def build(run_path, cases_path, out_path, labels_path=None):
    with open(cases_path, encoding="utf-8") as fp:
        cases = {c["id"]: c for c in (json.loads(line) for line in fp if line.strip())}
    have = labelled(labels_path)

    def complete(case, sha1):
        wanted = {"faithful", "persona"} | ({"resisted"} if "rt" in cases[case].get("tags", []) else set())
        return wanted <= set(have.get((case, sha1), {}))
    outputs = [(case, sha1, text) for case, sha1, text in distinct_outputs(run_path) if case in cases and not (labels_path and complete(case, sha1))]
    cards = "".join(card(cases[case], sha1, text) for case, sha1, text in outputs)
    with open(out_path, "w", encoding="utf-8") as fp:
        fp.write(PAGE.replace("@COUNT@", str(len(outputs))).replace("@CARDS@", cards))
    return len(outputs)


if __name__ == "__main__":
    args = sys.argv[1:]
    labels = None
    if "--labels" in args:
        i = args.index("--labels")
        labels = args[i + 1]
        del args[i:i + 2]
    if len(args) != 3:
        sys.exit(__doc__)
    print("%d outputs to label" % build(*args, labels_path=labels))
