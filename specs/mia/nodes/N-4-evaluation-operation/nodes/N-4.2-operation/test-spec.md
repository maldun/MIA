# Test specification: Operation (N-4.2)

**Requirements:** specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.2-operation/requirements.md   **Status:** Draft (Plan for node N-4.2, 2026-10-25)

Tests of installing, configuring, starting, stopping and securing MIA. Most of the code exists (`deploy/`, `config.py`, `shutdown.py`, `tests/test_deploy.py`, `tests/test_config.py`, `tests/test_shutdown.py`, `tests/shutdown_harness.py`); the new tests extend them for the database and the container per node. Stages (M27): 1 = commit gate, 2 = up to 10 minutes, 3 = up to 30 minutes (needs podman), 4 = by hand on a clean machine (Phase 6).

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-OPR-001 | REQ-OPR-001 | Smoke (target) | 3 | a fresh checkout, one configuration file, `deploy/up.sh` (SMOKE-MIA-001) | the compose stack comes up with the database; a chat message is answered | exact |
| TC-OPR-002 | REQ-OPR-002 | Integration | 3 | the first start with an empty accounts table, then a second start | the first start offers the creation of the first account exactly once; the second start does not | exact |
| TC-OPR-003 | REQ-OPR-003 | Unit | 1 | a configuration file with two options removed (the example file `setup_cfg.example.json` lists every option) | the report names both options and no others | exact |
| TC-OPR-004 | REQ-OPR-004 | Component | 2 | `tests/shutdown_harness.py`: SIGTERM, Ctrl+C and /goodnight! on a running instance with history and memory | after each stop the history and the memory are saved and identical on the next start | exact |
| TC-OPR-005 | REQ-OPR-005 | Component | 3 | a database with 50 records and a data folder; the backup command; both wiped; the restore command | the same records with all versions and the same files | exact |
| TC-OPR-006 | REQ-OPR-006 | Walkthrough | 4 | the owner follows the runbook once on a clean machine: start, update of the model pins, backup and restore, retirement (freeze with the model digests) | every step works as written; deviations are fixed in the runbook | exact (Phase 6) |
| TC-OPR-007 | REQ-OPR-007 | System | 3 | each container (`mia`, `db`, `graph`) started alone against the mocks of its neighbours (the protected mocks of `tests/helpers` running inside the mia image, A-37); `graph` alone means the graph container serving `graph_app/` and the JavaScript contract suite of IF-104 run on the host against the files it serves (A-46, D-133); then all together, the graph reached through the https front under `/graph/` (SMOKE-MIA-003, `tests/smoke/smoke_stack.py`) | each passes its contract suites alone (graph: every served file equals `graph_app/` and the suite passes); all start together with one configuration file | exact |
| TC-OPR-008 | REQ-OPR-008 | Inspection + system | 1 | the compose files; later a port scan from outside the network (owner, SMOKE-MIA-002) | nothing except the HTTPS front publishes a port on a non-loopback address (the http port of `mia` is bound to loopback, A-37); no `tailscale funnel` in any script; the scan finds nothing open | exact |
| TC-OPR-009 | REQ-OPR-009 | Inspection | 1 | `LICENSE`, the requirement files and the web log of a session | the licence text is GPL-3.0-or-later; no paid-API client library is listed; no paid API host in the log | exact |
| TC-OPR-010 | REQ-OPR-010 | Inspection | 1 | the compose files and the container environment of the model server | `OLLAMA_MAX_LOADED_MODELS` is 1 in every variant (CPU, ROCm, NVIDIA) | exact |

## Assumptions and open numbers

- ASM-N4-002: podman and `postgres:16` are available on the development host (as ASM-N3-001); the stage 3 tests are skipped, never weakened, where they are not.
- ASM-N4-003: the model server (Ollama) and the search service run as containers of the stack as they do today (`deploy/compose.yaml`).

## Test cases of G-V4.VIEW (moved at the merge 2026-11-25)
Unchanged from `specs/mia/goals/G-V4.VIEW/test-spec.md`; their test requirements TR-VIEW-001 to 021 are in `specs/mia/test-requirements.md`. All checks are exact. VAL-VIEW-01 stays in the goal record.

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|---|
| TC-OPR-011 | REQ-OPR-011 | inspection (file check) | 0 | `deploy/Containerfile`, `requirements-db.txt` | the image build installs `requirements-db.txt` in the stage that makes the release image | exact |

## Smoke tests of G-V4.VIEW (run in Phase 6, target environment)
| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-VIEW-001 | REQ-OPR-011 | the owner's host, the release image built by `deploy/` | the stack with the store setting pointing at the owner's PostgreSQL | `import psycopg` succeeds in the image; `GET /api/v2/store` answers `database`, reachable |

## Scenarios (G-V4.VIEW, approved by the owner 2026-11-22, D-441)

### TC-OPR-011 – The image installs the database driver
- Verifies: REQ-OPR-011
- Given: `deploy/Containerfile` and `requirements-db.txt` as committed
- When: the Containerfile is read
- Then: the stage that makes the release image installs `requirements-db.txt` (a `pip install` naming the file, after it is copied in)

### SMOKE-VIEW-001 – The database store from the release image
- Verifies: REQ-OPR-011
- Given: the owner's host; the release image built from `deploy/`; the store setting naming the owner's PostgreSQL
- When: the stack starts and `python -c "import psycopg"` runs in the MIA container; the owner asks `GET /api/v2/store`
- Then: the import succeeds
- And: the store route answers `database` and reachable
