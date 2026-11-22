# Deployment record: G-V4.GRAPHSTORE.CORE (`goal/v4` @ eb5ffb75) → the owner's host, MIA PostgreSQL server

**Kind:** subgoal; no version, no release artifact. Nothing of CORE is installed into the running MIA: the store has no user surface of its own, and the running release `mia:v0.2.1` stays as it is. Deploy is SMOKE-CORE-001 on the owner's two stores (plan.md, T-05; TR-CORE-009).
**Date:** 2026-11-22   **Run by:** the AI agent of this session, on the owner's decision (chat questionnaire: "I start db-only, run in container")

## Preflight
| Check | Result |
|---|---|
| Owner's database server | `mia_db_1` (postgres:16 by digest, volume `mia_pgdata`) was stopped; started with `deploy/up.sh db-only` in `/home/maldun/prog/Python/MIA`; healthy after 12 s |
| Reachability | no port is published (by design, `deploy/compose.yaml`); the check ran in a throw-away container `mia-core-smoke-<pid>` on the stack network `mia_default`, server URL `MIA_DATABASE_URL` of `deploy/.env` given as `MIA_SMOKE_DATABASE_URL` (the password was never printed) |
| Runtime | image `localhost/mia:v0.2.1` (Python 3.12.15) with the `goal/v4` worktree mounted read-only at `/w`; the image has **no psycopg** (see Known issues), so `psycopg` 3.3.6 and `psycopg_binary` of the host venv `mia312` (same Python 3.12, approved in `requirements-db.txt`) were mounted read-only; nothing downloaded, nothing installed into an image |
| Live data | the check writes only `mia_smoke` (it refuses any other target name) and a new temp folder; MIA's database `mia` and data volume are never written (TR-CORE-009) |

## Smoke tests (owner's host, owner's running PostgreSQL 16, stack network)
| Test | Result |
|---|---|
| SMOKE-CORE-001 files, workflow graph | ok: 3 versions by smoke-ann, smoke-bob, smoke-cy, each read as saved |
| SMOKE-CORE-001 files, context graph | ok: as above |
| SMOKE-CORE-001 postgres, workflow graph | ok: as above |
| SMOKE-CORE-001 postgres, context graph | ok: as above |
| Clean-up | temp folder removed; `mia_smoke` dropped by name; afterwards the server lists only `mia`, `postgres`, `template0`, `template1` |
| Overall | **SMOKE-CORE-001: green** (exit 0). REQ-WFM-152, 158, 159 on the owner's two stores: verified in Phase 6 |

Earlier the same check was green against a throw-away postgres:16 (Verify, 2026-11-22).

## Rollback
Nothing to roll back: no artifact was installed and no data of MIA was changed. Afterwards `mia_db_1` was stopped again (`podman stop`), so the stack is in the state it was found in (all `mia_*` containers stopped, `mia-searxng` running).

## Known issues
- **The release image cannot reach PostgreSQL:** `localhost/mia:v0.2.1` installs only `requirements.txt` (`deploy/Containerfile`), not `requirements-db.txt` with psycopg 3, and no product code reads `MIA_DATABASE_URL` yet. The database of `deploy/up.sh db` is provisioned but unused by MIA. Not a CORE defect: wiring MIA to the server is G-V4.GRAPHSTORE.TRANSFER (FR-58). It is a preflight item for that subgoal's Deploy: the image needs `requirements-db.txt`.
- Accepted deviations of the verification report: V-1, V-2, V-3 (D-414).

## Feedback items in this version
- none

## Open deferrals and shortcuts
- none in CORE's scope

## Validation hand-over
CORE has no validation of its own: Validate is the first test run of G-V5 (parked, D-386); the owner validated the behaviour on the prototype (round 03). The round 03 signatures (`Validated by`, `Decided by`) are still the owner's.

## Freeze (demonstrators only)
Not a demonstrator: no freeze.
