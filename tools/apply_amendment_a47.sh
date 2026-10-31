#!/usr/bin/env bash
# Amendment A-47 (N-4.2 Operation T-07, D-136): the smoke test of a fresh installation, SMOKE-MIA-001 / TC-OPR-001 (REQ-OPR-001, REQ-OPR-002).
# Protected files that change:
#   tests/smoke/smoke_fresh_install.py   new: fresh checkout, deploy/.env with the address of the running Ollama, deploy/up.sh db; containers, database,
#                                        first account, one chat answer; never pulls a model or an image
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after the merge of v1-n42-ops2 (up.sh of T-06 and T-07).
#   bash tools/apply_amendment_a47.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a47.sh --do      copy the draft and run the smoke test; commit afterwards as "plan: A-47 installed" (name the path, no `git add -A`)
# Idempotent: an identical file is left alone. The smoke test clones the committed HEAD: commit before running it.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-47
D=specs/mia/contract-drafts
[ -e $A/A-47-note.md ]
copy $D/tests/smoke/smoke_fresh_install.py tests/smoke/smoke_fresh_install.py
finish
echo
python tests/smoke/smoke_fresh_install.py
