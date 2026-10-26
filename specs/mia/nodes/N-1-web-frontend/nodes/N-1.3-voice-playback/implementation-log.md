# Implementation log: Voice playback (N-1.3)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Playback queue and claim of the voice by one page | done | `feat(sound)` | `tests/js/voice-player.test.mjs` (TC-VPB-001: five lines in order without overlap, an early line waits, the end of a line is reported with its serial, claim at most every 3 s); the IF-112 contract suite with the real `VoicePlayer` behind a small adapter (scratch run, 10 of 10) | `VoicePlayer` is IF-112 |
| T-02 Mute and stop per user | done | `feat(sound)` | same file (TC-VPB-002: a muted device plays no sound and a second one does, stop clears the queue and ends speaking, a page that is not the owner stays silent, losing the voice stops the line) | |
| T-03 Voice lines with a missing file | done | `feat(sound)` | same file (TC-VPB-003: a line that cannot be loaded, by an `error` event or a failing `play()`, is reported once and the next one plays; blocked autoplay holds the lines and loses none) | |
| T-04 No outside request, delivered by the backend | done | `test(frontend)` | `tests/js/no-outside-requests.test.mjs` (TC-VPB-004, 3 tests), `tests/test_frontend_delivery.py` (TC-VPB-005, 2 tests: no frontend service in compose, the page and `sound.js` come from the backend container) | the strict CSP test of `tests/test_chat_page.py` (11 tests, venv) stays green |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| While autoplay is blocked, every new line caused another `play()` attempt and another `onBlocked`; the IF-112 contract (TC-IF-112-05) expects one report and a held queue | T-01 | `while autoplay is blocked no new attempt is made ...` (found by the contract suite in the scratch run) |
| A stop must forget a held autoplay, otherwise the next line is never tried | T-01 | `a stop forgets a held autoplay` |
| A page that is told another page plays must be able to get the voice back: `audio_owner` with its own id now sets the owner again (before it never switched off, so it never had to switch on) | T-02 | `a page that is not the owner stays silent` |
| IF-112 text says muted lines are dropped; today's code and the requirement ("silence it on that device only") keep the lines running without sound, so the character's mouth and the server's serial acknowledgements stay in step. The contract test only checks that nothing audible plays | T-02 | `a muted device plays no sound ...`; proposal for an amendment of the IF-112 text (no test change) |
| A browser answers `play()` with a promise; a test double answers at once. `VoicePlayer` handles both, so the synchronous contract suite can drive the real player | T-01 | the scratch contract run and the `immediate refusal` test |

## Reuse check (owner rule: use existing code)
- `sound.js` already had the behaviour; it was tied to the page. `LineQueue` and `mayClaim` stay as they are (tests unchanged and green). The logic moved into `VoicePlayer` and `initSound` calls it, with the same socket events (`audio_reload`, `audio_ended`, `audio_claim`, `audio_owner`), the same storage keys and the same heartbeat. The 39 existing JS tests and the 11 tests of `test_chat_page.py` pass unchanged. Nothing was rewritten from scratch.
- Not run in this session: the browser check `ui/tools/chat_audio_e2e.js` (headless Chromium through flatpak did not answer in the background session). Run it on the owner's machine: `bash tools/start_testing.sh start`, then the command in the header of that file.

## Plan amendments
None.

## Open questions for Phase 4 and the integration step
- The real provider in the IF-112 suite needs the adapter of the scratch run in `tests/acceptance/contract/test_if_112_voice_player.test.mjs` (its `make`) and `tests/helpers/contract.mjs` (owner, amendment at the integration step of N-1, step 1).
- IF-112 text: "queued lines are dropped while muted" should say that muted lines run without sound.
