# Test specification: Run log (N-2.4.3)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.3-run-log/requirements.md   **Status:** Draft (Plan for node N-2.4.3, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-401 (provider), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-LOG-001 | REQ-LOG-001 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-21: the account equals a rendering of the logged events | exact |
| TC-LOG-002 | REQ-LOG-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-4: a secret fed to the writer does not appear in the log; a log with a broken order is reported | exact |
| TC-LOG-003 | REQ-LOG-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-4: replay equals the original | exact |
| TC-LOG-004 | REQ-LOG-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-4: on the recorded lookup run 100 % of statements link to a query | as stated |
| TC-LOG-005 | REQ-LOG-005 | Inspection | 1 | the code and the log files of the repository | AC-15: no database driver is imported by the code of the Run log or outside the storage client; the events of a run are appended to a file of the log folder and none is rewritten | as stated |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
