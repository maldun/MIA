#!/usr/bin/env bash
# Amendment A-189 (G-V4.GRAPHAPI.RUN T-02, 2026-11-25, D-483; joint amendment of IF-301): rule 3 also names a connection whose ID is not a non-empty
# text, because load leaves such a connection out and the rules on the loaded graph would no longer see it (the save then raised KeyError).
# REQ-GTB-043 changed, REQ-GTB-060 narrowed to stored forms with unique non-empty text connection IDs; golden 36 (TC-IF-301-39) and TC-GTB-053.
# Drafts in specs/mia/amendments/A-189/, note specs/mia/amendments/A-189-note.md.
# INSTALL IT ON THE LINE OF WORK goal/v4.graphapi.run.
#   bash tools/apply_amendment_a189.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a189.sh --do      install and run the checks; commit afterwards as "plan: A-189 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-189
G=specs/mia/goals/G-V4.GRAPHAPI.RUN

copy "$A/IF-301-graph-tables.md" contracts/IF-301-graph-tables.md
copy "$A/tests/helpers/mocks/if_301_graph_tables_v5.py" tests/helpers/mocks/if_301_graph_tables_v5.py
copy "$A/tests/acceptance/contract/test_if_301_v5_load.py" tests/acceptance/contract/test_if_301_v5_load.py
copy "$A/tests/acceptance/test_graph_loader.py" tests/acceptance/test_graph_loader.py
copy "$A/requirements.md" "$G/requirements.md"
copy "$A/test-spec.md" "$G/test-spec.md"
copy "$A/test-requirements.md" "$G/test-requirements.md"
finish

echo
echo "== expected before the T-02 code: TC-GTB-053 red, TC-IF-301-39 red on the real side only, TC-GTB-051 red (T-02); the v4 suite green"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/test_graph_loader.py tests/acceptance/contract/test_if_301_v5_load.py tests/acceptance/contract/test_if_301_v4_rule_set.py; do
    echo "-- $f"; "$PY" "$f" 2>&1 | grep -E '^(FAIL|ERROR):|^OK|^FAILED'
done
