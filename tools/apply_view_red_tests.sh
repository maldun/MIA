#!/usr/bin/env bash
# Red tests of G-V4.VIEW (Plan step 4, 2026-11-22): the checks of specs/mia/goals/G-V4.VIEW/test-spec.md that are new in VIEW (TC-API-018 to 025,
# TC-OPR-011, TC-GA-017 to 039, SMOKE-VIEW-001, 002) with their fixtures and helpers (TR-VIEW-001 to 021). Drafts in
# specs/mia/goals/G-V4.VIEW/red-tests/; the files are new and go into protected folders, so the owner installs them. The contract cases
# (TC-IF-104-17 to 27, TC-IF-302-13, 14) are installed already (A-171, A-172, A-174). The page stubs graph_app/viewer.js, api.js and drawing.js
# are in the branch, so the node checks fail on 'not written', the browser checks on the missing provider, the backend checks by assertion.
#   bash tools/apply_view_red_tests.sh           show what would be created (changes nothing)
#   bash tools/apply_view_red_tests.sh --do      install and run each file; commit afterwards as "test: VIEW acceptance tests (red)"
#                                                and tag plan-baseline-g-v4-view
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
R=specs/mia/goals/G-V4.VIEW/red-tests

copy "$R/fixtures/graph_view/graphs.json" tests/fixtures/graph_view/graphs.json
copy "$R/helpers/graph_view_data.py" tests/helpers/graph_view_data.py
copy "$R/helpers/graph_view_page.mjs" tests/helpers/graph_view_page.mjs
copy "$R/helpers/graph_view_server.py" tests/helpers/graph_view_server.py
copy "$R/acceptance/test_view_backend.py" tests/acceptance/test_view_backend.py
copy "$R/acceptance/test_graph_view_files.py" tests/acceptance/test_graph_view_files.py
copy "$R/acceptance/test_graph_view_browser.py" tests/acceptance/test_graph_view_browser.py
copy "$R/acceptance/graph_view_page.test.mjs" tests/acceptance/graph_view_page.test.mjs
copy "$R/smoke/smoke_view_image.py" tests/smoke/smoke_view_image.py
copy "$R/smoke/smoke_view_open_time.py" tests/smoke/smoke_view_open_time.py
finish

echo
echo "== red expected: failures, no ImportError (expected: backend 12 failures in 9 tests, files 2, browser 7, node 14 fail and 1 pass)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/test_view_backend.py tests/acceptance/test_graph_view_files.py tests/acceptance/test_graph_view_browser.py; do
    printf '%-48s ' "$f"; "$PY" "$f" 2>&1 | tail -1
done
printf '%-48s ' tests/acceptance/graph_view_page.test.mjs; node --test tests/acceptance/graph_view_page.test.mjs 2>&1 | grep -E "^# (pass|fail)" | tr '\n' ' '; echo
