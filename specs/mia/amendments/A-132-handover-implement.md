# Hand-over for the Implement session of TD-11, option B (written 2026-11-07, D-279): turn the red tests green

Read `CLAUDE.md` first. Skills: `dev-workflow`, `implement-phase`, `local-coder` (not for production code). No model step: `agent-app-implement` does not apply. Plan record: `specs/mia/amendments/A-132-td-11-playback-options.md` (decisions D-275, D-277, D-278, D-279). Line of work: the branch that carries the red commits (`worktree-td-11-step4`, based on master `43f2988`); the owner merges.

## What is done
Four red-test commits (names in `git log`): `tests/test_chat_speak_again.py`, `tests/js/sound-speak-again.test.mjs`, `tests/test_sound_server_handover.py`, `tests/test_speak_again_browser.py` + `tests/browser/speak_again.py`, plus the change of `ui/tools/chat_mock_server.py` (D-278). Two stubs exist in production code and do nothing: the keyword `speak=None` of `ChatService` (`chat_service.py`) and the no-op `speakAgain()` in the handle of `initSound` (`templates/static/chat/sound.js`). Replace them; do not keep them as they are.

## Tasks (each: test first is already done; make these green, nothing else)
| # | Task | Requirements | Tests that turn green | May touch |
|---|---|---|---|---|
| 1 | `ChatService.speak(text, should_stop)`: `speak_again` hands each spoken sentence, in order, to `self._speak` (after `speech_text`, split by `SENTENCE_END`), one at a time behind a lock; a failing route (`OSError`) is logged once (`logger.error`), nothing else changes; `speak_again` keeps returning `{"sentences": n}` and the `audio_chunk` events | REQ-CHA-030, 031, 033, 034 | `tests/test_chat_speak_again.py`: TC-CHA-030, 031, 033, 034 | `chat_service.py` |
| 2 | `stop()` ends a speak-again playback that runs or waits, also when no answer is generated; a stop with nothing speaking must not stay set for the next speak again; wire `speak` in `web_app.py` (`speak_answer`-style: `SpeechStreamer` + `wait(should_stop)`) | REQ-CHA-032 | TC-CHA-032 and "a stop with nothing speaking changes nothing" in the same file | `chat_service.py`, `web_app.py` |
| 3 | The page forgets the 3 s window when the user asks to speak again: `speakAgain()` clears `stoppedAt`; `chat.js` calls it from the speaker action (one call, e.g. an `onSpeakAgain` callback given by `app.js`); without the request a late line is still dropped | REQ-VPB-006 | `tests/js/sound-speak-again.test.mjs` (TC-VPB-006), `tests/test_speak_again_browser.py` (TC-VPB-007) | `templates/static/chat/sound.js`, `chat.js`, `app.js` |
| 4 | Hand check TC-CHA-035 on the host by the owner (four steps in `test-spec.md` of N-2.2); the result goes into the verification report (TR-VOICE-002) | REQ-CHA-030, 032 | not automated | – |

Tasks 1 and 3 are independent; 2 follows 1. Keep the existing suites green: `tests/test_chat_answers.py`, `tests/test_chat_regenerate_speak.py`, `tests/test_chat_answer_events.py`, `tests/test_speech_*.py`, the IF-201 and IF-204 contract suites, `node --test "tests/js/*.test.mjs"`, `tests/test_sound_server_handover.py` (stays green).

## Red state at hand-over (the failure line of each)
| Test | Result now | Failure line |
|---|---|---|
| TC-CHA-030, 031, 032 (two tests), 033, 034 | red | `Lists differ: [] != ['One.', 'Two.', 'Three.', 'Shall I go on?']` (and the same form for the others); `False is not true : the voice route was not called`; `no logs of level ERROR or higher triggered on root` |
| TC-VPB-006 | 1 red, 1 green control | `+ actual - expected  + []  - ['/audio/line-000007.wav']` |
| TC-VPB-007 | 1 red, 1 green control | `AssertionError: 0 != 1 : []` (the reload reached the page, `reloads == 1`, but nothing was played) |
| TC-CHA-036 | green (characterization) | – |

## Open points the owner has not answered (do not guess)
1. **DECIDED by the owner (D-280): per sentence, as the scenarios say; the tests stay unchanged.** The real route then calls `speak` once per sentence; the loss of rendering ahead is accepted for now and belongs to TD-61. Background: the approved scenarios (TC-CHA-030, 031, 034) say the voice route gets one call per sentence (`One.`, `Two.`, `Three.`), as the tests assert. A-132 section 3 describes the real `speak(text, should_stop)` as `speak_answer` = `SpeechStreamer.finish` of the whole text plus `wait`. With one call per sentence each call opens a connection and waits until that sentence is played, which loses the rendering ahead of `speak_chunks`. The tests follow the scenarios. If the owner wants one call with the whole text, the scenarios and tests TC-CHA-030, 031, 032, 034 change by a plan amendment first.
2. **Name of the page call.** TC-VPB-006 calls `sound.speakAgain()` on the handle of `initSound` (not a contract; IF-112 is `VoicePlayer`). The name is the test's choice; a different name is a one-line change in the test by amendment.
3. **A latent fault read while writing TC-CHA-036:** the sound server's handler ends only after the client has closed its connection (the `_watch_close` thread holds the reader; `finish()` waits for it). A client that waits for the reply and does not close keeps the single-threaded server blocked. `SpeechStreamer.wait` always closes, so today's route is not hit; the test client closes the same way. Not part of TD-11; noted for TD-61.
4. **Mock and the real `publish_audio`:** the mock sends the line at `/mock/audio/line-NNNNNN.wav` with `message: "mock"`; the real url is `/audio/line-NNNNNN.wav`. The page does not care; TC-CHA-035 is the comparison with the real thing (TR-VOICE-005).

## Rules that bite
- Protected: `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `test-requirements.md`. The new tests are not in them (the test-spec names `tests/`), so a change of an expected value or a skipped test still needs a plan amendment: stop and report.
- Do not touch G-V2 or G-V3 files; `ChatService` and `sound.js`/`chat.js` may also be changed by G-V3 (A-132 section 9): rebase on master before the merge.
- Do not add dependencies. No new part or interface: `speak` is injected, IF-101 and IF-201 stay unchanged.
- Every finding gets a test first.

## Commands
- `/home/maldun/prog/Python/venvs/mia312/bin/python tests/test_chat_speak_again.py` (about 10 s red, about 1 s green); `... tests/test_sound_server_handover.py` (about 3 s)
- `node --test tests/js/sound-speak-again.test.mjs`; the browser check (podman, images `localhost/mia:latest` and `localhost/mia-browser`, about 20 s, skipped where missing): `/home/maldun/prog/Python/venvs/mia312/bin/python tests/test_speak_again_browser.py`
- Checks: `python ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests` (the six "no marker" warnings of REQ-CHA-030..034 and REQ-VPB-006 are gone; 540 errors are old, as on master), `req_graph.py`, `test_doc_check.py --tests-dir tests` (the new Python files have no finding).
