#!/usr/bin/env bash
# Amendment A-31 (N-2.4.1 Pipeline runner, T-01, D-113): the real providers of IF-202 and IF-105 in the contract suites. One protected file changes:
#   tests/helpers/contract.py   an adapter for run_workflow.WorkflowRuns over the real Core and WorkflowLibrary with a fake model and the fixtures of the mocks
#                               (lookup: three steps, answer "42"; drifting: estimated at 2 calls, needs 4), and the removal of the reasons
#                               "N-2 Backend not integrated yet" (IF-105) and "N-2.4 Workflow execution not integrated yet" (IF-202)
# Effect: the 5 tests of test_if_202_run_workflow.py and the 4 of test_if_105_evaluation_access.py run as _real as well as _mock (18 tests, none skipped).
# Tested on a scratch copy: all 15 contract suites and the N-2.4 integration steps as before (skips only where the provider is not built).
# INSTALL IT AFTER THE MERGE of the branch n241-t01 (the adapter imports run_workflow.py).
# Run it yourself in the MAIN checkout:
#   bash tools/apply_amendment_a31.sh           show the compared file and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a31.sh --do      copy the draft over the installed file and run the suites; commit afterwards as "plan: A-31 installed" (name the paths, no `git add -A`)
# Idempotent: an identical file is left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/contract-drafts/tests/helpers/contract.py tests/helpers/contract.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_202_run_workflow.py tests/acceptance/contract/test_if_105_evaluation_access.py tests/acceptance/contract/test_if_401_run_events.py tests/acceptance/contract/test_if_203_workflow_library.py tests/test_run_workflow.py
