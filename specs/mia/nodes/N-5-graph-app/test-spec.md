# Test specification: Graph app (N-5)

**Requirements:** specs/mia/nodes/N-5-graph-app/requirements.md   **Status:** Draft (Plan for node N-5, 2026-10-26)

A leaf: an independent add-on tool that works only through the backend API IF-104, tested against the mock of IF-104 (the mock refuses an invalid graph with the broken rule named). The interface itself is tested by its contract suite against the mock and the real Backend. The integration step into the whole system is step 5 of N-0 (`tests/integration/N-0/step_05`), written outside the implementing session. Stages (M27): 1 = commit gate, 2 = up to 10 minutes (headless browser), 3 = up to 30 minutes (podman), 4 = by hand.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-GA-001 | REQ-GA-001 | Demonstration | 4 | the owner opens a recorded entry of the lookup in the app | AC-16: a recorded library entry of the lookup is drawn with all its nodes and edges | reviewer checklist |
| TC-GA-002 | REQ-GA-002 | Component | 1 | unit test against the mock of IF-104 (`tests/acceptance/contract` mock `if_104_graph_api`) | AC-16: a node edited as JSON is saved as the edited dictionary | exact |
| TC-GA-003 | REQ-GA-003 | Component | 1 | unit test against the mock of IF-104 (`tests/acceptance/contract` mock `if_104_graph_api`) | AC-27: each violation is refused with the rule named, in the app and again by the backend | as stated |
| TC-GA-004 | REQ-GA-004 | Component | 1 | unit test against the mock of IF-104 (`tests/acceptance/contract` mock `if_104_graph_api`) | AC-16: a former version is restored and saved as a new version | as stated |
| TC-GA-005 | REQ-GA-005 | Component | 1 | unit test against the mock of IF-104 (`tests/acceptance/contract` mock `if_104_graph_api`) | AC-15: the Graph app imports no database driver; every call goes to IF-104 | exact |
| TC-GA-006 | REQ-GA-006 | Component | 1 | unit test against the mock of IF-104 (`tests/acceptance/contract` mock `if_104_graph_api`) | AC-10: a context graph edit appears as a new version | as stated |
| TC-GA-007 | REQ-GA-007 | Component | 1 | unit test against the mock of IF-104 (`tests/acceptance/contract` mock `if_104_graph_api`) | AC-14: a request without a session shows the login only; the Graph app holds no password check of its own | exact |
| TC-GA-008 | REQ-GA-008 | Component | 1 | unit test against the mock of IF-104 (`tests/acceptance/contract` mock `if_104_graph_api`) | AC-16: export then seed gives identical entries | exact |
| TC-GA-009 | REQ-GA-009 | Inspection | 1 | the files of the Graph app | AC-20: no bundler files; the library is in the repository | exact |
| TC-GA-010 | REQ-GA-010 | Component (browser) | 2 | a headless browser against the mock of IF-104 | AC-5: a browser test finds 0 requests outside the host | exact |
| TC-GA-011 | REQ-GA-011 | System | 3 | the container started alone against the mock of IF-104, then in the compose stack | AC-29: starts alone against the mock of IF-104 and in the stack | exact |

Contract test cases of IF-104: TC-IF-104-01 to TC-IF-104-05 (listed in the root `test-spec.md`).

## Assumptions (checked in validation)

- ASM-N5-001: a headless Chromium is available for the browser tests; where it is not, the stage 2 tests are skipped, never weakened.
- ASM-N5-002: the Graph app is an add-on (owner, 2026-10-25): MIA is complete and usable without it, so a failing test here never blocks the other nodes.
