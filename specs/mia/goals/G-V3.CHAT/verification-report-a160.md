# Verification report A-160 (2026-11-19)

Reviewer read the plan package, commit `4446b553` and the tests, not the chat. Branch `verify/g-v3-chat-a160` from `master` `ee89fce2`.

## Result: Verified (no findings)
- Protected `tests/acceptance/test_end_message.py` 5/5 green; unit tests of chat, digest and review 85/85; JS 186/186.
- Full unit suite 2468 run, 2 failures, both `test_task_files_browser` (known, not ours). The other known reds (`test_checkout_untouched`, `test_make_voice_lines`) did not occur in this worktree.
- `check_sysml_model.py` OK. `trace_check.py`: no error or warning for REQ-CHA-073/074/075, REQ-WFM-142; its errors are old (other ids).
- Real wiring: `LiveDigest` -> `pipeline_model.chat(messages, profile, options)`; options are merged over the profile's base options, so `num_ctx` 8192 stays (REQ-CHA-073).
- Stop flag goes to the summary of a `done` run only (REQ-CHA-044 kept); `_stop` is cleared at the next queue item.
- Mutations, each caught: no `num_predict` (M1), no shorten (M2), no stop check (M3), stop flag for failed/stopped messages (M4, caught by unit test), full report as result (M5), no line clearing after text (M6).

## Verification matrix
Run in the clean worktree on 2026-11-19. "Mutation" = the code change that made the check fail (all restored).

| Requirement | Check | Where | Result | Mutation |
|---|---|---|---|---|
| REQ-CHA-073 (at most 1024 tokens per digest call) | TC-CHA-077 | `tests/acceptance/test_end_message.py` | pass | M1 no `num_predict`: fails |
| REQ-CHA-074 (summary over 1200 chars asked once more, never cut) | TC-CHA-078; TC-CHA-063 (3000-char text stays whole) | `test_end_message.py`, `tests/acceptance/test_chat_skill_turns.py` | pass | M2 no shorten: 2 failures |
| REQ-CHA-075 (Stop in the end message: plain sentence, no more call) | TC-CHA-079 | `test_end_message.py` | pass | M3 no stop check: fails; M4 flag also for failed/stopped: unit test fails |
| REQ-CHA-069 (line stays until the end message text is ready) | TC-CHA-080; `test_run_line_wiring.py`; IF-201 contract test | `test_end_message.py`, `tests/test_run_line_wiring.py`, `tests/acceptance/contract/test_if_201_chat_turn.py` | pass | M6 no clearing after text: fails |
| REQ-WFM-142 (review returns head, summary, flow count; no list of works) | TC-WFM-142; `test_review_chat.py`; `test_review_report.py` | `test_end_message.py`, `tests/test_review_chat.py`, `tests/test_review_report.py` | pass | M5 full report as result: both fail |
| REQ-CHA-044 (failed/stopped message still worded) | covered by code reading (`_worded` passes the flag for `done` only) and M4 | `chat_service.py:817` | pass | M4 |

Not in the matrix: no requirement of A-160 lacks a check. Status of the five requirements stays Draft until the Commit phase.

## Notes (not findings)
- Mutation M4 is caught only by the unit test, not by an acceptance test.
- Not measured: digest calls and seconds of the end message with the short result; the eval run after version 8 and the proposed eval case are still open (owner/labels).
