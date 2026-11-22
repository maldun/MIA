#!/usr/bin/env bash
# Amendment A-168 (G-V4.GRAPHSTORE.CORE, 2026-11-22, D-412): the four protected acceptance scripts that A-167 missed get scoped IDs of steps and
# connections (`g/<local>`, in a header `<header id>/<local>`); same tests, same rules, same expected results. In TC-GTB-027 the workflow header h2
# names the stored context node h2/c1, so it is still refused for the table (unknown_member) and not for the scope. Note: specs/mia/amendments/A-168-note.md
# Drafts in specs/mia/amendments/A-168/tests/acceptance/.
# INSTALL IT ON THE LINE OF WORK goal/v4 (after T-01, f2531cc8).
#   bash tools/apply_amendment_a168.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a168.sh --do      install and run the four test files; commit afterwards as "plan: A-168 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-168/tests/acceptance
FILES="test_graph_context_tables.py test_graph_document_size.py test_graph_node_fields.py test_graph_record_identity.py"

for f in $FILES; do
    copy "$A/$f" "tests/acceptance/$f"
done
finish

echo
echo "== the four test files (expected with T-01 installed: all OK)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in $FILES; do
    printf '%-52s ' "tests/acceptance/$f"; "$PY" "tests/acceptance/$f" 2>&1 | tail -n 1
done
