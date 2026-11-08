"""One-off, owner runs it (eval/suites and eval/baselines are protected), D-304 and the retag decision of 2026-11-08.
1. every case of eval/suites/skill_turns and skill_turns.holdout gets the tags req:REQ-CHA-053 and req:REQ-CHA-054 if missing,
   so the criteria select all 24 cases per split (n=24 of REQ-CHA-053 and 054); ids, inputs, notes, truth and splits stay as they are.
2. an empty baseline file eval/baselines/skill_turns__nodigest__baseline.jsonl records "no digest today" (D-304).
usage: python3 -I specs/mia/eval-drafts/retag_skill_turns.py [--do]   (run from the repository root; without --do it only reports)"""
import json, sys
from pathlib import Path

do = "--do" in sys.argv
need = ["req:REQ-CHA-053", "req:REQ-CHA-054"]
for folder in ("skill_turns", "skill_turns.holdout"):
    path = Path("eval/suites") / folder / "cases.jsonl"
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    changed = 0
    for r in rows:
        add = [t for t in need if t not in r["tags"]]
        if add:
            r["tags"] = sorted(r["tags"] + add)
            changed += 1
    print(f"{folder}: {len(rows)} cases, {changed} retagged")
    if do:
        path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
base = Path("eval/baselines/skill_turns__nodigest__baseline.jsonl")
print("baseline file:", "exists" if base.exists() else "to create (empty)")
if do and not base.exists():
    base.write_text("")
print("written" if do else "dry run; add --do")
