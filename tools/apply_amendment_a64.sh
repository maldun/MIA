#!/usr/bin/env bash
# Amendment A-64 (N-2.1 re-verification R-5, owner decision D-167): TC-API-013 gets its own stage-3 step.
# Protected file that changes:
#   stages.yaml          stage-3 step container-alone: python3 tests/test_container_alone.py (podman and the local image localhost/mia:latest, never pulled)
# stages.yaml is made from the INSTALLED file at run time (A-59 added a step too), so the script cannot bring back an older copy; it refuses when the
# anchor (the step smoke) is not found exactly once, and a second run reports unchanged.
# INSTALL IT ON THE LINE OF WORK goal/v1.
#   bash tools/apply_amendment_a64.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a64.sh --do      install; commit afterwards as "plan: A-64 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - stages.yaml "$WORK" <<'PY'
import os
import sys
stages, work = sys.argv[1:3]
text = open(stages, encoding="utf-8").read()
anchor = "  - {id: smoke,"
step = ('  # container-alone (A-64): TC-API-013, the mia image alone in a pod against the HTTP stand-in of IF-103; needs podman and localhost/mia:latest (never pulled)\n'
        '  - {id: container-alone, stage: 3, cmd: "python3 tests/test_container_alone.py", needs: [unit]}\n')
if step not in text:
    if text.count(anchor) != 1:
        sys.exit("%s: the step smoke is not found exactly once; install A-64 by hand" % stages)
    text = text.replace(anchor, step + anchor)
open(os.path.join(work, "stages.yaml"), "w", encoding="utf-8").write(text)
PY
copy "$WORK/stages.yaml" stages.yaml
finish
