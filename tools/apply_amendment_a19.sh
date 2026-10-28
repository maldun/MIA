#!/usr/bin/env bash
# Amendment A-19 (owner 2026-10-28, N-2.3 T-07, D-95): the agent view gets the model steps of the review workflow (ReviewKeywordStep, ReviewAbstractStep, ReviewSectionStep,
# ReviewFullStep, ReviewSummaryStep) in place of the proposed ReviewPlannerStep and ReviewScreeningStep; secondBudget = about three times the longest call measured on 2026-10-28
# (tools/measure_review_steps.py, pin MP-light). The threat model names the new steps at TB-user and TB-paper. Two plan files change:
#   specs/mia/architecture.sysml   specs/mia/threat-model.md
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a19.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a19.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-19 ..."
#   bash tools/apply_amendment_a19.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-19
copy $A/architecture.sysml specs/mia/architecture.sysml
copy $A/threat-model.md specs/mia/threat-model.md
finish
echo
echo "model checks after the amendment (about 15 s):"
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 -I tools/check_sysml_model.py .
