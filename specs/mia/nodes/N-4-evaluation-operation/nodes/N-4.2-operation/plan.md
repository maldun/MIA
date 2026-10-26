# Plan: Operation (N-4.2)

**Requirements:** specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.2-operation/requirements.md   **Test spec:** specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.2-operation/test-spec.md   **Status:** Draft (Plan for node N-4.2, 2026-10-25)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Report of missing options | REQ-OPR-003 | TC-OPR-003 | – |
| T-02 Orderly shutdown with the database | REQ-OPR-004 | TC-OPR-004 | N-3.1 T-01 (the storage interface) |
| T-03 Compose stack: one container per node, internal network, no public port | REQ-OPR-007, REQ-OPR-008, REQ-OPR-010 | TC-OPR-007, TC-OPR-008, TC-OPR-010 | N-3.1 T-08 |
| T-04 Licence and dependency check | REQ-OPR-009 | TC-OPR-009 | – |
| T-05 Backup and restore of all data | REQ-OPR-005 | TC-OPR-005 | N-3.1 T-07 (database part) |
| T-06 First account at installation | REQ-OPR-002 | TC-OPR-002 | N-2.1 (accounts) |
| T-07 One command from a fresh checkout | REQ-OPR-001 | TC-OPR-001 (SMOKE-MIA-001) | T-03, T-05, T-06 |
| T-08 Runbook | REQ-OPR-006 | TC-OPR-006 | T-07 |

## Tasks

### T-01: Report of missing options
- Implements: REQ-OPR-003
- Tests to turn green: TC-OPR-003
- Touches: `config.py`, `setup_cfg.example.json`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Extends `tests/test_config.py`.

### T-02: Orderly shutdown with the database
- Implements: REQ-OPR-004
- Tests to turn green: TC-OPR-004
- Touches: `shutdown.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-3.1 T-01 (the storage interface)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Extends `tests/test_shutdown.py` and the shutdown harness.

### T-03: Compose stack: one container per node, internal network, no public port
- Implements: REQ-OPR-007, REQ-OPR-008, REQ-OPR-010
- Tests to turn green: TC-OPR-007, TC-OPR-008, TC-OPR-010
- Touches: `deploy/compose.yaml`, `deploy/compose.rocm.yaml`, `deploy/compose.nvidia.yaml`, `deploy/Containerfile`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-3.1 T-08
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The frontend stays inside the backend image; the Graph app gets its own service (N-5).

### T-04: Licence and dependency check
- Implements: REQ-OPR-009
- Tests to turn green: TC-OPR-009
- Touches: `tools/` (a check script)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: A list of banned paid-API packages kept in one place.

### T-05: Backup and restore of all data
- Implements: REQ-OPR-005
- Tests to turn green: TC-OPR-005
- Touches: `tools/backup.sh`, `tools/restore.sh` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-3.1 T-07 (database part)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: A script, not a list of steps: it calls the database part of N-3.1 and adds the data folder.

### T-06: First account at installation
- Implements: REQ-OPR-002
- Tests to turn green: TC-OPR-002
- Touches: `deploy/up.sh`, `__main__.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.1 (accounts)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The check of who may create an account stays with the Backend.

### T-07: One command from a fresh checkout
- Implements: REQ-OPR-001
- Tests to turn green: TC-OPR-001 (SMOKE-MIA-001)
- Touches: `deploy/up.sh`, `deploy/README.md`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-03, T-05, T-06
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The smoke test of Phase 6.

### T-08: Runbook
- Implements: REQ-OPR-006
- Tests to turn green: TC-OPR-006
- Touches: `deploy/RUNBOOK.md` (new; template `dev-workflow/assets/runbook.md`)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-07
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Run once on a clean machine by the owner.
