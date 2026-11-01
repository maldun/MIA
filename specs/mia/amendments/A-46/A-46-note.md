# A-46: the smoke test of the compose stack, SMOKE-MIA-003 / TC-OPR-007 (N-4.2 T-03, D-133)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
TC-OPR-007 (REQ-OPR-007) is SMOKE-MIA-003, and `tests/smoke/` is protected. The owner chose (D-133): the `graph` container is the mia image serving `graph_app/` behind the https route `/graph/` (no own port); "graph alone" is the JavaScript contract suite of IF-104 run on the host against the files the container serves; the test is drafted here and installed by the owner.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `tests/smoke/smoke_stack.py` (new) | `specs/mia/contract-drafts/tests/smoke/smoke_stack.py` | builds `localhost/mia:smoke`; part 1 each alone: `mia` (the Python contract suites in the image), `db` (`tests/test_storage_postgres.py`, postgres:16 alone), `graph` (served files equal `graph_app/`, `node --test` of the IF-104 suite); part 2 together: `deploy/compose.yaml` with the db profile as project `mia-smoke` on free loopback ports, `/` and `/graph/` through the https front, the database ready, all five services running; removes its containers, volumes and image tag. Exit 0 green, 1 red, 2 cannot run |

Not protected, changed directly in the same commit (as A-37): the TC-OPR-007 row of the node's `test-spec.md` and the SMOKE-MIA-003 row of `specs/mia/test-spec.md` (one line each).

## Checked on a scratch copy (not installed)
Run on a copy of the branch (after 9c78385) with the draft laid into `tests/smoke/` and the venv `mia312`: mia alone 206 tests OK (25 skipped), db alone 17 OK, graph alone (served files equal `graph_app/`, IF-104 JS suite 5 pass, 5 skipped), all together (5 services, `/` and `/graph/` through https, db ready): "SMOKE-MIA-003: green", exit 0; everything it started was removed. It uses the model server already on the host (`OLLAMA_URL=http://host.containers.internal:11434`, `MIA_SMOKE_OLLAMA` overrides; exit 2 when none answers): with the stack's own ollama profile MIA pulls its models into an empty volume.

Install: `bash tools/apply_amendment_a46.sh` (look), then `bash tools/apply_amendment_a46.sh --do`; it needs `podman-compose`, `node` and the MIA virtualenv with `requirements-db.txt`.
