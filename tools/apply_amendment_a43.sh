#!/usr/bin/env bash
# Amendment A-43 (N-2.4.1, D-113, Verify finding F8): IF-202 v1, the statuses stopped and error and the error pin_unavailable; text only.
# Protected file that changes:
#   contracts/IF-202-run-workflow.md
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a43.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a43.sh --do      copy the draft and run the IF-202 suite; commit afterwards as "plan: A-43 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-43/IF-202-run-workflow.md contracts/IF-202-run-workflow.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_202_run_workflow.py tests/test_run_workflow.py
