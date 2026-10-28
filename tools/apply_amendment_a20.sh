#!/usr/bin/env bash
# Amendment A-20 (owner 2026-10-28, N-2.3 T-07, D-96): IF-101 v7, the task /review and the answer to a waiting review (owner chose "blocking with an answer channel"). One protected file changes:
#   contracts/IF-101-chat-api.md
# NOT part of this amendment (open, protected files): the mock tests/helpers/mocks/if_101_chat_api.py, the real adapter in tests/helpers/contract.py and a contract test of the waiting review
# in tests/acceptance/contract/test_if_101_chat_api.py. The behaviour is tested by tests/test_chat_review.py; the installed contract suite is unchanged and passes.
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a20.sh           show the compared file and the diff (changes nothing)
#   bash tools/apply_amendment_a20.sh --do      copy the draft over the installed file and run the checks; commit afterwards as "plan: A-20 ..."
#   bash tools/apply_amendment_a20.sh --full    the whole diff instead of the first 60 lines
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-20
copy $A/IF-101-chat-api.md contracts/IF-101-chat-api.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/test_chat_review.py
