#!/usr/bin/env bash
# Merge of G-V4.GRAPHAPI.RULES (Commit phase, 2026-11-22, plan.md "At the merge"): the test requirements TR-RULES-001 to 009 move,
# unchanged, from specs/mia/goals/G-V4.GRAPHAPI.RULES/test-requirements.md into the protected specs/mia/test-requirements.md (new section
# at the end; their groups as rows of the one `## Groups` table at the top: EX and CR shared with CORE, DA and EP new), next to the checks
# that moved into the node test specs (N-3.2, N-2.3, N-2.4.1). Not an amendment: no text of a test requirement changes (only the Status line
# records the move, as for CORE). Draft in specs/mia/amendments/merge-g-v4-rules/specs/mia/test-requirements.md.
#   bash tools/apply_merge_g_v4_rules.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_merge_g_v4_rules.sh --do      install and run the traceability check; commit afterwards as "plan: RULES test requirements installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/merge-g-v4-rules/specs/mia/test-requirements.md specs/mia/test-requirements.md
finish

echo
echo "== traceability: errors that name a RULES check or test requirement (expected after --do: 0)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep "| ERROR |" \
    | grep -cE "TC-GTB-0(3[7-9]|4[0-7])|TC-WFM-1(79|8[0-4])|TC-RUN-0(3[6-9]|40)|TC-IF-301-(2[7-9]|3[0-4])|SMOKE-RULES|TR-RULES" || true
