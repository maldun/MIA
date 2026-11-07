# Test specification: Voice playback (N-1.3)

**Requirements:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/requirements.md   **Status:** Draft (Plan for node N-1.3, 2026-10-25)

Tests of this part alone against the mocks of its neighbours (the mock of IF-101, and of IF-111 and IF-112 where used). The interface IF-112 is tested by its contract suite against the mock and the real part. Existing tests in `tests/js/` (`chat.test.mjs`, `character.test.mjs`, `sound.test.mjs`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = headless browser, up to 10 minutes; 4 = by hand or on the reference hardware.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-VPB-001 | REQ-VPB-001 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-13: with 5 scripted audio chunks the playback order equals the arrival order and no sentence overlaps | as stated |
| TC-VPB-002 | REQ-VPB-002 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-13: after mute no audio plays on this device; a second device still plays; after Stop no line of the stopped answer plays on this device, also one that arrives later, until the next answer begins or 3 s after the Stop, whichever comes first (its lines play, and so does a line that arrives later, such as the shocked line of a minus vote; fake clock) (D-157, D-165) | as stated |
| TC-VPB-003 | REQ-VPB-003 | Component | 1 | unit test in `tests/js/` with the mocks of the interfaces (`node --test`) | AC-13: a line with a missing file produces one report through `onLineError` (the page: one browser console warning) and no error shown; the conversation continues; no backend event (A-50) | as stated |
| TC-VPB-004 | REQ-VPB-004 | Component (browser) | 3 | `tests/test_page_requests.py` (D-141): the stub server `ui/tools/chat_stub_server.py` in the MIA image (stage `chat-on-stub`), headless Chromium of `localhost/mia-browser` (`tests/browser/Containerfile`) on loopback; the page is loaded, one voice line is uploaded and played, every request comes from Chromium's performance log; skipped (never passed) without podman or an image. Stage 1 keeps the source scan `tests/js/no-outside-requests.test.mjs` | AC-5: a browser test records every request of a session and finds 0 outside the host; the console shows no CSP violation | exact |
| TC-VPB-005 | REQ-VPB-005 | System | 3 | the compose stack, a real browser (D-144): `tests/test_delivery_on_stack.py` builds its own image tag of the checkout (`localhost/mia:vpb005`, `--pull=never`) and starts `deploy/compose.yaml` under its own project (`mia-vpb005`) on 127.0.0.1 only, with the host's Ollama through `OLLAMA_URL` (never the `ollama` profile, nothing pulled); headless Chromium of `localhost/mia-browser` (D-141) loads the page over the stack's http front and plays one voice line; every request comes from Chromium's performance log; the test removes its containers, volumes, network and image tag; skipped (never passed) without podman, podman-compose, an image or the model server. `tests/test_frontend_delivery.py` keeps the quick checks on `deploy/compose.yaml`, the Containerfile and the stub stage | AC-29: the chat page loads from the backend container; the frontend has no container of its own. Checked as: every request of the session (page, scripts, socket, the voice line) goes to the stack's own host and the line plays to its end; `sound.js` over the http and the https front equals the file in the `mia` container; the running services of the project are exactly mia, graph, https, searxng | as stated |
| TC-VPB-006 | REQ-VPB-006 | Component | 1 | unit test in `tests/js/` on the fake page of `tests/js/fake-dom.mjs` with a clock (`node --test`), A-132 | AC-1: with a stop 1 s ago a line that arrives after the speak-again request is enqueued; without the request it is still dropped | exact |

## Scenarios (speak again, A-132; the older checks of this file have none yet)

### TC-VPB-006 – speak again right after a stop
- Verifies: REQ-VPB-006
- Given: the voice player of the page with a clock, a Stop pressed 1 s ago
- When: the user asks to speak an answer again and an audio_reload arrives; in a second run no request is made and an audio_reload arrives
- Then: in the first run the line is enqueued; in the second run it is dropped, as before

## Assumptions (checked in validation)

- ASM-N1-001: a headless Chromium is available for the browser tests (`ui/tools/browser_check.py` uses it today); where it is not, the stage 2 tests are skipped, never weakened.
- ASM-N1-002: the phone figure (30 fps on any phone inside the network) is measured on the phones the owner has at hand; no particular device is named (HLS amendment 9).
