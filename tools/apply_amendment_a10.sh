#!/usr/bin/env bash
# Amendment A-10 (owner 2026-10-27): structured memory (REQ-CHA-011, decision D-78). IF-302 v2: a `memory` record may carry `kind`, `status`, `subject`, `updated`; `kind` and `status` are checked when present. Three protected files change:
#   contracts/IF-302-record-tables.md   tests/helpers/mocks/if_302_record_tables.py   tests/acceptance/contract/test_if_302_record_tables.py
# Run it yourself in the MAIN checkout, after the branch with the amendment is merged:
#   bash tools/apply_amendment_a10.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a10.sh --do      copy the drafts over the installed files and run the suites; commit afterwards as "plan: A-10 ..."
#   bash tools/apply_amendment_a10.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
A=specs/mia/amendments/A-10
copy $A/IF-302-record-tables.md contracts/IF-302-record-tables.md
copy $D/tests/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
copy $D/tests/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
finish
echo
echo "contract suites after the amendment (in the image: the real providers need flask):"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_102_storage.py tests/test_record_tables.py
