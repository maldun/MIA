#!/usr/bin/env bash
# Amendment A-09 (owner 2026-10-27): the due time of a task (REQ-CHA-019). IF-101 v6: `save_item` takes an optional `due` (tasks only), `items` shows it, `invalid_item` gets the rule `due`. Four protected files change:
#   contracts/IF-101-chat-api.md   tests/helpers/mocks/if_101_chat_api.py   tests/helpers/contract.py   tests/acceptance/contract/test_if_101_chat_api.py
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a09.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a09.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-09 ..."
#   bash tools/apply_amendment_a09.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
A=specs/mia/amendments/A-09
copy $A/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy $D/tests/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy $D/tests/helpers/contract.py tests/helpers/contract.py
copy $D/tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
finish
echo
echo "contract suites after the amendment (in the image: the real providers need flask):"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_201_chat_turn.py tests/test_chat_mock_server.py tests/test_items_api.py
