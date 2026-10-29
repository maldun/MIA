# Plan: Chat and login views (N-1.1)

**Requirements:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.1-chat-and-login-views/requirements.md   **Test spec:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.1-chat-and-login-views/test-spec.md   **Status:** Draft (Plan for node N-1.1, 2026-10-25)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Chat view with sender, streaming and shared history | REQ-CLV-001, REQ-CLV-003, REQ-CLV-021 | TC-CLV-001, TC-CLV-003, TC-CLV-021 | T-01 of the root plan (mocks installed) |
| T-02 Stop, queue position, regenerate and speak again | REQ-CLV-002, REQ-CLV-005 | TC-CLV-002, TC-CLV-005 | T-01 |
| T-03 Connection state and drafts | REQ-CLV-004 | TC-CLV-004 | T-01 |
| T-04 Login views, password change and secure channel | REQ-CLV-014, REQ-CLV-015, REQ-CLV-018, REQ-CLV-022 | TC-CLV-014, TC-CLV-015, TC-CLV-018, TC-CLV-022 | T-01 |
| T-05 Status line, account of a task, voting, source trust edit, variant label | REQ-CLV-008, REQ-CLV-010, REQ-CLV-012, REQ-CLV-013 | TC-CLV-008, TC-CLV-010, TC-CLV-012, TC-CLV-013 | T-01 |
| T-06 Tasks, memos and memory views, editors | REQ-CLV-011, REQ-CLV-009 | TC-CLV-009, TC-CLV-011 | T-01 |
| T-07 Layout, accessibility, devices, chat without the character | REQ-CLV-006, REQ-CLV-007, REQ-CLV-016 | TC-CLV-006, TC-CLV-007, TC-CLV-016 (phone part by checklist) | T-01 |
| T-08 Plain stack, no outside request, delivered by the backend | REQ-CLV-017, REQ-CLV-019, REQ-CLV-020 | TC-CLV-017, TC-CLV-019, TC-CLV-020 | T-01 |
| T-09 Status card of a task and the files list | REQ-CLV-023, REQ-CLV-024 | TC-CLV-023, TC-CLV-024 (the card and the list in the browser by checklist) | T-01 |

## Tasks

### T-01: Chat view with sender, streaming and shared history
- Implements: REQ-CLV-001, REQ-CLV-003, REQ-CLV-021
- Tests to turn green: TC-CLV-001, TC-CLV-003, TC-CLV-021
- Touches: `templates/static/chat/chat.js`, `templates/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Extends `tests/js/chat.test.mjs`; the page talks to the Backend only through IF-101.

### T-02: Stop, queue position, regenerate and speak again
- Implements: REQ-CLV-002, REQ-CLV-005
- Tests to turn green: TC-CLV-002, TC-CLV-005
- Touches: `templates/static/chat/chat.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Positions 1 to 3 from the mock queue.

### T-03: Connection state and drafts
- Implements: REQ-CLV-004
- Tests to turn green: TC-CLV-004
- Touches: `templates/static/chat/chat.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Mock connection cut for 5 s.

### T-04: Login views, password change and secure channel
- Implements: REQ-CLV-014, REQ-CLV-015, REQ-CLV-018, REQ-CLV-022
- Tests to turn green: TC-CLV-014, TC-CLV-015, TC-CLV-018, TC-CLV-022
- Touches: `templates/`, `templates/static/chat/chat.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The password goes only over HTTPS or to localhost.

### T-05: Status line, account of a task, voting, source trust edit, variant label
- Implements: REQ-CLV-008, REQ-CLV-010, REQ-CLV-012, REQ-CLV-013
- Tests to turn green: TC-CLV-008, TC-CLV-010, TC-CLV-012, TC-CLV-013
- Touches: `templates/static/chat/chat.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The shocked reaction itself belongs to the character view (N-1.2).

### T-06: Tasks, memos and memory views, editors
- Implements: REQ-CLV-011, REQ-CLV-009
- Tests to turn green: TC-CLV-009, TC-CLV-011
- Touches: `templates/static/chat/chat.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: 50 mock records listed; an edit and a delete send one event each.

### T-07: Layout, accessibility, devices, chat without the character
- Implements: REQ-CLV-006, REQ-CLV-007, REQ-CLV-016
- Tests to turn green: TC-CLV-006, TC-CLV-007, TC-CLV-016 (phone part by checklist)
- Touches: `templates/`, `templates/static/chat/chat.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Viewports 360, 768 and 1440 px in both themes.

### T-08: Plain stack, no outside request, delivered by the backend
- Implements: REQ-CLV-017, REQ-CLV-019, REQ-CLV-020
- Tests to turn green: TC-CLV-017, TC-CLV-019, TC-CLV-020
- Touches: `templates/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The browser test records every request of a session.

### T-09: Status card of a task and the files list
- Implements: REQ-CLV-023, REQ-CLV-024
- Tests to turn green: TC-CLV-023, TC-CLV-024
- Touches: `templates/static/chat/task-card.js`, `task-card-model.js`, `workspace.js`, `api.js`, `app.js`, `messages.css`, `i18n/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Built on 2026-10-29 together with N-2.3 T-09 and T-10 (the model of the card is tested in `tests/js/taskcard.test.mjs`); the DOM parts wait for the owner's look in the browser.
