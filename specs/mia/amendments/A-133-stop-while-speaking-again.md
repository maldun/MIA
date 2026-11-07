# A-133 (Draft): the stop button while a message is spoken again

Status: **proposed; the requirements REQ-CHA-035 and REQ-CHA-036 are Draft and wait for the owner's review. Nothing is implemented.** Decision ids: **D-282** (owner choices of 2026-11-08). Follows A-132 (TD-11 option B), D-279 to D-281. No model step is involved.

## 1. The finding
Hand check TC-CHA-035 (2026-11-08, owner): the stop button is missing while the voice is repeated. Step 3 of the check ("press the speaker button, then Stop") could not be done.

## 2. Cause (read in the code, reproduced by the red test)
The page shows its stop button only while `chat_status` says `busy` and the activity is `thinking` or `speaking` (`mood.js` `followStatus` calls `composer.setBusy`; `composer.js` `stop.hidden = !busy`). `ChatService.status()` sets `busy` from a running answer (`_running`). A speak again runs no answer: no status is published and `busy` stays false, so no stop button.

The specification never said the page offers a stop during a repeat: REQ-CLV-002 speaks of "the running answer", and REQ-CHA-032 only says that a stop ends the playback. The hand check scenario assumed a button that the requirements did not promise. This is a gap in the specification (a decision that changes what users see), not a coding slip.

## 3. Decided by the owner (D-282)
- **How:** option "server status": while a spoken-again message plays or waits, `ChatService` reports `busy` true with the activity `speaking`, and returns to the former status afterwards. The page needs no change: it already shows Stop for that status. IF-101 `chat_status` has these fields and values, so the **contract stays unchanged**.
- **Process:** amendment, then requirement and scenario, then the red test, then the fix (the Implement task), the requirements being approved by the owner's review first.

Not chosen: a page-only stop while a line plays (no stop during the 1 to 2 s the engine needs before the first line); leaving it (TC-CHA-035 step 3 would have to change).

## 4. What this amendment changes (all Draft or new)
| Item | Change |
|---|---|
| `N-2.2-chat-agent/requirements.md` | new REQ-CHA-035 (busy and speaking while a repeat runs or waits), REQ-CHA-036 (status returns afterwards), both Draft, group SA, no approved text touched |
| `N-2.2-chat-agent/test-spec.md` | new check TC-CHA-037 (table row and scenario); TC-CHA-035 stays the hand check and now also confirms the visible button |
| `N-2.2-chat-agent/test-requirements.md` | TR-VOICE-001 applies to TC-CHA-037 too (the same fake voice route) |
| `tests/test_chat_speak_again.py` | two red tests for TC-CHA-037 (REQ-CHA-035, REQ-CHA-036) |

## 5. Checks (level, stage)
TC-CHA-037: component, stage 1, in the existing file with the fake voice route. Failing first against today's code: `AssertionError: [] is not true : no chat_status was published`.

## 6. Sketch for the Implement task (not built; do not build before the requirements are approved)
In `chat_service.py`: `status()` reports `busy` as `self._running or self._speak_pending > 0`; when a repeat is requested (`_speak_pending` goes 0 to 1) set the activity `speaking` and `publish_status()`; when the last playback ends or is stopped (`_play_again`, `finally`) clear the activity (`set_activity(None)`) unless an answer is running, and publish. Files: `chat_service.py` only. A speak again while an answer runs leaves that answer's status alone.

## 7. Plausibility (proposal only; a person rates)
REQ-CHA-035, 036: plausible: `publish_status` and `set_activity` exist and are used at the same places for answers; no number is introduced; the test uses the existing fake. `plausibility.yaml` is untouched.

## 8. Open for the owner
Review of REQ-CHA-035 and REQ-CHA-036 and the scenario of TC-CHA-037 (approve, change or reject); the hand-check step 3 stays as written.
