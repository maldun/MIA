# Test specification: Workflow execution (N-2.4)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/requirements.md   **Status:** Draft (Plan for node N-2.4, 2026-10-26)

The tests of the inner node: the parts put together step by step in the order of `decomposition.yaml` (N-2.4.3 → N-2.4.2 → N-2.4.1); step 0 is the skeleton with all parts as mocks. Each step case decides the requirements whose last refining part is integrated at that step. The tests of the parts are in their own test specifications. Model-dependent criteria are decided by the eval suites on the pinned model, never by these cases. Stages (M27): 1 = commit gate, 2 = up to 10 minutes, 3 = up to 30 minutes, 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-N24-001 | REQ-WFX-001, REQ-WFX-008, REQ-WFX-009, REQ-WFX-010, REQ-WFX-022 | Integration | 2 | step 1 of N-2.4: the run log real, the runner and the tools as mocks; every scenario of the node on the mocks of the neighbours | the requirements listed here hold end to end (AC-4, AC-15, AC-21); the tests of the parts involved still pass | as stated in the criteria; statistical criteria are decided by the eval suites, not by this case |
| TC-N24-002 | REQ-WFX-005, REQ-WFX-006, REQ-WFX-007, REQ-WFX-014, REQ-WFX-015, REQ-WFX-016, REQ-WFX-017 | Integration | 2 | step 2 of N-2.4: the tools and the sandbox real as well; every scenario of the node on the mocks of the neighbours | the requirements listed here hold end to end (AC-2, AC-3, AC-5, AC-6); the tests of the parts involved still pass | as stated in the criteria; statistical criteria are decided by the eval suites, not by this case |
| TC-N24-003 | REQ-WFX-002, REQ-WFX-003, REQ-WFX-004, REQ-WFX-011, REQ-WFX-012, REQ-WFX-013, REQ-WFX-018, REQ-WFX-019, REQ-WFX-020, REQ-WFX-021, REQ-WFX-023, REQ-WFX-024, IF-202 | Integration | 2 | step 3 of N-2.4: the pipeline runner real as well: the whole workflow execution with the fake model server; every scenario of the node on the mocks of the neighbours | the requirements listed here hold end to end (AC-2, AC-8, AC-19, AC-22, AC-23, AC-28); the tests of the parts involved still pass | as stated in the criteria; statistical criteria are decided by the eval suites, not by this case |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
