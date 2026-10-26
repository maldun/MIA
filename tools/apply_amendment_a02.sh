#!/usr/bin/env bash
# Amendment A-02: the Database (N-3) is integrated. The contract suites of IF-301, IF-302 and IF-102 get the real providers (graph_tables, record_tables,
# the Storage layer on the file backend, or on PostgreSQL when MIA_TEST_DATABASE_URL is set), and the integration helper lists N-3.2, N-3.3, N-3.1 and
# N-3 as ready, so the steps 1 to 3 of N-3 and step 1 of N-0 run on the real parts instead of skipping. Two protected files change:
#   tests/helpers/contract.py   tests/helpers/integration.py
# Run it yourself in the MAIN checkout (the coding agent may not write there), after the branch with the amendment is merged:
#   bash tools/apply_amendment_a02.sh          (shows what differs and runs the tests that change)
#   bash tools/apply_amendment_a02.sh --do     (copies the drafts over the installed files; commit them afterwards as "plan: A-02 ...")
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
do_it=0
[ "${1:-}" = "--do" ] && do_it=1
changed=0
copy() {   # draft installed
    if [ ! -e "$2" ]; then echo "MISSING   $2 (install the drafts first)"; exit 1; fi
    if cmp -s "$1" "$2"; then echo "unchanged $2"; return; fi
    changed=$((changed + 1))
    if [ "$do_it" = 1 ]; then cp "$1" "$2" && echo "updated   $2"; else echo "DIFFERS   $2"; fi
}
copy specs/mia/contract-drafts/tests/helpers/contract.py tests/helpers/contract.py
copy specs/mia/integration-drafts/tests/helpers/integration.py tests/helpers/integration.py
if [ "$do_it" = 0 ] && [ "$changed" -gt 0 ]; then echo "$changed file(s) differ: run again with --do"; exit 0; fi
for suite in test_if_102_storage test_if_301_graph_tables test_if_302_record_tables; do
    printf '%-34s' "$suite"; python3 "tests/acceptance/contract/$suite.py" 2>&1 | tail -1
done
python3 -I tools/run_integration_steps.py . | grep -E "N-0/step_01|N-3/|failed"
