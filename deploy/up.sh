#!/bin/bash
# deploy/up.sh [rocm|nvidia] [compose arguments]   start the stack (default: up -d --build); `deploy/up.sh down` stops it
# Makes deploy/.env with a secret for SearXNG on the first call. Needs podman with a compose provider (sudo dnf install podman-compose) or docker compose.
set -e
HERE="$(dirname "$(readlink -f "$0")")"
CALLER="$PWD"
# a path argument as the caller wrote it (relative to where the caller stood, not to deploy/)
abspath() { case "$1" in /*) echo "$1" ;; *) echo "$CALLER/$1" ;; esac; }
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
  ZIP="$([ -n "${2:-}" ] && abspath "$2" || true)"
  if [ -n "$ZIP" ] && [ ! "$ZIP" -ef "$ROOT/ui/character/$(basename "$ZIP")" ]; then cp "$ZIP" "$ROOT/ui/character/"; fi
  python3 "$ROOT/ui/tools/character_pack.py" install web
  exec "$0" up -d --no-deps --force-recreate mia
fi
# deploy/up.sh calibration [path/to/calibration.txt]   the personality text of MIA ("address me master ...") is not in git; copy it into the data volume
# (default: calibration.txt of the MIA folder) and restart MIA, which reads it at the start
if [ "${1:-}" = "calibration" ]; then
  FILE="$([ -n "${2:-}" ] && abspath "$2" || echo "$(dirname "$HERE")/calibration.txt")"
  [ -f "$FILE" ] || { echo "no such file: $FILE"; exit 1; }
  ENGINE="$(command -v podman || command -v docker)"
  CONTAINER="$($ENGINE ps -aq --filter "label=com.docker.compose.project=${MIA_PROJECT:-mia}" --filter label=com.docker.compose.service=mia | head -1)"
  [ -n "$CONTAINER" ] || { echo "MIA container not found, start the stack first: deploy/up.sh"; exit 1; }
  $ENGINE cp "$FILE" "$CONTAINER:/opt/mia/MIA/data/calibration.txt"
  $ENGINE restart "$CONTAINER" >/dev/null
  echo "calibration.txt copied into the data volume, MIA restarted"
  exit 0
fi
# deploy/up.sh memories [folder]   take over MIA's memories of an old installation (memories.json, long_time_history.json from the MIA folder or the given folder)
# MIA is stopped first (it saves its history when it stops), the files are copied over the ones in the data volume, then MIA starts again. The files the
# container had are kept next to the new ones as <name>.container-previous.
if [ "${1:-}" = "memories" ]; then
  DIR="$([ -n "${2:-}" ] && abspath "$2" || dirname "$HERE")"
  ENGINE="$(command -v podman || command -v docker)"
  CONTAINER="$($ENGINE ps -aq --filter "label=com.docker.compose.project=${MIA_PROJECT:-mia}" --filter label=com.docker.compose.service=mia | head -1)"
  [ -n "$CONTAINER" ] || { echo "MIA container not found, start the stack first: deploy/up.sh"; exit 1; }
  FOUND=()
  for name in memories.json long_time_history.json; do [ -f "$DIR/$name" ] && FOUND+=("$name"); done
  [ ${#FOUND[@]} -gt 0 ] || { echo "no memories.json or long_time_history.json in $DIR"; exit 1; }
  $ENGINE stop "$CONTAINER" >/dev/null
  SAVE="$(mktemp -d)"
  for name in "${FOUND[@]}"; do
    if $ENGINE cp "$CONTAINER:/opt/mia/MIA/data/$name" "$SAVE/$name" 2>/dev/null; then
      $ENGINE cp "$SAVE/$name" "$CONTAINER:/opt/mia/MIA/data/$name.container-previous"
    fi
    $ENGINE cp "$DIR/$name" "$CONTAINER:/opt/mia/MIA/data/$name"
    echo "copied $name"
  done
  rm -rf "$SAVE"
  $ENGINE start "$CONTAINER" >/dev/null
  echo "MIA started again with the old memories"
  exit 0
fi
# deploy/up.sh backup [file.tar.gz]    everything MIA keeps (data volume: histories, presets, gestures, chat log, calibration, library index ...) as one archive
# deploy/up.sh restore file.tar.gz     put it back (after a backup of the current state, made automatically as mia-before-restore-<time>.tar.gz)
# MIA is stopped while the files are copied (it saves its history when it stops) and started again.
if [ "${1:-}" = "backup" ] || [ "${1:-}" = "restore" ]; then
  MODE="$1"
  ENGINE="$(command -v podman || command -v docker)"
  CONTAINER="$($ENGINE ps -aq --filter "label=com.docker.compose.project=${MIA_PROJECT:-mia}" --filter label=com.docker.compose.service=mia | head -1)"
  [ -n "$CONTAINER" ] || { echo "MIA container not found, start the stack first: deploy/up.sh"; exit 1; }
  DATA=/opt/mia/MIA/data
  make_backup() {      # $1: archive; MIA is stopped before and started after by the caller
    local tmp; tmp="$(mktemp -d)"
    $ENGINE cp "$CONTAINER:$DATA/." "$tmp/"
    tar -czf "$1" -C "$tmp" .
    rm -rf "$tmp"
  }
  if [ "$MODE" = "backup" ]; then
    OUT="$(abspath "${2:-mia-backup-$(date +%Y%m%d-%H%M).tar.gz}")"
    $ENGINE stop "$CONTAINER" >/dev/null
    make_backup "$OUT"
    $ENGINE start "$CONTAINER" >/dev/null
    echo "backup written: $OUT ($(du -h "$OUT" | cut -f1))"
  else
    [ -n "${2:-}" ] || { echo "usage: deploy/up.sh restore file.tar.gz"; exit 1; }
    IN="$(abspath "$2")"
    [ -f "$IN" ] && tar -tzf "$IN" >/dev/null 2>&1 || { echo "not a readable .tar.gz: $IN"; exit 1; }
    $ENGINE stop "$CONTAINER" >/dev/null
    SAFE="$CALLER/mia-before-restore-$(date +%Y%m%d-%H%M%S).tar.gz"
    make_backup "$SAFE"
    echo "state before the restore saved: $SAFE"
    TMP="$(mktemp -d)"
    tar -xzf "$IN" -C "$TMP" --no-same-owner
    $ENGINE cp "$TMP/." "$CONTAINER:$DATA/"
    rm -rf "$TMP"
    $ENGINE start "$CONTAINER" >/dev/null
    echo "restored from $IN, MIA started again (files that are only in the volume stay; they are in $SAFE)"
  fi
  exit 0
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
