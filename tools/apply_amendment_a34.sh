#!/usr/bin/env bash
# Amendment A-34 (N-2.4.1 Pipeline runner, T-07, D-122): IF-402 v2 offers fetch_page, the tool the research pipelines read pages with, so the runner reaches it
# through the door (REQ-RUN-012). The real provider (tool_calls.ToolCalls._fetch_page) is in commit 356f90b. Protected files that change:
#   contracts/IF-402-tool-calls.md                           v2: the row fetch_page, golden example 4, the version line
#   tests/helpers/mocks/if_402_tool_calls.py                 fetch_page on the scripted pages (source_error for an unknown page)
#   tests/acceptance/contract/test_if_402_tool_calls.py      TC-IF-402-06 (golden 4), against the mock and the real provider
#   specs/mia/test-spec.md                                   the row of TC-IF-402-06
# Effect: test_if_402_tool_calls.py runs 12 tests (6 _mock, 6 _real), none skipped. The adapter of tests/helpers/contract.py is unchanged.
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), after commit 356f90b.
# Run it yourself in that worktree:
#   bash tools/apply_amendment_a34.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a34.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-34 installed" (name the paths, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-34
D=specs/mia/contract-drafts
copy $A/IF-402-tool-calls.md contracts/IF-402-tool-calls.md
copy $D/tests/helpers/mocks/if_402_tool_calls.py tests/helpers/mocks/if_402_tool_calls.py
copy $D/tests/acceptance/contract/test_if_402_tool_calls.py tests/acceptance/contract/test_if_402_tool_calls.py
copy $A/test-spec.md specs/mia/test-spec.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_402_tool_calls.py tests/test_tool_calls.py tests/test_runner_interfaces.py
