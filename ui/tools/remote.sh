#!/usr/bin/env bash
# Remote access to MIA over Tailscale (https inside your tailnet, no open port, nothing public).
#
#   ui/tools/remote.sh up [port]      publish MIA's web port (default 8585) with `tailscale serve --bg`, print the address
#   ui/tools/remote.sh status         what is served, and whether MIA answers on the port
#   ui/tools/remote.sh down [port]    stop publishing
#
# Install once:  curl -fsSL https://tailscale.com/install.sh | sh    then    sudo tailscale up
# In the admin console (https://login.tailscale.com/admin/dns) turn on MagicDNS and HTTPS Certificates (see the README: the machine name
# becomes public in certificate logs). Start MIA (python -m MIA) before or after; with "tailscale": true in setup_cfg.json MIA does `up`/`down` itself.
set -euo pipefail
ACTION="${1:-status}"
PORT="${2:-8585}"

command -v tailscale >/dev/null || { echo "tailscale is not installed: curl -fsSL https://tailscale.com/install.sh | sh"; exit 1; }
NAME="$(tailscale status --json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["Self"]["DNSName"].rstrip("."))' 2>/dev/null || true)"
[ -n "$NAME" ] || { echo "Tailscale is not running or not logged in: sudo tailscale up"; exit 1; }

case "$ACTION" in
  up)
    tailscale serve --bg "$PORT"
    echo "MIA is reachable in your tailnet: https://$NAME/"
    ;;
  down)
    tailscale serve --https=443 "$PORT" off
    echo "stopped"
    ;;
  status)
    tailscale serve status || true
    if curl -fsS -m 3 -o /dev/null "http://127.0.0.1:$PORT/"; then echo "MIA answers on port $PORT"; else echo "MIA does not answer on port $PORT (start it: python -m MIA)"; fi
    echo "address: https://$NAME/"
    ;;
  *) echo "usage: remote.sh up|down|status [port]"; exit 2 ;;
esac
