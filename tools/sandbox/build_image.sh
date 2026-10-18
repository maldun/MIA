#!/bin/bash
# Builds (or rebuilds) the image of the podman sandbox backend: localhost/mia-sandbox:1. Needs podman and network access once.
#   tools/sandbox/build_image.sh          build
#   tools/sandbox/build_image.sh remove   remove the image again
set -e
HERE="$(dirname "$(readlink -f "$0")")"
IMAGE="${MIA_SANDBOX_IMAGE:-localhost/mia-sandbox:1}"
case "${1:-build}" in
  remove) podman rmi -f "$IMAGE" ;;
  build)  podman build --pull=newer -t "$IMAGE" -f "$HERE/Containerfile" "$HERE"
          echo "built $IMAGE: $(podman image inspect --format '{{.Size}}' "$IMAGE") bytes" ;;
  *)      echo "usage: $0 [build|remove]"; exit 1 ;;
esac
