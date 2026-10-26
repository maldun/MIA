# Test specification: Character view (N-1.2)

**Requirements:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.2-character-view/requirements.md   **Status:** Draft (Plan for node N-1.2, 2026-10-25)

Tests of this part alone against the mocks of its neighbours (the mock of IF-101, and of IF-111 and IF-112 where used). The interface IF-111 is tested by its contract suite against the mock and the real part. Existing tests in `tests/js/` (`chat.test.mjs`, `character.test.mjs`, `sound.test.mjs`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = headless browser, up to 10 minutes; 4 = by hand or on the reference hardware.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-CHV-001 | REQ-CHV-001 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-1: with the character iframe blocked, a message is sent and answered | exact |
| TC-CHV-002 | REQ-CHV-002 | Inspection | 1 | the files and the page text of the repository | AC-17: a scripted list of 14 presets and 5 gestures played through the API shows each on the character; no other call path exists | as stated |
| TC-CHV-003 | REQ-CHV-003 | Demonstration | 4 | the reviewer checklist `ui/CHECKLIST_CHAT_PHONE.md` and the character checklist | AC-1: reviewer checklist for mouth, blending, blinking, idle motion on desktop and phone | reviewer checklist |
| TC-CHV-004 | REQ-CHV-004 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-17: for every mood of the map and for 1 unknown mood the shown expression is the mapped one or neutral | exact |
| TC-CHV-005 | REQ-CHV-005 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-17: a change pushed by the mock appears within 2 s without reload | as stated |
| TC-CHV-006 | REQ-CHV-006 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-11: on a mock negative-vote answer the shocked expression is shown | exact |
| TC-CHV-007 | REQ-CHV-007 | Demonstration | 4 | the reviewer checklist `ui/CHECKLIST_CHAT_PHONE.md` and the character checklist | AC-17: a second .vrm model loads and the unmapped list is shown | reviewer checklist |
| TC-CHV-008 | REQ-CHV-008 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-17: a mock run with a variant changes the outfit and shows the label; a run without keeps the chat's variant | as stated |
| TC-CHV-009 | REQ-CHV-009 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-1: browser checks at 360, 768 and 1440 px in both themes; touch targets measured at 44 px or more | exact; phone part by the checklist (Demonstration) |
| TC-CHV-010 | REQ-CHV-010 | Benchmark | 4 | BM-MIA-002 on the reference hardware and a phone in the network | AC-19: median of 10 runs of 30 s reaches 30 fps on any phone inside the network (no particular device) and on the desktop | median of 10 runs |
| TC-CHV-011 | REQ-CHV-011 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-5: a browser test records every request of a session and finds 0 outside the host | exact |
| TC-CHV-012 | REQ-CHV-012 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-14: over plain HTTP to a LAN address the character does not load | exact |
| TC-CHV-013 | REQ-CHV-013 | Inspection | 1 | the files and the page text of the repository | AC-20: no bundler files; the Godot version string is 4.6.1 | exact |
| TC-CHV-014 | REQ-CHV-014 | System | 3 | the compose stack, a real browser | AC-29: the chat page loads from the backend container; the frontend has no container of its own | as stated |

## Assumptions (checked in validation)

- ASM-N1-001: a headless Chromium is available for the browser tests (`ui/tools/browser_check.py` uses it today); where it is not, the stage 2 tests are skipped, never weakened.
- ASM-N1-002: the phone figure (30 fps on any phone inside the network) is measured on the phones the owner has at hand; no particular device is named (HLS amendment 9).
