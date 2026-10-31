#!/usr/bin/env bash
# TC-API-013 (REQ-API-013, AC-29) as the stage-3 step `container-alone` of stages.yaml (amendment A-64, D-167, D-169): the mia image alone in a pod
# against the HTTP stand-in of IF-103 (tests/test_container_alone.py; needs podman and localhost/mia:latest, never pulled).
# A skipped test counts as a failure here, as in tools/contract_postgres.sh: without podman or the image the step must not pass without evidence.
#   bash tools/container_alone.sh                MIA_STEP_PYTHON=/path/to/python picks the python (default python3)
set -eu
cd "$(dirname "$0")/.."
PY=${MIA_STEP_PYTHON:-python3}
OUT=$("$PY" tests/test_container_alone.py 2>&1) && status=0 || status=$?
printf '%s\n' "$OUT" | tail -n 4
if [ "$status" = 0 ] && printf '%s\n' "$OUT" | grep -q "skipped"; then echo "a test was skipped: TC-API-013 did not run (podman, the image or the stand-in is missing)"; exit 1; fi
exit "$status"
