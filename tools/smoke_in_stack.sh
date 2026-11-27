#!/usr/bin/env bash
# Runs a smoke check in a throw-away container on the stack's network, where the names of deploy/.env resolve (`db` of MIA_DATABASE_URL;
# compose publishes no database port, by design). The host cannot reach them (VIEW Deploy finding F-2).
#   bash tools/smoke_in_stack.sh --image IMAGE [--network NET] [--env-file FILE] SCRIPT [ARGS...]
# IMAGE: a MIA image with psycopg (default $MIA_IMAGE); NET: default ${MIA_PROJECT:-mia}_default; FILE: default deploy/.env.
# The container gets an export of this checkout (tracked and new files, no .env), read-only, and the database URL through the environment
# only (from MIA_SMOKE_DATABASE_URL, MIA_DATABASE_URL or FILE; never printed, never in the arguments). The stack's database must be up.
# Exit: the smoke's own code; 2 when it cannot run.
set -u
IMAGE="${MIA_IMAGE:-}" NET="${MIA_PROJECT:-mia}_default" ENVF=deploy/.env
while [ $# -gt 0 ]; do
  case "$1" in
    --image) IMAGE="$2"; shift 2 ;;
    --network) NET="$2"; shift 2 ;;
    --env-file) ENVF="$2"; shift 2 ;;
    *) break ;;
  esac
done
usage="usage: bash tools/smoke_in_stack.sh --image IMAGE [--network NET] [--env-file FILE] SCRIPT [ARGS...]"
[ $# -ge 1 ] && [ -n "$IMAGE" ] || { echo "$usage" >&2; exit 2; }
SCRIPT="$1"; shift
cd "$(dirname "$0")/.."
podman="${PODMAN:-podman}"

[ -f "$SCRIPT" ] || { echo "cannot run: $SCRIPT does not exist in this checkout"; exit 2; }
"$podman" network exists "$NET" || { echo "cannot run: no network $NET (start the stack: deploy/up.sh)"; exit 2; }
"$podman" image exists "$IMAGE" || { echo "cannot run: no image $IMAGE"; exit 2; }

url="${MIA_SMOKE_DATABASE_URL:-${MIA_DATABASE_URL:-}}"
if [ -z "$url" ] && [ -f "$ENVF" ]; then url=$(grep -E '^MIA_DATABASE_URL=' "$ENVF" | tail -1 | cut -d= -f2-); fi

export_dir=$(mktemp -d)
trap 'rm -rf "$export_dir"' EXIT
# tracked files deleted in the checkout are skipped; .env files never leave the host
git ls-files -z -co --exclude-standard | while IFS= read -r -d '' f; do
  [ -f "$f" ] && [ "${f##*/}" != .env ] && printf '%s\0' "$f"
done | tar --null -T - -cf - | tar -xf - -C "$export_dir"

MIA_DATABASE_URL="$url" "$podman" run --rm --init --user 0 --network "$NET" -v "$export_dir:/work:ro,z" -w /work \
  -e PYTHONDONTWRITEBYTECODE=1 -e MIA_DATABASE_URL --entrypoint python "$IMAGE" "$SCRIPT" "$@"
