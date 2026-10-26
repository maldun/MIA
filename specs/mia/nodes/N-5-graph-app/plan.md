# Plan: Graph app (N-5)

**Requirements:** specs/mia/nodes/N-5-graph-app/requirements.md   **Test spec:** specs/mia/nodes/N-5-graph-app/test-spec.md   **Status:** Draft (Plan for node N-5, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Show graphs as nodes and edges | REQ-GA-001 | TC-GA-001 | T-01 of the root plan (mocks installed) |
| T-02 Edit nodes as JSON, graph rules before saving | REQ-GA-002, REQ-GA-003 | TC-GA-002, TC-GA-003 | T-01 |
| T-03 Versions, history, diff and context graphs | REQ-GA-004, REQ-GA-006 | TC-GA-004, TC-GA-006 | T-01 |
| T-04 Login and work through the backend API only | REQ-GA-005, REQ-GA-007 | TC-GA-005, TC-GA-007 | T-01 |
| T-05 Library export and seed | REQ-GA-008 | TC-GA-008 | T-01 |
| T-06 Plain stack, no outside request, own container | REQ-GA-009, REQ-GA-010, REQ-GA-011 | TC-GA-009, TC-GA-010, TC-GA-011 | T-01 |

## Tasks

### T-01: Show graphs as nodes and edges
- Implements: REQ-GA-001
- Tests to turn green: TC-GA-001
- Touches: the Graph app (new folder `graph_app/`, plain HTML and JavaScript, no bundler)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Demonstration by the owner on a recorded lookup entry.

### T-02: Edit nodes as JSON, graph rules before saving
- Implements: REQ-GA-002, REQ-GA-003
- Tests to turn green: TC-GA-002, TC-GA-003
- Touches: the Graph app (new folder `graph_app/`, plain HTML and JavaScript, no bundler)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The rules are the shared graph rules module of N-3.2; the Backend validates again (TB-edit).

### T-03: Versions, history, diff and context graphs
- Implements: REQ-GA-004, REQ-GA-006
- Tests to turn green: TC-GA-004, TC-GA-006; TC-IF-104-01..05 (consumer side) in T-03
- Touches: the Graph app (new folder `graph_app/`, plain HTML and JavaScript, no bundler)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: A restore is saved as a new version.

### T-04: Login and work through the backend API only
- Implements: REQ-GA-005, REQ-GA-007
- Tests to turn green: TC-GA-005, TC-GA-007
- Touches: the Graph app (new folder `graph_app/`, plain HTML and JavaScript, no bundler)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: No database driver, no password check of its own.

### T-05: Library export and seed
- Implements: REQ-GA-008
- Tests to turn green: TC-GA-008
- Touches: the Graph app (new folder `graph_app/`, plain HTML and JavaScript, no bundler)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Export then seed gives identical entries.

### T-06: Plain stack, no outside request, own container
- Implements: REQ-GA-009, REQ-GA-010, REQ-GA-011
- Tests to turn green: TC-GA-009, TC-GA-010, TC-GA-011
- Touches: the Graph app (new folder `graph_app/`, plain HTML and JavaScript, no bundler)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The library for drawing is vendored in the repository.
