#!/usr/bin/env bash
# Amendment A-21 (N-2.3 T-07, D-97): the contract of IF-101 v7 (A-20, the waiting /review) gets its mock, its real adapter and two contract tests. Three protected files change:
#   tests/helpers/mocks/if_101_chat_api.py   tests/helpers/contract.py   tests/acceptance/contract/test_if_101_chat_api.py
# Mock: option `review` (the questions a scripted /review asks, default one), the answer of the same account is not queued (`queued` false, position 0), `stop` ends a waiting
# review, the status has `activity`; every ack has `queued`. Adapter: the real ChatService with a scripted review (a thread, because a review blocks while it waits), `stop`
# for a running review (the stop of an answer that has not started still skips, N-2.2 T-01). Tests: TC-IF-101-24 (the answer channel), TC-IF-101-25 (stop while waiting).
# Tested on a scratch copy: all IF-101 tests pass as mock and real (3 skips as before), the IF-201, IF-102, IF-302, IF-203 suites and tests/test_chat_mock_server.py are unchanged.
# Run it yourself in the MAIN checkout, after the branch is merged:
#   bash tools/apply_amendment_a21.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a21.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-21 ..."
#   bash tools/apply_amendment_a21.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
copy $D/tests/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy $D/tests/helpers/contract.py tests/helpers/contract.py
copy $D/tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_201_chat_turn.py tests/test_chat_mock_server.py
