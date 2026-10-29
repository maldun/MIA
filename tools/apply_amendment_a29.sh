#!/usr/bin/env bash
# Amendment A-29 (N-2.4.3 Run log, T-01, D-109): the real provider of IF-401 in the contract suite. One protected file changes:
#   tests/helpers/contract.py   an adapter for run_events.RunEvents (the provider of this branch) and the removal of the reason "N-2.4.3 Run log not integrated yet"
# Effect: the four tests of tests/acceptance/contract/test_if_401_run_events.py run as _real as well as _mock (8 tests, none skipped); no other suite changes.
# INSTALL IT AFTER THE MERGE of the branch if401-provider (the adapter imports run_events.py).
# Run it yourself in the MAIN checkout:
#   bash tools/apply_amendment_a29.sh           show the compared file and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a29.sh --do      copy the draft over the installed file and run the suites; commit afterwards as "plan: A-29 ..." (name the paths, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/contract-drafts/tests/helpers/contract.py tests/helpers/contract.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_401_run_events.py tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_201_chat_turn.py tests/test_run_events.py
