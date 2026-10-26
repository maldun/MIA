#!/usr/bin/env bash
# Backup of the shared state: the PostgreSQL database and the data folder as ONE archive (REQ-SLY-008).
#   tools/backup.sh OUT.tar.gz --db-container NAME [--db-user postgres] [--db-name postgres] [--data DIR]
# The archive holds db.dump (pg_dump custom format, all tables with all versions) and, with --data, data.tar (the folder with histories, presets,
# calibration ...). It is a script, not a list of steps: restore.sh puts both back. `deploy/up.sh backup` keeps covering the compose data volume.
set -eu
usage() { echo "usage: $0 OUT.tar.gz --db-container NAME [--db-user USER] [--db-name NAME] [--data DIR]" >&2; exit 2; }
[ $# -ge 1 ] || usage
OUT="$1"; shift
CONTAINER=""; DB_USER=postgres; DB_NAME=postgres; DATA=""
while [ $# -gt 0 ]; do
    case "$1" in
        --db-container) CONTAINER="${2:?}"; shift 2 ;;
        --db-user) DB_USER="${2:?}"; shift 2 ;;
        --db-name) DB_NAME="${2:?}"; shift 2 ;;
        --data) DATA="${2:?}"; shift 2 ;;
        *) usage ;;
    esac
done
[ -n "$CONTAINER" ] || usage
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT
podman exec "$CONTAINER" pg_dump -U "$DB_USER" -Fc "$DB_NAME" > "$STAGE/db.dump"
[ -s "$STAGE/db.dump" ] || { echo "the dump is empty" >&2; exit 1; }
[ -z "$DATA" ] || tar -C "$DATA" -cf "$STAGE/data.tar" .
mkdir -p "$(dirname "$OUT")"
tar -C "$STAGE" -czf "$OUT" .
echo "backup written: $OUT ($(du -h "$OUT" | cut -f1))"
