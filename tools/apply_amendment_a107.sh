#!/usr/bin/env bash
# Amendment A-107 (G-V2.MODEL, stop of task T-06, owner's decisions of 2026-11-08): `library.py` has no skill listing and no skill start (it is the
# pipeline and node library); the only place that registers commands is `extension_loader.load_extensions` (Task objects in `TaskRegistry`), which has no
# access to the records and whose Task carries no graph ID. Decided: option A, T-06 is reworded: `load_extensions` gets an optional `catalog` parameter, a skill
# with a record registers under the record's command and its task carries `workflow_graph_id` from `SkillCatalog.start`; `task_registry.py` (one new
# attribute on `Task`) and `web_app.py` (create the catalog, pass it) come into T-06's bounds. No protected file, contract or requirement text changes.
# Note: specs/mia/amendments/A-107-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing):
#   specs/mia/goals/G-V2.MODEL/plan.md (T-06 row and section)     specs/mia/review-log.md (row D-308, appended)
#   bash tools/apply_amendment_a107.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a107.sh --do      install and run the checks; commit afterwards as "plan: A-107 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
PLAN=specs/mia/goals/G-V2.MODEL/plan.md
LOG=specs/mia/review-log.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$PLAN" "$LOG" "$WORK" <<'PY'
import os
import sys
plan, log, work = sys.argv[1:4]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)

p = read(plan)
new_row = ("| T-06 Skill listing and start take the record (extension loader) | REQ-WFM-041 | new tests (marked TC-WFM-041) for `extension_loader.py` and the wiring, "
           "written first | T-05 |\n")
new_sec = """### T-06: Skill listing and start take the record (extension loader)
- Implements: REQ-WFM-041
- Tests to turn green: new tests marked TC-WFM-041, written first: (1) `load_extensions` with a `catalog` registers a skill that has a record under the record's command and its task carries the record's `workflow_graph_id`; (2) a skill without a record is registered exactly as before; (3) a record-only skill (no manifest folder) is not invented as a runnable task; the listing of commands (`TaskRegistry.commands`) shows the record's command; (4) the wiring in `web_app.py` creates the catalog from the Storage layer and passes it (as far as a test without a running server can show it)
- Touches: `extension_loader.py` (new optional parameter `catalog`, default None = behaviour as today), `task_registry.py` (one new attribute `workflow_graph_id` on `Task`, default None), `web_app.py` (create the `SkillCatalog` over `SkillRecords` and pass it to `load_extensions`), their tests
- Must not touch: protected material, STORE's files (`storage.py`, `graph_tables.py`, `storage_copy.py`), `library.py` (it has no skill listing: the plan's first wording was wrong)
- Depends on: T-05
- Done when: the listing and the start of a skill with a record use the record, and a skill without a record behaves as before (the existing tests of the three modules stay green)
- Notes: A-107 (2026-11-08): the first wording named `library.py`, which has no skill listing or start; the T-06 agent stopped and reported. Owner decision: option A (the extension loader) and the two extra files in the bounds. What runs when a record exists but no entry module does is not decided here: such a skill is listed by its command but is not made runnable by T-06 (report as a note, G-V2.CONVERT moves the skills one by one).

"""
if "A-107 (2026-11-08)" not in p:
    row_start = p.index("| T-06 Skill listing and start take the record |")
    row_end = p.index("\n", row_start) + 1
    p = p[:row_start] + new_row + p[row_end:]
    sec_start = p.index("### T-06:")
    sec_end = p.index("### T-07:")
    p = p[:sec_start] + new_sec + p[sec_end:]
out("plan", p)

row = ("| D-308 | **G-V2.MODEL, stop of T-06, owner maldun, 2026-11-08 (A-107).** `library.py` has no skill listing or start; the only place that registers commands "
       "is `extension_loader.load_extensions`, without access to the records. Decided: option A. T-06 is reworded: `load_extensions` takes an optional `catalog`, a skill "
       "with a record registers under the record's command and its task carries `workflow_graph_id` from `SkillCatalog.start`; `task_registry.py` (one new attribute on "
       "`Task`) and `web_app.py` (create and pass the catalog) are in the bounds; `library.py` is not touched. |\n")
l = read(log)
if "| D-308 |" not in l:
    l = l + ("" if l.endswith("\n") else "\n") + row
out("log", l)
PY
copy "$WORK/plan" "$PLAN"
copy "$WORK/log" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "checks after --do:"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -3 || true
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E '^\*\*' || true
fi
