#!/usr/bin/env bash
# Amendment A-91 (G-V2.STORE, integration step T-05; approved in principle by the owner 2026-11-07): the real side of the IF-301 v2 contract suite runs
# without a skip. Note: specs/mia/amendments/A-91-note.md
# Made from the INSTALLED suite at run time, each edit refused when its anchor is not found exactly once:
#   tests/acceptance/contract/test_if_301_v2_graph_tables.py   the header text and subject(): the environment switch IF301_V2_REAL and its skip are removed,
#                                                              subject("real") returns the real Graph tables
# INSTALL IT AFTER T-01 TO T-04 OF G-V2.STORE (the real side must pass: the script checks it and says so).
#   bash tools/apply_amendment_a91.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a91.sh --do      install, run both sides of the suite and the v1 and v0 suites; commit afterwards as "plan: A-91 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
SUITE=tests/acceptance/contract/test_if_301_v2_graph_tables.py
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$SUITE" "$WORK" <<'PY'
import os
import sys
suite, work = sys.argv[1:3]
text = open(suite, encoding="utf-8").read()

def replace_once(text, old, new, what):
    if text.count(old) != 1:
        if text.count(new) == 1:
            return text                      # done already
        sys.exit("%s: %s is not found exactly once; install A-91 by hand" % (suite, what))
    return text.replace(old, new, 1)

text = replace_once(text, '''the contract suite runs against the mock (stage 1, green) and the
real Graph tables (stage 2, skipped with the reason below until N-3.2 is integrated). The v1 cases stay in test_if_301_graph_tables.py (unchanged).
Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_301_v2_graph_tables.py
The real side runs on request while N-3.2 is built:  IF301_V2_REAL=1 python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _real
Removing the skip (the environment switch) is part of the integration step of N-3.2.
"""''', '''the contract suite runs against the mock (stage 1, green) and the
real Graph tables (stage 2; no skip since A-91, N-3.2 integrated). The v1 cases stay in test_if_301_graph_tables.py (unchanged).
Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_301_v2_graph_tables.py
"""''', "the header text")
text = replace_once(text, '''    """The provider of this suite: the v2 mock, or the real Graph tables once N-3.2 is integrated."""
    if kind == "mock":
        from if_301_graph_tables_v2 import GraphTablesV2Mock
        return GraphTablesV2Mock()
    if os.environ.get("IF301_V2_REAL") != "1":
        raise unittest.SkipTest("N-3.2 not integrated yet")
    return contract_module._real_graph_tables()
''', '''    """The provider of this suite: the v2 mock, or the real Graph tables (A-91: no skip, N-3.2 is integrated)."""
    if kind == "mock":
        from if_301_graph_tables_v2 import GraphTablesV2Mock
        return GraphTablesV2Mock()
    return contract_module._real_graph_tables()
''', "subject()")
open(os.path.join(work, "suite.py"), "w", encoding="utf-8").write(text)
PY
copy "$WORK/suite.py" "$SUITE"
finish
if [ "$do_it" = 1 ]; then
    echo
    echo "== the v2 suite on both sides: every case must pass, none may be skipped"
    out=$(python "$SUITE" 2>&1 | tail -3); echo "$out"
    case "$out" in *skipped*) echo "A SKIP IS LEFT: the real side did not run"; exit 1 ;; esac
    echo "== the v1 suite and the IF-203 v0 suite are unchanged and pass"
    python tests/acceptance/contract/test_if_301_graph_tables.py 2>&1 | tail -1
    python tests/acceptance/contract/test_if_203_workflow_library.py 2>&1 | tail -1
    echo "== TC-GTB-015 (hashes of the v1 and v0 suite files)"
    python tests/acceptance/test_graph_records.py -k test_the_document_form_still_works 2>&1 | tail -1
fi
