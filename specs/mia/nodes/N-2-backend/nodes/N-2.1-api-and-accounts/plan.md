# Plan: API and accounts (N-2.1)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/test-spec.md   **Status:** Draft (Plan for node N-2.1, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Login, session, throttling, password handling, owner-only accounts | REQ-API-003, REQ-API-004, REQ-API-005, REQ-API-006 | TC-API-003, TC-API-004, TC-API-005, TC-API-006 | T-01 of the root plan (mocks installed) |
| T-02 Authenticated requests, secure channel, attribution, everything visible | REQ-API-007, REQ-API-008, REQ-API-009, REQ-API-010 | TC-API-007, TC-API-008, TC-API-009, TC-API-010 | T-01 |
| T-03 Chat events, streaming, changes reach all devices, realise IF-101 | REQ-API-001, REQ-API-002, REQ-API-015 | TC-API-001, TC-API-002, TC-API-015 | T-01 |
| T-04 Workflow and graph API, realise IF-104 | REQ-API-014, REQ-API-016 | TC-API-014, TC-API-016 | T-01 |
| T-05 Python versions, storage only through the interface, serve the frontend | REQ-API-011, REQ-API-012, REQ-API-013 | TC-API-011, TC-API-012, TC-API-013 | T-01 |

## Tasks

### T-01: Login, session, throttling, password handling, owner-only accounts
- Implements: REQ-API-003, REQ-API-004, REQ-API-005, REQ-API-006
- Tests to turn green: TC-API-003, TC-API-004, TC-API-005, TC-API-006
- Touches: `web_app.py`, `chat_api.py`, `presets_api.py`, `tls_proxy.py`, accounts (new `accounts.py`)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Password hash `hashlib.scrypt` (ASM-N3-002).

### T-02: Authenticated requests, secure channel, attribution, everything visible
- Implements: REQ-API-007, REQ-API-008, REQ-API-009, REQ-API-010
- Tests to turn green: TC-API-007, TC-API-008, TC-API-009, TC-API-010
- Touches: `web_app.py`, `chat_api.py`, `presets_api.py`, `tls_proxy.py`, accounts (new `accounts.py`)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-03: Chat events, streaming, changes reach all devices, realise IF-101
- Implements: REQ-API-001, REQ-API-002, REQ-API-015
- Tests to turn green: TC-API-001, TC-API-002, TC-API-015
- Touches: `web_app.py`, `chat_api.py`, `presets_api.py`, `tls_proxy.py`, accounts (new `accounts.py`)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-101; consumes IF-201.

### T-04: Workflow and graph API, realise IF-104
- Implements: REQ-API-014, REQ-API-016
- Tests to turn green: TC-API-014, TC-API-016
- Touches: `web_app.py`, `chat_api.py`, `presets_api.py`, `tls_proxy.py`, accounts (new `accounts.py`)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-104; consumes IF-203.

### T-05: Python versions, storage only through the interface, serve the frontend
- Implements: REQ-API-011, REQ-API-012, REQ-API-013
- Tests to turn green: TC-API-011, TC-API-012, TC-API-013
- Touches: `web_app.py`, `chat_api.py`, `presets_api.py`, `tls_proxy.py`, accounts (new `accounts.py`)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Consumes IF-102.
