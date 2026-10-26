# Test specification: Pipeline runner (N-2.4.1)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/requirements.md   **Status:** Draft (Plan for node N-2.4.1, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-202 and IF-105 (provider), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-RUN-001 | REQ-RUN-001 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: a chat message alone starts no internet task | exact |
| TC-RUN-002 | REQ-RUN-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: /light! and /full! switch after confirmation; memory is freed on request | as stated |
| TC-RUN-003 | REQ-RUN-003 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-23: with the fake server down the user gets the plain message | exact |
| TC-RUN-004 | REQ-RUN-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-22: a learned choice is logged with the default and can be switched off and reversed | as stated |
| TC-RUN-005 | REQ-RUN-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-22: over the lookup suites 100 % of inputs are at most 4096 tokens at num_ctx 8192 | as stated |
| TC-RUN-006 | REQ-RUN-006 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-22: on the lookup suites the maximum is below 15 | per the criterion; never decided on one run |
| TC-RUN-007 | REQ-RUN-007 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-19: median over 20 runs is within 10 s, also while a review slice runs | per the criterion; never decided on one run |
| TC-RUN-008 | REQ-RUN-008 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-19: each of the four budgets ends a scripted run with a message naming it | as stated |
| TC-RUN-009 | REQ-RUN-009 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19: with a review slice running a chat message gets its first text within 10 s | as stated |
| TC-RUN-010 | REQ-RUN-010 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19: two simultaneous messages are answered one after the other | as stated |
| TC-RUN-011 | REQ-RUN-011 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: the contract suite test_if_103_model_server.py passes against the Workflow execution (stage 2) | as stated |
| TC-RUN-012 | REQ-RUN-012 | Inspection | 1 | the code and the log files of the repository | AC-1: with the mocks of the three interfaces a scripted workflow runs end to end; no other import exists | as stated |
| TC-RUN-013 | REQ-RUN-013 | Inspection | 1 | the code and the log files of the repository | AC-9: the lookup, verify and review entries run with the same runner; a new valid entry runs without a change of code | as stated |
| TC-RUN-014 | REQ-RUN-014 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19, AC-28: the contract suite test_if_202_run_workflow.py passes against the Pipeline runner (stage 2) | as stated |
| TC-RUN-015 | REQ-RUN-015 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2, AC-8: the contract suite test_if_105_evaluation_access.py passes against the Pipeline runner (stage 2) | as stated |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
