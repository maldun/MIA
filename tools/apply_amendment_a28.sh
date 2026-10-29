#!/usr/bin/env bash
# Amendment A-28 (owner 2026-10-29, N-2.4.3 Run log, D-107): REQ-LOG-005 is reworded. The events of a run stay append-only files in the log folder (as run_log.py writes them), the
# Run log imports no database driver, and the results of benchmark runs go through the storage interface IF-102 (REQ-WFX-022). Before: "run events and run results only through IF-102".
# Reason: the events are a stream of logs, not the shared state of NFR-8; files fit the stream, the replay and the account. Two plan files change (the model block of the SysML file was
# regenerated); the test that checks it is tests/test_run_log_files.py (TC-LOG-005, green on the existing code).
#   N-2.4.3 requirements.md, test-spec.md   specs/mia/architecture.sysml
# Run it yourself in the MAIN checkout, after the branch is merged:
#   bash tools/apply_amendment_a28.sh           show the compared files and the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a28.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-28 ..." (name the paths, no `git add -A`)
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-28
N=specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.3-run-log
copy $A/N243-requirements.md $N/requirements.md
copy $A/N243-test-spec.md $N/test-spec.md
copy $A/architecture.sysml specs/mia/architecture.sysml
finish
echo
echo "checks after the amendment:"
python3 -I tools/check_sysml_model.py .
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 tests/test_run_log_files.py 2>&1 | tail -3
