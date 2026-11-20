#!/bin/bash
# deploy/build.sh TAG   build the mia image from a clean checkout of exactly TAG, tag it localhost/mia:TAG and :latest.
# The image is what deploy/up.sh starts (up -d --no-build afterwards, or up.sh rebuilds the same layers from the cache).
# Why the checks: a release image must come from the tag, not from whatever is in the folder. No pull: the base image is pinned by digest
# in deploy/Containerfile and must be local. Optional: SAVE=1 also writes dist/mia-TAG.tar (podman save) as the frozen artifact.
set -euo pipefail

TAG="${1:-}"
[ -n "$TAG" ] || { echo "usage: deploy/build.sh TAG   (e.g. v0.2.1)" >&2; exit 2; }
cd "$(dirname "$0")/.."

[ "$(git describe --tags --exact-match HEAD 2>/dev/null)" = "$TAG" ] || { echo "ERROR: HEAD is not the tag $TAG" >&2; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "ERROR: tracked files differ from the tag $TAG" >&2; exit 1; }

podman build --pull=never -f deploy/Containerfile -t "localhost/mia:$TAG" .
podman tag "localhost/mia:$TAG" localhost/mia:latest

echo "tag:       $TAG ($(git rev-parse --short HEAD))"
echo "image id:  $(podman image inspect --format '{{.Id}}' "localhost/mia:$TAG")"
echo "base:      $(grep -m1 '^FROM' deploy/Containerfile | cut -d' ' -f2)"
if [ "${SAVE:-}" = 1 ]; then
  mkdir -p dist
  podman save -o "dist/mia-$TAG.tar" "localhost/mia:$TAG"
  echo "saved:     dist/mia-$TAG.tar (sha256 $(sha256sum "dist/mia-$TAG.tar" | cut -d' ' -f1))"
fi
