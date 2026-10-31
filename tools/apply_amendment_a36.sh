#!/usr/bin/env bash
# Amendment A-36 (N-5 Graph app, Q-3, D-122): a protected JavaScript mock of IF-104, so the page of the Graph app is tested on the HTTP routes it calls
# (TC-GA-002 to TC-GA-008: "unit test against the mock of IF-104"). Note: specs/mia/amendments/A-36/A-36-note.md. Protected files that change:
#   contracts/IF-104-graph-api.md                                v1: the wire of the routes, the JavaScript mock and suite named, the version line
#   tests/helpers/mocks/if_104_graph_api.mjs                     new: GraphApiMock, a fake fetch on the routes, twin of if_104_graph_api.py
#   tests/acceptance/contract/test_if_104_graph_api.test.mjs     new: TC-IF-104-01..05 on the routes, against the mock and the real Backend (skipped)
#   tests/helpers/contract.mjs                                   REAL_NOT_READY gets IF-104
# Effect: the new suite runs 10 tests (5 [mock] pass, 5 [real] skipped); the Python suite of IF-104 is unchanged.
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1), BEFORE N-5 T-02.
# Run it yourself in that worktree:
#   bash tools/apply_amendment_a36.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a36.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-36 installed" (name the paths, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-36
D=specs/mia/contract-drafts
copy $A/IF-104-graph-api.md contracts/IF-104-graph-api.md
copy $D/tests/helpers/mocks/if_104_graph_api.mjs tests/helpers/mocks/if_104_graph_api.mjs
copy $D/tests/acceptance/contract/test_if_104_graph_api.test.mjs tests/acceptance/contract/test_if_104_graph_api.test.mjs
copy $D/tests/helpers/contract.mjs tests/helpers/contract.mjs
finish
echo
node --test tests/acceptance/contract/*.test.mjs
node --test "tests/js/*.test.mjs"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_104_graph_api.py
