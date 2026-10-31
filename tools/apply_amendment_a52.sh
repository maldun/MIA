#!/usr/bin/env bash
# Amendment A-52 (N-2.1, D-147, 2026-10-31): an Ollama-shaped HTTP stand-in of the model server IF-103, so that the mia container can start alone
# (REQ-API-013, AC-29, TC-API-013: tests/test_container_alone.py, stage 3). Note: specs/mia/amendments/A-52/A-52-note.md
# Protected file that is created:
#   tests/helpers/mocks/if_103_model_server_http.py     the stand-in (standard library only)
# The contract, the in-process mock and the suite of IF-103 are unchanged.
# INSTALL IT ON THE LINE OF WORK goal/v1 after the merge of v1-n21b.
#   bash tools/apply_amendment_a52.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a52.sh --do      install and run TC-API-013 on the host (podman, localhost/mia:latest); commit afterwards as "plan: A-52 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
copy $D/tests/helpers/mocks/if_103_model_server_http.py tests/helpers/mocks/if_103_model_server_http.py
finish
echo
python3 tests/test_container_alone.py
