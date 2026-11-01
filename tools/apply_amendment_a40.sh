#!/usr/bin/env bash
# Amendment A-40 (D-132): retire the eval case n-planted-figure of eval/suites/hard_checks (tag retired, note); see specs/mia/amendments/A-40/A-40-note.md.
# Protected file that changes:
#   eval/suites/hard_checks/cases.jsonl     one line: the case n-planted-figure gets the tag `retired`
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a40.sh           show the compared file and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a40.sh --do      copy the draft over the installed file and run the harness test; commit afterwards as "plan: A-40 installed"
# Idempotent: an identical file is left alone. The draft is a whole-file copy: if the suite changed after 2026-10-31, redo the draft first.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/contract-drafts/eval/suites/hard_checks/cases.jsonl eval/suites/hard_checks/cases.jsonl
finish
echo
bash tools/run_in_image.sh tests/test_harness.py
