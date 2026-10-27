#!/usr/bin/env bash
# Amendment A-15 (owner 2026-10-27, N-2.3 T-01, D-89): the lifecycle of a workflow (status, specification, benchmark) lives in a new record table. IF-302 v3: the table
# `workflow_meta` (versioned, not deletable; `status` required and one of draft, tested, trusted, retired). Four protected files change:
#   contracts/IF-302-record-tables.md   tests/helpers/mocks/if_302_record_tables.py   tests/helpers/mocks/if_102_storage.py   tests/acceptance/contract/test_if_302_record_tables.py
# record_tables.py and workflow_library.py (not protected) already use the table.
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a15.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a15.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-15 ..."
#   bash tools/apply_amendment_a15.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
A=specs/mia/amendments/A-15
copy $A/IF-302-record-tables.md contracts/IF-302-record-tables.md
copy $D/tests/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
copy $D/tests/helpers/mocks/if_102_storage.py tests/helpers/mocks/if_102_storage.py
copy $D/tests/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
finish
echo
echo "contract suites after the amendment (in the image):"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_102_storage.py tests/test_record_tables.py tests/test_storage.py tests/test_workflow_library.py
