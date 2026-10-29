#!/usr/bin/env bash
# Amendment A-30 (N-2.4.3 Run log, D-110): IF-401 v1 names the three errors the provider already raises (invalid_run, invalid_payload, invalid_user) and the order of the checks of emit.
# Five files change (three protected):
#   contracts/IF-401-run-events.md                          v1: three rows in Errors, the order of the checks, golden example 2, version history
#   tests/helpers/mocks/if_401_run_events.py                the mock raises the three errors in the same order as run_events.RunEvents
#   tests/acceptance/contract/test_if_401_run_events.py     TC-IF-401-05 (mock and real)
#   specs/mia/test-spec.md                                  the row TC-IF-401-05
#   .../N-2.4.3-run-log/requirements.md                     IF-401 verified by TC-IF-401-01..05, history
# Nothing in the code changes: run_events.py raises these errors since T-01 (A-29). Tested on a scratch copy: 10 tests of the IF-401 suite pass (5 mock, 5 real), the N-2.4 scenario and tests/test_run_events.py unchanged.
# Run it yourself in the MAIN checkout, after the branch a30-if401-errors is merged:
#   bash tools/apply_amendment_a30.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a30.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-30 installed" (name the paths, no `git add -A`)
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-30
D=specs/mia/contract-drafts
N=specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.3-run-log
copy $A/IF-401-run-events.md contracts/IF-401-run-events.md
copy $D/tests/helpers/mocks/if_401_run_events.py tests/helpers/mocks/if_401_run_events.py
copy $D/tests/acceptance/contract/test_if_401_run_events.py tests/acceptance/contract/test_if_401_run_events.py
copy $A/test-spec.md specs/mia/test-spec.md
copy $A/N243-requirements.md $N/requirements.md
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_401_run_events.py tests/test_run_events.py
