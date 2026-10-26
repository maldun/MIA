# Test specification: API and accounts (N-2.1)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md   **Status:** Draft (Plan for node N-2.1, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-101 and IF-104 (provider), IF-201 and IF-203 (consumer), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-API-001 | REQ-API-001 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-1: with the fake model each scripted answer arrives as ordered sentences | as stated |
| TC-API-002 | REQ-API-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-15: a change by one user is visible on a second connection within 5 s with its author | as stated |
| TC-API-003 | REQ-API-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: correct credentials open a session; wrong ones do not | exact |
| TC-API-004 | REQ-API-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: the sixth failed attempt within a minute is refused even with the right password | exact |
| TC-API-005 | REQ-API-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: a search of the database and all logs after 10 logins finds no password | exact |
| TC-API-006 | REQ-API-006 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: a non-owner's create request is refused | exact |
| TC-API-007 | REQ-API-007 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: a request without a session is refused; a foreign origin is refused; the rate limit value is set in Plan | as stated |
| TC-API-008 | REQ-API-008 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-14: plain HTTP from a LAN address is refused | exact |
| TC-API-009 | REQ-API-009 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-15: 100 % of changes in a scripted session carry the account | as stated |
| TC-API-010 | REQ-API-010 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-20: a second user sees and changes a first user's workflow, preset and persona | as stated |
| TC-API-011 | REQ-API-011 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-20: the unit tests pass on 3.12 and the import works on 3.11 and 3.13 | exact |
| TC-API-012 | REQ-API-012 | Inspection | 1 | the code and the log files of the repository | AC-15: no database driver is imported outside the storage client | as stated |
| TC-API-013 | REQ-API-013 | System | 3 | the container started alone against the mocks of its neighbours | AC-29: the container starts alone against the mocks and serves the chat page | as stated |
| TC-API-014 | REQ-API-014 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-16: with the fake storage each of the six operations works; an invalid graph is refused with the rule named | exact |
| TC-API-015 | REQ-API-015 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1, AC-14: the contract suite test_if_101_chat_api.py passes against the API and accounts (stage 2) | as stated |
| TC-API-016 | REQ-API-016 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-16: the contract suite test_if_104_graph_api.py passes against the API and accounts (stage 2) | as stated |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
