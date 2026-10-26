# Test specification: Voice synthesis (N-2.5)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.5-voice-synthesis/requirements.md   **Status:** Draft (Plan for node N-2.5, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-204 (provider), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-VOI-001 | REQ-VOI-001 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-13: each sentence of a 5-sentence answer yields one audio chunk | as stated |
| TC-VOI-002 | REQ-VOI-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-13: on 10 answers with markup the synthesis input contains none | exact |
| TC-VOI-003 | REQ-VOI-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-13: every mood of the map has a line or is declared silent; a missing file is logged and skipped | as stated |
| TC-VOI-004 | REQ-VOI-004 | Inspection | 1 | the code and the log files of the repository | AC-13: no default line is a third-party recording | as stated |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
