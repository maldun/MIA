#!/usr/bin/env bash
# Amendment A-06 (owner 2026-10-27): (1) IF-101 v4: the score (and the event `score`) carries `series`, the sums per ISO week of the vote's time (REQ-CLV-010, "by time, per week").
# (2) IF-201 v1: the chat agent offers regenerate, speak_again, account, vote and score (and the events variant and score) that IF-101 v1 needs; records, trust and persona
# go through the Database (IF-102), not through the chat agent. (3) The mocks and the contract suites follow; the suite of IF-201 also loses a failure that was there since A-03
# (the mock of IF-201 leaked the `message` of the IF-101 ack). The real provider for the new operations comes later (A-07) when the code exists. Six protected files change:
#   contracts/IF-101-chat-api.md   contracts/IF-201-chat-turn.md
#   tests/helpers/mocks/if_101_chat_api.py   tests/helpers/mocks/if_201_chat_turn.py
#   tests/acceptance/contract/test_if_101_chat_api.py   tests/acceptance/contract/test_if_201_chat_turn.py
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a06.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a06.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-06 ..."
#   bash tools/apply_amendment_a06.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
copy specs/mia/amendments/A-06/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy specs/mia/amendments/A-06/IF-201-chat-turn.md contracts/IF-201-chat-turn.md
copy $D/tests/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy $D/tests/helpers/mocks/if_201_chat_turn.py tests/helpers/mocks/if_201_chat_turn.py
copy $D/tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
copy $D/tests/acceptance/contract/test_if_201_chat_turn.py tests/acceptance/contract/test_if_201_chat_turn.py
finish
echo
echo "contract suites after the amendment:"
for suite in test_if_101_chat_api test_if_201_chat_turn; do
    printf '   %-26s' "$suite"; python3 "tests/acceptance/contract/$suite.py" 2>&1 | tail -1
done
