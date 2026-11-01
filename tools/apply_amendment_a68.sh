#!/usr/bin/env bash
# Amendment A-68 (N-4.1 re-verification R1, R4; owner decision D-172, 2026-11-01): the protected smoke test of the number gate drops `--model` (the pin decides
# the model, D-166); the guard tests of the command line see whether a holdout suite was read.
# Note: specs/mia/amendments/A-68/A-68-note.md
# Protected files that change (copied from the drafts):
#   tests/smoke/smoke_gate.py                   no --model next to --pin
#   tests/acceptance/test_decide_guard.py       watch_reads: the holdout suite is not read when it is refused or hidden
# INSTALL IT ON THE LINE OF WORK goal/v1 (after the merge of v1-n41c: the tests need the early refusal of tools/eval.py `open_suite`).
#   bash tools/apply_amendment_a68.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a68.sh --do      install and run the guard test; commit afterwards as "plan: A-68 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/amendments/A-68
copy $D/tests/smoke/smoke_gate.py tests/smoke/smoke_gate.py
copy $D/tests/acceptance/test_decide_guard.py tests/acceptance/test_decide_guard.py
finish
echo
echo "== tests/acceptance/test_decide_guard.py"
python3 tests/acceptance/test_decide_guard.py 2>&1 | tail -3
