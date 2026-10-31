#!/usr/bin/env bash
# Amendment A-45 (N-2.4.2, re-verification findings N-1, N-2; D-133): IF-402 v5, text only: bad_arguments also for an argument of the wrong type;
# evidence of number_check may be one text (one passage). The provider side is on branch v1-f7-n2 (commits ad9f482, b667a43).
# Protected file that changes:
#   contracts/IF-402-tool-calls.md
# Not in it: the mock does not check types (a wrong type raises a raw error there); the contract suite has no case for it yet.
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after A-44 and the merge of v1-f7-n2.
#   bash tools/apply_amendment_a45.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a45.sh --do      copy the draft and run the IF-402 suite; commit afterwards as "plan: A-45 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-45/IF-402-tool-calls.md contracts/IF-402-tool-calls.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_402_tool_calls.py tests/test_tool_calls.py
