#!/usr/bin/env bash
# Amendment A-170b (G-V4.GRAPHAPI.RULES, 2026-11-22, D-428): test data of TC-GTB-046 (tests/acceptance/test_rules_measures.py).
# The second graph's data step d1 has no value and no writer, so the run check rightly adds an unsupplied input (REQ-GTB-051) and the run named one
# part more than the rule report; the test now runs that graph with {"d1": "x"} (the owner's choice). Requirement, scenario intent and contract unchanged;
# the scenario wording in test-spec.md names the value. Found in T-03 (implementation-log.md).
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.rules.
#   bash tools/apply_amendment_a170b.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a170b.sh --do      install and run the file; commit afterwards as "plan: A-170b installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-170b

copy "$A/tests/acceptance/test_rules_measures.py" tests/acceptance/test_rules_measures.py
finish

echo
echo "== the measures file (expected: OK, TC-GTB-046 green on both graphs)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
printf '%-52s ' tests/acceptance/test_rules_measures.py; "$PY" tests/acceptance/test_rules_measures.py 2>&1 | grep -E '^(OK|FAILED)'
