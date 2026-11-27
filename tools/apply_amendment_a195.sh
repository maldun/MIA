#!/usr/bin/env bash
# Amendment A-195 (G-V4.GRAPHSTORE.TRANSFER, 2026-11-27, D-543 to D-546): the copy setting's behaviour that no requirement text stated.
# REQ-API-064 changed (lag while the live store does not answer), REQ-API-065 and 066 new (in requirements.md, not protected); this script
# installs the protected part: TC-API-065 to 067 in the backend checks and their "Applies to" entries. Note: specs/mia/amendments/A-195-note.md.
# Drafts in specs/mia/amendments/A-195/. INSTALL IT ON THE LINE OF WORK goal/v4.graphstore.transfer.
#   bash tools/apply_amendment_a195.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a195.sh --do      install and run the backend checks; commit afterwards as "plan: A-195 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-195
G=specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER
copy "$A/tests/acceptance/test_transfer_backend.py" tests/acceptance/test_transfer_backend.py
copy "$A/$G/test-requirements.md" "$G/test-requirements.md"
finish

echo
echo "== the backend checks (8 green expected on the branch)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
"$PY" tests/acceptance/test_transfer_backend.py 2>&1 | tail -3
