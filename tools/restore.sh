#!/usr/bin/env bash
# Restore of a backup made by tools/backup.sh (REQ-SLY-008).
#   tools/restore.sh IN.tar.gz --db-container NAME [--db-user postgres] [--db-name postgres] [--data DIR]
# Order: the archive is checked first (nothing is touched if it is not a backup); then the state before the restore is saved next to the archive as
# mia-before-restore-<time>.tar.gz (a backup of the same kind); then the database is replaced and, with --data, the data folder is replaced.
set -eu
usage() { echo "usage: $0 IN.tar.gz --db-container NAME [--db-user USER] [--db-name NAME] [--data DIR]" >&2; exit 2; }
[ $# -ge 1 ] || usage
IN="$1"; shift
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
[ -f "$IN" ] || { echo "no such archive: $IN" >&2; exit 1; }
HERE="$(cd "$(dirname "$0")" && pwd)"
STAGE="$(mktemp -d)"; trap 'rm -rf "$STAGE"' EXIT

tar -C "$STAGE" -xzf "$IN" 2>/dev/null || { echo "not a backup archive: $IN" >&2; exit 1; }
[ -s "$STAGE/db.dump" ] || { echo "not a backup of MIA (no db.dump): $IN" >&2; exit 1; }
if [ -n "$DATA" ] && [ ! -f "$STAGE/data.tar" ]; then echo "the archive has no data folder but --data was given" >&2; exit 1; fi

SAFE="$(cd "$(dirname "$IN")" && pwd)/mia-before-restore-$(date +%Y%m%d-%H%M%S).tar.gz"
if [ -n "$DATA" ] && [ -d "$DATA" ]; then bash "$HERE/backup.sh" "$SAFE" --db-container "$CONTAINER" --db-user "$DB_USER" --db-name "$DB_NAME" --data "$DATA" >/dev/null
else bash "$HERE/backup.sh" "$SAFE" --db-container "$CONTAINER" --db-user "$DB_USER" --db-name "$DB_NAME" >/dev/null; fi
echo "state before the restore saved: $SAFE"

podman exec -i "$CONTAINER" pg_restore -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner < "$STAGE/db.dump"
if [ -n "$DATA" ]; then
    rm -rf "$DATA"; mkdir -p "$DATA"
    tar -C "$DATA" -xf "$STAGE/data.tar"
fi
echo "restored from: $IN"
