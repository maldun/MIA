#!/usr/bin/env bash
# Amendment A-11 (owner 2026-10-27): the agent view gets the model step MemoryWriteStep (skill memory_write, D-78) and the threat THR-006 names the structural mitigation. Two plan files change:
#   specs/mia/architecture.sysml   specs/mia/threat-model.md
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a11.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a11.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-11 ..."
#   bash tools/apply_amendment_a11.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-11
copy $A/architecture.sysml specs/mia/architecture.sysml
copy $A/threat-model.md specs/mia/threat-model.md
finish
echo
echo "model checks after the amendment (about 15 s):"
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 -I tools/check_sysml_model.py .
