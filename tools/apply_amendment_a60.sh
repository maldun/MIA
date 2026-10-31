#!/usr/bin/env bash
# Amendment A-60 (N-3.2 Verify F1, F2, F9; owner decision D-160, 2026-10-31): IF-301 v1, a session limit is a positive integer (an int >= 1, not a bool;
# null = not given) and a malformed part (a stop that is not an object, an edge endpoint that is not text) is named by its rule instead of raising.
# Note: specs/mia/amendments/A-60/A-60-note.md
# Protected files that change:
#   contracts/IF-301-graph-tables.md                         v1: the rules in detail, golden 4, the version line
#   tests/helpers/mocks/graph_rules.py                       the mock's rules follow F1 and F2 (also used by the mock of IF-102)
#   tests/acceptance/contract/test_if_301_graph_tables.py    TC-IF-301-04 (golden 4), mock and real
#   tests/helpers/mocks/if_104_graph_api.mjs                 the JS mock of IF-104 follows the limit rule (D-162)
#   tests/acceptance/contract/test_if_104_graph_api.test.mjs TC-IF-104-06, the limit rule over HTTP (the real side skips as before)
#   tests/helpers/contract.py                                the IF-301 line of REAL_NOT_READY no longer says "not integrated yet" (F9); real_subject("IF-301")
#                                                            loads graph_tables with the REAL graph_rules (specs/mia/amendments/A-60/real_graph_tables.py):
#                                                            before, the mock side had cached the mock's graph_rules under the same name, so the real side ran the mock rules
# Not protected, changed with it:
#   specs/mia/test-spec.md                                   the rows of TC-IF-301-04 (after -03) and TC-IF-104-06 (after -05)
#   specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md   IF-301: Verified by TC-IF-301-01..04, History v1 (A-60)
# contract.py, test-spec.md and requirements.md are made from the INSTALLED files at run time (contract.py is shared with other amendments, e.g. A-59),
# so the script cannot bring back an older copy; it refuses when an anchor is not found exactly once.
# INSTALL IT ON THE LINE OF WORK goal/v1 after the merge of v1-n32b (graph_rules.py must have the F1/F2 fixes, otherwise TC-IF-301-04 is red on the real side).
#   bash tools/apply_amendment_a60.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a60.sh --do      install and run the IF-301, IF-102 and IF-104 (JS) suites; commit afterwards as "plan: A-60 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-60
D=specs/mia/contract-drafts
NODE=specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - tests/helpers/contract.py specs/mia/test-spec.md "$NODE" "$WORK" "$A/real_graph_tables.py" <<'PY'
import os
import sys
contract, spec, node, work, snippet_path = sys.argv[1:6]


def edit(path, old, new, what, text=None):
    """old -> new exactly once; a text that has the new part already is left as it is (the copy then reports unchanged)."""
    text = open(path, encoding="utf-8").read() if text is None else text
    if new in text:
        return text
    if text.count(old) != 1:
        sys.exit("%s: %s is not found exactly once; install A-60 by hand" % (path, what))
    return text.replace(old, new)


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


text = edit(contract,
            '    "IF-301": "N-3.2 Graph tables not integrated yet",\n',
            '    "IF-301": "unused: real_subject gives graph_tables",       # real_subject since A-02 (graph_tables); the reason fixed by A-60 (F9)\n',
            "the IF-301 line of REAL_NOT_READY")
text = edit(contract, '    if interface == "IF-301":\n        import graph_tables\n        return graph_tables\n',
            '    if interface == "IF-301":\n        return _real_graph_tables()\n', "the IF-301 branch of real_subject", text)
snippet = open(snippet_path, encoding="utf-8").read()
anchor = "def real_subject(interface, **options):\n"
if "def _real_graph_tables" not in text:
    if text.count(anchor) != 1:
        sys.exit("%s: def real_subject is not found exactly once; install A-60 by hand" % contract)
    text = text.replace(anchor, snippet + anchor)
write("contract.py", text)
row3 = "| TC-IF-301-03 | IF-301 | Contract | 1 (mock) and 2 (real) | golden 3: p->d->p is a cycle named as [p, d, p]; a table that is not a graph table is a ValueError. | exact |\n"
row4 = ("| TC-IF-301-04 | IF-301 | Contract | 1 (mock) and 2 (real) | golden 4 (A-60): a session limit that is not an integer >= 1 (or is a bool) and a stop that "
        "is not an object are session_stopping_criterion; an edge endpoint that is not text is node_identity; max_cycles 1 is valid; nothing raises. | exact |\n")
text = edit(spec, row3, row3 + row4, "the row of TC-IF-301-03")
row5 = "| TC-IF-104-05 | IF-104 | Contract | 1 (mock) and 2 (real) | golden 3: unknown id and kind are 404; a stale expected_version is 409 with the current version. | exact |\n"
row6 = ("| TC-IF-104-06 | IF-104 | Contract | 1 (mock) and 2 (real) | (A-60, D-162) a session limit that is not an integer >= 1 is 422 "
        "session_stopping_criterion; max_cycles 1 with a null max_seconds is saved. | exact |\n")
write("test-spec.md", edit(spec, row5, row5 + row6, "the row of TC-IF-104-05", text))
text = edit(node, "- Verified by: TC-IF-301-01..03\n", "- Verified by: TC-IF-301-01..04\n", "the Verified by line of IF-301")
write("requirements.md", edit(node, "- History: v0, amendment 5/7 (2026-10-25)\n",
                              "- History: v0, amendment 5/7 (2026-10-25); v1, A-60 (2026-10-31): session limit and malformed parts\n", "the History line of IF-301", text))
PY
copy $A/IF-301-graph-tables.md contracts/IF-301-graph-tables.md
copy $D/tests/helpers/mocks/graph_rules.py tests/helpers/mocks/graph_rules.py
copy $D/tests/acceptance/contract/test_if_301_graph_tables.py tests/acceptance/contract/test_if_301_graph_tables.py
copy $D/tests/helpers/mocks/if_104_graph_api.mjs tests/helpers/mocks/if_104_graph_api.mjs
copy $D/tests/acceptance/contract/test_if_104_graph_api.test.mjs tests/acceptance/contract/test_if_104_graph_api.test.mjs
copy "$WORK/contract.py" tests/helpers/contract.py
copy "$WORK/test-spec.md" specs/mia/test-spec.md
copy "$WORK/requirements.md" "$NODE"
finish
echo
for suite in tests/acceptance/contract/test_if_301_graph_tables.py tests/acceptance/contract/test_if_102_storage.py; do
    echo "== $suite"
    python3 "$suite" 2>&1 | tail -n 3
done
echo "== tests/acceptance/contract/test_if_104_graph_api.test.mjs"
node --test tests/acceptance/contract/test_if_104_graph_api.test.mjs 2>&1 | grep -E "^# (pass|fail|skipped)"
