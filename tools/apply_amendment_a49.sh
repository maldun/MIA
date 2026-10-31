#!/usr/bin/env bash
# Amendment A-49 (N-2.4.3, D-138): IF-101 v11, text only: `account` is the steps kept with every answer (also without a status block), not the run log IF-401.
# The provider side is on branch v1-n243 (commit 7f0d59e, chat_service.py). Protected file that changes:
#   contracts/IF-101-chat-api.md
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after the merge of v1-n243.
#   bash tools/apply_amendment_a49.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a49.sh --do      copy the draft and run the IF-101 suite; commit afterwards as "plan: A-49 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-49/IF-101-chat-api.md contracts/IF-101-chat-api.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/test_chat_backend.py
