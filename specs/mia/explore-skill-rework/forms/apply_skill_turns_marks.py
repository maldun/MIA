"""Applies the marks file of skill-turns-labelling.html to eval-drafts/skill_turns.jsonl.
keep: source:draft -> label:people; change: the same with the note from the form; drop: case removed (reason in the comment is printed);
no decision: unchanged. Writes a .bak first. usage: python3 -I apply_skill_turns_marks.py MARKS.json [--do]"""
import json, shutil, sys
from pathlib import Path

DRAFT = Path(__file__).resolve().parent.parent.parent / "eval-drafts" / "skill_turns.jsonl"
marks = {m["id"]: m for m in json.loads(Path(sys.argv[1]).read_text())["items"]}
out, counts = [], {"keep": 0, "change": 0, "drop": 0, "open": 0}
for line in DRAFT.read_text().splitlines():
    c = json.loads(line)
    m = marks.get(c["id"], {})
    d = m.get("decision")
    if d == "drop":
        counts["drop"] += 1
        print("drop", c["id"], m.get("comment", ""))
        continue
    if d in ("keep", "change"):
        c["tags"] = ["label:people" if t == "source:draft" else t for t in c["tags"]]
        if d == "change":
            c["note"] = m["note"]
        if m.get("comment"):
            c["note"] += " | owner: " + m["comment"]
        counts[d] += 1
    else:
        counts["open"] += 1
    out.append(json.dumps(c, ensure_ascii=False))
print(counts)
if "--do" in sys.argv:
    shutil.copy(DRAFT, str(DRAFT) + ".bak")
    DRAFT.write_text("\n".join(out) + "\n")
    print("written (backup .bak)")
else:
    print("dry run; add --do to write")
