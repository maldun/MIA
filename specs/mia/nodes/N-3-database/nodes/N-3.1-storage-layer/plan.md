# Plan: Storage layer (N-3.1)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/requirements.md   **Test spec:** specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/test-spec.md   **Status:** Draft (Plan for node N-3.1, 2026-10-25)

A leaf of the Database. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own (Phase 2, step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/` or `contracts/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Storage interface and file backend | REQ-SLY-002, REQ-SLY-003, REQ-SLY-006, REQ-SLY-012 | TC-SLY-002, TC-SLY-003, TC-SLY-006 (files), TC-IF-102 (file backend as the real subject) | – |
| T-02 Validation hook | REQ-SLY-004 | TC-SLY-004 | T-01 |
| T-03 Accounts | REQ-SLY-005 | TC-SLY-005 | T-01 |
| T-04 Library export and seed | REQ-SLY-009 | TC-SLY-009 | T-01 |
| T-05 Migration command | REQ-SLY-007 | TC-SLY-007 (file side; the database side joins with T-06) | T-01 |
| T-06 PostgreSQL backend (needs approval) | REQ-SLY-001, REQ-SLY-002, REQ-SLY-003, REQ-SLY-006, REQ-SLY-012 | TC-SLY-001, TC-SLY-002, TC-SLY-003, TC-SLY-006 (PostgreSQL), TC-SLY-007 | T-01, T-05, **owner approval of psycopg 3** |
| T-07 Backup and restore | REQ-SLY-008 | TC-SLY-008 | T-06 |
| T-08 Container, network and compose service | REQ-SLY-010, REQ-SLY-011 | TC-SLY-010, TC-SLY-011 | T-06 |

## Tasks

### T-01: Storage interface and file backend
- Implements: REQ-SLY-002, REQ-SLY-003, REQ-SLY-006, REQ-SLY-012
- Tests to turn green: TC-SLY-002, TC-SLY-003, TC-SLY-006 (files), TC-IF-102 (file backend as the real subject)
- Touches: `storage.py`, `storage_files.py` (new); the existing stores (`chat_log.py`, `preset_store.py`, `gesture_store.py`) are moved behind it in later tasks of N-2
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Stage 0 of `deploy/REQUIREMENTS_DB.md`: interfaces first, the file implementation only, nothing changes for users.

### T-02: Validation hook
- Implements: REQ-SLY-004
- Tests to turn green: TC-SLY-004
- Touches: `storage.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Uses the mocks of IF-301 and IF-302 until the real parts exist.

### T-03: Accounts
- Implements: REQ-SLY-005
- Tests to turn green: TC-SLY-005
- Touches: `accounts.py` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: `hashlib.scrypt`, a random salt per account; the check of who may create an account stays in N-2.1.

### T-04: Library export and seed
- Implements: REQ-SLY-009
- Tests to turn green: TC-SLY-009
- Touches: `storage.py`, `tools/` script
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Uses the library files as they are today.

### T-05: Migration command
- Implements: REQ-SLY-007
- Tests to turn green: TC-SLY-007 (file side; the database side joins with T-06)
- Touches: `migrate.py` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Reads the file stores through the same interface, so both directions are the same code.

### T-06: PostgreSQL backend (needs approval)
- Implements: REQ-SLY-001, REQ-SLY-002, REQ-SLY-003, REQ-SLY-006, REQ-SLY-012
- Tests to turn green: TC-SLY-001, TC-SLY-002, TC-SLY-003, TC-SLY-006 (PostgreSQL), TC-SLY-007
- Touches: `storage_postgres.py`, `requirements-db.txt` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01, T-05, **owner approval of psycopg 3**
- Done when: the listed tests are green and all other tests are unchanged
- Notes: A spike first (one session): psycopg 3 against `postgres:16` in a podman container, LISTEN/NOTIFY across two connections within 2 s. Stop and report if the dependency is not approved.

### T-07: Backup and restore
- Implements: REQ-SLY-008
- Tests to turn green: TC-SLY-008
- Touches: `tools/backup.sh`, `tools/restore.sh` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-06
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The backup includes the database and the data folder; a script, not a list of steps.

### T-08: Container, network and compose service
- Implements: REQ-SLY-010, REQ-SLY-011
- Tests to turn green: TC-SLY-010, TC-SLY-011
- Touches: `deploy/` (compose file, database service, internal network)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-06
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The database is on an internal network of the stack; no published port.
