#!/usr/bin/env bash
# Amendment A-105 (G-V2.MODEL, finding of task T-05, owner's answers of 2026-11-08): the fake of the graph tables cannot pass the IF-301 v2 contract suite
# (it is a versioned key-value store, the suite tests record checks and conversion), and the five checks TC-WFM-040/041/042/044/049 hardcode the fake.
# Decided: TR-MODEL-001 and task T-05 are reworded (the same scenarios also run on the real Storage layer in a new test file outside tests/acceptance),
# task T-06 is new (REQ-WFM-041: the skill listing and start take command and graphs from the record). No protected file, contract or requirement text changes.
# Note: specs/mia/amendments/A-105-note.md
# Files that change (made from the INSTALLED files at run time; every edit is skipped when it is done already and refused when its anchor is not found
# exactly once, so a second --do changes nothing):
#   specs/mia/test-requirements.md (TR-MODEL-001)     specs/mia/goals/G-V2.MODEL/plan.md (T-05 reworded, T-06 new, counts)
#   specs/mia/review-log.md (row D-306, appended)
# THE OWNER REVIEWS TR-MODEL-001 (its text changes: it comes back in req_review/test review), then installs.
#   bash tools/apply_amendment_a105.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a105.sh --do      install and run the checks; commit afterwards as "plan: A-105 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
TR=specs/mia/test-requirements.md
PLAN=specs/mia/goals/G-V2.MODEL/plan.md
LOG=specs/mia/review-log.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$TR" "$PLAN" "$LOG" "$WORK" <<'PY'
import os
import sys
tr, plan, log, work = sys.argv[1:5]
read = lambda path: open(path, encoding="utf-8").read()
out = lambda name, text: open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def once(text, old, new, where):
    """Replace `old` by `new` when `old` occurs exactly once; the edit counts as done when `new` is in the text already (checked FIRST)."""
    if new in text:
        return text
    if text.count(old) == 1:
        return text.replace(old, new)
    sys.exit("anchor not found exactly once (%d) in %s: %r" % (text.count(old), where, old[:70]))


# --- TR-MODEL-001 -------------------------------------------------------------------------------------------------------------------------------
t = read(tr)
t = once(t,
         "- Text: The checks shall use a minimal fake of the graph tables that keeps versions and fields, and the fake shall be run against the contract suite of IF-301 v2 as soon as that suite exists.\n",
         "- Text: The checks shall use a minimal fake of the graph tables that keeps versions and fields, and the same scenarios shall also run, in a test file outside the protected folders, on the real Storage layer with the record checks of IF-301 v2; a difference between the fake and the real Storage layer shall be reported as a finding for these checks.\n",
         tr)
t = once(t,
         "- Rationale: owner decision 2026-11-07: the checks do not wait for the IF-301 v2 mock of STORE. The fake is only as faithful as the contract suite shows; until the suite exists the gap is known, and a fake that fails the suite later is a finding for these checks.\n",
         "- Rationale: owner decision 2026-11-07: the checks do not wait for the IF-301 v2 mock of STORE. Owner decision 2026-11-08 (T-05): the contract suite of IF-301 v2 tests record checks and conversion, the fake is a versioned key-value store, so the suite cannot judge it; its fidelity is shown by running the same scenarios on the real Storage layer. A difference is a finding for these checks.\n",
         tr)
i = t.index("### TR-MODEL-001")
j = t.index("### TR-MODEL-002")
block = t[i:j]
block = once(block, "- Verified by: contract suite\n", "- Verified by: adapter test on the real Storage layer\n", "TR-MODEL-001")
block = once(block, "- History: changed at review (2026-11-07) from \"use only the IF-301 v2 mock\" at the owner's answer\n",
             "- History: changed at review (2026-11-07) from \"use only the IF-301 v2 mock\" at the owner's answer; A-105 (2026-11-08): from \"run the fake against the contract suite\" to the adapter test on the real Storage layer (T-05 finding)\n",
             "TR-MODEL-001")
t = t[:i] + block + t[j:]
out("tr", t)

# --- plan.md ------------------------------------------------------------------------------------------------------------------------------------
p = read(plan)
p = once(p, "Five small tasks, pure logic:", "Six small tasks, pure logic:", plan)
p = once(p,
         "| T-05 Replace the fake storage by the contract-checked one | REQ-WFM-040 (TR-MODEL-001) | TC-WFM-040, 041, 042, 044, 049 against the IF-301 v2 contract suite, no skip | T-02; G-V2.STORE merged |\n",
         "| T-05 Skill records on the real Storage layer (adapter test) | REQ-WFM-040 (TR-MODEL-001) | the five scenarios of TC-WFM-040, 041, 042, 044, 049 give the same answers on the fake and on the real Storage layer, in `tests/test_skill_record_storage.py` | T-02; G-V2.STORE merged |\n"
         "| T-06 Skill listing and start take the record | REQ-WFM-041 | new tests (marked TC-WFM-041) for `library.py` and `extension_loader.py`, written first | T-05 |\n",
         plan)
i = p.index("### T-05:")
j = p.index("## Order and checks")
new_t05 = """### T-05: Skill records on the real Storage layer (adapter test)
- Implements: REQ-WFM-040 (TR-MODEL-001 as reworded by A-105)
- Tests to turn green: a new file `tests/test_skill_record_storage.py` (outside the protected folders) that runs the scenarios of TC-WFM-040, TC-WFM-041, TC-WFM-042, TC-WFM-044 and TC-WFM-049 on the real `Storage` of STORE (file backend; PostgreSQL where the test environment offers it) and on the fake, and compares the answers; the five protected tests in `tests/acceptance/test_graph_model.py` stay green on the fake
- Touches: `skill_record.py` (wiring to `Storage`: the list of skill IDs comes from `Storage.ids("skills")` instead of the `skill_index` record, the `author` of `put` is given by the caller), the new test file
- Must not touch: protected material (`tests/acceptance/`, `tests/helpers/`, `contracts/`), STORE's files (`storage.py`, `graph_tables.py`, `storage_copy.py`)
- Depends on: T-02; G-V2.STORE merged
- Done when: the adapter test is green on the file backend (and on PostgreSQL where available, no skip there), the fake and the real Storage layer give the same answers for the five scenarios, or each difference is reported as a finding for these checks
- Notes: T-05 stopped on 2026-11-08 because the fake cannot pass the contract suite of IF-301 v2 (key-value store against record checks); A-105 is the answer. A skill record that the real record checks refuse is a finding for the skill record (REQ-WFM-040), not a reason to change STORE.

### T-06: Skill listing and start take the record
- Implements: REQ-WFM-041
- Tests to turn green: new tests marked TC-WFM-041 for the real skill listing and start, written first
- Touches: `library.py`, `extension_loader.py` (a skill with a record takes its command and its graph IDs from the record; the old forms stay for a skill without a record), their tests
- Must not touch: protected material, STORE's files
- Depends on: T-05
- Done when: the listing and the start of a skill with a record use the record, and a skill without a record behaves as before (the existing tests of both modules stay green)
- Notes: left out of T-02 on purpose (no test needed it); owner decision 2026-11-08: own task after T-05.

"""
p = p[:i] + new_t05 + p[j:]
p = once(p, "T-05 waits for STORE.", "T-05 waits for STORE; T-06 needs T-05.", plan)
p = once(p, "14 requirements, five tasks of one session each, no task across two nodes except T-02 (N-2.3 only)",
         "14 requirements, six tasks of one session each, no task across two nodes except T-02 (N-2.3 only), T-05 and T-06 (N-2.3 only)", plan)
out("plan", p)

# --- review-log.md (append-only) ----------------------------------------------------------------------------------------------------------------
row = ("| D-306 | **G-V2.MODEL, finding of T-05 and open points, owner maldun, 2026-11-08 (answers to a questionnaire; A-105).** (1) T-05 stopped: the fake of the "
       "graph tables is a versioned key-value store, the IF-301 v2 suite tests record checks and conversion, so 0 of its 20 cases pass on the fake and the five checks "
       "hardcode the fake. Decided: plan amendment A-105 plus a new adapter test outside `tests/acceptance` that runs the scenarios on the fake and on the real Storage "
       "layer; TR-MODEL-001 and T-05 reworded; no protected file changes. (2) The node field names are confirmed as proposed (`data`: value, parameters; `transform`: "
       "toolbox_id; `master`: stop, toolbox_id, task optional). (3) REQ-WFM-041 (skill listing and start from the record in `library.py` and `extension_loader.py`) "
       "becomes task T-06 after T-05. (4) No `Quality:` lines for REQ-WFM-040 and REQ-RUN-017; the gap is noted as known at Verify. Open points on the graph header, "
       "the membership and the skill record table are answered by IF-301 v2 (tables `graphs` and `skills`, D-264). |\n")
l = read(log)
if "| D-306 |" not in l:
    l = l + ("" if l.endswith("\n") else "\n") + row
out("log", l)
PY
copy "$WORK/tr" "$TR"
copy "$WORK/plan" "$PLAN"
copy "$WORK/log" "$LOG"
finish
if [ "$do_it" = 1 ]; then
    echo "checks after --do:"
    python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia 2>&1 | tail -3 || true
    python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E '^\*\*' || true
fi
