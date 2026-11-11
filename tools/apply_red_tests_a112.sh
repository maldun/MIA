#!/usr/bin/env bash
# Installs the mock and the suite case of A-112 (IF-302 v9, the table transforms, TC-IF-302-10 / TC-RTB-009) from the staging folder
# specs/mia/goals/G-V2.TOOLBOX/red-tests-a112/ into the protected folders tests/acceptance/contract and tests/helpers/mocks. The owner runs it:
#   bash tools/apply_red_tests_a112.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_red_tests_a112.sh --do      copy the files; commit afterwards as "test: install the A-112 suite case (transforms)"
# The staged copies are the installed files plus the table (+7 and +21 lines): look at the diff first; if another goal changed the two files in the meantime
# (A-141 adds TC-IF-302-08 and skill_runs), merge by hand, do not overwrite.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
S=specs/mia/goals/G-V2.TOOLBOX/red-tests-a112
copy $S/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
copy $S/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
finish
