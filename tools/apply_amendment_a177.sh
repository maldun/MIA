#!/usr/bin/env bash
# Amendment A-177 (G-V4.VIEW, 2026-11-26, D-504): TC-GA-040 also tries an unknown theme value under dark; TC-GA-040 traced to its test requirements
# (findings F-3, F-4 of the Verify of fix/g-v4-view-theme). See specs/mia/amendments/A-177-note.md.
# INSTALL IT ON THE BRANCH fix/g-v4-view-theme.
#   bash tools/apply_amendment_a177.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a177.sh --do      install and run the browser checks and the trace check; commit afterwards as "plan: A-177 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-177

copy "$A/tests/acceptance/test_graph_view_browser.py" tests/acceptance/test_graph_view_browser.py
copy "$A/specs/mia/test-requirements.md" specs/mia/test-requirements.md
finish

echo
echo "== the browser checks (expected: 8 tests OK)"
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/test_graph_view_browser.py 2>&1 | grep -E '^Ran|^OK|^FAILED|^(FAIL|ERROR):'
echo "== trace check, lines naming TC-GA-040 (expected: none)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep 'TC-GA-040' || echo "none"
