#!/usr/bin/env bash
# The real MIA backend with the accounts switched on, driven like a browser: no session is refused, login, a socket with the session, ONE real answer of the light
# model (gemma4:12b-it-qat through the Ollama container), the message carries the account, the change is recorded, logout drops the socket. About a minute.
#   bash tools/check_accounts_real.sh
# It starts the container `ollama` if it is not running, runs web_app in the MIA image with host networking and a throw-away config and data folder
# (setup_cfg.json is replaced for the run and put back), then unloads the model and stops Ollama again if this script started it. Needs podman and the image.
set -u
cd "$(dirname "$0")/.."
started=0
if ! curl -sf localhost:11434/api/tags > /dev/null; then
    podman start ollama > /dev/null 2>&1 && started=1
    for _ in $(seq 1 30); do curl -sf localhost:11434/api/tags > /dev/null && break; sleep 2; done
fi
curl -sf localhost:11434/api/tags | grep -q "gemma4:12b-it-qat" || { echo "the light model gemma4:12b-it-qat is not on this Ollama"; exit 2; }
timeout 330 podman run --rm --user 0 --network host -v "$PWD:/work:Z" -w /work "${MIA_IMAGE:-localhost/mia:latest}" python tools/check_accounts_real.py
code=$?
curl -s localhost:11434/api/generate -d '{"model":"gemma4:12b-it-qat","keep_alive":0}' > /dev/null    # let the card go before anything stops
sleep 5
[ "$started" = 1 ] && podman stop ollama > /dev/null 2>&1
exit $code
