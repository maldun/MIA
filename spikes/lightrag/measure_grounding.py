"""Offline measurement of rule 2 of option1b.py on the owner's 195 marks of LightRAG (spike C), no model, no GPU.
usage: python3 -I measure_grounding.py MARKING.html MARKS.json
For each ENTITY the description LightRAG gave is checked against the passage the owner saw: how many content words are
not in the passage? Shows whether the rule would flag the owner's invented/wrong entities and how many right ones it
would also flag. Indicative only: LightRAG's descriptions are free text, option 1b asks for a restating description."""
import html, json, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from option1b import ungrounded

form, marks = Path(sys.argv[1]).read_text(encoding="utf-8"), json.loads(Path(sys.argv[2]).read_text())["items"]
rows = []
for m in marks:
    if m["kind"] != "entity":
        continue
    card = re.search(r'<section class="card" data-id="%s">(.*?)</section>' % m["id"], form, re.S).group(1)
    desc = html.unescape(re.sub(r"<[^>]+>", "", re.search(r'<p class="desc">(.*?)</p>', card, re.S).group(1)))
    src = re.search(r"<div class='src'>(.*?)</div>", card, re.S)
    src = html.unescape(re.sub(r"<[^>]+>", "", src.group(1))) if src else ""
    rows.append((m["id"], m["decision"], len(ungrounded(desc, src))))

print("entities:", len(rows), dict(Counter(r[1] for r in rows)))
for limit in (0, 1, 2, 3, 5):
    flagged = Counter(r[1] for r in rows if r[2] > limit)
    bad = flagged["invented"] + flagged["wrong"]
    print(f"refuse when more than {limit} ungrounded word(s): refuses {sum(flagged.values())}: "
          f"invented {flagged['invented']}/12, wrong {flagged['wrong']}/6, right {flagged['right']}/{sum(1 for r in rows if r[1]=='right')}, "
          f"trivial {flagged['trivial']}/4  (bad refused {bad}/18)")
