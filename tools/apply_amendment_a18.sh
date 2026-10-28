#!/usr/bin/env bash
# Amendment A-18 (owner 2026-10-28, N-2.3 T-07, D-94): the example workflow review is a literature review in fixed stages (keywords, search per keyword, collection, abstract and
# full-text screening with decision and grade 0 to 3, keyword extension after approval, report). REQ-WFM-018 to -020 reworded, REQ-WFM-027 and -028 new (Draft), TC-WFM-027/028, plan T-07.
# Four plan files change (the model block of architecture.sysml was regenerated with tools/gen_node_requirements_model.py):
#   N-2.3 requirements.md, test-spec.md, plan.md   specs/mia/architecture.sysml
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a18.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a18.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-18 ..."
#   bash tools/apply_amendment_a18.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-18
N=specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management
copy $A/N23-requirements.md $N/requirements.md
copy $A/N23-test-spec.md $N/test-spec.md
copy $A/N23-plan.md $N/plan.md
copy $A/architecture.sysml specs/mia/architecture.sysml
finish
echo
echo "model checks after the amendment (about 15 s):"
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 -I tools/check_sysml_model.py .
