#!/usr/bin/env bash
# Amendment A-66 (N-3.2 re-verification R1, R2; owner decision D-169, 2026-10-31): `max_cycles: 2.0` is refused by the JS graph mock as by the real
# rules; the real side of TC-IF-104-06 is named; the deferral TD-06 of REQ-GTB-004 gets the Relaxed/Target lines, a skip reason and a dated trigger.
# Note: specs/mia/amendments/A-66/A-66-note.md
# Protected files that change (copied from the drafts):
#   tests/helpers/mocks/if_104_graph_api.mjs                  a session limit written as 2.0 or 1e0 in the JSON body keeps its source text and is refused
#   tests/acceptance/contract/test_if_104_graph_api.test.mjs  TC-IF-104-07: max_cycles 2.0 in a hand-written body is 422, 2 is saved
# Made from the INSTALLED files at run time (A-62 and A-65 also change specs/mia/test-spec.md), each edit refused when its anchor is not found once:
#   specs/mia/test-spec.md     the row TC-IF-104-06 names its real side (tests/test_graph_api.py), the row TC-IF-104-07 after it
#   specs/mia/deferred.md      TD-06: the trigger gets the date 2026-12-31, the target check becomes `skip: <reason>`
#   specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md   REQ-GTB-004: `Relaxed: TD-06` and its `Target`
# INSTALL IT ON THE LINE OF WORK goal/v1 (A-60 must be installed: the row TC-IF-104-06 is its).
#   bash tools/apply_amendment_a66.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a66.sh --do      install, run the IF-104 JS suite and the trace check for TD-06; commit afterwards as "plan: A-66 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
NODE=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - specs/mia/test-spec.md specs/mia/deferred.md "$NODE" "$WORK" <<'PY'
import os
import sys
spec, deferred, node, work = sys.argv[1:5]


def edit(text, old, new, where, what):
    """old -> new exactly once; a text that has the new part already is left as it is (the copy then reports unchanged)."""
    if new in text:
        return text
    if text.count(old) != 1:
        sys.exit("%s: %s is not found exactly once; install A-66 by hand" % (where, what))
    return text.replace(old, new)


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


read = lambda path: open(path, encoding="utf-8").read()
old6 = ("| TC-IF-104-06 | IF-104 | Contract | 1 (mock) and 2 (real) | (A-60, D-162) a session limit that is not an integer >= 1 is 422 "
        "session_stopping_criterion; max_cycles 1 with a null max_seconds is saved. | exact |\n")
new6 = ("| TC-IF-104-06 | IF-104 | Contract | 1 (mock); real: `tests/test_graph_api.py` `test_a_session_limit_that_is_not_a_positive_integer_is_422` "
        "(the routes of N-2.1; the JS real side skips) | (A-60, D-162) a session limit that is not an integer >= 1 is 422 "
        "session_stopping_criterion; max_cycles 1 with a null max_seconds is saved. | exact |\n")
row7 = ("| TC-IF-104-07 | IF-104 | Contract | 1 (mock); real: `tests/test_graph_rules.py` `test_a_session_limit_is_a_positive_integer` (a float "
        "such as 1.0 or 2.5 is refused) | (A-66, D-169) max_cycles written as 2.0 in the JSON body is 422 session_stopping_criterion; 2 is saved. | exact |\n")
text = edit(read(spec), old6, new6, spec, "the row of TC-IF-104-06 (A-60)")
write("test-spec.md", edit(text, new6, new6 + row7, spec, "the new row of TC-IF-104-06"))

text = edit(read(deferred), "- Trigger: root task T-10, or the Plan of the next iteration, whichever first\n- Target check: TC-GTB-005\n",
            "- Trigger: root task T-10, or 2026-12-31, whichever first\n"
            "- Target check: skip: `library/workflows` is missing (root task T-10); TC-GTB-005 is rewritten with FB-03 and then carries deferred('TD-06') until green\n",
            deferred, "the Trigger and Target check lines of TD-06")
write("deferred.md", text)

old = ("- Verified by: TC-GTB-005\n- Status: Approved\n- History: –\n")
new = ("- Verified by: TC-GTB-005\n- Status: Approved\n- Relaxed: TD-06\n"
       "- Target: the five seed entries in `library/workflows` pass validate(workflows, ...) and TC-GTB-005, rewritten for the entry format of FB-03, runs green\n"
       "- History: A-66 (2026-10-31): Relaxed TD-06 (D-160, D-169)\n")
write("requirements.md", edit(read(node), old, new, node, "the Verified by/Status/History lines of REQ-GTB-004"))
PY
copy $D/tests/helpers/mocks/if_104_graph_api.mjs tests/helpers/mocks/if_104_graph_api.mjs
copy $D/tests/acceptance/contract/test_if_104_graph_api.test.mjs tests/acceptance/contract/test_if_104_graph_api.test.mjs
copy "$WORK/test-spec.md" specs/mia/test-spec.md
copy "$WORK/deferred.md" specs/mia/deferred.md
copy "$WORK/requirements.md" "$NODE"
finish
echo
echo "== tests/acceptance/contract/test_if_104_graph_api.test.mjs"
node --test tests/acceptance/contract/test_if_104_graph_api.test.mjs 2>&1 | grep -E "^not ok|^# (pass|fail|skipped)"
echo "== trace_check, TD-06 errors (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "ERROR.*TD-06" || echo "none"
