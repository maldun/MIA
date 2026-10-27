#!/usr/bin/env bash
# Amendment A-13 (N-2.5 T-01): the real provider of IF-204 in the contract suite. tests/helpers/contract.py gets an adapter (_SpeechAdapter) that drives the REAL
# SpeechService (speech_service.py) with a fake Speaker (writes a short silent wav, no TTS packages) and a generated hello.wav; the suite forwards the options of
# `make` (engine_down) to the real provider. Result: the three _real cases of IF-204 run instead of skipping. Two protected files change:
#   tests/helpers/contract.py   tests/acceptance/contract/test_if_204_speech.py
# Run it yourself in the MAIN checkout, after the branch n-2-5-t01 is merged:
#   bash tools/apply_amendment_a13.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a13.sh --do      copy the drafts over the installed files and run the suite; commit afterwards as "plan: A-13 ..."
#   bash tools/apply_amendment_a13.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
D=specs/mia/contract-drafts
copy $D/tests/helpers/contract.py tests/helpers/contract.py
copy $D/tests/acceptance/contract/test_if_204_speech.py tests/acceptance/contract/test_if_204_speech.py
finish
echo
echo "contract suite after the amendment (in the image):"
bash tools/run_in_image.sh tests/acceptance/contract/test_if_204_speech.py tests/acceptance/contract/test_if_201_chat_turn.py
