# Implementation log of TD-11, option B (A-132; written 2026-11-07)

Line of work: branch `worktree-td-11-impl` (from master `77b93a2`). Input: `A-132-handover-implement.md`. The test runs below are feedback of the implementing session, not verification.

| Task | Commit | Tests reported green | Notes |
|---|---|---|---|
| 1 `ChatService.speak`: per sentence, in order, one playback at a time, one error line when the route fails | `7e5f91a` | TC-CHA-030, 031, 033, 034 | `speak_again` spawns the playback with the injected `spawn`, so the request returns at once in the app |
| (finding) mock sends `audio_reload` after speak again only with `MOCK_VOICE=1` | `410a4dd` | TC-CLV-021 and the 12 chat view browser tests; TC-VPB-007 still red until task 3 | see Findings |
| 2 `stop()` ends a spoken-again playback; `web_app.py` wires `speak_answer(sentence, should_stop)` | `e1a75d9` | TC-CHA-032 and the extra "stop with nothing speaking" test; all of `tests/test_chat_speak_again.py` | `stop()` now returns True when it ended a playback too |
| 3 page: `speakAgain()` clears the stop window, `chat.js` calls it before the request, `app.js` wires it | `d9d656c` | TC-VPB-006, TC-VPB-007; all 163 node tests; the chat view browser tests | |
| 4 hand check TC-CHA-035 | – | – | by the owner on the host (TR-VOICE-002); not done here |

Also green after the last commit: `tests/test_chat_*.py` (164), `tests/test_speech*.py` (36), `tests/test_workflow_voice.py`, the IF-201 contract suite (16), `tests/test_sound_server_handover.py` (2), `tests/test_chat_page.py`, `tests/test_frontend_delivery.py`.

## Findings (each with its test)
1. The Step 4 mock change (D-278) made the click-through of TC-CLV-021 fetch `/mock/audio/...`, a path outside IF-101. Test: the existing `test_the_session_uses_only_the_wire_of_if_101`. Fix: the speak hook of the mock is on only with `MOCK_VOICE=1`, which `tests/test_speak_again_browser.py` sets. Both files are test tooling, not protected.
2. `tests/test_chat_review.py::test_the_status_says_waiting_while_a_question_is_open` errored once in a loaded full run and passed alone and in two later full runs. Not in this task's files; looks timing dependent; no test added. For Phase 4 to watch.

## Decisions that are only in the code (for Phase 4, no requirement says them)
- `stop()` returns True when it ended a spoken-again playback although no answer ran (before: only True for a running answer). The chat_stop acknowledgement `{"stopped": ...}` therefore says True then.
- A stop ends every playback that runs or waits at that moment; a speak again requested after the stop is spoken (a generation counter, no flag stays set).
- A failing voice route (any exception, not only `OSError`) is logged once with `logger.error` and drops the rest of that request.
- In the app `speak_answer` makes one connection per sentence (decision D-280).

## Open questions for Phase 4
- TC-CHA-035 (hand check on the host) is still to be done by the owner.
- Documentation: no user-visible text changed (the button already existed); no doc task.
