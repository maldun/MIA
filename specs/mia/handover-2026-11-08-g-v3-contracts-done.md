# Hand-over for the next G-V3 session (written 2026-11-08, evening): cases, plausibility, contract change and goal records done; red tests and plan.md open

For the session that continues **G-V3** (subgoals G-V3.PANEL and G-V3.CHAT) on branch `goal/v3`, worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3`. Start with `CLAUDE.md`, the goal records `specs/mia/goals/G-V3/goal.md`, `goals/G-V3.PANEL/goal.md`, `goals/G-V3.CHAT/goal.md`, then the previous hand-over `handover-2026-11-08-g-v3-plan-review.md` (for the way the owner works, the ID ranges and the pitfalls, all still valid), then this file. Load the skills `dev-workflow`, `agent-app`, `plan-phase`, `agent-app-plan` (and `agent-app-implement` when Step 5 is done).

Phase: Plan, supervised, both subgoals. Reviewer name in the review log: **maldun**. Nothing is pushed (the push and the merge are the owner's). Work in the worktree only; **one session at a time**: a second session edited requirements and `architecture.sysml` in this worktree during the last hour and left uncommitted changes (kept by the owner, D-305).

## Done in this session (review-log rows D-304 and D-305)
- **EV-skill_turns:** 24 dev and 24 holdout cases drafted by the agent, labelled by the owner with `specs/mia/explore-skill-rework/forms/skill-turns-labelling.html`, applied (`apply_skill_turns_marks.py`), promoted to `eval/suites/skill_turns` and `skill_turns.holdout` (all 48 carry `req:REQ-CHA-053` and `054` so that n=24 is selected; the 12 injection cases carry `rt:RT-014`, THR-012 names RT-014). The suites have target `pending`. The holdout was not read by the agent (one dry run of the retag script opened its file and printed only counts).
- **Baseline (D-304):** "no digest at all" (today there is no summary); an empty file `eval/baselines/skill_turns__nodigest__baseline.jsonl` makes `agent_check` A13 pass; no holdout run exists.
- **Plausibility:** PANEL 33 items and CHAT 26 items recorded in `plausibility.yaml` (hand-merge in the tool's item format, **`tools/apply_plausibility.py` not run**: it rewrites the whole record, drops 39 hand-added ratings and re-stamps 437 dates; do not run it). REQ-CHA-049, 053, 054 are questionable with accepted risk (follow-up VAL-013), REQ-CLV-041 questionable with probe. `req_plausibility`: no G-V3 error (40 errors left are other goals').
- **HLS and glossary (A-131):** FR-46, FR-34, FR-35, AC-30, AC-39 changed, glossary "Skill run view", FR docs in `architecture.sysml` (check_sysml_model and check_sysml clean). **TD-01 stays on REQ-CLV-023** with a note (the owner did not want approved text changed); it moves to REQ-CLV-038 (which needs `Relaxed: TD-01` and a `Target:` line then) when REQ-CLV-023 is retired in Implement of PANEL.
- **Contract change (A-140, A-141, A-142), installed by the owner:** IF-101 v16, IF-201 v3, IF-302 v8, IF-102 v4 with mocks and suites; payload and `install.py` in `specs/mia/goals/G-V3/contract-change/`. Mock variants of all four suites pass; the real variants fail in the new or changed tests only (red until the code follows): IF-302 TC-IF-302-01 and -08; IF-201 TC-IF-201-09 to 12; IF-101 TC-IF-101-31, -30, -36 (changed or new, real) and -34, -37, -38 (errors); -35 and -39 skip on the real subject. New: TC-IF-101-34 to 39 (A-140 said "28 onward", taken), TC-IF-201-09 to 12, TC-IF-302-08, TC-IF-102-12; changed: TC-IF-101-24, -30, -31, TC-IF-302-01. The IF-102 real variants need the database and graph rules and error in a sandbox; run them in the real checkout.
- **Goal records:** G-V3, G-V3.PANEL, G-V3.CHAT read one by one, approved, Status `Agreed` (`Approved` is not a goal status). Scope rows were added so that `goal_check` GL3 is clean (parent G-V3 lists IF-302, IF-102, REQ-RTB-007, REQ-BE-078, REQ-CHA-040 to 063; PANEL has an N-3.3 part; CHAT lists the 24 REQ-CHA ids). G-V3 and CHAT were re-marked after that.
- **Left-over edits of the other session, approved:** REQ-BE-078 drops the method Evaluation (agent_check A1; re-approved); SkillDigestStep gets `secondBudget = 20.0` (was 0.0, A9; not measured, tune in Implement).

## Open (in this order)
1. **Step 4, red acceptance tests** for both subgoals (the contract suites are done; the rest are the checks TC-CLV-030 to 047, TC-WFM-130 to 138, TC-RTB-007, TC-CHA-040 to 063 with their scenarios and test requirements). Local-coder may type the files; in TR-PANEL-001 name the font and the Chromium version of the harness (agreed). Details of `Files:`/`skill_run` are in A-140, the link form is `[Open in the Skill run view](#run=<id>)`.
2. **Step 5, `plan.md`** for both subgoals (tasks; the target kind and scorer of EV-skill_turns are a task, see below).
3. **Mock server and page:** `ui/tools/chat_mock_server.py` serves the IF-101 mock; its text changed (no `Files:` suffix, link at the end, new task_status fields). Browser tests of the old page (`tests/test_task_files_browser.py`, `tests/js`) may break; they are rewritten for the view anyway (A-131 list). Check before Implement.
4. **Real code follows the contracts** in Implement: `chat_service.py` still words a failed task as `/<id> could not finish: ...` and appends `Files:`; `record_tables.py` has no `skill_runs`; no `skill_turn`; the real adapters must accept the mock options (`phases` for IF-201).
5. **Not committed yet?** check `git status`; this session's last commit holds everything described here.

## Stop-and-report items still open
- **EV-skill_turns has no harness target** (`pending`) and no scorer (hard checks of TR-CHAT-004, labels): a new part, belongs in the plan as a task, needs the owner's approval before it is built.
- **Rule `both` of REQ-CHA-053 and 054** includes a sign test against a baseline that is empty: `eval_decide.py` will answer NOT DECIDED or FAIL on it. Test it in Verify with the empty file; the owner's options were to change the rule to `threshold` (sends the criteria back into review) or accept. Not decided.
- REQ-CHA-049 is weak (miss rate 22 % at n 6, accepted by the owner).
- `trace_check` has ~545 old errors, none of G-V3; `req_review` shows TC-WFM-047 and TR-MODEL-003 as changed since review (not G-V3, another goal's).

## Checks
```
python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia          # only GL1 (D-271)
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests
python3 ~/.claude/skills/plan-phase/scripts/req_review.py --spec-dir specs/mia --tests-dir tests status
python3 ~/.claude/skills/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval   # errors left: REQ-WFM-059 (A2), THR-011 (A8), not G-V3
python3 -I tools/gen_node_requirements_model.py . && python3 -I tools/check_sysml_model.py . && bash tools/check_sysml.sh
for t in if_302_record_tables if_201_chat_turn if_101_chat_api if_102_storage; do /home/maldun/prog/Python/venvs/mia312/bin/python -m unittest -q tests.acceptance.contract.test_$t -k _mock; done
```
Run the suites from the repository root. The `_real` variants of the new tests are red on purpose.

## Pitfalls met in this session
- A permission rule blocked edits of `tests/acceptance` and `tests/helpers`; the way that worked: build and run the change in a sandbox, store it as a payload with an install script, the owner runs the script.
- Typed into a normal terminal, a leading `!` negates the exit status (`! cd x && cmd` never runs `cmd`). The `!` prefix is for the Claude Code prompt only.
- `tools/promote_labelled.py` writes `eval/suites` relative to the current directory; run it from the worktree root.
- Do not mark goals `Approved` (invalid status): `Agreed`.

## Not touched
The voice path, TD-11, A-130, FR-43, the graph editor, everything of G-V2, master, `eval/suites` (except the promoted suite and its retag by the owner), `plausibility.yaml` ratings of other goals.
