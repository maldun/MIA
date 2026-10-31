#!/usr/bin/env bash
# Amendment A-61 (N-3.3 Verify, owner decisions D-161: F3, F5, F8): IF-302 v6, a document that is not a mapping is rule `schema` in every table,
# and a vote value is an integer (a boolean or a float such as 1.0 is rule `schema`, detail `value`); the mock does both, as the Record tables do.
# Protected files that change:
#   contracts/IF-302-record-tables.md                          v6: the two `schema` cases, golden example 4, the version line ("draft v0" dropped from the header)
#   tests/helpers/mocks/if_302_record_tables.py                a non-mapping is `schema` in every table; a bool or float vote value is `schema`
#   tests/acceptance/contract/test_if_302_record_tables.py     TC-IF-302-07 (golden 4)
#   specs/mia/test-spec.md                                     the rows TC-IF-302-04..07 after TC-IF-302-03 (F8; made from the installed file at run time, so it cannot go stale)
# Also (node file, made from the installed file): the node requirements.md of N-3.3, IF-302 `Verified by: TC-IF-302-01..07` and its History.
# The real side of TC-IF-302-07 is green already: record_tables.py refuses both since the F3/F5 fix of branch v1-n33b (merge that first).
# Not in A-61: the vote categories as an IF-302 operation for N-2.2 (F6): N-2.2 and N-3.3 are not siblings, see the implementation log of N-3.3.
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a61.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a61.sh --do      install and run the IF-302 suite (mock and real); commit afterwards as "plan: A-61 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-61
D=specs/mia/contract-drafts
NODE=specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/requirements.md
SPEC=$(mktemp)
REQS=$(mktemp)
trap 'rm -f "$SPEC" "$REQS"' EXIT
python3 - specs/mia/test-spec.md "$SPEC" <<'PY'
import sys
after = "| TC-IF-302-03 | IF-302 | Contract | 1 (mock) and 2 (real) | a memory record needs a source (rule schema, detail source); text with newlines, quotes and non-ASCII characters is valid; a foreign table is a ValueError. | exact |"
rows = [
    "| TC-IF-302-04 | IF-302 | Contract | 1 (mock) and 2 (real) | v2: a memory record's kind (fact, preference, commitment) and status (active, replaced) are checked when present, subject and updated are free; a record of v1 stays valid; the source stays required. | exact |",
    "| TC-IF-302-05 | IF-302 | Contract | 1 (mock) and 2 (real) | v3: the status of workflow_meta is required and one of draft, tested, trusted, retired; specification and benchmark are free. | exact |",
    "| TC-IF-302-06 | IF-302 | Contract | 1 (mock) and 2 (real) | v4, v5: a reports record needs task, skill, skill_version, question, account, model_pin and report; a missing field is rule schema with that field as detail; the table is versioned and not deletable. | exact |",
    "| TC-IF-302-07 | IF-302 | Contract | 1 (mock) and 2 (real) | golden 4 (v6, A-61): a document that is not a mapping is rule schema in every table; a vote value 1.0, -1.0, True or False is rule schema, detail value. | exact |",
]
text = open(sys.argv[1], encoding="utf-8").read()
if after not in text:
    sys.exit("the row of TC-IF-302-03 is not where A-61 expects it: check specs/mia/test-spec.md")
missing = [row for row in rows if row not in text]
if missing and len(missing) != len(rows):
    sys.exit("some rows TC-IF-302-04..07 are there and some not: check specs/mia/test-spec.md")
if missing:
    text = text.replace(after, "\n".join([after] + rows))
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
python3 - "$NODE" "$REQS" <<'PY'
import sys
old_by, new_by = "- Verified by: TC-IF-302-01..03\n", "- Verified by: TC-IF-302-01..07\n"
old_hist = "- History: v0, amendment 5/7 (2026-10-25)\n"
new_hist = "- History: v0, amendment 5/7 (2026-10-25); 2026-10-31 A-61 (D-161): IF-302 v6; Verified by names TC-IF-302-01..07 (it said 01..03)\n"
text = open(sys.argv[1], encoding="utf-8").read()
if new_by not in text:
    if text.count(old_by) != 1 or text.count(old_hist) != 1:
        sys.exit("the IF-302 entry of the N-3.3 requirements is not what A-61 expects: check " + sys.argv[1])
    text = text.replace(old_by, new_by).replace(old_hist, new_hist)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
copy $A/IF-302-record-tables.md contracts/IF-302-record-tables.md
copy $D/tests/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
copy $D/tests/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
copy "$SPEC" specs/mia/test-spec.md
copy "$REQS" "$NODE"
finish
echo
python3 tests/acceptance/contract/test_if_302_record_tables.py
