# Plan: Tools and sandbox (N-2.4.2)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.2-tools-and-sandbox/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.2-tools-and-sandbox/test-spec.md   **Status:** Draft (Plan for node N-2.4.2, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Code checks first, budget and trust label per call | REQ-TLS-001, REQ-TLS-008, IF-402 | TC-TLS-001, TC-TLS-008, contract suite of IF-402 | T-01 of the root plan (mocks installed) |
| T-02 Untrusted text is data | REQ-TLS-004 | TC-TLS-004 | T-01 |
| T-03 Sandbox or refuse | REQ-TLS-005 | TC-TLS-005 | T-01 |
| T-04 Web search and fetch, only queries leave the host | REQ-TLS-007, IF-404 | TC-TLS-007, contract suite of IF-404 | T-01 |
| T-05 Scholarly sources and the strict cut-off | REQ-TLS-003, IF-405 | TC-TLS-003, contract suite of IF-405 | T-01 |
| T-06 Lookup with sources | REQ-TLS-002 | TC-TLS-002 | T-01 |
| T-07 No invented source | REQ-TLS-006 | TC-TLS-006 | T-01 |

## Tasks

### T-01: Code checks first, budget and trust label per call
- Implements: REQ-TLS-001, REQ-TLS-008, IF-402
- Tests to turn green: TC-TLS-001, TC-TLS-008, contract suite of IF-402
- Touches: `checks.py`, `sandbox.py`, `sandbox_runner.py`, `web_tools.py`, `scholar.py`, `evidence.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-402, the one door to the tools.

### T-02: Untrusted text is data
- Implements: REQ-TLS-004
- Tests to turn green: TC-TLS-004
- Touches: `checks.py`, `sandbox.py`, `sandbox_runner.py`, `web_tools.py`, `scholar.py`, `evidence.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Injected instructions change no verdict and start no tool.

### T-03: Sandbox or refuse
- Implements: REQ-TLS-005
- Tests to turn green: TC-TLS-005
- Touches: `checks.py`, `sandbox.py`, `sandbox_runner.py`, `web_tools.py`, `scholar.py`, `evidence.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: `sandbox.py` exists.

### T-04: Web search and fetch, only queries leave the host
- Implements: REQ-TLS-007, IF-404
- Tests to turn green: TC-TLS-007, contract suite of IF-404
- Touches: `checks.py`, `sandbox.py`, `sandbox_runner.py`, `web_tools.py`, `scholar.py`, `evidence.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: From the real `web_tools.py`.

### T-05: Scholarly sources and the strict cut-off
- Implements: REQ-TLS-003, IF-405
- Tests to turn green: TC-TLS-003, contract suite of IF-405
- Touches: `checks.py`, `sandbox.py`, `sandbox_runner.py`, `web_tools.py`, `scholar.py`, `evidence.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: From the real `scholar.py`.

### T-06: Lookup with sources
- Implements: REQ-TLS-002
- Tests to turn green: TC-TLS-002
- Touches: `checks.py`, `sandbox.py`, `sandbox_runner.py`, `web_tools.py`, `scholar.py`, `evidence.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: A tool, not a workflow (D-50).

### T-07: No invented source
- Implements: REQ-TLS-006
- Tests to turn green: TC-TLS-006
- Touches: `checks.py`, `sandbox.py`, `sandbox_runner.py`, `web_tools.py`, `scholar.py`, `evidence.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Statistical; decided on the suite.
