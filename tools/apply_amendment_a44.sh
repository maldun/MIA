#!/usr/bin/env bash
# Amendment A-44 (N-2.4.2, re-verification findings N-3, N-4): IF-402 v4, text only (what leaves the host as REQ-TLS-007 after A-41; result of run_script only
# when the script reached a sandbox). Protected file that changes:
#   contracts/IF-402-tool-calls.md
# Not in it: the mock still has no `result` for run_script and cannot end `failed` (N-3, open).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after A-42.
#   bash tools/apply_amendment_a44.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a44.sh --do      copy the draft and run the IF-402 suite; commit afterwards as "plan: A-44 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-44/IF-402-tool-calls.md contracts/IF-402-tool-calls.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_402_tool_calls.py
