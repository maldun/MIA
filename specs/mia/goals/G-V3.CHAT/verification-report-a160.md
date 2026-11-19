# Verification report A-160 (2026-11-19)

Reviewer read the plan package, commit `4446b553` and the tests, not the chat. Branch `verify/g-v3-chat-a160` from `master` `ee89fce2`.

## Result: Verified (no findings)
- Protected `tests/acceptance/test_end_message.py` 5/5 green; unit tests of chat, digest and review 85/85; JS 186/186.
- Full unit suite 2468 run, 2 failures, both `test_task_files_browser` (known, not ours). The other known reds (`test_checkout_untouched`, `test_make_voice_lines`) did not occur in this worktree.
- `check_sysml_model.py` OK. `trace_check.py`: no error or warning for REQ-CHA-073/074/075, REQ-WFM-142; its errors are old (other ids).
- Real wiring: `LiveDigest` -> `pipeline_model.chat(messages, profile, options)`; options are merged over the profile's base options, so `num_ctx` 8192 stays (REQ-CHA-073).
- Stop flag goes to the summary of a `done` run only (REQ-CHA-044 kept); `_stop` is cleared at the next queue item.
- Mutations, each caught: no `num_predict` (M1), no shorten (M2), no stop check (M3), stop flag for failed/stopped messages (M4, caught by unit test), full report as result (M5), no line clearing after text (M6).

## Notes (not findings)
- Mutation M4 is caught only by the unit test, not by an acceptance test.
- Not measured: digest calls and seconds of the end message with the short result; the eval run after version 8 and the proposed eval case are still open (owner/labels).
