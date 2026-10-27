#!/usr/bin/env bash
# Amendment A-14 (N-2.3 T-01): the real provider of IF-203 in the contract suite. tests/helpers/contract.py gets an adapter (_WorkflowLibraryAdapter) that drives
# the REAL WorkflowLibrary (workflow_library.py) on the real Storage with the file backend; the suite passes the node costs (`costs=COSTS`) to the real provider.
# Result: the four _real cases of IF-203 run instead of skipping. Two protected files change:
#   tests/helpers/contract.py   tests/acceptance/contract/test_if_203_workflow_library.py
# Run it yourself in the MAIN checkout, after the branch n-2-3-t01 is merged:
#   bash tools/apply_amendment_a14.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a14.sh --do      copy the drafts over the installed files and run the suite; commit afterwards as "plan: A-14 ..."
#   bash tools/apply_amendment_a14.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
copy $D/tests/helpers/contract.py tests/helpers/contract.py
copy $D/tests/acceptance/contract/test_if_203_workflow_library.py tests/acceptance/contract/test_if_203_workflow_library.py
finish
echo
echo "contract suites after the amendment (in the image):"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_203_workflow_library.py tests/acceptance/contract/test_if_204_speech.py tests/acceptance/contract/test_if_102_storage.py
