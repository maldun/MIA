#!/usr/bin/env bash
# Amendment A-42 (N-2.4.2 Tools and sandbox, Verify findings 6, 8, 11; D-132): IF-402 v3. The provider side is commit 191a8f3 (tool_calls.py).
# Protected files that change:
#   contracts/IF-402-tool-calls.md                           v3: run_script status failed and its result; the dropped works of scholar_search; the error bad_arguments
#   tests/helpers/mocks/if_402_tool_calls.py                 bad_arguments before anything is counted
#   tests/acceptance/contract/test_if_402_tool_calls.py      TC-IF-402-07 (bad_arguments, uncounted), mock and real
#   specs/mia/test-spec.md                                   the row of TC-IF-402-07
# The model part toolDoor (tool_calls.py, finding 9) is already in specs/mia/architecture.sysml (not protected).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after commit 191a8f3.
#   bash tools/apply_amendment_a42.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a42.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-42 installed" (name the paths, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-42
D=specs/mia/contract-drafts
copy $A/IF-402-tool-calls.md contracts/IF-402-tool-calls.md
copy $D/tests/helpers/mocks/if_402_tool_calls.py tests/helpers/mocks/if_402_tool_calls.py
copy $D/tests/acceptance/contract/test_if_402_tool_calls.py tests/acceptance/contract/test_if_402_tool_calls.py
copy $A/test-spec.md specs/mia/test-spec.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_402_tool_calls.py tests/test_tool_calls.py tests/test_tool_calls_sandbox.py tests/test_runner_interfaces.py
