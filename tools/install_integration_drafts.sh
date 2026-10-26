#!/usr/bin/env bash
# Install the drafted integration tests from specs/mia/integration-drafts/ into the protected folders
# (tests/helpers/integration.py and tests/integration/<node>/). Run it yourself: the coding agent may not write there.
# Needs the contract drafts first (tools/install_contract_drafts.sh): the steps use the mocks and contract.py.
# Idempotent: a missing file is copied, an identical file is left alone, a file that differs is NOT overwritten
# (protected files change by amendment only); the script says so and exits with 1 at the end.
# After it: run the steps with  bash tools/install_integration_drafts.sh --run
set -u
cd "$(dirname "$0")/.."
SRC=specs/mia/integration-drafts
status=0

if [ ! -e tests/helpers/contract.py ]; then
    echo "tests/helpers/contract.py is missing: run  bash tools/install_contract_drafts.sh  first"
    exit 1
fi

if [ "${1:-}" != "--run" ]; then
    while IFS= read -r file; do
        rel=${file#"$SRC"/}
        if [ ! -e "$rel" ]; then
            mkdir -p "$(dirname "$rel")" && cp "$file" "$rel" && echo "installed  $rel"
        elif cmp -s "$file" "$rel"; then
            echo "unchanged  $rel"
        else
            echo "DIFFERS    $rel (not overwritten; change protected files by amendment)"
            status=1
        fi
    done < <(find "$SRC/tests" -type f -name '*.py' | sort)
fi

if [ "${1:-}" = "--run" ] || [ "$status" = 0 ]; then
    for step in tests/integration/*/step_*/test_step.py; do
        echo "== $step"
        python3 "$step" 2>&1 | tail -3
    done
fi
exit $status
