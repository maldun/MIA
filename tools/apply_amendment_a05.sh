#!/usr/bin/env bash
# Amendment A-05 (owner 2026-10-27): (1) IF-101 v3 names the two errors that the Backend gives and the contract did not list: 403 bad_origin and 403 insecure_channel
# (REQ-API-007, REQ-API-008); the title now says v3. (2) The contract suite of IF-101 gets a real provider as far as the Backend exists: login, throttling, whoami,
# change_password, logout and the 401 of every other operation without a session run against api_sessions.py (TC-IF-101-01, -02, -03, -10, -18 as _real tests);
# the operations that are not built yet skip. Two protected files change:
#   contracts/IF-101-chat-api.md      tests/helpers/contract.py
# Run it yourself in the MAIN checkout (the coding agent may not write there), after the branch with the amendment is merged:
#   bash tools/apply_amendment_a05.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a05.sh --do      copy the drafts over the installed files and run the suite; commit afterwards as "plan: A-05 ..."
#   bash tools/apply_amendment_a05.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-05/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy specs/mia/contract-drafts/tests/helpers/contract.py tests/helpers/contract.py
finish
echo
echo "contract suites after the amendment:"
printf '   %-26s' "test_if_101_chat_api"; python3 tests/acceptance/contract/test_if_101_chat_api.py 2>&1 | tail -1
for suite in test_if_102_storage test_if_301_graph_tables test_if_302_record_tables; do
    printf '   %-26s' "$suite"; python3 "tests/acceptance/contract/$suite.py" 2>&1 | tail -1
done
