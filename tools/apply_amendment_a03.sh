#!/usr/bin/env bash
# Amendment A-03 (owner 2026-10-26: "IF-101 v1"): the interface between the browser and the Backend gets what the views of N-1.1 need.
# Three protected files change:
#   contracts/IF-101-chat-api.md                              (the specification, v1)
#   tests/helpers/mocks/if_101_chat_api.py                    (the mock)
#   tests/acceptance/contract/test_if_101_chat_api.py         (the contract suite: TC-IF-101-09 to 17 are new)
# Run it yourself in the MAIN checkout (the coding agent may not write there), after the branch with the amendment is merged:
#   bash tools/apply_amendment_a03.sh          (shows what differs)
#   bash tools/apply_amendment_a03.sh --do     (copies the drafts over the installed files, runs the suite; commit afterwards as "plan: A-03 ...")
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
do_it=0
[ "${1:-}" = "--do" ] && do_it=1
changed=0
copy() {   # draft installed
    if [ ! -e "$2" ]; then echo "MISSING   $2"; exit 1; fi
    if cmp -s "$1" "$2"; then echo "unchanged $2"; return; fi
    changed=$((changed + 1))
    if [ "$do_it" = 1 ]; then cp "$1" "$2" && echo "updated   $2"; else echo "DIFFERS   $2"; fi
}
copy specs/mia/amendments/A-03/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy specs/mia/contract-drafts/tests/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy specs/mia/contract-drafts/tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
if [ "$do_it" = 0 ] && [ "$changed" -gt 0 ]; then echo "$changed file(s) differ: run again with --do"; exit 0; fi
printf '%-34s' "test_if_101_chat_api"; python3 tests/acceptance/contract/test_if_101_chat_api.py 2>&1 | tail -1
