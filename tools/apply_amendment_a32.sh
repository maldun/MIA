#!/usr/bin/env bash
# Amendment A-32 (N-2.4.2 Tools and sandbox, T-01, D-115): IF-402 v1 and the real provider of IF-402 in the contract suite. Protected files that change:
#   contracts/IF-402-tool-calls.md                           v1: the problems of schema_check are readable texts that name the path and the key ("$: missing 'reason'")
#   tests/acceptance/contract/test_if_402_tool_calls.py      TC-IF-402-05 checks that the one problem names 'reason' instead of comparing it with ["reason"]
#   tests/helpers/contract.py                                an adapter for tool_calls.ToolCalls with the scripted page, finding, work and trust entry of the mock and no
#                                                            sandbox; the reason "N-2.4.2 Tools and sandbox not integrated yet" is removed
#   specs/mia/test-spec.md                                   the criterion of TC-IF-402-05 (the row was cut off after "checks are")
# Effect: the 5 tests of test_if_402_tool_calls.py run as _real as well as _mock (10 tests, none skipped). The mock is unchanged.
# Tested on a scratch copy: all 15 contract suites and the integration steps of N-2 and N-2.4 as before (skips only where the provider is not built).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after commit 3f7d5c8 (the adapter imports tool_calls.py).
# Run it yourself in that worktree:
#   bash tools/apply_amendment_a32.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a32.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-32 installed" (name the paths, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-32
D=specs/mia/contract-drafts
copy $A/IF-402-tool-calls.md contracts/IF-402-tool-calls.md
copy $D/tests/acceptance/contract/test_if_402_tool_calls.py tests/acceptance/contract/test_if_402_tool_calls.py
copy $D/tests/helpers/contract.py tests/helpers/contract.py
copy $A/test-spec.md specs/mia/test-spec.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_402_tool_calls.py tests/test_tool_calls.py
