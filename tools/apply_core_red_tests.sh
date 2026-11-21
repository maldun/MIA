#!/usr/bin/env bash
# Red tests of G-V4.GRAPHSTORE.CORE (Plan step 4, 2026-11-21): the 22 checks of specs/mia/goals/G-V4.GRAPHSTORE.CORE/test-spec.md and SMOKE-CORE-001,
# with their helper (TR-CORE-001 to -009). Drafts in specs/mia/goals/G-V4.GRAPHSTORE.CORE/red-tests/; the files are new (protected folders, so the
# owner installs them). The stubs graph_model.GraphModel.graph_versions and step_history are already in the branch, so every check fails by assertion
# (TC-WFM-164 is green from the start, D-410).
# INSTALL IT ON THE LINE OF WORK goal/v4.
#   bash tools/apply_core_red_tests.sh           show what would be created (changes nothing)
#   bash tools/apply_core_red_tests.sh --do      install and run the four acceptance files; commit afterwards as
#                                                "test: CORE acceptance tests (red)" and tag plan-baseline-g-v4-core
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
R=specs/mia/goals/G-V4.GRAPHSTORE.CORE/red-tests

copy "$R/helpers/core_stores.py" tests/helpers/core_stores.py
copy "$R/acceptance/test_core_scoped_ids.py" tests/acceptance/test_core_scoped_ids.py
copy "$R/acceptance/test_core_save.py" tests/acceptance/test_core_save.py
copy "$R/acceptance/test_core_context_and_history.py" tests/acceptance/test_core_context_and_history.py
copy "$R/acceptance/test_core_both_stores.py" tests/acceptance/test_core_both_stores.py
copy "$R/smoke/smoke_core_graphs.py" tests/smoke/smoke_core_graphs.py
finish

echo
echo "== the four acceptance files (red expected: failures, no ImportError; PostgreSQL halves run where podman and postgres:16 are present)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/test_core_scoped_ids.py tests/acceptance/test_core_save.py tests/acceptance/test_core_context_and_history.py tests/acceptance/test_core_both_stores.py; do
    printf '%-52s ' "$f"; "$PY" "$f" 2>&1 | tail -1
done
