#!/usr/bin/env bash
# Stage: the whole MIA as it is today, with the real model, voice and character, in the compose stack (deploy/up.sh).
# Node status: the current code base (old backend). As the new nodes replace its parts, this stage keeps the same command and gets new things to try.
. "$(dirname "$0")/_common.sh"
case "${1:-}" in
    describe) echo "the whole MIA in containers with the real model (needs podman and the models; first start downloads them)" ;;
    available) command -v podman >/dev/null || { echo "podman is not installed"; exit 1; }
               [ -x "$ROOT/deploy/up.sh" ] || { echo "deploy/up.sh is missing"; exit 1; } ;;
    auto) exit 1 ;;                                  # not started by default: it is heavy
    start) (cd "$ROOT" && bash deploy/up.sh "${MIA_GPU:-}") ;;
    stop) (cd "$ROOT" && bash deploy/up.sh down) ;;
    status) (cd "$ROOT" && podman ps --format '{{.Names}} {{.Status}}' | grep -E '^mia_' || echo "stopped") ;;
    *) echo "usage: $0 describe|available|auto|start|stop|status"; exit 2 ;;
esac
