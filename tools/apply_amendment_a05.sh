#!/usr/bin/env bash
# Amendment A-05 (owner 2026-10-27): (1) IF-101 v3 names the two errors that the Backend gives and the contract did not list: 403 bad_origin and 403 insecure_channel
# (REQ-API-007, REQ-API-008); the title now says v3. (2) The contract suite of IF-101 gets a real provider as far as the Backend exists: login, throttling, whoami,
# change_password, logout and the 401 of every other operation without a session run against api_sessions.py (TC-IF-101-01, -02, -03, -10, -18 as _real tests);
# the operations that are not built yet skip. Two protected files change:
#   contracts/IF-101-chat-api.md      tests/helpers/contract.py
# Run it yourself in the MAIN checkout (the coding agent may not write there), after the branch with the amendment is merged:
#   bash tools/apply_amendment_a05.sh          (shows what differs)
#   bash tools/apply_amendment_a05.sh --do     (copies the drafts over the installed files and runs the suite; commit afterwards as "plan: A-05 ...")
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
do_it=0
[ "${1:-}" = "--do" ] && do_it=1
changed=0
copy() {   # draft installed
    if [ ! -e "$2" ]; then echo "MISSING   $2"; exit 1; fi
    if cmp -s "$1" "$2"; then echo "unchanged $2"; return; fi
    changed=$((changed + 1))
    if [ "$do_it" = 1 ]; then cp "$1" "$2" && echo "updated   $2"; else echo "DIFFERS   $2"; fi
}
copy specs/mia/amendments/A-05/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy specs/mia/contract-drafts/tests/helpers/contract.py tests/helpers/contract.py
if [ "$do_it" = 0 ] && [ "$changed" -gt 0 ]; then echo "$changed file(s) differ: run again with --do"; exit 0; fi
printf '%-34s' "test_if_101_chat_api"; python3 tests/acceptance/contract/test_if_101_chat_api.py 2>&1 | tail -1
printf '%-34s' "other contract suites"; for suite in 102 301 302; do python3 "tests/acceptance/contract/test_if_${suite}_$(case $suite in 102) echo storage;; 301) echo graph_tables;; 302) echo record_tables;; esac).py" 2>&1 | tail -1; done | sort | uniq -c | tr '\n' ' '; echo
