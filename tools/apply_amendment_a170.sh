#!/usr/bin/env bash
# Amendment A-170 (G-V4.GRAPHAPI.RULES, 2026-11-22): IF-301 v4, the rule set of graphs (D-417; text approved by the owner in three parts, D-419).
# New operations kinds(), rule_report(graph), run_check(graph, given) offered by the module graph_rule_set of N-3.2; the operations of v3 and the
# document form are unchanged (REQ-GTB-052). The contract suite gets TC-IF-301-27 to 34 (golden 24 to 31) in a file of its own, run against the new
# mock and the real module; the suite uses the RULES helper rules_graphs.py (converted skills, sentences), installed here too (same file as the
# RULES red tests, so installing both in any order gives the same result).
# Drafts in specs/mia/amendments/A-170/ and specs/mia/goals/G-V4.GRAPHAPI.RULES/red-tests/helpers/.
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.rules.
#   bash tools/apply_amendment_a170.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a170.sh --do      install and run the suite; commit afterwards as "plan: A-170 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-170
R=specs/mia/goals/G-V4.GRAPHAPI.RULES/red-tests

copy "$A/IF-301-graph-tables.md" contracts/IF-301-graph-tables.md
copy "$A/tests/helpers/mocks/if_301_graph_tables_v4.py" tests/helpers/mocks/if_301_graph_tables_v4.py
copy "$A/tests/acceptance/contract/test_if_301_v4_rule_set.py" tests/acceptance/contract/test_if_301_v4_rule_set.py
copy "$R/helpers/rules_graphs.py" tests/helpers/rules_graphs.py
finish

echo
echo "== the v4 suite (expected until task T-01 of the RULES plan: the mock side green, the real side red by assertion) and the older IF-301 suites (green)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/contract/test_if_301_v4_rule_set.py tests/acceptance/contract/test_if_301_v2_graph_tables.py tests/acceptance/contract/test_if_301_graph_tables.py; do
    printf '%-62s ' "$f"; "$PY" "$f" 2>&1 | tail -1
done
