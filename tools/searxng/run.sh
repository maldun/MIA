#!/bin/bash
# Starts SearXNG for MIA's research on 127.0.0.1:8888 with podman (or docker).
#   tools/searxng/run.sh          start (or restart) the container
#   tools/searxng/run.sh stop     stop and remove it
#   tools/searxng/run.sh check    ask it for a test search and show the first results
# The container restarts with the machine ("--restart unless-stopped" works with docker; with podman use `podman generate systemd` if wanted).
set -e
HERE="$(dirname "$(readlink -f "$0")")"
ENGINE="${CONTAINER_ENGINE:-$(command -v podman || command -v docker)}"
NAME=mia-searxng
PORT="${SEARXNG_PORT:-8888}"
CONF="$HERE/settings.local.yml"

case "${1:-start}" in
  stop)
    "$ENGINE" rm -f "$NAME"
    ;;
  check)
    curl -s -m 30 "http://127.0.0.1:$PORT/search?q=python+asyncio&format=json" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(len(data.get('results', [])), 'results; engines that did not answer:', data.get('unresponsive_engines'))
for r in data.get('results', [])[:5]:
    print('-', r.get('title'), '|', r.get('url'))
"
    ;;
  start)
    if [ -z "$ENGINE" ]; then echo "podman or docker is needed"; exit 1; fi
    if [ ! -f "$CONF" ]; then
      sed "s/__SECRET__/$(openssl rand -hex 32)/" "$HERE/settings.yml" > "$CONF"
      chmod 600 "$CONF"
    fi
    "$ENGINE" rm -f "$NAME" >/dev/null 2>&1 || true
    "$ENGINE" run -d --name "$NAME" --restart unless-stopped -p "127.0.0.1:$PORT:8080" \
      -v "$CONF":/etc/searxng/settings.yml:Z docker.io/searxng/searxng:latest
    echo "SearXNG starts on http://127.0.0.1:$PORT (give it a few seconds), then: $0 check"
    ;;
  *)
    echo "usage: $0 [start|stop|check]"; exit 1
    ;;
esac
