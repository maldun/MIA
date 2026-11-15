#!/usr/bin/env bash
# Amendment A-90, contract text of IF-301 v2 (G-V2.STORE, Plan step 4, 2026-11-07; owner decisions D-188, D-262 to D-266 and the answer on definitions()).
# Replaces contracts/IF-301-graph-tables.md (v1) by the v2 text staged in specs/mia/amendments/A-90/IF-301-graph-tables.md. Nothing else changes here:
# the mock and the suite are installed by tools/install_red_tests_g_v2_store.sh (do that first or in the same session, so the contract and its tests agree).
# THE OWNER APPROVES THE TEXT FIRST, including the section "Clarifications fixed by the v2 mock and suite" at its end; only then --do.
# Not done here (parent session, root files): rows TC-IF-301-05 to TC-IF-301-19 in specs/mia/test-spec.md (IF-301 v2 contract cases, see handover-step4.md).
#   bash tools/apply_amendment_a90_if301.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a90_if301.sh --do      install and run the trace check; commit afterwards as "plan: A-90 contract text IF-301 v2 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
copy specs/mia/amendments/A-90/IF-301-graph-tables.md contracts/IF-301-graph-tables.md
finish
echo
echo "== the v1 suite and the v2 suite on the mocks (stage 1), both must pass"
python tests/acceptance/contract/test_if_301_graph_tables.py -k _mock 2>&1 | tail -1
python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _mock 2>&1 | tail -1
echo "== trace_check, errors about IF-301 (none expected)"
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests 2>&1 | grep -E "ERROR.*IF-301" || echo none
