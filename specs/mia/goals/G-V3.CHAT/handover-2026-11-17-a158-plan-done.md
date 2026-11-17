# Hand-over G-V3.CHAT (2026-11-17, second of the day): A-158 planned, ready for Implement at T-07

Read `CLAUDE.md`, then this file, then `specs/mia/amendments/A-158-draft-chat-shows-the-run-like-a-chatbot.md`, `specs/mia/goals/G-V3.CHAT/amendment-a158/IF-101-change.md` and `plan.md` (T-07 to T-09). The earlier hand-over `handover-2026-11-17-a156-code.md` still holds the suite state and traps.

## What A-158 is
The owner (2026-11-17, questionnaires): the status card is superseded by the Skill run view; the chat behaves like a chatbot: it tells what to answer, what currently happens, and the summary; the current state is shown last. Decided: one **live status line**, always last, replaced in place; **transient** (not in the log, history or speech); a run without phases shows `working`; fixed wording from the manifest's phase names (no model call); `/review` questions are spoken; interface change approved.

## Done this session (commits, oldest first)
- `bd459bc4` dead code: `SkillDigestStep.status` removed (prompt, version 7 unchanged).
- `fd4ad242` the stage `chat-on-stub` forces `accounts_enabled` off (`ui/tools/chat_stub_server.py`); proposal option 1 of `proposal-browser-tests-own-config.md`.
- `f2f98af0`, `fb6afc70` A-158 draft and the owner's decisions.
- `9e735f2b` plan: REQ-CHA-068 to 071, REQ-CLV-053, 054 (all Draft), REQ-CHA-041 and 055 reworded, TC-CHA-073 to 075, TC-CLV-053 with scenarios, `architecture.sysml` entries (model checks pass).
- `7a750eea`, `907ef3fa` patches for the protected files and `amendment-a158/apply.sh`; IF-201 v4 notes.
- `cd4c6e1a` `tests/js/run-line.test.mjs` (red).
- `8db7aa54` tasks T-07 to T-09, draft review-log lines.
- The owner ran `apply.sh`: `test-requirements.md` and `tests/acceptance/test_chat_skill_turns.py` (class `LiveLine`) changed in the working tree. **Check `git status`: if they are still uncommitted, the owner commits them** (`git add specs/mia/test-requirements.md tests/acceptance/test_chat_skill_turns.py`).

## Red state to start from
- `python tests/acceptance/test_chat_skill_turns.py`: 3 `LiveLine` tests red (3 failures, 2 errors); the other 23 green.
- `node --test tests/js/run-line.test.mjs`: red (`runLineState`, `withRunLine` not exported).

## Interface to build (fixed by the red tests)
- Event `chat_run_status` {"run": id, "text": str | None}; `None` clears. Not a chat message: no id, not in the log, not in `model_history()`, not spoken.
- `skill_turn` kinds `start` and `answered` (new, IF-201 v4): `start` gives `working` only for a run without declared phases; `answered` repeats the current phase line (or `working`). `phase` of a declared, changed phase gives the line and still returns `{"id": None}`. `question` sends `waiting for your answer` after the question message. `done`, `failed`, `stopped` send the clearing before the end message.
- Page: `runLineState(line, event)` and `withRunLine(messages, line)` in `templates/static/chat/chat-model.js` (`kind: 'run_line'`, `href: '#run=<run>'`; the clearing of another run leaves the line).

## Tasks
T-07 (service, no model needed) then T-08 (page and stub server) then T-09 (wiring from the run; needs the extended integration check of AC-39, written outside the implementing session first). Start with T-07 in a fresh context.

## Open for the owner (not blocking T-07, T-08)
1. Apply the contract text of `amendment-a158/IF-101-change.md` to `contracts/IF-101-chat-api.md` and IF-201, and the mock plus the contract suite TC-IF-201-13 to -15 (protected). Needed before T-09 and before Verify.
2. Rate plausibility of the six new requirements at the plan gate review; approve them (they are `Draft`).
3. Number and append the two lines of `amendment-a158/review-log-draft.md` to `specs/mia/review-log.md`.
4. Everything of the earlier hand-over: push `master` and `goal/v3.chat`, merge `origin/goal/v3.report` (A-156/A-157 renumbering and the F-3 fix of the 12 order-dependent tests), full suite re-run afterwards.

## Traps
- `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `test-requirements.md`, `contracts/` are protected: never edit, never copy files into them; a change goes as a patch with an apply script for the owner.
- Never `git add -A`; name the paths. Untracked and not ours: `eval/baselines/verdicts_*`, `specs/mia/goals/G-V2.CONVERT/handover-2026-11-16-convert-complete.md`, `templates/UI/`.
- `model_sync.py --write` creates 22 untracked `specification.sysml` files; the repo does not track them, delete them after a run. `architecture.sysml` is hand-written (requirement defs, `satisfy`, `allocate`, `dependency`), check with `python3 -I tools/check_sysml_model.py .` and `bash tools/check_sysml.sh specs/mia/architecture.sysml`.
- `trace_check.py` reports many old errors (unknown requirement markers, etc.); only look at the lines for CHA-068 to 071, CLV-053, 054 and TC-CHA-073 to 075, TC-CLV-053.
- The A-156/A-157 number collision: here A-156 is always the "speaks once" amendment.
