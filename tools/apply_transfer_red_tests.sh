#!/usr/bin/env bash
# Red tests of G-V4.GRAPHSTORE.TRANSFER (Plan step 4, 2026-11-23, D-468, D-469): the checks of specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/test-spec.md
# TC-SLY-009, TC-SLY-016 to 039 and SMOKE-TRANSFER-001, with the new helper transfer_stores.py and CORE's core_stores.py, whose FailingBackend now
# also counts removals, cut backs and file writes (TR-TRANSFER-004; CORE's counts unchanged). Drafts in
# specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/red-tests/. The stub graph_store_transfer.py and the stub commands lag/sync of migrate.py are in the
# branch, so every check fails by assertion; green from the start: TC-SLY-022 (CORE already answers alike on both backends); skipped until VIEW
# is merged: TC-SLY-030 (TR-TRANSFER-010). TC-API-060 to 064 come later with their own script, once VIEW is merged (D-469).
# INSTALL IT ON THE LINE OF WORK goal/v4.graphstore.transfer.
#   bash tools/apply_transfer_red_tests.sh           show what would be created or changed (changes nothing)
#   bash tools/apply_transfer_red_tests.sh --do      install and run the four acceptance files and CORE's save checks; commit afterwards as
#                                                    "test: TRANSFER acceptance tests (red)" and tag plan-baseline-g-v4-transfer
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
R=specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/red-tests

copy "$R/helpers/core_stores.py" tests/helpers/core_stores.py
copy "$R/helpers/transfer_stores.py" tests/helpers/transfer_stores.py
copy "$R/acceptance/test_transfer_move.py" tests/acceptance/test_transfer_move.py
copy "$R/acceptance/test_transfer_sync.py" tests/acceptance/test_transfer_sync.py
copy "$R/acceptance/test_transfer_interrupt.py" tests/acceptance/test_transfer_interrupt.py
copy "$R/acceptance/test_transfer_sets.py" tests/acceptance/test_transfer_sets.py
copy "$R/smoke/smoke_transfer.py" tests/smoke/smoke_transfer.py
finish

echo
echo "== the four acceptance files (red expected: failures, no ImportError) and CORE's save checks (green expected: the helper change)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/test_transfer_move.py tests/acceptance/test_transfer_sync.py tests/acceptance/test_transfer_interrupt.py \
         tests/acceptance/test_transfer_sets.py tests/acceptance/test_core_save.py; do
    printf '%-52s ' "$f"; "$PY" "$f" 2>&1 | tail -1
done
