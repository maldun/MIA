#!/usr/bin/env bash
# Amendment A-08 (owner 2026-10-27): the adaptation counters and the cases of a minus on a fact (REQ-CHA-016 to -018, parents REQ-BE-029 to -031).
# (1) IF-302 v1: two tables, `cases` (proposed benchmark cases) and `behaviours` (the adaptation counters), versioned and not deletable.
# (2) IF-101 v5: `counters`, `reset_counter`, the event `counters_changed`; `invalid_vote` gets the rule `subject` (a `character_behaviour` vote on a name that is not on
#     the list); the mock keeps one vote per user, category and subject like the real Backend; `regenerate` of a user message is 422, written down.
# (3) IF-201 v2: the same operations of the chat agent. The mocks, the suites (TC-IF-101-22, TC-IF-201-08, tables in TC-IF-302-01/03) and the real adapters of
#     tests/helpers/contract.py follow; the suites now have five accounts (anna, ben, carl, dora, emil): 5 net negative votes need 5 voters. Eleven protected files change:
#   contracts/IF-101-chat-api.md   contracts/IF-201-chat-turn.md   contracts/IF-302-record-tables.md
#   tests/helpers/mocks/if_101_chat_api.py   if_201_chat_turn.py   if_302_record_tables.py   if_102_storage.py   tests/helpers/contract.py
#   tests/acceptance/contract/test_if_101_chat_api.py   test_if_201_chat_turn.py   test_if_302_record_tables.py
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a08.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a08.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-08 ..."
#   bash tools/apply_amendment_a08.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
A=specs/mia/amendments/A-08
copy $A/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy $A/IF-201-chat-turn.md contracts/IF-201-chat-turn.md
copy $A/IF-302-record-tables.md contracts/IF-302-record-tables.md
for mock in if_101_chat_api if_201_chat_turn if_302_record_tables if_102_storage; do
    copy $D/tests/helpers/mocks/$mock.py tests/helpers/mocks/$mock.py
done
copy $D/tests/helpers/contract.py tests/helpers/contract.py
for suite in test_if_101_chat_api test_if_201_chat_turn test_if_302_record_tables; do
    copy $D/tests/acceptance/contract/$suite.py tests/acceptance/contract/$suite.py
done
finish
echo
echo "contract suites after the amendment (in the image: the real providers need flask):"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_201_chat_turn.py tests/acceptance/contract/test_if_102_storage.py \
    tests/acceptance/contract/test_if_301_graph_tables.py tests/acceptance/contract/test_if_302_record_tables.py
