#!/usr/bin/env bash
# Installs the red tests of G-V2.TOOLBOX (Plan Step 4) from the staging folder specs/mia/goals/G-V2.TOOLBOX/red-tests/ into the protected folders tests/acceptance and tests/helpers.
# The owner runs it (the coding agent may not write there):
#   bash tools/apply_red_tests_toolbox.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_red_tests_toolbox.sh --do      copy the files; commit afterwards as "test: install the red tests of G-V2.TOOLBOX"
# The two IF-302 files overwrite the installed ones (the staged copies are the installed files plus the table transform_meta, A-110): look at the diff first; if G-V3 changed them in
# the meantime (A-141, skill_runs), merge by hand, do not overwrite.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
S=specs/mia/goals/G-V2.TOOLBOX/red-tests
copy $S/acceptance/test_toolbox.py tests/acceptance/test_toolbox.py
copy $S/acceptance/contract/test_if_203_v1_transforms.py tests/acceptance/contract/test_if_203_v1_transforms.py
copy $S/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
copy $S/helpers/toolbox_fakes.py tests/helpers/toolbox_fakes.py
copy $S/helpers/mocks/if_203_transforms.py tests/helpers/mocks/if_203_transforms.py
copy $S/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
finish
