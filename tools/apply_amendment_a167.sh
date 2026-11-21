#!/usr/bin/env bash
# Amendment A-167 (G-V4.GRAPHSTORE.CORE, 2026-11-21): IF-301 v3, scoped IDs of steps and connections (REQ-GTB-029 to 031, D-368, D-402, D-409).
# A record of graph_nodes, graph_edges, context_nodes or context_edges is stored under `<graph id>/<local id>`; any other non-empty ID, and a header
# member of another graph, is refused as `unscoped_id`. The protected tests of v2 that wrote plain IDs are rewritten with scoped IDs (same tests, same
# rules); the suite gets TC-IF-301-25 and -26 (golden 22, 23). Note: specs/mia/amendments/A-167-note.md
# Drafts in specs/mia/amendments/A-167/; the two N-3.2 node files get one note paragraph each, made from the INSTALLED file at run time (refused when the
# anchor is missing; running it twice changes nothing).
# INSTALL IT ON THE LINE OF WORK goal/v4.
#   bash tools/apply_amendment_a167.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a167.sh --do      install and run the four test files; commit afterwards as "plan: A-167 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-167
N32=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

python3 - "$N32/test-spec.md" "$WORK/test-spec.md" "$N32/requirements.md" "$WORK/requirements.md" <<'PY'
import sys
NOTE = ("IDs of steps and connections (A-167, IF-301 v3): the IDs `n1`, `e1`, `c1`, ... named in the {what} below are local IDs. Since IF-301 v3 "
        "(REQ-GTB-029) a step or connection is stored under `<graph id>/<local id>`, so the tests write the scoped form (`wf1/n1`, `g/e1`, `h1/c1`); "
        "the rules and the expected results are unchanged.\n\n")
for installed, out, anchor, what in ((sys.argv[1], sys.argv[2], "## Test cases\n", "scenarios"),
                                     (sys.argv[3], sys.argv[4], "## Requirements\n", "acceptance criteria")):
    text = open(installed, encoding="utf-8").read()
    if "(A-167, IF-301 v3)" not in text:
        if text.count(anchor) != 1:
            sys.exit("%s: anchor %r not found once; install A-167 by hand" % (installed, anchor.strip()))
        text = text.replace(anchor, NOTE.format(what=what) + anchor)
    open(out, "w", encoding="utf-8").write(text)
PY

copy "$A/IF-301-graph-tables.md" contracts/IF-301-graph-tables.md
copy "$A/tests/helpers/mocks/if_301_graph_tables_v2.py" tests/helpers/mocks/if_301_graph_tables_v2.py
copy "$A/tests/acceptance/contract/test_if_301_v2_graph_tables.py" tests/acceptance/contract/test_if_301_v2_graph_tables.py
copy "$A/tests/acceptance/test_graph_records.py" tests/acceptance/test_graph_records.py
copy "$A/tests/test_graph_record_checks.py" tests/test_graph_record_checks.py
copy "$WORK/test-spec.md" "$N32/test-spec.md"
copy "$WORK/requirements.md" "$N32/requirements.md"
finish

echo
echo "== the four test files (expected until the CORE task that adds the rule: only the real side of TC-IF-301-25 and -26 fails)"
PY=${MIA_PYTHON:-/home/maldun/prog/Python/venvs/mia312/bin/python}
for f in tests/acceptance/contract/test_if_301_v2_graph_tables.py tests/acceptance/test_graph_records.py tests/test_graph_record_checks.py tests/acceptance/contract/test_if_301_graph_tables.py; do
    printf '%-62s ' "$f"; "$PY" "$f" 2>&1 | tail -1
done
