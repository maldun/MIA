# Hand-over G-V3.CHAT (written 2026-11-17): A-156 code done, suite state explained, two things wait for the owner

Read `CLAUDE.md`, then this file, then `amendments` A-156 (`specs/mia/amendments/A-156-draft-skill-run-speaks-once.md`) and `implementation-log.md` (last bullet of the T-06 block). Branch `master` in the main checkout, not pushed (push and merge are the owner's).

## Done this session (commits, oldest first)
- `440e599b` plan: A-156 applied (the six protected files, `requirements.md`, A-156, FB-09, `amendment-a156/`); red as announced (6 of 23 in `test_chat_skill_turns.py`).
- `7bdd9419` code: `skill_turn` adds no `phase` message and returns `{"id": None}` (REQ-CHA-041); `SkillRunObserver` notes an unchanged phase once; `model_history` has no last-status rule; `workflow_voice.speaker_for(..., end_messages=True)` gives the skill no voice (REQ-CHA-067); `web_app.py` passes `chat_service.has_end_messages()`. Acceptance `test_chat_skill_turns.py` 23 of 23 green. Unit tests adapted: `test_skill_history.py`, `test_chat_verify_fixes.py`.
- `ae1c4d93` new unit tests (`RunSpeaksOnce`: `has_end_messages`, a run spoken once, a phase noted once) and the log entry.
- This commit: the proposal `proposal-browser-tests-own-config.md` and this hand-over.
The owner saw the behaviour in the app and judged it much better.

## State of the full unit suite (one run, 2410 tests, 572 s, before the unit adaptions)
- Chat modules: green after the adaptions (`test_skill_turn`, `test_skill_history`, `test_chat_verify_fixes` 46, acceptance 23).
- 12 order-dependent failures (`test_control_entries`, `test_converted_tools`, `test_core_converted`, `test_harness_converted`): found by another session, caused by `test_character_integration` importing the package `MIA` before them (two module objects of `common_operations`); G-V2.CONVERT's test setup, not new. That session is writing a test-first fix (clear `MIA*` from `sys.modules`); its commit is not in this checkout yet.
- Local causes in the main checkout, not code: `accounts_enabled: true` in `setup_cfg.json` (`test_character_requests`, `test_page_requests`; confirmed green with it off), `templates/static/answer.html` and `templates/node_modules/` (moved to the scratchpad of that session, not deleted; restore by moving back), checkout named `MIA` (`test_make_voice_lines`).
- Also red on `440e599b`, not looked at: `test_task_files_browser` (2), `test_checkout_untouched` (1).
- A full suite run was not repeated after the adaptions and after the local causes were removed.

## For the owner
1. Push `master` (three commits of A-156 and this one).
2. Decide `proposal-browser-tests-own-config.md` (option 1 recommended).
3. The R: review-log line with a D-number for A-156 from the parent's range is still to be written by the owner (A-156 text, last section).
4. Open from A-156: where the status card shows phases (assumed unchanged); is a `/review` question spoken (assumed yes).

## For the next session
- Dead code: `SkillDigestStep.status` is no longer called; remove it with the next change of the step (version stays 7, prompt unchanged).
- No test for the lambda in `web_app.py` that connects the voice rule to the service (one line, the module needs the full app).
- Re-run the full suite once the other session's fix is merged and `accounts_enabled` is off; expect `test_task_files_browser`, `test_checkout_untouched`, `test_make_voice_lines` red for the reasons above.
- The Skill run view reads the phases from the recorder; the change to `skill_turn` should not touch it, but only the unit tests ran, not the browser tests of the view (`TC-CLV-*`).

## Number collision
`69d8a76a` ("A-156 TC-WFM-137 report case") and `tests/acceptance/test_skill_run_report.py` use A-156 for the G-V3.REPORT amendment. That session renumbered it to **A-157** on `origin/goal/v3.report` (`52ff24e1`, with a docstring-rename patch for the protected test); the renumbering is not on `master` yet. In this goal A-156 is always the FB-09 amendment (a skill run speaks once). The same branch holds `371ec72f`, the fix of the 12 order-dependent converted-test failures (F-3, option 1).

## Traps
- Never `git add -A`; name the paths. The untracked `specs/mia/goals/G-V2.CONVERT/handover-2026-11-16-convert-complete.md`, `templates/UI/` and `eval/baselines/verdicts_*` are not this session's.
- The stage container `mia-test-chat-on-stub` is shared by all checkouts and sessions: a stage running in another session makes the browser tests skip.
- Never commit protected material outside an approved amendment.
