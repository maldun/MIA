# Plan: Record tables (N-3.3)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/requirements.md   **Test spec:** specs/mia/nodes/N-3-database/nodes/N-3.3-memories-history-feedback/test-spec.md   **Status:** Draft (Plan for node N-3.3, 2026-10-25)

A leaf of the Database. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own (Phase 2, step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/` or `contracts/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Definitions of the ten record tables | REQ-RTB-001, REQ-RTB-006 | TC-RTB-001, TC-RTB-006, TC-IF-302-01 | – |
| T-02 Required fields and validation | REQ-RTB-002, REQ-RTB-003, REQ-RTB-004, REQ-RTB-005 | TC-RTB-002..005, TC-IF-302-02, TC-IF-302-03 | T-01 |

## Tasks

### T-01: Definitions of the ten record tables
- Implements: REQ-RTB-001, REQ-RTB-006
- Tests to turn green: TC-RTB-001, TC-RTB-006, TC-IF-302-01
- Touches: `record_tables.py` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-302.

### T-02: Required fields and validation
- Implements: REQ-RTB-002, REQ-RTB-003, REQ-RTB-004, REQ-RTB-005
- Tests to turn green: TC-RTB-002..005, TC-IF-302-02, TC-IF-302-03
- Touches: `record_tables.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Validation never changes a document; the four vote categories come from the one place that names them.
