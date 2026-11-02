#!/usr/bin/env bash
# Preflight of the target before MIA is installed or updated (Phase 6; deploy/RUNBOOK.md). Fails loudly, changes nothing.
#   bash deploy/preflight.sh            checks the host, then the model server against the pins of specs/mia/eval-spec.md
# Reads OLLAMA_URL from the environment or deploy/.env (default http://127.0.0.1:11434). MIA_PREFLIGHT_MIN_GB (default 30) is the free space needed.
# A digest that differs from the pin is a model change (an amendment), not an install detail: the script stops there.
set -u
cd "$(dirname "$0")/.."
failed=0
fail() { echo "FAIL: $*"; failed=1; }
warn() { echo "WARN: $*"; }
ok() { echo "ok:   $*"; }

podman="${PODMAN:-podman}"
command -v "$podman" >/dev/null 2>&1 && ok "podman $("$podman" --version 2>/dev/null | head -1)" || fail "podman is not installed (PODMAN names another binary)"
command -v python3 >/dev/null 2>&1 || fail "python3 is not installed (the model check needs it)"

free_gb=$(df --output=avail -BG . | tail -1 | tr -dc 0-9)
[ "${free_gb:-0}" -ge "${MIA_PREFLIGHT_MIN_GB:-30}" ] && ok "${free_gb} GB free" || fail "only ${free_gb:-0} GB free here, ${MIA_PREFLIGHT_MIN_GB:-30} needed"

[ -f deploy/.env ] && ok "deploy/.env exists" || warn "deploy/.env is missing: up.sh makes it at the first start"

# ports: free, or held by the mia project already (an update)
for port in "${MIA_PORT:-8585}" "${MIA_HTTPS_PORT:-8586}"; do
    if command -v ss >/dev/null 2>&1 && ss -ltn 2>/dev/null | awk '{print $4}' | grep -q ":${port}\$"; then
        warn "port ${port} is in use (fine when it is the running mia stack, an update)"
    else
        ok "port ${port} is free"
    fi
done

# the GPU, for the AMD profile (deploy/up.sh rocm): the devices the container needs
if [ -e /dev/kfd ] && [ -e /dev/dri ]; then ok "GPU devices /dev/kfd and /dev/dri"; else warn "/dev/kfd or /dev/dri is missing: only the CPU profile will work"; fi

# what a fresh checkout lacks (deploy/RUNBOOK.md): MIA runs without them, but without character and voice
[ -d ui/godot/build/web ] || warn "ui/godot/build/web is missing: no character page (deploy/up.sh character <zip>)"
# the folder the stack mounts (compose.yaml: MIA_KOKORO_DIR, default voice/models/kokoro); both files must be there or speak.py crashes at its start
kdir="${MIA_KOKORO_DIR:-}"
if [ -z "$kdir" ] && [ -f deploy/.env ]; then kdir=$(grep -E '^MIA_KOKORO_DIR=' deploy/.env | tail -1 | cut -d= -f2-); fi
kdir="${kdir:-voice/models/kokoro}"
kmissing=0
for f in kokoro-v1.0.onnx voices-v1.0.bin; do
    [ -f "$kdir/$f" ] || { warn "$f missing in $kdir: no voice, speak.py crashes at its start (bash tools/fetch_kokoro.sh; MIA_KOKORO_DIR in deploy/.env)"; kmissing=1; }
done
[ "$kmissing" = 0 ] && ok "Kokoro voice files in $kdir"
ls voice/expressions/*.wav >/dev/null 2>&1 || warn "voice/expressions/*.wav is missing: no voice lines of the moods"

# the sandbox: the compose config switches the script check off
backend=$(python3 -c "import json;print(json.load(open('deploy/setup_cfg.compose.json')).get('sandbox_backend','?'))" 2>/dev/null)
[ "$backend" = "none" ] && warn "sandbox_backend is 'none' in deploy/setup_cfg.compose.json: the script check is off (known limitation, record it)" || ok "sandbox_backend is '$backend'"

url="${OLLAMA_URL:-}"
if [ -z "$url" ] && [ -f deploy/.env ]; then url=$(grep -E '^OLLAMA_URL=' deploy/.env | tail -1 | cut -d= -f2-); fi
url="${url:-http://127.0.0.1:11434}"
echo "-- model server $url against the pins of specs/mia/eval-spec.md"
python3 deploy/preflight_agent.py --pins specs/mia/eval-spec.md --ollama "$url" || failed=1

echo "Also by hand: free VRAM with the other residents of the card (ollama ps), the search engine (SearXNG container), the certificate of the https front."
[ "$failed" = 0 ] && echo "Preflight OK" || { echo "Preflight FAILED"; exit 1; }
