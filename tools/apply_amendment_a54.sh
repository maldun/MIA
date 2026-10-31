#!/usr/bin/env bash
# Amendment A-54 (N-2.1, D-149, 2026-10-31, Verify finding V-5): IF-101 v12, a message over the rate limit (10 per 60 s per account) is `429 rate_limited`.
# Protected files that change:
#   contracts/IF-101-chat-api.md                              v12: the send row, a row of the error table, the version line
#   tests/helpers/mocks/if_101_chat_api.py                   the mock counts the messages of an account within 60 s (RATE_LIMIT 10)
#   tests/acceptance/contract/test_if_101_chat_api.py        TC-IF-101-30 (mock and real)
#   specs/mia/test-spec.md                                    the row of TC-IF-101-30 after the one of TC-IF-101-19 (made from the installed file at run time)
# The real side passes already: chat_service.py answers the refusal with the code rate_limited (branch v1-n21b) and the adapter of
# tests/helpers/contract.py maps that code to 429. Note: specs/mia/amendments/A-54/A-54-note.md
# INSTALL IT ON THE LINE OF WORK goal/v1 after the merge of v1-n21b.
#   bash tools/apply_amendment_a54.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a54.sh --do      install and run the IF-101 suite in the image; commit afterwards as "plan: A-54 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-54
D=specs/mia/contract-drafts
SPEC=$(mktemp)
trap 'rm -f "$SPEC"' EXIT
python3 - specs/mia/test-spec.md "$SPEC" <<'PY'
import sys
row = ("| TC-IF-101-30 | IF-101 | Contract | 1 (mock) and 2 (real) | v12 (A-54, D-149): ten messages of one account within 60 s pass; the 11th is "
       "429 rate_limited and is not stored; another account still sends. REQ-API-007. | exact |\n")
text = open(sys.argv[1], encoding="utf-8").read()
if row not in text:
    lines = text.splitlines(keepends=True)
    after = [i for i, line in enumerate(lines) if line.startswith("| TC-IF-101-19 |")]
    if len(after) != 1:
        sys.exit("the row of TC-IF-101-19 is not found exactly once in specs/mia/test-spec.md; add the row of TC-IF-101-30 by hand")
    lines.insert(after[0] + 1, row)
    text = "".join(lines)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
copy $A/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy $D/tests/helpers/mocks/if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
copy $D/tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_101_chat_api.py
copy "$SPEC" specs/mia/test-spec.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py
