# Test specification: Voice playback (N-1.3)

**Requirements:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/requirements.md   **Status:** Draft (Plan for node N-1.3, 2026-10-25)

Tests of this part alone against the mocks of its neighbours (the mock of IF-101, and of IF-111 and IF-112 where used). The interface IF-112 is tested by its contract suite against the mock and the real part. Existing tests in `tests/js/` (`chat.test.mjs`, `character.test.mjs`, `sound.test.mjs`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = headless browser, up to 10 minutes; 4 = by hand or on the reference hardware.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-VPB-001 | REQ-VPB-001 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-13: with 5 scripted audio chunks the playback order equals the arrival order and no sentence overlaps | as stated |
| TC-VPB-002 | REQ-VPB-002 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-13: after mute no audio plays on this device; a second device still plays | as stated |
| TC-VPB-003 | REQ-VPB-003 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-13: a line with a missing file produces one report event and no error shown; the conversation continues | as stated |
| TC-VPB-004 | REQ-VPB-004 | Component (browser) | 2 | a headless browser against the stub server `ui/tools/chat_stub_server.py` and the mocks of the interfaces | AC-5: a browser test records every request of a session and finds 0 outside the host | exact |
| TC-VPB-005 | REQ-VPB-005 | System | 3 | the compose stack, a real browser | AC-29: the chat page loads from the backend container; the frontend has no container of its own | as stated |

## Assumptions (checked in validation)

- ASM-N1-001: a headless Chromium is available for the browser tests (`ui/tools/browser_check.py` uses it today); where it is not, the stage 2 tests are skipped, never weakened.
- ASM-N1-002: the phone figure (30 fps on any phone inside the network) is measured on the phones the owner has at hand; no particular device is named (HLS amendment 9).
