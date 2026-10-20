#!/bin/bash
# deploy/up.sh [rocm|nvidia] [compose arguments]   start the stack (default: up -d --build); `deploy/up.sh down` stops it
# Makes deploy/.env with a secret for SearXNG on the first call. Needs podman with a compose provider (sudo dnf install podman-compose) or docker compose.
set -e
HERE="$(dirname "$(readlink -f "$0")")"
cd "$HERE"
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
case "${1:-}" in
  rocm|nvidia) FILES+=(-f "compose.$1.yaml"); shift ;;
esac
DEFAULT=(up -d --build)
if [ -n "${COMPOSE:-}" ]; then
  if [ $# -eq 0 ]; then set -- "${DEFAULT[@]}"; fi
  exec $COMPOSE "${FILES[@]}" "$@"
elif command -v podman-compose >/dev/null 2>&1; then
  # podman-compose keeps a running container after a rebuild; the volumes (data, models) survive the recreation
  if [ $# -eq 0 ]; then set -- "${DEFAULT[@]}" --force-recreate; fi
  exec podman-compose "${FILES[@]}" "$@"
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  if [ $# -eq 0 ]; then set -- "${DEFAULT[@]}"; fi
  exec docker compose "${FILES[@]}" "$@"
else
  echo "no compose provider found: sudo dnf install podman-compose   (or set COMPOSE=\"...\")"; exit 1
fi
