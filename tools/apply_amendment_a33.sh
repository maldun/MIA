#!/usr/bin/env bash
# Amendment A-33 (N-2.4.2 Tools and sandbox, T-04, D-116): IF-404 v1 allows the ports 8080 and 8443 besides 80 and 443, as web_tools.ALLOWED_PORTS does (owner's decision).
# Protected files that change:
#   contracts/IF-404-web.md                         v1: the port rule and golden 3 (port 22 is the refused example)
#   tests/helpers/mocks/if_404_web.py               the mock allows 80, 443, 8080, 8443
#   tests/acceptance/contract/test_if_404_web.py    TC-IF-404-02 uses port 22 instead of 8080 as the refused port
#   specs/mia/test-spec.md                          the row of TC-IF-404-02
# Tested on a scratch copy: the IF-404 and IF-402 suites and the N-2.4 integration steps as before (IF-404 real side stays skipped: stage 2).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1). Run it yourself in that worktree:
#   bash tools/apply_amendment_a33.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a33.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-33 installed" (name the paths, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-33
D=specs/mia/contract-drafts
copy $A/IF-404-web.md contracts/IF-404-web.md
copy $D/tests/helpers/mocks/if_404_web.py tests/helpers/mocks/if_404_web.py
copy $D/tests/acceptance/contract/test_if_404_web.py tests/acceptance/contract/test_if_404_web.py
copy $A/test-spec.md specs/mia/test-spec.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_404_web.py tests/acceptance/contract/test_if_402_tool_calls.py tests/test_web_tools.py
