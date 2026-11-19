#!/usr/bin/env bash
# Dev run of EV-skill_turns as feedback after the digest step went from version 7 to 8 (A-160). Never the holdout. Feedback, not verification.
#   eval_skill_turns_dev.sh         look only: branch, tracked changes, other sessions' model use, model server, pin; prints what --do would do
#   eval_skill_turns_dev.sh --do    starts Ollama if needed, runs the dev suite (3 repeats, pin MP-light), prints the report
# Tell a running session first ("real run for about 5 minutes, please hold model tests"): the Ollama server is shared and has no queue.
set -euo pipefail
REPO=/home/maldun/prog/Python/MIA
PY=/home/maldun/prog/Python/venvs/mia312/bin/python
PIN_DIGEST=sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3
mode=look; [ "${1:-}" = "--do" ] && mode=do
cd "${MIA_REPO:-$REPO}"
echo "== state"
echo "branch $(git rev-parse --abbrev-ref HEAD), HEAD $(git rev-parse --short HEAD)"
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "STOP: tracked files changed; the run header names the commit"; exit 1; }
v=$(sed -n 's/^VERSION = "\([0-9]*\)".*/\1/p' skill_digest.py); echo "digest step version $v"
[ "$v" = 8 ] || echo "NOTE: this run is for version 8"
echo "== model server and pin"
if ! curl -sf localhost:11434/api/tags >/dev/null; then
    echo "Ollama is not answering on localhost:11434"
    if [ "$mode" = do ]; then podman start ollama >/dev/null; for _ in $(seq 30); do curl -sf localhost:11434/api/tags >/dev/null && break; sleep 1; done
    else echo "(--do would run: podman start ollama)"; fi
fi
if curl -sf localhost:11434/api/tags >/dev/null; then
    have=$(curl -s localhost:11434/api/tags | $PY -c "import json,sys; print(next((m['digest'] for m in json.load(sys.stdin)['models'] if m['name']=='gemma4:12b-it-qat'), 'missing'))")
    [ "sha256:$have" = "$PIN_DIGEST" ] || [ "$have" = "$PIN_DIGEST" ] || { echo "STOP: gemma4:12b-it-qat is $have, the pin says $PIN_DIGEST"; exit 1; }
    echo "pin MP-light: digest matches"
fi
if [ "$mode" = look ]; then echo "== would run: $PY tools/eval.py run skill_turns --pin MP-light --repeats 3   (dev split, saved in data/eval/)"; exit 0; fi
echo "== run"
$PY tools/eval.py run skill_turns --pin MP-light --repeats 3
echo "== done: the run file is the newest skill_turns__default__*.jsonl in data/eval/; read the outputs, do not decide a criterion from it (feedback only)"
