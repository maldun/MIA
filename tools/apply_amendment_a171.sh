#!/usr/bin/env bash
# Amendment A-171 (G-V4.VIEW, D-425 A, D-430, D-433, D-434, D-460): IF-104 v2, the graph API of the stored form under /api/v2, beside the
# unchanged v1. Installs the contract text, the Python and JavaScript mocks and the two contract suites from specs/mia/amendments/A-171/.
# The mock cases are green at once; the real cases (files, PostgreSQL) stay red until Track A builds graph_api_v2.create_app.
#   bash tools/apply_amendment_a171.sh            show the diff (changes nothing); --report for the readable form
#   bash tools/apply_amendment_a171.sh --do       install, then run both suites; commit afterwards as "plan: A-171 installed (owner)"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/amendments/A-171
copy $D/IF-104-graph-api.md contracts/IF-104-graph-api.md
copy $D/tests/helpers/mocks/if_104_v2_graph_api.py tests/helpers/mocks/if_104_v2_graph_api.py
copy $D/tests/helpers/mocks/if_104_v2_graph_api.mjs tests/helpers/mocks/if_104_v2_graph_api.mjs
copy $D/tests/acceptance/contract/test_if_104_v2_graph_api.py tests/acceptance/contract/test_if_104_v2_graph_api.py
copy $D/tests/acceptance/contract/test_if_104_v2_graph_api.test.mjs tests/acceptance/contract/test_if_104_v2_graph_api.test.mjs
finish

echo
echo "== the v2 suites (expected: JS 11 pass, 11 skipped; Python 11 mock cases pass, 22 real cases fail until graph_api_v2 exists)"
node --test tests/acceptance/contract/test_if_104_v2_graph_api.test.mjs 2>&1 | grep -E "^# (pass|fail|skipped)" || true
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/contract/test_if_104_v2_graph_api.py 2>&1 | tail -1 || true
