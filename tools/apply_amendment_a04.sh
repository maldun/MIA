#!/usr/bin/env bash
# Amendment A-04 (owner 2026-10-26): (1) IF-111: an unknown expression name keeps the current expression (was: neutral);
# (2) IF-101 v2: logout (new requirements REQ-FE-031, REQ-CLV-022, REQ-BE-077, REQ-API-017).
# Protected files that change:
#   contracts/IF-101-chat-api.md, contracts/IF-111-character-bridge.md          (the specifications)
#   tests/helpers/mocks/if_101_chat_api.py, tests/helpers/mocks/if_111_character_bridge.mjs   (the mocks)
#   tests/acceptance/contract/test_if_101_chat_api.py (TC-IF-101-18 is new), test_if_111_character_bridge.test.mjs (TC-IF-111-02 changed)
# Run it yourself in the MAIN checkout (the coding agent may not write there), after the branch with the amendment is merged:
#   bash tools/apply_amendment_a04.sh          (shows what differs)
#   bash tools/apply_amendment_a04.sh --do     (copies the drafts over the installed files, runs both suites; commit afterwards as "plan: A-04 ...")
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
copy specs/mia/amendments/A-04/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy specs/mia/amendments/A-04/IF-111-character-bridge.md contracts/IF-111-character-bridge.md
copy specs/mia/contract-drafts/tests/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy specs/mia/contract-drafts/tests/helpers/mocks/if_111_character_bridge.mjs tests/helpers/mocks/if_111_character_bridge.mjs
copy specs/mia/contract-drafts/tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
copy specs/mia/contract-drafts/tests/acceptance/contract/test_if_111_character_bridge.test.mjs tests/acceptance/contract/test_if_111_character_bridge.test.mjs
if [ "$do_it" = 0 ] && [ "$changed" -gt 0 ]; then echo "$changed file(s) differ: run again with --do"; exit 0; fi
printf '%-34s' "test_if_101_chat_api"; python3 tests/acceptance/contract/test_if_101_chat_api.py 2>&1 | tail -1
printf '%-34s' "test_if_111_character_bridge"; node --test tests/acceptance/contract/test_if_111_character_bridge.test.mjs 2>&1 | grep -E "^# (pass|fail)" | tr '\n' ' '; echo
