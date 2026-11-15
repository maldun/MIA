#!/usr/bin/env bash
# Installs the red acceptance tests of G-V2.MODEL (Plan step 4) from their staging folder into the protected folders tests/acceptance and tests/helpers.
# Why a script: the deny rules of .claude/settings.json keep the coding agent from writing there; the owner installs (plan.md).
# Usage:  bash tools/install_red_tests_g_v2_model.sh          show what would change, change nothing
#         bash tools/install_red_tests_g_v2_model.sh --do     copy the files; running it again changes nothing
# Then:   python tests/acceptance/test_graph_model.py ; python tests/acceptance/test_graph_run.py   (both must fail by assertion, not by ImportError)
set -euo pipefail
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh; amendment_args "$@"
S=specs/mia/goals/G-V2.MODEL/red-tests
copy $S/helpers/graph_model_fakes.py      tests/helpers/graph_model_fakes.py
copy $S/acceptance/test_graph_model.py    tests/acceptance/test_graph_model.py
copy $S/acceptance/test_graph_run.py      tests/acceptance/test_graph_run.py
finish
