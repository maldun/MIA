#!/usr/bin/env bash
# Puts HTTPS (TLS) in front of a plain HTTP server, e.g. MIA's web app or the character test server.
# Browsers only run the Godot character (audio worklets, WebGL) in a "secure context": localhost or HTTPS.
# Opening http://<lan address>:<port> from another computer or phone fails with a message that HTTPS is needed.
#
# usage: ui/tools/https_proxy.sh <https port> [target host:port]
#   ui/tools/https_proxy.sh 8586 192.168.1.236:8585    MIA's web app (set "https_port":8586 in setup_cfg.json)
#   ui/tools/https_proxy.sh 8443 127.0.0.1:8060        the character test server (ui/tools/serve_web.py)
#
# A self-signed certificate is created in ui/certs (git-ignored) for localhost, this host name and the LAN addresses.
# Browsers warn once ("not secure", Advanced > continue); import ui/certs/mia.crt as trusted certificate to avoid the warning.
# Needs: openssl and socat. Web sockets (socket.io) pass through unchanged. For access from outside the home network
# use Tailscale instead (docs in the main README).
set -euo pipefail
UI="$(cd "$(dirname "$0")/.." && pwd)"
PORT="${1:?usage: https_proxy.sh <https port> [target host:port]}"
TARGET="${2:-127.0.0.1:8585}"
CERTS="$UI/certs"
mkdir -p "$CERTS"

if [ ! -f "$CERTS/mia.crt" ] || [ ! -f "$CERTS/mia.key" ]; then
  SAN="DNS:localhost,DNS:$(hostname),IP:127.0.0.1"
  for ip in $(hostname -I); do
    case "$ip" in *:*) ;; *) SAN="$SAN,IP:$ip" ;; esac   # IPv4 only
  done
  openssl req -x509 -newkey rsa:2048 -nodes -days 825 -subj "/CN=MIA local" -addext "subjectAltName=$SAN" \
    -keyout "$CERTS/mia.key" -out "$CERTS/mia.crt" 2>/dev/null
  chmod 600 "$CERTS/mia.key"
  echo "created certificate $CERTS/mia.crt for $SAN"
fi

echo "https://$(hostname -I | cut -d' ' -f1):$PORT  ->  http://$TARGET   (Ctrl+C to stop)"
exec socat "OPENSSL-LISTEN:$PORT,reuseaddr,fork,cert=$CERTS/mia.crt,key=$CERTS/mia.key,verify=0" "TCP:$TARGET"
