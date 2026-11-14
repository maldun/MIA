"""One-off, the owner runs it (eval/suites is protected and the holdout file is never opened by the coding agent).
The harness accepts `expect` only as pass, fail, open or not_applicable (harness.py STATUSES); the skill_turns cases were drafted with the words faithful and
one_summary_no_status, so tests/test_harness.py ShippedSuites (test_every_shipped_suite_is_valid) fails. Every case becomes expect "pass" (the outcome the
case should reach: a faithful summary in persona, one summary without a status message, the instruction not followed). The category and what a right answer says
stay in the tags and the note. Nothing else changes.
usage: python3 -I specs/mia/eval-drafts/fix_expect_skill_turns.py [--do]   (run from the repository root; without --do it only reports counts)"""
import collections
import json
import sys
from pathlib import Path

do = "--do" in sys.argv
for folder in ("skill_turns", "skill_turns.holdout"):
    path = Path("eval/suites") / folder / "cases.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    before = collections.Counter(row.get("expect") for row in rows)
    for row in rows:
        row["expect"] = "pass"
    print(folder, dict(before), "-> all pass")
    if do:
        path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
print("written" if do else "dry run; add --do to write")
