#!/usr/bin/env bash
# Amendment A-174 (G-V4.VIEW, D-440 (1)): the cases of the IF-104 v2 suites are renumbered TC-IF-104-17 to 27 (installed as 06 to 16 by A-171),
# because TC-IF-104-06 and 07 are v1 cases (A-60, A-66). Only the case IDs in docstrings and test names change; no step, value or assertion.
#   bash tools/apply_amendment_a174.sh            show the diff (changes nothing); --report for the readable form
#   bash tools/apply_amendment_a174.sh --do       install, then run both suites; commit afterwards as "plan: A-174 installed (owner)"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/amendments/A-174
copy $D/tests/acceptance/contract/test_if_104_v2_graph_api.py tests/acceptance/contract/test_if_104_v2_graph_api.py
copy $D/tests/acceptance/contract/test_if_104_v2_graph_api.test.mjs tests/acceptance/contract/test_if_104_v2_graph_api.test.mjs
finish

echo
echo "== the IF-104 v2 suites (expected as before A-174: Python 11 mock cases pass, the real cases red until graph_api_v2 exists; JS 11 pass, 11 skipped)"
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/contract/test_if_104_v2_graph_api.py 2>&1 | tail -1 || true
node --test tests/acceptance/contract/test_if_104_v2_graph_api.test.mjs 2>&1 | grep -E "^# (pass|fail|skipped)" || true
