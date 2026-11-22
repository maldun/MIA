#!/usr/bin/env bash
# Amendment A-172 (G-V4.VIEW, D-425 B, D-430 (7), D-435): IF-302 v15, the record tables `arrangements` and `graph_changes` for IF-104 v2.
# Installs the contract text, the mock and the contract suite from specs/mia/amendments/A-172/. The mock cases are green at once; the two new real
# cases (TC-IF-302-13, -14) stay red until Track A adds the tables to record_tables.py.
#   bash tools/apply_amendment_a172.sh            show the diff (changes nothing); --report for the readable form
#   bash tools/apply_amendment_a172.sh --do       install, then run the suite; commit afterwards as "plan: A-172 installed (owner)"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/amendments/A-172
copy $D/contracts/IF-302-record-tables.md contracts/IF-302-record-tables.md
copy $D/tests/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
copy $D/tests/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
finish

echo
echo "== the IF-302 suite (expected: 26 pass, 2 errors: the real side of TC-IF-302-13 and -14 until record_tables.py has the tables)"
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/contract/test_if_302_record_tables.py 2>&1 | tail -1 || true
