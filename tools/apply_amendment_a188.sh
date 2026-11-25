#!/usr/bin/env bash
# Amendment A-188 (G-V4.GRAPHAPI.RUN, 2026-11-25, T-01 finding F-1, D-482): TC-GTB-050 also checks that of two steps d1 the first is kept with its
# data and position 0. Before, the case listed only the node IDs, so a loader whose second d1 overwrites the first (networkx add_node on an existing
# key updates its attributes) passed it, and TR-RUN-007 "the loader keeps a second d1" could not be shown on TC-GTB-050. No code changes; the test
# spec of the goal follows. Drafts in specs/mia/amendments/A-188/.
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.run.
#   bash tools/apply_amendment_a188.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a188.sh --do      install and run the check; commit afterwards as "plan: A-188 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-188

copy "$A/tests/acceptance/test_graph_loader.py" tests/acceptance/test_graph_loader.py
copy "$A/test-spec.md" specs/mia/goals/G-V4.GRAPHAPI.RUN/test-spec.md
finish

echo
echo "== TC-GTB-048 to 050 green after T-01; TC-GTB-051 stays red until T-02"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
"$PY" tests/acceptance/test_graph_loader.py 2>&1 | grep -E '^(FAIL|ERROR):|^OK|^FAILED'
