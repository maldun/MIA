#!/usr/bin/env bash
# Merge of G-V4.VIEW (Commit phase, 2026-11-25, plan.md "At the merge"): the test requirements TR-VIEW-001 to 021 move, unchanged, from
# specs/mia/goals/G-V4.VIEW/test-requirements.md into the protected specs/mia/test-requirements.md (new section at the end; their groups as
# rows of the one `## Groups` table at the top: EX and CR shared with CORE and RULES, SD, SI, BR, DP and SM new), next to the checks that
# moved into the node test specs (N-2.1, N-3.3, N-4.2, N-5). Not an amendment: no text of a test requirement changes (only the Status line
# records the move, as for CORE and RULES). Draft in specs/mia/amendments/merge-g-v4-view/specs/mia/test-requirements.md.
# Also the five deferrals TD-91 to TD-95 of D-502 (Verify V-11 and V-14 items 1, 10, 11, 12) appended to the protected specs/mia/deferred.md;
# their Sign-off boxes stay empty for the owner.
#   bash tools/apply_merge_g_v4_view.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_merge_g_v4_view.sh --do      install and run the traceability check; commit afterwards as "plan: VIEW test requirements and deferrals TD-91 to TD-95 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/merge-g-v4-view/specs/mia/test-requirements.md specs/mia/test-requirements.md
copy specs/mia/amendments/merge-g-v4-view/specs/mia/deferred.md specs/mia/deferred.md
finish

echo
echo "== traceability: errors that name a VIEW check or test requirement (expected after --do: 1, SMOKE-VIEW-002 -> NFR-11, see the merge request)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep "| ERROR |" \
    | grep -cE "TC-API-0(1[89]|2[0-5])|TC-OPR-011|TC-GA-0(1[7-9]|[23][0-9])|TC-IF-104-(1[7-9]|2[0-7])|TC-IF-302-1[34]|SMOKE-VIEW|TR-VIEW" || true
