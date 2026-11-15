#!/usr/bin/env bash
# Installs the red acceptance tests, the IF-301 v2 mock and contract suite of G-V2.STORE (Plan step 4) from their staging folder into the protected folders
# tests/acceptance and tests/helpers. New files only: nothing that exists is overwritten except by an identical or newer staged copy of these same files.
# Why a script: the deny rules of .claude/settings.json keep the coding agent from writing there; the owner installs (plan-phase, step 4).
# Usage:  bash tools/install_red_tests_g_v2_store.sh          show what would change, change nothing
#         bash tools/install_red_tests_g_v2_store.sh --do     copy the files; running it again changes nothing
# Then:   python tests/acceptance/contract/test_if_301_v2_graph_tables.py    (the mock side passes, the real side is skipped: N-3.2 not integrated yet)
#         python tests/acceptance/test_graph_records.py                      (fails by assertion until N-3.2 and the Storage layer are built; not by ImportError)
#         the v1 suite tests/acceptance/contract/test_if_301_graph_tables.py stays as it is and passes
set -euo pipefail
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh; amendment_args "$@"
S=specs/mia/goals/G-V2.STORE/red-tests
copy $S/helpers/mocks/if_301_graph_tables_v2.py                  tests/helpers/mocks/if_301_graph_tables_v2.py
copy $S/helpers/graph_store_standin.py                            tests/helpers/graph_store_standin.py
copy $S/acceptance/contract/test_if_301_v2_graph_tables.py        tests/acceptance/contract/test_if_301_v2_graph_tables.py
copy $S/acceptance/test_graph_records.py                          tests/acceptance/test_graph_records.py
finish
