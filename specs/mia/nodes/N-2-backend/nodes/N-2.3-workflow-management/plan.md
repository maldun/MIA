# Plan: Workflow management (N-2.3)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/test-spec.md   **Status:** Draft (Plan for node N-2.3, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Versioned library and graph rules | REQ-WFM-002, REQ-WFM-003, REQ-WFM-004, REQ-WFM-026, IF-203 | TC-WFM-002, TC-WFM-003, TC-WFM-004, TC-WFM-026, contract suite of IF-203 | T-01 of the root plan (mocks installed) |
| T-02 Skills as tasks, drafts, specification before trust, time record | REQ-WFM-001, REQ-WFM-005, REQ-WFM-006, REQ-WFM-007 | TC-WFM-001, TC-WFM-005, TC-WFM-006, TC-WFM-007 | T-01 |
| T-03 Context graphs, schedule and estimate, variant per workflow | REQ-WFM-008, REQ-WFM-009, REQ-WFM-010 | TC-WFM-008, TC-WFM-009, TC-WFM-010 | T-01 |
| T-04 Verify workflow: code checks first, unclear without evidence, failed check informs the judge | REQ-WFM-011, REQ-WFM-012, REQ-WFM-013 | TC-WFM-011, TC-WFM-012, TC-WFM-013 | T-01 |
| T-05 Verify quality: judgement, stable verdicts, confidence by code, no invented source | REQ-WFM-014, REQ-WFM-015, REQ-WFM-023, REQ-WFM-024 | TC-WFM-014, TC-WFM-015, TC-WFM-023, TC-WFM-024 | T-01 |
| T-06 Lookup workflow and search command | REQ-WFM-016, REQ-WFM-017 | TC-WFM-016, TC-WFM-017 | T-01 |
| T-07 Review workflow: report, time slices, stop by code, source records | REQ-WFM-018, REQ-WFM-019, REQ-WFM-020, REQ-WFM-021 | TC-WFM-018, TC-WFM-019, TC-WFM-020, TC-WFM-021 | T-01 |
| T-08 Method transfer and storage only through the interface | REQ-WFM-022, REQ-WFM-025 | TC-WFM-022, TC-WFM-025 | T-01 |

## Tasks

### T-01: Versioned library and graph rules
- Implements: REQ-WFM-002, REQ-WFM-003, REQ-WFM-004, REQ-WFM-026, IF-203
- Tests to turn green: TC-WFM-002, TC-WFM-003, TC-WFM-004, TC-WFM-026, contract suite of IF-203
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-203; the graph rules module comes from N-3.2.

### T-02: Skills as tasks, drafts, specification before trust, time record
- Implements: REQ-WFM-001, REQ-WFM-005, REQ-WFM-006, REQ-WFM-007
- Tests to turn green: TC-WFM-001, TC-WFM-005, TC-WFM-006, TC-WFM-007
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-03: Context graphs, schedule and estimate, variant per workflow
- Implements: REQ-WFM-008, REQ-WFM-009, REQ-WFM-010
- Tests to turn green: TC-WFM-008, TC-WFM-009, TC-WFM-010
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The estimate comes from stored costs.

### T-04: Verify workflow: code checks first, unclear without evidence, failed check informs the judge
- Implements: REQ-WFM-011, REQ-WFM-012, REQ-WFM-013
- Tests to turn green: TC-WFM-011, TC-WFM-012, TC-WFM-013
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Delivered as a library entry that runs on the platform (D-50).

### T-05: Verify quality: judgement, stable verdicts, confidence by code, no invented source
- Implements: REQ-WFM-014, REQ-WFM-015, REQ-WFM-023, REQ-WFM-024
- Tests to turn green: TC-WFM-014, TC-WFM-015, TC-WFM-023, TC-WFM-024
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Statistical; criteria decided against the baseline.

### T-06: Lookup workflow and search command
- Implements: REQ-WFM-016, REQ-WFM-017
- Tests to turn green: TC-WFM-016, TC-WFM-017
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Lookup is the proof-of-concept scenario.

### T-07: Review workflow: report, time slices, stop by code, source records
- Implements: REQ-WFM-018, REQ-WFM-019, REQ-WFM-020, REQ-WFM-021
- Tests to turn green: TC-WFM-018, TC-WFM-019, TC-WFM-020, TC-WFM-021
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-08: Method transfer and storage only through the interface
- Implements: REQ-WFM-022, REQ-WFM-025
- Tests to turn green: TC-WFM-022, TC-WFM-025
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –
