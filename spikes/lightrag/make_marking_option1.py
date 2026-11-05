"""Builds the marking page for spike C option 1 (own builder): a fixed-seed sample of ACCEPTED proposals of option1.py,
each with the quote the model gave and the paragraph of the document around it. Same page and answer format as
make_marking.py (score_marks.py reads both); ids start with O, the saved file is spike-c-option1-marks.json.
usage: python3 -I make_marking_option1.py RUNDIR DOCS_DIR OUT.html [items_per_doc=20]"""
import html, json, random, re, sys
from pathlib import Path

run, docs_dir, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
per_doc = int(sys.argv[4]) if len(sys.argv) > 4 else 20
rng = random.Random(1)
here = Path(__file__).resolve().parent
PAGE = re.search(r'PAGE = """(.*?)"""\n', (here / "make_marking.py").read_text(), re.S).group(1)
PAGE = (PAGE.replace("Spike C: mark the extracted items", "Spike C, option 1: mark the proposed items")
        .replace("(LightRAG, gemma4:12b-it-qat, num_ctx 8192)", "(own builder, gemma4:12b-it-qat, num_ctx 8192; the model's quote is shown on each card)")
        .replace("mia-spike-c-marking", "mia-spike-c-option1-marking").replace("spike-c-marks.json", "spike-c-option1-marks.json"))


def squash(s):
    return " ".join(s.split())


def context(doc_text, quote):
    q = squash(quote).casefold()
    for para in re.split(r"\n\s*\n", doc_text):
        p = squash(para)
        if q[:60] in p.casefold():
            return p
    return ""


def mark(text, names):
    t = html.escape(text)
    for n in sorted({n for n in names if len(n) > 2}, key=len, reverse=True):
        t = re.sub("(?i)(" + re.escape(html.escape(n)) + ")", r"<mark>\1</mark>", t)
    return t


items = []
for f in sorted(run.glob("*.json")):
    acc = json.loads(f.read_text())["accepted"]
    text = (docs_dir / f"{f.stem}.txt").read_text()
    rng.shuffle(acc)
    ent = [a for a in acc if a["kind"] == "entity"][:per_doc * 6 // 10]
    rel = [a for a in acc if a["kind"] == "relation"][:per_doc - len(ent)]
    for a in ent + rel:
        names = [a["name"]] if a["kind"] == "entity" else [a["source"], a["target"]]
        head = a["name"] if a["kind"] == "entity" else f"{a['source']}  —  {a['target']}  [{a['relation']}]"
        items.append(dict(id=f"O{len(items) + 1:03d}", doc=f.stem, kind=a["kind"], key=names, head=head,
                          quote=a["quote"], source=mark(context(text, a["quote"]) or a["quote"], names)))

cards, last = [], None
for it in items:
    if it["doc"] != last:
        last = it["doc"]
        cards.append(f'<h2 class="doc">{html.escape(last)}</h2><p class="miss"><label>Important things the text says that are missing from the items: '
                     f'<input data-doc="{html.escape(last)}" class="missing" placeholder="short note or empty"></label></p>')
    cards.append(f"""<section class="card" data-id="{it['id']}">
<h3>{it['id']} · {it['kind']}: {html.escape(it['head'])}</h3>
<p class="desc">Model's quote: “{html.escape(it['quote'])}”</p>
<details><summary>Source passage</summary><div class='src'>{it['source']}</div></details>
<p class="opts"><label><input type="radio" name="d-{it['id']}" value="right"> right</label>
<label><input type="radio" name="d-{it['id']}" value="trivial"> right but useless</label>
<label><input type="radio" name="d-{it['id']}" value="wrong"> wrong (text says otherwise)</label>
<label><input type="radio" name="d-{it['id']}" value="invented"> invented (not in the text)</label></p>
<input class="note" placeholder="comment (optional)"></section>""")

meta = [dict(id=i["id"], doc=i["doc"], kind=i["kind"], key=i["key"]) for i in items]
out.write_text(PAGE.replace("__N__", str(len(items))).replace("__D__", str(len({i["doc"] for i in items})))
               .replace("__CARDS__", "\n".join(cards)).replace("__META__", json.dumps(meta)))
print(len(items), "items ->", out)
