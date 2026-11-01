#!/usr/bin/env bash
# The IF-102 contract suite on a throwaway PostgreSQL (REQ-SLY-012, TC-SLY-001): the stage-3 step `contract-postgres` of stages.yaml (amendment A-59,
# D-158, N-3.1 Verify F6). Starts postgres:16 with its data on tmpfs on a random local port, runs the real side of the suite with
# MIA_TEST_DATABASE_URL, and removes the container again. It never pulls: the image must be local. A skipped test counts as a failure here.
#   bash tools/contract_postgres.sh                      MIA_DB_PYTHON=/path/to/python picks a python with psycopg 3 (requirements-db.txt)
set -eu
cd "$(dirname "$0")/.."
IMAGE=docker.io/library/postgres:16
PY=${MIA_DB_PYTHON:-python}
NAME=mia-contract-postgres-$$

podman image exists "$IMAGE" || { echo "the image $IMAGE is not local (this step never pulls; the owner runs: podman pull $IMAGE)"; exit 1; }
"$PY" -c "import psycopg" 2>/dev/null || { echo "$PY has no psycopg 3 (requirements-db.txt): set MIA_DB_PYTHON"; exit 1; }
podman run -d --rm --name "$NAME" -e POSTGRES_PASSWORD=test --tmpfs /var/lib/postgresql/data -p 127.0.0.1::5432 "$IMAGE" >/dev/null
trap 'podman rm -f "$NAME" >/dev/null 2>&1 || true' EXIT
URL="postgresql://postgres:test@127.0.0.1:$(podman port "$NAME" 5432 | sed 's/.*://')/postgres"
for _ in $(seq 60); do
    "$PY" -c "import psycopg, sys; psycopg.connect(sys.argv[1], connect_timeout=2).close()" "$URL" 2>/dev/null && break
    sleep 0.5
done

OUT=$(MIA_TEST_DATABASE_URL="$URL" "$PY" -m unittest discover -s tests/acceptance/contract -p "test_if_102_storage.py" -k _real 2>&1) && status=0 || status=$?
printf '%s\n' "$OUT" | tail -n 4
if [ "$status" = 0 ] && printf '%s\n' "$OUT" | grep -q "skipped"; then echo "a test was skipped: the suite did not run on PostgreSQL"; exit 1; fi
exit "$status"
