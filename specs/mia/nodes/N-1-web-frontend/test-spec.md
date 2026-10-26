# Test specification: Web Frontend (N-1)

**Requirements:** specs/mia/nodes/N-1-web-frontend/requirements.md   **Status:** Draft (Plan for node N-1, 2026-10-25)

The tests of the inner node: the voice playback, the character view and the chat page put together, step by step (steps 1 to 3 of `decomposition.yaml`; step 0 is the skeleton with all three as mocks). They decide the requirements that no single part can show: the whole page in a browser, a whole session, the frame rate with everything running, the stack. The tests of the parts are in their own test specifications. Stages (M27): 1 = commit gate, 2 = up to 10 minutes (headless browser), 3 = up to 30 minutes, 4 = by hand or on the reference hardware.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-N1-001 | REQ-FE-011, REQ-FE-012, REQ-FE-013 | Integration | 2 | step 1: the voice player real, the chat page and the character view as mocks; 5 scripted audio chunks and one voice line over the mock of IF-101 | playback in arrival order without overlap; mute and stop only on this device; a missing voice line is reported once | exact |
| TC-N1-002 | REQ-FE-006, REQ-FE-008, REQ-FE-009, REQ-FE-010, REQ-FE-015, REQ-FE-017, REQ-FE-020, REQ-FE-021 | Integration | 2 | step 2: the character view real in its iframe (Godot web export), the voice player real, the chat page as a mock; the 14 presets, the 5 gestures, every mood of the map and one unknown mood | each expression is shown; an unknown mood gives neutral; with the iframe blocked the mock chat still sends and receives | exact |
| TC-N1-003 | REQ-FE-001, REQ-FE-002, REQ-FE-003, REQ-FE-004, REQ-FE-005, REQ-FE-007, REQ-FE-014, REQ-FE-016, REQ-FE-018, REQ-FE-019, REQ-FE-022, REQ-FE-024, REQ-FE-031 | Integration | 3 | step 3: the whole page in a real browser against the mock of IF-101 at 360, 768 and 1440 px, both themes; two users, a queue of 3, 50 history records, a cut connection of 5 s | the chat, queue, history, drafts, regenerate, status line, voting, memory views, source edit and the login views behave as in the leaf tests with the character and the voice running at the same time | exact; phone part by `ui/CHECKLIST_CHAT_PHONE.md` (Demonstration) |
| TC-N1-004 | REQ-FE-026, REQ-FE-027, REQ-FE-028 | Integration | 3 | a whole session of the page with all three parts, recorded by a browser test; the same page opened over plain HTTP from a LAN address | 0 requests leave the host; the character does not load and the login form sends nothing over plain HTTP | exact |
| TC-N1-005 | REQ-FE-025 | Benchmark | 4 | BM-MIA-002 with the chat answering and the voice playing, 10 runs of 30 s on the desktop and on a phone in the network | median of the 10 runs is 30 fps or more on the desktop and on the phone | median of 10 runs, no particular device |
| TC-N1-006 | REQ-FE-029, REQ-FE-030, REQ-FE-023 | Inspection + system | 3 | the files of the frontend and the compose stack | no bundler files, Godot 4.6.1; the chat page loads from the backend container and the frontend has no container of its own | exact |

## Assumptions (checked in validation)

- ASM-N1-001: a headless Chromium is available for the browser tests (`ui/tools/browser_check.py` uses it today); where it is not, the stage 2 tests are skipped, never weakened.
- ASM-N1-002: the phone figure (30 fps on any phone inside the network) is measured on the phones the owner has at hand; no particular device is named (HLS amendment 9).
