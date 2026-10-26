#!/usr/bin/env bash
# Amendment A-07 (owner 2026-10-27): the real providers of IF-101 and IF-201 in the contract suites, as far as the code exists. The adapter in tests/helpers/contract.py
# now drives the REAL routes (items_api, trust_persona_api, chat_ops_api) and the real ChatService with a scripted model, so the tests of records, trust, persona,
# votes, scores, regenerate, speak again, account, history and the queue run as _real tests instead of skipping: IF-101 15 -> 3 skipped, IF-201 7 -> 2 skipped
# (what is still skipped: expression/audio_chunk events N-2.5, stop of an answer that has not started N-2.2 T-01, the character variant REQ-CHV-008). The suites forward
# the options of `make` (scripted answers, queue limit) to the real provider; nothing else in them changes. Three protected files change:
#   tests/helpers/contract.py   tests/acceptance/contract/test_if_101_chat_api.py   tests/acceptance/contract/test_if_201_chat_turn.py
# The same branch fixes chat_service.py (regenerate of a user message is 422 not_the_last_answer like the contract, not 404), found by the first real run.
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a07.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a07.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-07 ..."
#   bash tools/apply_amendment_a07.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
copy $D/tests/helpers/contract.py tests/helpers/contract.py
copy $D/tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
copy $D/tests/acceptance/contract/test_if_201_chat_turn.py tests/acceptance/contract/test_if_201_chat_turn.py
finish
echo
echo "contract suites after the amendment (in the image: the real providers need flask):"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_201_chat_turn.py tests/acceptance/contract/test_if_102_storage.py \
    tests/acceptance/contract/test_if_301_graph_tables.py tests/acceptance/contract/test_if_302_record_tables.py
