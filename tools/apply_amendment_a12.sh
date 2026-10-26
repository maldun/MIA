#!/usr/bin/env bash
# Amendment A-12 (owner 2026-10-27): REQ-CHA-011 reworded (records with kind, time and source, in English; AC-24 measured on the holdout of the checked memory sample and by the token cost, D-85). Three plan files change:
#   specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md   specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/test-spec.md   specs/mia/architecture.sysml
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a12.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a12.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-12 ..."
#   bash tools/apply_amendment_a12.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-12
N=specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent
copy $A/requirements.md $N/requirements.md
copy $A/test-spec.md $N/test-spec.md
copy $A/architecture.sysml specs/mia/architecture.sysml
finish
echo
echo "model checks after the amendment (about 15 s):"
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 -I tools/check_sysml_model.py .
bash tools/check_agent.sh --errors
