#!/usr/bin/env bash
# Amendment A-22 (N-2.3 T-01, D-98): the acceptance tests TC-WFM-002, TC-WFM-003, TC-WFM-004 and TC-WFM-026 get a file that carries their markers (the criteria were covered by
# tests/test_workflow_library.py, but no file named the TC ids). One new protected file:
#   tests/acceptance/test_workflow_library.py
# The tests run on the real WorkflowLibrary and the real Storage (file backend), so they are green from the start. TC-WFM-002 and -004 were typed by the local coder model
# and reviewed line by line against the instruction; TC-WFM-003 (seeded property test) and TC-WFM-026 were written by hand.
# Run it yourself in the MAIN checkout, after the branch is merged:
#   bash tools/apply_amendment_a22.sh           show the compared file (changes nothing)
#   bash tools/apply_amendment_a22.sh --do      copy the draft and run it; commit afterwards as "plan: A-22 ..."
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/contract-drafts/tests/acceptance/test_workflow_library.py tests/acceptance/test_workflow_library.py
finish
echo
python3 tests/acceptance/test_workflow_library.py
