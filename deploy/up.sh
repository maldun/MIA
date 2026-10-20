#!/bin/bash
# deploy/up.sh [rocm|nvidia] [compose arguments]   start the stack (default: up -d --build); `deploy/up.sh down` stops it
# Makes deploy/.env with a secret for SearXNG on the first call. Needs podman with a compose provider (sudo dnf install podman-compose) or docker compose.
set -e
HERE="$(dirname "$(readlink -f "$0")")"
cd "$HERE"
# a value of .env (the environment wins), with a default
envval() { local v="${!1:-}"; if [ -z "$v" ] && [ -f .env ]; then v="$(sed -n "s/^$1=//p" .env | tail -1)"; fi; echo "${v:-$2}"; }
if [ ! -f .env ]; then
  echo "SEARXNG_SECRET=$(openssl rand -hex 32)" > .env
  chmod 600 .env
  echo "deploy/.env written (the SearXNG secret of this machine)"
fi
# deploy/up.sh character [path/to/mia-character-web-N.zip]   put the character into the stack: the zip (from your Drive) is checked against ui/character/manifest.json
# and unpacked to ui/godot/build/web, which the container mounts; MIA is then recreated so that it sees the new folder
if [ "${1:-}" = "character" ]; then
  ROOT="$(dirname "$HERE")"
  if [ -n "${2:-}" ] && [ ! "$2" -ef "$ROOT/ui/character/$(basename "$2")" ]; then cp "$2" "$ROOT/ui/character/"; fi
  python3 "$ROOT/ui/tools/character_pack.py" install web
  exec "$0" up -d --no-deps --force-recreate mia
fi
# the project name gives containers and volumes their prefix (mia_ollama ...); another name = a second stack next to the first
export COMPOSE_PROJECT_NAME="${MIA_PROJECT:-mia}"
FILES=(-f compose.yaml)
# OLLAMA_URL in .env (or the environment): use that Ollama and do not start one; otherwise the stack runs its own
if [ -z "${OLLAMA_URL:-}" ] && [ -f .env ]; then OLLAMA_URL="$(sed -n 's/^OLLAMA_URL=//p' .env | tail -1)"; fi
if [ -n "$OLLAMA_URL" ]; then export OLLAMA_URL; else FILES+=(--profile ollama); fi
case "${1:-}" in
  rocm|nvidia) FILES+=(-f "compose.$1.yaml"); shift ;;
esac
# for other devices (MIA_BIND=0.0.0.0): MIA must accept the pages that come by this machine's addresses and name
if [ -z "${MIA_PUBLIC_HOSTS:-}" ] && [ "$(envval MIA_BIND 127.0.0.1)" != "127.0.0.1" ]; then
  MIA_PUBLIC_HOSTS="$(hostname -s),$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -v ':' | paste -sd, -)"
  export MIA_PUBLIC_HOSTS
fi
DEFAULT=(up -d --build)
if [ -n "${COMPOSE:-}" ]; then
  if [ $# -eq 0 ]; then set -- "${DEFAULT[@]}"; fi
  RUN=($COMPOSE "${FILES[@]}")
elif command -v podman-compose >/dev/null 2>&1; then
  # podman-compose keeps a running container after a rebuild; the volumes (data, models) survive the recreation
  if [ $# -eq 0 ]; then set -- "${DEFAULT[@]}" --force-recreate; fi
  RUN=(podman-compose "${FILES[@]}")
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  if [ $# -eq 0 ]; then set -- "${DEFAULT[@]}"; fi
  RUN=(docker compose "${FILES[@]}")
else
  echo "no compose provider found: sudo dnf install podman-compose   (or set COMPOSE=\"...\")"; exit 1
fi


if [ "$1" != "up" ]; then
  exec "${RUN[@]}" "$@"
fi

"${RUN[@]}" "$@"
BIND="$(envval MIA_BIND 127.0.0.1)"; PORT="$(envval MIA_PORT 8585)"; SPORT="$(envval MIA_HTTPS_PORT 8586)"
HOSTS=(localhost)
if [ "$BIND" != "127.0.0.1" ]; then
  for ip in $(hostname -I 2>/dev/null); do case "$ip" in *:*) ;; *) HOSTS+=("$ip") ;; esac; done
fi
echo
echo "MIA is starting (it first waits for Ollama, the first start may download the models):"
for h in "${HOSTS[@]}"; do
  echo "  http://$h:$PORT    https://$h:$SPORT   (self-signed certificate: the browser asks once)"
done
if [ "$BIND" = "127.0.0.1" ]; then
  echo "  other devices: MIA_BIND=0.0.0.0 in deploy/.env, then deploy/up.sh again"
fi
echo "  log: deploy/up.sh logs -f mia      stop: deploy/up.sh down"
echo -n "waiting for the page "
for _ in $(seq 1 60); do
  if curl -s -o /dev/null -m 2 "http://127.0.0.1:$PORT/"; then echo " ready."; exit 0; fi
  echo -n "."; sleep 2
done
echo " not yet (a model download can take long); follow it with: deploy/up.sh logs -f mia"
