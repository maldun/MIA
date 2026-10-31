#!/usr/bin/env bash
# Amendment A-46 (N-4.2 Operation T-03, D-133): the smoke test of the compose stack, SMOKE-MIA-003 / TC-OPR-007 (REQ-OPR-007).
# Protected files that change:
#   tests/smoke/smoke_stack.py        new: each container alone (mia, db, graph), then all together through the https front
# The rows of TC-OPR-007 (node test-spec) and SMOKE-MIA-003 (specs/mia/test-spec.md) are changed in the branch already (not protected).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after the merge of v1-n42-ops2 (the graph service and the Caddyfile route).
#   bash tools/apply_amendment_a46.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a46.sh --do      copy the draft and run the smoke test; commit afterwards as "plan: A-46 installed" (name the path, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-46
D=specs/mia/contract-drafts
[ -e $A/A-46-note.md ]
copy $D/tests/smoke/smoke_stack.py tests/smoke/smoke_stack.py
finish
echo
python tests/smoke/smoke_stack.py
