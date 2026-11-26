#!/usr/bin/env bash
# Amendment A-176 (G-V4.VIEW, 2026-11-26, D-503): the graph page shows the theme chosen in the main app (mia.theme); new browser check TC-GA-040
# for the changed REQ-GA-016. See specs/mia/amendments/A-176-note.md.
# INSTALL IT ON THE BRANCH fix/g-v4-view-theme.
#   bash tools/apply_amendment_a176.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a176.sh --do      install and run the browser checks; commit afterwards as "plan: A-176 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-176

copy "$A/tests/acceptance/test_graph_view_browser.py" tests/acceptance/test_graph_view_browser.py
finish

echo
echo "== the browser checks (expected before the fix: TC-GA-033 to 039 ok, TC-GA-040 FAIL)"
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/test_graph_view_browser.py 2>&1 | grep -E '^(test_|Ran|OK|FAILED)|\.\.\. (ok|FAIL|ERROR)'
