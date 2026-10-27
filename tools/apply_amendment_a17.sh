#!/usr/bin/env bash
# Amendment A-17 (owner 2026-10-27, N-2.3 T-05, D-93): what "limits" means in REQ-WFM-023 / NFR-4 (the limits of the evidence and the basis of the confidence figure, each a {code, text} made by code) and the new field
# `limits` of the result record IF-003 from verify.number_gate@5. Two plan files change (the code, the nodes code.gate_record@2 / code.gate_abstain@2, the pipeline @5 and tests/test_gate_limits.py are on the branch):
#   specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md   specs/number-gate/requirements.md
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a17.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a17.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-17 ..."
#   bash tools/apply_amendment_a17.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-17
copy $A/N23-requirements.md specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md
copy $A/number-gate-requirements.md specs/number-gate/requirements.md
finish
echo
echo "checks after the amendment:"
python3 -I tools/check_sysml_model.py .
bash tools/run_in_image.sh tests/test_gate_limits.py tests/test_number_gate.py tests/acceptance/test_number_gate.py
