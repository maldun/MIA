# Plan: Run log (N-2.4.3)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.3-run-log/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.3-run-log/test-spec.md   **Status:** Draft (Plan for node N-2.4.3, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Typed run events with secrets removed | REQ-LOG-002, IF-401 | TC-LOG-002, contract suite of IF-401 | T-01 of the root plan (mocks installed) |
| T-02 Step-by-step account | REQ-LOG-001 | TC-LOG-001 | T-01 |
| T-03 Replay and comparison | REQ-LOG-003 | TC-LOG-003 | T-01 |
| T-04 Statements traceable to a query | REQ-LOG-004 | TC-LOG-004 | T-01 |
| T-05 State only through the storage interface | REQ-LOG-005 | TC-LOG-005 | T-01 |

## Tasks

### T-01: Typed run events with secrets removed
- Implements: REQ-LOG-002, IF-401
- Tests to turn green: TC-LOG-002, contract suite of IF-401
- Touches: `run_log.py`, `events.py`, `run_explain.py`, `reproduce.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-401; extends `events.py`.

### T-02: Step-by-step account
- Implements: REQ-LOG-001
- Tests to turn green: TC-LOG-001
- Touches: `run_log.py`, `events.py`, `run_explain.py`, `reproduce.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: A rendering of the logged events.

### T-03: Replay and comparison
- Implements: REQ-LOG-003
- Tests to turn green: TC-LOG-003
- Touches: `run_log.py`, `events.py`, `run_explain.py`, `reproduce.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: `reproduce.py` and `run_explain.py` already exist; align them with IF-401.

### T-04: Statements traceable to a query
- Implements: REQ-LOG-004
- Tests to turn green: TC-LOG-004
- Touches: `run_log.py`, `events.py`, `run_explain.py`, `reproduce.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-05: State only through the storage interface
- Implements: REQ-LOG-005
- Tests to turn green: TC-LOG-005
- Touches: `run_log.py`, `events.py`, `run_explain.py`, `reproduce.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Needs the mock of IF-102.
