#!/usr/bin/env bash
# Amendments A-196 and A-197 (G-V4.GRAPHSTORE.TRANSFER, 2026-11-27, D-548, D-550): records no graph names synced like a graph (V-2) and
# TC-SLY-037 searching every folder the check made (V-4). REQ-SLY-024 to 027 and 037 changed in requirements.md, TC-SLY-040 new in test-spec.md
# (not protected, committed with the drafts); this script installs the protected part. Note: specs/mia/amendments/A-196-197-note.md.
# Drafts in specs/mia/amendments/A-196-197/. INSTALL IT ON THE LINE OF WORK goal/v4.graphstore.transfer.
#   bash tools/apply_amendment_a196_a197.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a196_a197.sh --do      install and run the two acceptance files; commit afterwards as "plan: A-196, A-197 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-196-197
G=specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER
copy "$A/tests/acceptance/test_transfer_sync.py" tests/acceptance/test_transfer_sync.py
copy "$A/tests/acceptance/test_transfer_sets.py" tests/acceptance/test_transfer_sets.py
copy "$A/$G/test-requirements.md" "$G/test-requirements.md"
finish

echo
echo "== the sync checks (TC-SLY-040 red until A-196 is implemented: 2 failures, files and database, by assertion)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
"$PY" tests/acceptance/test_transfer_sync.py 2>&1 | tail -1
echo "== the set checks (green expected)"
"$PY" tests/acceptance/test_transfer_sets.py 2>&1 | tail -1
