#!/usr/bin/env bash
# Amendment A-106 (G-V2.MODEL, finding 3 of task T-05, owner's decision of 2026-11-08): the graph rules of T-01 (`GraphModel`) save graphs into a table
# `workflow_graphs` that the real Storage layer does not have, so they never run on stored data. Decided: a new task T-07 wires `GraphModel` to the record
# tables of IF-301 v2 (`graphs`, `graph_nodes`, `graph_edges`), moving the mapping that the adapter test of T-05 holds today into the production code.
# Also recorded: the owner's answer to finding 1 of T-05 (a skill record refused by the record checks is a refused result, not an exception; follow-up
# commit of T-05, no plan text changes for it). No protected file, contract or requirement text changes.
# Note: specs/mia/amendments/A-106-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing):
#   specs/mia/goals/G-V2.MODEL/plan.md (T-07 new, counts, order)     specs/mia/review-log.md (row D-307, appended)
#   bash tools/apply_amendment_a106.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a106.sh --do      install and run the checks; commit afterwards as "plan: A-106 installed"
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


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once; the edit counts as done when `new` is in the text already (checked FIRST)."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new)
    sys.exit("anchor not found exactly once (%d) in %s: %r" % (text.count(old), where, old[:70]))


p = read(plan)
p = once(p, "Six small tasks, pure logic:", "Seven small tasks, pure logic:", plan)
p = once(p,
         "| T-06 Skill listing and start take the record | REQ-WFM-041 | new tests (marked TC-WFM-041) for `library.py` and `extension_loader.py`, written first | T-05 |\n",
         "| T-06 Skill listing and start take the record | REQ-WFM-041 | new tests (marked TC-WFM-041) for `library.py` and `extension_loader.py`, written first | T-05 |\n"
         "| T-07 Graph model on the record tables | REQ-WFM-043..049 (stored form), REQ-WFM-044 | the adapter test of T-05 runs the graph scenarios (TC-WFM-044, 049) on the real Storage through `graph_model.py` itself, without the test-side mapping | T-05 |\n",
         plan)
i = p.index("## Order and checks")
new_t07 = """### T-07: Graph model on the record tables
- Implements: REQ-WFM-043, REQ-WFM-044, REQ-WFM-045, REQ-WFM-046, REQ-WFM-047, REQ-WFM-048, REQ-WFM-049 (the stored form of a graph; the rules themselves are T-01)
- Tests to turn green: the graph scenarios of the adapter test `tests/test_skill_record_storage.py` (TC-WFM-044, TC-WFM-049) with the test-side class `RealGraphTables` removed, so that `GraphModel(Storage)` itself saves a graph as `graph_nodes` and `graph_edges` records plus a `graphs` header that pins the member versions, and reads it back; a graph refused by the record checks of the Storage layer is a refused result naming the rule and detail, not an exception; the 10 protected tests in `tests/acceptance/test_graph_model.py` stay green on the fake
- Touches: `graph_model.py` (detects the real Storage as `SkillRecords` does; the `workflow_graphs` table name stays only for the fake path), `tests/test_skill_record_storage.py` (the mapping moves out of the test)
- Must not touch: protected material (`tests/acceptance/`, `tests/helpers/`, `contracts/`), STORE's files (`storage.py`, `graph_tables.py`, `storage_copy.py`)
- Depends on: T-05 (independent of T-06)
- Done when: the graph scenarios give the same answers on the fake, the file backend and PostgreSQL with the production wiring; the rules of T-01 are checked before the write (the record checks of STORE check each record again); a graph header that names an unknown member version is refused with the rule of the Storage layer
- Notes: finding 3 of T-05 (2026-11-08): `GraphModel` saved into `workflow_graphs`, which the real Storage does not have (`unknown_table`), and the real Storage returns `put` as `{"version": n}` and `get` as an entry with `doc`. A difference that is not an adapter detail is a finding for TR-MODEL-001, reported, not changed in the fake (`tests/helpers` is protected).

"""
if "### T-07:" not in p:
    p = p[:i] + new_t07 + p[i:]
p = once(p, "T-05 waits for STORE; T-06 needs T-05.", "T-05 waits for STORE; T-06 and T-07 need T-05 and are independent of each other.", plan)
p = once(p, "14 requirements, six tasks of one session each, no task across two nodes except T-02 (N-2.3 only), T-05 and T-06 (N-2.3 only)",
         "14 requirements, seven tasks of one session each, no task across two nodes except T-02 (N-2.3 only), T-05, T-06 and T-07 (N-2.3 only)", plan)
out("plan", p)

row = ("| D-307 | **G-V2.MODEL, findings of T-05, owner maldun, 2026-11-08 (A-106).** Finding 1: a skill record that the record checks of the Storage layer refuse is "
       "caught by `SkillRecords.store` and given back as a refused result (rule and detail of the Storage refusal), not raised; follow-up commit of T-05, no plan text "
       "changes. Finding 3: `GraphModel` saved into a table `workflow_graphs` that the real Storage does not have, so the graph rules of T-01 never ran on stored "
       "data; decided: new task T-07 wires `GraphModel` to `graphs`, `graph_nodes` and `graph_edges` (mapping moved from the adapter test into `graph_model.py`). |\n")
l = read(log)
if "| D-307 |" not in l:
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
