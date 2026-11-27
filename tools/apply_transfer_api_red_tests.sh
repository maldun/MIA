#!/usr/bin/env bash
# Red tests of G-V4.GRAPHSTORE.TRANSFER's backend checks (D-469, D-470, D-540 to D-542): TC-API-060 to 064 of
# specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/test-spec.md, written after VIEW's merge into goal/v4. Drafts in
# specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/red-tests/: the acceptance file test_transfer_backend.py and TRANSFER's own helper web_app_probe.py
# (a copy of VIEW's WebAppProbe and checkout_with plus run_main, D-470). The checks start the backend through `start_backend()` and stop it
# through `graceful_shutdown(stop_list())` of MIA's __main__ (TR-TRANSFER-009, D-541); both are built in T-06, so today every check fails by
# assertion (the start function is missing; for TC-API-063 the start also stops at the unreachable database). Nothing is skipped: VIEW's store
# setting and GET /api/v2/store exist (TR-TRANSFER-010).
# INSTALL IT ON THE LINE OF WORK goal/v4.graphstore.transfer.
#   bash tools/apply_transfer_api_red_tests.sh           show what would be created or changed (changes nothing)
#   bash tools/apply_transfer_api_red_tests.sh --do      install and run the new acceptance file; commit afterwards as
#                                                        "test: TRANSFER API acceptance tests (red)"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
R=specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/red-tests

copy "$R/helpers/web_app_probe.py" tests/helpers/web_app_probe.py
copy "$R/acceptance/test_transfer_backend.py" tests/acceptance/test_transfer_backend.py
finish

echo
echo "== the new acceptance file (red expected: 5 failures, no ImportError, no skip)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
"$PY" tests/acceptance/test_transfer_backend.py 2>&1 | tail -3
