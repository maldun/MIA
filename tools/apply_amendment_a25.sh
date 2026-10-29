#!/usr/bin/env bash
# Amendment A-25 (follow-up of A-23 and A-24, D-102): the contract suite of IF-101 gets what v8 promised and T-11 needs. Four protected files change:
#   contracts/IF-101-chat-api.md (v9)   tests/helpers/contract.py   tests/helpers/mocks/if_101_chat_api.py   tests/acceptance/contract/test_if_101_chat_api.py
# Adapter: the real ChatService now gets a task registry (T-11 removed the old `run_review=` argument, which the installed adapter still passes: 23 real tests fail without this amendment),
# a files volume, pause/resume/files/file. Mock: task_status, pause/resume, `/review options`, files, the result as the newest message. Tests: TC-IF-101-26 (result at the end),
# -27 (status card), -28 (pause, resume, stop), -29 (options), -30 (files). Contract text v9: a bad option is `422 invalid_command` (v8 said "a message of MIA").
# INSTALL THIS TOGETHER WITH THE MERGE OF t11-extensions (the branch changes chat_service.py; the installed adapter does not fit it).
# Run it yourself in the MAIN checkout, after the branch is merged:
#   bash tools/apply_amendment_a25.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a25.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-25 ..." (name the paths, no `git add -A`)
#   bash tools/apply_amendment_a25.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts/tests
copy specs/mia/amendments/A-25/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy $D/helpers/contract.py tests/helpers/contract.py
copy $D/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy $D/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_201_chat_turn.py tests/test_chat_mock_server.py
