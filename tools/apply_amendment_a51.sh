#!/usr/bin/env bash
# Amendment A-51 (N-2.1 T-04, 2026-10-31): the real provider of IF-104 in the Python contract suite. The routes of IF-104 v1 exist (graph_api.py on the
# workflow library IF-203, behind the guard of accounts_api); tests/helpers/contract.py gets the adapter `_GraphApiAdapter` that drives them over HTTP, so
# TC-IF-104-01 to -05 run on the real side (stage 2) instead of skipping. The contract, the suite and the mocks are unchanged. Note: specs/mia/amendments/A-51/A-51-note.md
# Protected file that changes:
#   tests/helpers/contract.py   the adapter class (specs/mia/amendments/A-51/graph_api_adapter.py) before real_subject, one dispatch line for IF-104, the
#                               comment of IF-104 in REAL_NOT_READY; made from the INSTALLED file at run time (it is shared by many amendments, so it cannot go stale)
# INSTALL IT ON THE LINE OF WORK goal/v1 after the merge of v1-n21 (graph_api.py must exist).
#   bash tools/apply_amendment_a51.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a51.sh --do      install and run the IF-104 suite in the image; commit afterwards as "plan: A-51 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-51
HELPER=$(mktemp)
trap 'rm -f "$HELPER"' EXIT
python3 - tests/helpers/contract.py "$A/graph_api_adapter.py" "$HELPER" <<'PY'
import sys
installed, snippet, out = sys.argv[1:4]
text = open(installed, encoding="utf-8").read()
if "class _GraphApiAdapter" in text:
    open(out, "w", encoding="utf-8").write(text)          # installed already: the copy below reports "unchanged"
    sys.exit(0)
old_reason = '    "IF-104": "N-2 Backend not integrated yet",\n'
new_reason = '    "IF-104": "N-2 Backend not integrated yet",       # real_subject since A-51: the routes of graph_api.py behind the guard of accounts_api\n'
anchor = "def real_subject(interface, **options):\n"
dispatch_old = "    if interface == \"IF-402\":\n        return _ToolCallsAdapter()\n    return None\n"
dispatch_new = "    if interface == \"IF-402\":\n        return _ToolCallsAdapter()\n    if interface == \"IF-104\":\n        return _GraphApiAdapter()\n    return None\n"
for piece, name in ((old_reason, "the IF-104 line of REAL_NOT_READY"), (anchor, "def real_subject"), (dispatch_old, "the end of real_subject")):
    if text.count(piece) != 1:
        sys.exit("tests/helpers/contract.py: %s is not found exactly once; install A-51 by hand" % name)
text = text.replace(old_reason, new_reason).replace(anchor, open(snippet, encoding="utf-8").read() + anchor).replace(dispatch_old, dispatch_new)
open(out, "w", encoding="utf-8").write(text)
PY
copy "$HELPER" tests/helpers/contract.py
finish
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_104_graph_api.py
