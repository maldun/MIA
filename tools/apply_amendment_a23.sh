#!/usr/bin/env bash
# Amendment A-23 (owner 2026-10-29, hand review of /review, N-2.3 T-09 and T-10, D-99): the usability of long tasks. Run mode by default (hard caps, no question at a limit), slices as the
# option `slice` and for paid models; skill id = command and the options `/<id> options ... --` (REQ-WFM-029, -030); a task monitor with a status card and pause (REQ-WFM-031 to -033);
# the class of the model asked once (REQ-WFM-035); the result as the newest message (REQ-WFM-036); a files volume (REQ-WFM-037); the report as a database record (REQ-WFM-038).
# REQ-WFM-019 and REQ-BE-054 reworded, REQ-WFM-029 to -038 new (Draft), TC-WFM-029 to -038, plan T-09 and T-10, IF-101 v8, IF-302 v4 (table reports).
# Seven plan files change (the model block of architecture.sysml was regenerated with tools/gen_node_requirements_model.py):
#   N-2 requirements.md   N-2.3 requirements.md, test-spec.md, plan.md   specs/mia/architecture.sysml   contracts/IF-101-chat-api.md   contracts/IF-302-record-tables.md
# NOT part of this amendment (follows as A-24 together with the code): the mocks and contract tests of IF-101 v8 and IF-302 v4, the requirements of N-1 for the status card and the Files tab.
# NOT installed: three places of the HLS (specs/mia/amendments/A-23/HLS-changes.md): the owner changes the HLS by hand.
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a23.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a23.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-23 ..."
#   bash tools/apply_amendment_a23.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-23
N=specs/mia/nodes/N-2-backend
copy $A/N2-requirements.md $N/requirements.md
copy $A/N23-requirements.md $N/nodes/N-2.3-workflow-management/requirements.md
copy $A/N23-test-spec.md $N/nodes/N-2.3-workflow-management/test-spec.md
copy $A/N23-plan.md $N/nodes/N-2.3-workflow-management/plan.md
copy $A/architecture.sysml specs/mia/architecture.sysml
copy $A/IF-101-chat-api.md contracts/IF-101-chat-api.md
copy $A/IF-302-record-tables.md contracts/IF-302-record-tables.md
finish
echo
echo "model checks after the amendment (about 15 s):"
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 -I tools/check_sysml_model.py .
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py tests/acceptance/contract/test_if_302_record_tables.py
