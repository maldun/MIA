#!/usr/bin/env bash
# Installs the red acceptance tests of A-162 (TC-EVL-012 to 015, TR-CHAT-012; REQ-EVL-012 to 015) from the staging folder
# specs/mia/goals/G-V3.CHAT/red-tests-a162/ into the protected folder tests/acceptance. The owner runs it:
#   bash tools/apply_red_tests_a162.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_red_tests_a162.sh --do      copy the file; commit afterwards as "test: red acceptance tests of A-162 (the digest target as production)"
# The tests are red until harness.py and tools/eval.py are changed (the next task).
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
S=specs/mia/goals/G-V3.CHAT/red-tests-a162
copy $S/acceptance/test_eval_digest_production.py tests/acceptance/test_eval_digest_production.py
finish
