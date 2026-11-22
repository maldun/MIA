#!/usr/bin/env bash
# Merge of G-V4.GRAPHSTORE.CORE (Commit phase, 2026-11-22, plan.md "At the merge", D-408): the test requirements TR-CORE-001 to 009 move,
# unchanged, from specs/mia/goals/G-V4.GRAPHSTORE.CORE/test-requirements.md into the protected specs/mia/test-requirements.md (new section
# at the end), next to the checks that moved into the node test specs. Not an amendment: no text of a test requirement changes.
# Draft in specs/mia/amendments/merge-g-v4-core/specs/mia/test-requirements.md.
#   bash tools/apply_merge_g_v4_core.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_merge_g_v4_core.sh --do      install and run the traceability check; commit afterwards as "plan: CORE test requirements installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/merge-g-v4-core/specs/mia/test-requirements.md specs/mia/test-requirements.md
finish

echo
echo "== traceability: the CORE checks without a test requirement (expected after --do: none)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep "| ERROR |" | grep -cE "TC-GTB-03[3-6]|TC-WFM-1(6[2-9]|7[0-8])" || true
