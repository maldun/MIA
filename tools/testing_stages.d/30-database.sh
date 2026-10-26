#!/usr/bin/env bash
# Stage: the PostgreSQL storage (node N-3.1, task T-08): the database container, the migration of the data folder and back.
# Available as soon as the compose file has a `db` service. Until then it says what is missing.
. "$(dirname "$0")/_common.sh"
has_db() { grep -qE '^\s+db:' "$ROOT/deploy/compose.yaml" 2>/dev/null; }
case "${1:-}" in
    describe) echo "database container (profile db) and 'migrate files-to-db / db-to-files' on a copy of your data folder" ;;
    available) has_db || { echo "not yet: N-3.1 T-08 (compose service db) is not built"; exit 1; } ;;
    auto) exit 1 ;;
    start) has_db || { echo "not yet: N-3.1 T-08 is not built"; exit 1; }
           (cd "$ROOT" && MIA_PROJECT=mia-testing bash deploy/up.sh db-only) && echo "try: bash tools/backup.sh out.tar.gz --db-container mia-testing_db_1 --db-user mia --db-name mia   (the data volume stays when the stage is stopped)" ;;
    stop) (cd "$ROOT" && MIA_PROJECT=mia-testing bash deploy/up.sh db down) ;;
    status) has_db && echo "available" || echo "not built" ;;
    *) echo "usage: $0 describe|available|auto|start|stop|status"; exit 2 ;;
esac
