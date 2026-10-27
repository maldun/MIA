#!/usr/bin/env bash
# Amendment A-16 (owner 2026-10-27, N-2.3 T-02, D-91): REQ-WFM-006 and its parent REQ-BE-039 reworded: the gate of the library refuses to promote a workflow without a specification or a benchmark (as IF-203 says);
# the context graph and the baseline of the shipped workflows stay required by AC-10 and are checked by inspection (TC-MIA-009, TC-MIA-010). AC-10 (FR-26) loses the clause "refuses to promote one without [all three]".
# Seven plan files change (the model block of architecture.sysml was regenerated with tools/gen_node_requirements_model.py):
#   N-2.3 requirements.md and test-spec.md   N-2 requirements.md   specs/mia/high-level-spec.md, requirements.md, test-spec.md   specs/mia/architecture.sysml
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a16.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a16.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-16 ..."
#   bash tools/apply_amendment_a16.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-16
N=specs/mia/nodes/N-2-backend
copy $A/N23-requirements.md $N/nodes/N-2.3-workflow-management/requirements.md
copy $A/N23-test-spec.md $N/nodes/N-2.3-workflow-management/test-spec.md
copy $A/N2-requirements.md $N/requirements.md
copy $A/high-level-spec.md specs/mia/high-level-spec.md
copy $A/requirements.md specs/mia/requirements.md
copy $A/test-spec.md specs/mia/test-spec.md
copy $A/architecture.sysml specs/mia/architecture.sysml
finish
echo
echo "model checks after the amendment (about 15 s):"
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 -I tools/check_sysml_model.py .
