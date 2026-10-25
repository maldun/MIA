#!/usr/bin/env bash
# Install the drafted mocks and contract suites from specs/mia/contract-drafts/ into the protected folders
# (tests/helpers/ and tests/acceptance/contract/). Run it yourself: the coding agent may not write there.
# Idempotent: a file that is missing is copied, an identical file is left alone, a file that differs is NOT overwritten
# (protected files change by amendment only); the script says so and exits with 1 at the end.
# After it: run the suites with  bash tools/install_contract_drafts.sh --run
set -u
cd "$(dirname "$0")/.."
SRC=specs/mia/contract-drafts
status=0

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
    done < <(find "$SRC/tests" -type f \( -name '*.py' -o -name '*.mjs' \) | sort)
fi

if [ "${1:-}" = "--run" ] || [ "$status" = 0 ]; then
    for suite in tests/acceptance/contract/test_if_*.py; do
        echo "== $suite"
        python3 "$suite" 2>&1 | tail -3
    done
    echo "== node --test tests/acceptance/contract/*.test.mjs"
    node --test tests/acceptance/contract/*.test.mjs 2>&1 | grep -E '^# (tests|pass|fail|skipped)'
fi
exit $status
