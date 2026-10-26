# Test specification: Chat agent (N-2.2)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md   **Status:** Draft (Plan for node N-2.2, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-201 (provider), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-CHA-001 | REQ-CHA-001 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-1: with the fake model each scripted answer arrives as ordered sentences | as stated |
| TC-CHA-002 | REQ-CHA-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: two users' messages appear with their names in the same history | as stated |
| TC-CHA-003 | REQ-CHA-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19: with 5 waiting messages the sixth is refused with a plain message; a third waiting message of one user is refused while another user can still send; positions are reported | as stated |
| TC-CHA-004 | REQ-CHA-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: after a stop request no further sentence is sent | exact |
| TC-CHA-005 | REQ-CHA-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: the bound is held; deletion without confirmation is refused | as stated |
| TC-CHA-006 | REQ-CHA-006 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: two requests give a new answer and a new audio stream | as stated |
| TC-CHA-007 | REQ-CHA-007 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-13: every mood of the map has a line or is declared silent; a missing file is logged and skipped | as stated |
| TC-CHA-008 | REQ-CHA-008 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-8: check dialogues pass at a rate fixed in Plan against the recorded baseline, decided statistically | per the criterion; never decided on one run |
| TC-CHA-009 | REQ-CHA-009 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-17: for each of the 7 situations the held mood equals the mood map | as stated |
| TC-CHA-010 | REQ-CHA-010 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-18: a scripted score change moves the mood offset in the right direction | as stated |
| TC-CHA-011 | REQ-CHA-011 | Measurement + component | 4 | (a) the holdout cases of the memory sample scored as in tools/memory_dev_run.py, run by the verifier and never by the implementer, pin MP-light, 3 repeats; (b) tests/test_memory_records.py (budget, exact) and tools/memory_cost.py on the owner's recent messages | AC-24: at least 9 of 11 holdout cases right (Wilson lower bound 0.5); the block within the budget and cheaper than dreaming | rule threshold, false alarm 0.0002 and miss 0.064 (n 11, good 0.95, bad 0.5, with the re-run); never decided on one run |
| TC-CHA-012 | REQ-CHA-012 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-6: a page that states a fact about a user leaves the memory unchanged | exact |
| TC-CHA-013 | REQ-CHA-013 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-24: the three actions work on a sample record | as stated |
| TC-CHA-014 | REQ-CHA-014 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-25: the detectors keep their recorded precision and recall on the behaviour suite | as stated |
| TC-CHA-015 | REQ-CHA-015 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-18: 100 % of scripted votes are stored complete and the scores equal their sums | as stated |
| TC-CHA-016 | REQ-CHA-016 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-18, AC-11: after the minus the answer text is unchanged and one case is proposed | exact |
| TC-CHA-017 | REQ-CHA-017 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-11: in 1000 opportunities after 5 net negative votes the behaviour appears at most 10 times | as stated |
| TC-CHA-018 | REQ-CHA-018 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-11: a reset restores the default rate; a vote on a fact leaves counters of facts unchanged | as stated |
| TC-CHA-019 | REQ-CHA-019 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-12: 50 of 50 stored items are recited word for word on request and at their due time | exact |
| TC-CHA-020 | REQ-CHA-020 | Inspection | 1 | the code and the log files of the repository | AC-15: no database driver is imported outside the storage client | as stated |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
