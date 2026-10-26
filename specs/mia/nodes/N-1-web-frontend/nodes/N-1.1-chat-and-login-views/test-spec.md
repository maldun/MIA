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

## Assumptions (checked in validation)

- ASM-N1-001: a headless Chromium is available for the browser tests (`ui/tools/browser_check.py` uses it today); where it is not, the stage 2 tests are skipped, never weakened.
- ASM-N1-002: the phone figure (30 fps on any phone inside the network) is measured on the phones the owner has at hand; no particular device is named (HLS amendment 9).
