#!/usr/bin/env bash
# Amendment A-27 (owner's hand test of /review, 2026-10-29, D-106): (1) the time cap of the mode run is 30 minutes of WORK time (a pause and the time the user needs to answer do not count)
# and at a hard cap the review asks: continue, summarize or stop (no answer summarizes); (2) a task that fails leaves a result that says why; (3) the files of a task are download links at
# the end of its result. REQ-WFM-019, -034, -036, -037 and REQ-BE-054 reworded, TC-WFM-034/-036/-037 reworded, IF-101 v10, mock and contract tests (TC-IF-101-24 exact text, -30 link, -31 failure).
# The code for this is on the branch hand-test-fixes; the installed contract test TC-IF-101-24 expects the old exact text, so INSTALL THIS TOGETHER WITH THE MERGE of that branch.
# Files that change:  N-2 requirements.md   N-2.3 requirements.md, test-spec.md   specs/mia/architecture.sysml (model block)   contracts/IF-101-chat-api.md
#                     tests/helpers/contract.py   tests/helpers/mocks/if_101_chat_api.py   tests/acceptance/contract/test_if_101_chat_api.py
# Run it yourself in the MAIN checkout, after the branch is merged:
#   bash tools/apply_amendment_a27.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a27.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-27 ..." (name the paths, no `git add -A`)
#   bash tools/apply_amendment_a27.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-27
D=specs/mia/contract-drafts/tests
copy $A/N2-requirements.md specs/mia/nodes/N-2-backend/requirements.md
copy $A/N23-requirements.md specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md
copy $A/N23-test-spec.md specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/test-spec.md
copy $A/architecture.sysml specs/mia/architecture.sysml
copy $A/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy $D/helpers/contract.py tests/helpers/contract.py
copy $D/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy $D/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
finish
echo
echo "checks after the amendment:"
python3 -I tools/check_sysml_model.py .
bash tools/check_sysml.sh specs/mia/architecture.sysml
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/test_review_chain.py tests/test_chat_mock_server.py
