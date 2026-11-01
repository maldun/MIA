# Test specification: Chat and login views (N-1.1)

**Requirements:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.1-chat-and-login-views/requirements.md   **Status:** Draft (Plan for node N-1.1, 2026-10-25)

Tests of this part alone against the mocks of its neighbours (the mock of IF-101, and of IF-111 and IF-112 where used). The interface IF-101 (consumer), providing IF-111 and IF-112 to the parts is tested by its contract suite against the mock and the real part. Existing tests in `tests/js/` (`chat.test.mjs`, `character.test.mjs`, `sound.test.mjs`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = headless browser, up to 10 minutes; 4 = by hand or on the reference hardware.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-CLV-001 | REQ-CLV-001 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-1: with the mock of IF-101, two users' messages show their names and the scripted answer appears sentence by sentence | as stated |
| TC-CLV-002 | REQ-CLV-002 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-1: with a mock queue of 3, the positions 1, 2, 3 are shown; stop sends the stop event once | as stated |
| TC-CLV-003 | REQ-CLV-003 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-1: after reload the last 50 messages of the mock appear in order; a message sent by the mock from another user appears within 2 s | as stated |
| TC-CLV-004 | REQ-CLV-004 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-1: with the mock connection cut for 5 s the state shows offline, the draft text stays, the page reconnects without a reload | as stated |
| TC-CLV-005 | REQ-CLV-005 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-1: the two controls send one event each; the mock answers are shown | as stated |
| TC-CLV-006 | REQ-CLV-006 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-1: with the character iframe blocked, a message is sent and answered | exact |
| TC-CLV-007 | REQ-CLV-007 | Demonstration | 4 | the reviewer checklist `ui/CHECKLIST_CHAT_PHONE.md` and the character checklist | AC-1: viewports 360, 768 and 1440 px show the layout; collapsed view shows the caption | reviewer checklist |
| TC-CLV-008 | REQ-CLV-008 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-21: the status line shows the mock mood and activity; opening an answer shows the mock account | as stated; phone part by the checklist (Demonstration) |
| TC-CLV-009 | REQ-CLV-009 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-17: a change pushed by the mock appears within 2 s without reload | as stated |
| TC-CLV-010 | REQ-CLV-010 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-18: a vote sends one event with category and subject; the mock scores are drawn per category and overall | as stated; phone part by the checklist (Demonstration) |
| TC-CLV-011 | REQ-CLV-011 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-12, AC-24: with 50 mock records all are listed; an edit and a delete send one event each | as stated |
| TC-CLV-012 | REQ-CLV-012 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-3: the edit event carries source id, old and new value | as stated |
| TC-CLV-013 | REQ-CLV-013 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-17: a mock run with a variant changes the outfit and shows the label; a run without keeps the chat's variant | as stated |
| TC-CLV-014 | REQ-CLV-014 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-14: the three views send one event each | as stated |
| TC-CLV-015 | REQ-CLV-015 | Inspection | 1 | the files and the page text of the repository | AC-20: the login page text is present | exact |
| TC-CLV-016 | REQ-CLV-016 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-1: browser checks at 360, 768 and 1440 px in both themes; touch targets measured at 44 px or more | exact; phone part by the checklist (Demonstration) |
| TC-CLV-017 | REQ-CLV-017 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-5: a browser test records every request of a session and finds 0 outside the host | exact |
| TC-CLV-018 | REQ-CLV-018 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-14: over plain HTTP to a LAN address the login form sends nothing | exact |
| TC-CLV-019 | REQ-CLV-019 | Inspection | 1 | the files and the page text of the repository | AC-20: no bundler files; the Godot version string is 4.6.1 | exact |
| TC-CLV-020 | REQ-CLV-020 | System | 3 | the compose stack, a real browser | AC-29: the chat page loads from the backend container; the frontend has no container of its own | as stated |
| TC-CLV-021 | REQ-CLV-021 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-1: with the mock of IF-101 every scenario of the chat page runs; no other request leaves the page | as stated |
| TC-CLV-022 | REQ-CLV-022 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-14: one logout request, socket closed, login shown | exact |
| TC-CLV-023 | REQ-CLV-023 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`); the card in the browser by checklist | AC-17: the card draws the figures, is updated in place, pause and resume, stays after done | exact |
| TC-CLV-024 | REQ-CLV-024 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-17: the files are listed newest first with a download link; files_changed draws again; no delete | exact |

## Assumptions (checked in validation)

- ASM-N1-001: a headless Chromium is available for the browser tests (`ui/tools/browser_check.py` uses it today); where it is not, the stage 2 tests are skipped, never weakened.
- ASM-N1-002: the phone figure (30 fps on any phone inside the network) is measured on the phones the owner has at hand; no particular device is named (HLS amendment 9).

## Scenarios

Status: **Draft** (written in Phase 3 after the verification, finding F11 / D-163; to be reviewed by the owner). Each block describes what its tests check today: the unit tests in `tests/js/` on fakes (a fake DOM, socket and REST client), the stage-2 browser tests in `tests/test_chat_views_browser.py` (the real page on the IF-101 mock server, headless Chromium, loopback only).

### TC-CLV-001 – Two users and a streamed answer
- Verifies: REQ-CLV-001
- Given: the page of anna and the mock of IF-101
- When: a message of ben and one of anna arrive, then an answer starts and two cumulative deltas and the end arrive
- Then: ben's message is headed "ben", anna's "You"; the answer grows in one row ("Hello", then "Hello anna."), its actions appear only at the end
- And: two users in a row are two groups

### TC-CLV-002 – Queue places and stop
- Verifies: REQ-CLV-002
- Given: three messages acknowledged at places 1, 2 and 3
- When: an answer starts, then the next one
- Then: the places read "–, 1, 2", then "–, –, 1"; a start for another user's message moves mine up instead of clearing it
- And: Stop sends `chat_stop` once (the page's Stop button)

### TC-CLV-003 – Shared history after a reload
- Verifies: REQ-CLV-003
- Given: the mock history holds three messages, sent out of order
- When: the page loads and another user writes
- Then: one request `/api/chat/history?limit=50`; the rows stand in the order of their ids and the live message is added last

### TC-CLV-004 – Connection cut and back
- Verifies: REQ-CLV-004
- Given: the page online in a browser with "my unsent draft" typed
- When: the socket's transport is closed
- Then: the state is offline or reconnecting with a banner, Send is off, the draft stays
- And: the page is online again within 20 s without a reload, the draft still there

### TC-CLV-005 – Regenerate and speak again
- Verifies: REQ-CLV-005
- Given: two written answers
- When: the controls under the last answer are used
- Then: each sends one call (`/api/regenerate`, `/api/speak_again`); regenerate is offered on the last answer only and moves to the new answer

### TC-CLV-006 – Chat without the character
- Verifies: REQ-CLV-006
- Given: a browser with WebGL whose requests to `*/character/*` are blocked
- When: the click-through of every view runs
- Then: the page tried to load `/character/`, and messages are sent and answered and every view works (no problem reported)

### TC-CLV-007 – The character as stage
- Verifies: REQ-CLV-007
- Given: the owner's checklist `ui/CHECKLIST_CHAT_PHONE.md`
- When: the page is viewed at 360, 768 and 1440 px
- Then: the layout of each size is shown; the collapsed view shows the caption

### TC-CLV-008 – Status line and the account of an answer
- Verifies: REQ-CLV-008
- Given: a status of the server (mood "curious", activity thinking, light model) and a written answer whose account has two steps
- When: the status arrives, and "how I got this" is clicked twice
- Then: the mood line, the busy composer and the model chip follow the status; the two steps are listed under the answer, asked once, and hidden by the second click

### TC-CLV-009 – The persona, live
- Verifies: REQ-CLV-009
- Given: the open Persona tab
- When: another user changes the persona; then again while the reader types in it
- Then: the persona is read and drawn again; while typing nothing is overwritten and a note says why

### TC-CLV-010 – A vote and the score
- Verifies: REQ-CLV-010
- Given: a written answer
- When: plus is clicked and the Score tab is opened
- Then: one vote with category `answer_quality` and the answer as subject; plus is marked pressed; the score shows overall and four categories

### TC-CLV-011 – Tasks, memos and memory
- Verifies: REQ-CLV-011
- Given: the Tasks tab with a task that is due
- When: its text is edited and saved; a record changes elsewhere
- Then: the save carries the text and the same due time; a memory without a source is refused before sending; `item_changed` of the open kind draws it again, another kind does not

### TC-CLV-012 – The trust of a source
- Verifies: REQ-CLV-012
- Given: the Sources tab
- When: a value is typed ("0,2", "1.5", "50%") and saved
- Then: 0.2 is sent with the source id; values outside 0..1 are refused before sending; the server's event carries old and new

### TC-CLV-013 – The variant label
- Verifies: REQ-CLV-013
- Given: the mock answers every third message from a workflow with the variant summer
- When: that answer and the next one arrive
- Then: "Outfit: summer" is shown and the variant goes to the character; with the next answer the label goes and the character gets none (the chat's variant)

### TC-CLV-014 – Login, password, account
- Verifies: REQ-CLV-014
- Given: the login and the account dialog
- When: a login, a wrong login, a throttled login and a change of password are sent
- Then: one request each; each failure is named differently; the passwords are checked before they are sent

### TC-CLV-015 – The login page says everything is visible
- Verifies: REQ-CLV-015
- Given: the page and its English and German texts
- When: the login text is read
- Then: it states that everything is visible to all users, in both languages

### TC-CLV-016 – Touch targets and sizes
- Verifies: REQ-CLV-016
- Given: a browser that emulates a phone (360 px, coarse pointer) with one written answer; a desktop browser in dark and light
- When: every visible control is measured; the window is set to 360, 768 and 1440 px
- Then: every control, the five answer actions included, is at least 44 x 44 px; no size scrolls sideways in either theme

### TC-CLV-017 – No request leaves the host
- Verifies: REQ-CLV-017
- Given: a browser session of the click-through (and TC-VPB-004's session with a voice line)
- When: every request is recorded
- Then: none goes to another host

### TC-CLV-018 – Password only over HTTPS or to localhost
- Verifies: REQ-CLV-018
- Given: the page opened as `http://mia-lan:8686` (a home-network name over plain HTTP)
- When: the login form is forced open and sent; the change of password is sent from such an address
- Then: the form is off and names HTTPS; no request reaches `/api/login` or `/api/change_password`

### TC-CLV-019 – Plain stack
- Verifies: REQ-CLV-019
- Given: the repository
- When: its files are inspected
- Then: no bundler files; ES modules and vendored libraries; the Godot version string is 4.6.1

### TC-CLV-020 – Delivered by the backend
- Verifies: REQ-CLV-020
- Given: the compose stack
- When: the chat page is loaded in a real browser
- Then: it comes from the backend container; the frontend has no container of its own

### TC-CLV-021 – Only IF-101 on the wire
- Verifies: REQ-CLV-021
- Given: the click-through of every view against the mock of IF-101, with every request and websocket event recorded
- When: the paths and events are compared with `contracts/IF-101-chat-api.md`
- Then: every one is named there (the page's files, the character page and the socket transport aside); none goes to another host

### TC-CLV-022 – Logout
- Verifies: REQ-CLV-022
- Given: a logged-in page with an open socket
- When: the user logs out
- Then: one `/api/logout`, the socket is closed, then the login is shown; a lost connection keeps the user logged in and says so

### TC-CLV-023 – The status card of a task
- Verifies: REQ-CLV-023
- Given: `task_status` events of one task
- When: a second status, Pause, Resume, Stop and the final status arrive
- Then: one card, updated in place; Pause and Resume call their operation; Stop is sent; the finished card stays with the final figures and without buttons

### TC-CLV-024 – The files list
- Verifies: REQ-CLV-024
- Given: the server lists a file
- When: the Files tab is opened and a task stores another file
- Then: the file is a download link `/api/files/<name>`, no delete is offered; `files_changed` draws the list again
