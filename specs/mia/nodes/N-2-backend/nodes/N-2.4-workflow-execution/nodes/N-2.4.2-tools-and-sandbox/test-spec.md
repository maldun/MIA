# Test specification: Tools and sandbox (N-2.4.2)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.2-tools-and-sandbox/requirements.md   **Status:** Draft (Plan for node N-2.4.2, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-402 (provider), IF-404 and IF-405 (external), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-TLS-001 | REQ-TLS-001 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2: in the run log the code checks precede the first model call of each claim | as stated |
| TC-TLS-002 | REQ-TLS-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown | as stated |
| TC-TLS-003 | REQ-TLS-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: 0 violations of the cut-off; retracted works are dropped and listed | exact |
| TC-TLS-004 | REQ-TLS-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-6: injected instructions change no verdict and start no tool (red-team cases) | as stated |
| TC-TLS-005 | REQ-TLS-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-6: with the sandbox removed script checks report unavailable and nothing runs | exact |
| TC-TLS-006 | REQ-TLS-006 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-3: 0 invented references and 100 % of cited quotes found in their source | per the criterion; never decided on one run |
| TC-TLS-007 | REQ-TLS-007 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-5: the web log lists every query that left the machine | as stated |
| TC-TLS-008 | REQ-TLS-008 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-6: a call over the budget is refused with the budget named; every output carries its trust label | as stated |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
