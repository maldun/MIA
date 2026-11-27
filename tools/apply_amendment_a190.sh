#!/usr/bin/env bash
# Amendment A-190 (G-V4.GRAPHAPI.RUN T-03, 2026-11-27, D-485): REQ-RUN-046 (the answer of a run from the stored graph is the value of the data step the
# skill's pipeline names as its result) with TC-RUN-048, and REQ-RUN-047 (graph_run.py and graph_rule_set.py import only the standard library, networkx
# and each other: the owner's "re-use as a module boundary") with TC-RUN-049.
# Drafts in specs/mia/amendments/A-190/, note specs/mia/amendments/A-190-note.md.
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.run.
#   bash tools/apply_amendment_a190.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a190.sh --do      install and run the checks; commit afterwards as "plan: A-190 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-190
G=specs/mia/goals/G-V4.GRAPHAPI.RUN

copy "$A/tests/acceptance/test_stored_graph_run.py" tests/acceptance/test_stored_graph_run.py
copy "$A/tests/acceptance/test_run_graph_order.py" tests/acceptance/test_run_graph_order.py
copy "$A/requirements.md" "$G/requirements.md"
copy "$A/test-spec.md" "$G/test-spec.md"
copy "$A/test-requirements.md" "$G/test-requirements.md"
copy "$A/plan.md" "$G/plan.md"
finish

echo
echo "== expected before the rest of the T-03 code: TC-RUN-048 green, TC-RUN-049 red (graph_run.py imports graph_model); the rest green"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/test_stored_graph_run.py tests/acceptance/test_run_graph_order.py; do
    echo "-- $f"; "$PY" "$f" 2>&1 | grep -E '^(FAIL|ERROR):|^OK|^FAILED'
done
