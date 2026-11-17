# Hand-over G-V3.CHAT (2026-11-17, third): A-158 built and verified, ready for the owner's gates and the Commit phase

Read `CLAUDE.md`, then this file, then `verification-report-a158.md` and `amendment-a158/` (README is the amendment `specs/mia/amendments/A-158-draft-chat-shows-the-run-like-a-chatbot.md`, last section). Earlier hand-overs: `handover-2026-11-17-a156-code.md`, `handover-2026-11-17-a158-plan-done.md` (suite state and traps still hold).

## State
- A-158 done in code and tests: T-07 (chat service: event `chat_run_status`, turn kinds `start`, `answered`), T-08 (page: `runLineState`, `withRunLine`, `runLineLabel`, i18n en/de, CSS, stub server with a scripted run: say `run`), T-09 (the run feeds the line: `working`, phases, `waiting for your answer`, phase again, clearing before the end message).
- Verify (fresh reviewer, 2026-11-17): **pass with findings**, 0 blocker/high. F-01, F-02, F-03, F-05 fixed test-first (`1fd427e4`); F-06 and F-03 written into the requirements (`74b46dad`: REQ-CHA-072, REQ-CHA-069 clarified, REQ-CLV-055, TC-CHA-076); F-04 (line lost on reload) recorded as accepted "not now" in the amendment; F-08 is a `trace_check` parsing quirk.
- Last full re-run of the A-158 checks (after `599d6590`): chat unit tests, acceptance 26/26, integration TC-CHA-068, browser test 2/2, JS 176 pass / 4 fail (known), SysML checks clean. Not run: the full suite of the repo (see the order-dependent failures of the first hand-over).
- `master` is 22 commits ahead of `origin/master`; nothing of this session is pushed. `goal/v3.chat` (local `1e0dd0c7`) is behind `master` by the A-156/A-158 work: decide whether the merge goes from `master` or from the goal branch.

## For the owner (blocking the Commit phase)
1. **Contract text**: apply `amendment-a158/IF-101-change.md` to `contracts/IF-101-chat-api.md` and IF-201 (event `chat_run_status`; IF-201 v4 turn kinds `start`, `answered`), the IF-201 mock `tests/helpers/mocks/if_201_chat_turn.py` and the contract suite TC-IF-201-13 to -15 (protected). `TC-CLV-021` stays red until the contract names the event.
2. **Rate plausibility and approve** the 8 Draft requirements: REQ-CHA-068, 069, 070, 071, 072, REQ-CLV-053, 054, 055 (plan gate review in small batches; `plausibility.yaml` entries are a person's). Evidence: `amendment-a158/prototype-report.md`.
3. **Review log**: number and append the two lines of `amendment-a158/review-log-draft.md` (A-156, A-158) and add: F-04 accepted as "not now" (reload loses the line), the approver of the protected patches (F-07: `7a750eea`, `907ef3fa`, `aa2150b5`, `be60bf2a`, `97122a8a`, `599d6590` were applied and committed by the owner).
4. Look at a real `/lookup` and `/review` run in the app (only the scripted stub was run).
5. Push: `! git push origin master` (and `goal/v3.chat` if used). Merge `origin/goal/v3.report` (A-156/A-157 renumbering, F-3 fix of the 12 order-dependent test failures) before a full suite run; switch `accounts_enabled` off locally for that run.

## Commit phase (after 1 to 3), load `commit-phase`
- Update the goal branch with its target, re-run the automated checks (full unit suite, `node --test`, trace_check, `check_sysml_model.py`, `check_sysml.sh`), clean the history to one commit per task with requirement IDs (T-07 to T-09 are in `bd459bc4`, `fd4ad242`, `bdeffabf`, `7fb8156d`, `e03a8fa6`, `e3e30555`, `1fd427e4` plus the plan commits), draft the merge request (extend `merge-request.md` with A-156 and A-158), requirement status changes Draft -> Verified for the 8 new ones only after the owner's approval.
- Expected red in the full suite, not ours: `test_task_files_browser` (2), `test_checkout_untouched` (1), `test_make_voice_lines` (checkout named MIA), TC-CLV-049 (2), TC-CLV-052 (node), the 12 order-dependent converted tests until `371ec72f` is merged.

## Traps
- Protected: `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `tests/integration/`, `test-requirements.md`, `contracts/`: patch plus apply script only; never `git add -A`; name the paths. `model_sync.py --write` leaves 22 untracked `specification.sysml` files: delete them.
- The reviewer's report (`verification-report-a158.md`) is the reviewer's own; do not edit it, answer in `implementation-log.md` (done: "A-158 Verify findings fixed").
- Untracked and not ours: `eval/baselines/verdicts_*`, `specs/mia/goals/G-V2.CONVERT/handover-2026-11-16-convert-complete.md`, `templates/UI/`.
