#!/usr/bin/env bash
# Amendment A-187 (G-V4.GRAPHAPI.RUN, 2026-11-24): IF-301 v5, the loader of graphs (D-473, D-475). New operation load(graph) of the module graph_rule_set
# of N-3.2: the stored form as one networkx MultiDiGraph; the operations of v4 are unchanged (REQ-GTB-060). The contract suite gets TC-IF-301-35 to 38
# (golden 32 to 35) in a file of its own, run against the new mock and the real module. Also installed: the helpers of the RUN checks, the red acceptance tests of RUN (loader and rules, order and run order, stored-graph path), their helper run_store.py, the generator of
# the 500 random graphs (TR-RUN-003) and the oracle recorded at goal/v4 before any code changed (TR-RUN-002, tools/record_run_oracle.py).
# Drafts in specs/mia/amendments/A-187/.
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.run.
#   bash tools/apply_amendment_a187.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a187.sh --do      install and run the suite; commit afterwards as "plan: A-187 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-187

copy "$A/IF-301-graph-tables.md" contracts/IF-301-graph-tables.md
copy "$A/tests/helpers/mocks/if_301_graph_tables_v5.py" tests/helpers/mocks/if_301_graph_tables_v5.py
copy "$A/tests/acceptance/contract/test_if_301_v5_load.py" tests/acceptance/contract/test_if_301_v5_load.py
copy "$A/tests/helpers/run_graphs.py" tests/helpers/run_graphs.py
copy "$A/tests/helpers/run_oracle.json" tests/helpers/run_oracle.json
copy "$A/tests/helpers/run_store.py" tests/helpers/run_store.py
copy "$A/tests/acceptance/test_graph_loader.py" tests/acceptance/test_graph_loader.py
copy "$A/tests/acceptance/test_graph_order.py" tests/acceptance/test_graph_order.py
copy "$A/tests/acceptance/test_stored_graph_run.py" tests/acceptance/test_stored_graph_run.py
finish

echo
echo "== the v5 suite (expected until the loader task of the RUN plan: networkx is not installed, so the mock side errors on import; the real side raises NotImplementedError) and the older IF-301 suites (green)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/test_graph_loader.py tests/acceptance/test_graph_order.py tests/acceptance/test_stored_graph_run.py tests/acceptance/contract/test_if_301_v5_load.py tests/acceptance/contract/test_if_301_v4_rule_set.py tests/acceptance/contract/test_if_301_v2_graph_tables.py tests/acceptance/contract/test_if_301_graph_tables.py; do
    printf '%-62s ' "$f"; "$PY" "$f" 2>&1 | tail -1
done
