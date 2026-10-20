#!/bin/bash
# Starts SearXNG for MIA's research on 127.0.0.1:<searxng_port> (default 8590) with podman (or docker).
#   tools/searxng/run.sh          start (or restart) the container
#   tools/searxng/run.sh stop     stop and remove it
#   tools/searxng/run.sh refresh  write settings.local.yml again from the template settings.yml (this machine's secret key stays), then restart the container: after a change of the engines
#   tools/searxng/run.sh check    ask it for a test search and show the first results
# The container restarts with the machine ("--restart unless-stopped" works with docker; with podman use `podman generate systemd` if wanted).
set -e
HERE="$(dirname "$(readlink -f "$0")")"
ENGINE="${CONTAINER_ENGINE:-$(command -v podman || command -v docker)}"
NAME=mia-searxng
# the port: $SEARXNG_PORT, else "searxng_port" of setup_cfg.json (or of setup_cfg.example.json when this machine has none yet), else 8590 (MIA reads the same key)
PORT="${SEARXNG_PORT:-$(python3 -c "import json, os; d='$HERE/../..'; f=d+'/setup_cfg.json'; f=f if os.path.exists(f) else d+'/setup_cfg.example.json'; print(json.load(open(f)).get('searxng_port', 8590))" 2>/dev/null || echo 8590)}"
CONF="$HERE/settings.local.yml"

case "${1:-start}" in
  stop)
    "$ENGINE" rm -f "$NAME"
    ;;
  refresh)
    # the secret key of this machine is kept (a new one would only log out nobody, but there is no reason to change it)
    SECRET="$(grep -m1 'secret_key:' "$CONF" 2>/dev/null | sed 's/.*"\(.*\)".*/\1/')"
    if [ -z "$SECRET" ]; then SECRET="$(openssl rand -hex 32)"; fi
    sed "s/__SECRET__/$SECRET/" "$HERE/settings.yml" > "$CONF"
    chmod 600 "$CONF"
    "$ENGINE" restart "$NAME"
    echo "settings.local.yml written from settings.yml, $NAME restarted; give it a few seconds, then: $0 check"
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
    echo "usage: $0 [start|stop|refresh|check]"; exit 1
    ;;
esac
