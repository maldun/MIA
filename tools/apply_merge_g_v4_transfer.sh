#!/usr/bin/env bash
# Merge of G-V4.GRAPHSTORE.TRANSFER (Commit phase, 2026-11-27, plan.md "At the merge"): the test requirements TR-TRANSFER-001 to 011 move, unchanged,
# from specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/test-requirements.md (with A-196 and A-197 installed) into the protected specs/mia/test-requirements.md
# (new section at the end; their groups FI, BK, EX, CR and EP as rows of the one `## Groups` table at the top, shared with CORE, RULES and VIEW),
# next to the checks that moved into the node test specs (N-3.1, N-2.1). Not an amendment: no text of a test requirement changes; a History line
# records the move, the Status lines stay as they are. Draft in specs/mia/amendments/merge-g-v4-transfer/specs/mia/test-requirements.md.
#   bash tools/apply_merge_g_v4_transfer.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_merge_g_v4_transfer.sh --do      install and run the traceability check; commit afterwards as "plan: TRANSFER test requirements installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/merge-g-v4-transfer/specs/mia/test-requirements.md specs/mia/test-requirements.md
finish

echo
echo "== traceability: errors that name a TRANSFER check or test requirement (expected after --do: 0; all ERROR lines together: 584, one fewer than before the merge)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep "| ERROR |" \
    | grep -cE "TC-SLY-(009|01[6-9]|0[23][0-9]|040)|TC-API-06[0-7]|SMOKE-TRANSFER|TR-TRANSFER" || true
