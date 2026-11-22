#!/usr/bin/env bash
# Red tests of G-V4.GRAPHAPI.RULES (Plan step 4, 2026-11-22): the checks of specs/mia/goals/G-V4.GRAPHAPI.RULES/test-spec.md (TC-GTB-037 to 047,
# TC-WFM-179 to 184, TC-RUN-036 to 040) and SMOKE-RULES-001, with their helper rules_graphs.py (TR-RULES-001 to 009). Drafts in
# specs/mia/goals/G-V4.GRAPHAPI.RULES/red-tests/; the files are new (protected folders, so the owner installs them). The stub graph_rule_set.py is in
# the branch, so every check fails by assertion; green from the start (CORE behaviour or protection): TC-WFM-182, TC-WFM-183, TC-RUN-038, TC-GTB-045.
# The IF-301 v4 suite and mock come with tools/apply_amendment_a170.sh (either order).
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.rules.
#   bash tools/apply_rules_red_tests.sh           show what would be created (changes nothing)
#   bash tools/apply_rules_red_tests.sh --do      install and run the four acceptance files; commit afterwards as
#                                                 "test: RULES acceptance tests (red)" and tag plan-baseline-g-v4-rules
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
R=specs/mia/goals/G-V4.GRAPHAPI.RULES/red-tests

copy "$R/helpers/rules_graphs.py" tests/helpers/rules_graphs.py
copy "$R/acceptance/test_rules_rule_set.py" tests/acceptance/test_rules_rule_set.py
copy "$R/acceptance/test_rules_measures.py" tests/acceptance/test_rules_measures.py
copy "$R/acceptance/test_rules_save.py" tests/acceptance/test_rules_save.py
copy "$R/acceptance/test_rules_run.py" tests/acceptance/test_rules_run.py
copy "$R/smoke/smoke_rules.py" tests/smoke/smoke_rules.py
finish

echo
echo "== the four acceptance files (red expected: failures, no ImportError)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/test_rules_rule_set.py tests/acceptance/test_rules_measures.py tests/acceptance/test_rules_save.py tests/acceptance/test_rules_run.py; do
    printf '%-52s ' "$f"; "$PY" "$f" 2>&1 | tail -1
done
