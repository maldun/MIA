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
| TC-OPR-007 | REQ-OPR-007 | System | 3 | each container started alone against the mocks of its neighbours, then all together (SMOKE-MIA-003) | each passes its contract suites alone; all start together with one configuration file | exact |
| TC-OPR-008 | REQ-OPR-008 | Inspection + system | 1 | the compose files; later a port scan from outside the network (owner, SMOKE-MIA-002) | only the HTTPS front publishes a port, bound to the host's network addresses; no `tailscale funnel` in any script; the scan finds nothing open | exact |
| TC-OPR-009 | REQ-OPR-009 | Inspection | 1 | `LICENSE`, the requirement files and the web log of a session | the licence text is GPL-3.0-or-later; no paid-API client library is listed; no paid API host in the log | exact |
| TC-OPR-010 | REQ-OPR-010 | Inspection | 1 | the compose files and the container environment of the model server | `OLLAMA_MAX_LOADED_MODELS` is 1 in every variant (CPU, ROCm, NVIDIA) | exact |

## Assumptions and open numbers

- ASM-N4-002: podman and `postgres:16` are available on the development host (as ASM-N3-001); the stage 3 tests are skipped, never weakened, where they are not.
- ASM-N4-003: the model server (Ollama) and the search service run as containers of the stack as they do today (`deploy/compose.yaml`).
