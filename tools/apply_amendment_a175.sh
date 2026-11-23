#!/usr/bin/env bash
# Amendment A-175 (G-V4.VIEW, 2026-11-23, D-454): ctx.small gets a step of the workflow type data, so TC-GA-025 sees a graph of another kind
# drawn with the workflow shapes (finding F-1 of T-09). Requirement unchanged. See specs/mia/amendments/A-175/A-175-note.md.
# INSTALL IT ON THE LINE OF WORK goal/v4.view.
#   bash tools/apply_amendment_a175.sh           show the diff (changes nothing)
#   bash tools/apply_amendment_a175.sh --do      install and run the page checks; commit afterwards as "plan: A-175 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-175

copy "$A/tests/fixtures/graph_view/graphs.json" tests/fixtures/graph_view/graphs.json
copy "$A/tests/acceptance/graph_view_page.test.mjs" tests/acceptance/graph_view_page.test.mjs
copy "$A/specs/mia/goals/G-V4.VIEW/test-requirements.md" specs/mia/goals/G-V4.VIEW/test-requirements.md
finish

echo
echo "== the page node checks (expected: TC-GA-025 ok; the checks of T-10 and T-11 still not ok until those tasks)"
node --test tests/acceptance/graph_view_page.test.mjs 2>&1 | grep -E '^(ok|not ok) [0-9]+ - TC-GA-025|^# (pass|fail)'
