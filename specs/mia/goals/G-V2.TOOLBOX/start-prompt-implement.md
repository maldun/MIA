# Start prompt for the Implement session of G-V2.TOOLBOX

Copy everything below the line into a fresh Claude Code session started in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox` (branch `goal/v2.toolbox`). One session at a time in this worktree.

---

You implement G-V2.TOOLBOX (phase 3, Implement) of MIA, supervised. Load the skills `dev-workflow`, `implement-phase` (`agent-app` only to know it does not apply: no model step, prompt or eval). Read in this order: `CLAUDE.md`, `specs/mia/goals/G-V2.TOOLBOX/handover-step4.md` (state, choices of the tests, open points), `specs/mia/goals/G-V2.TOOLBOX/plan.md` (tasks T-01 to T-06), `specs/mia/amendments/A-110-note.md` and `A-111-note.md`.

Work test first, one task at a time, in the order of `plan.md`: T-01, then T-02 to T-05 (independent of each other), then T-06 (waits for A-110, installed, and A-111, which the owner must approve before you touch `contracts/IF-203`; if A-111 is not approved, do T-01 to T-05 and stop before T-06).

Rules:
- Python for every test: `/home/maldun/prog/Python/venvs/mia312/bin/python`. Tests run as scripts: `python tests/acceptance/test_toolbox.py` (17 tests, red today), `python tests/acceptance/contract/test_if_203_v1_transforms.py`, `python tests/acceptance/contract/test_if_302_record_tables.py`.
- Turn the red tests green by replacing the stub `toolbox.py` (repo root) with the real module; keep the interface in its docstring. Never edit `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `eval/`, `benchmarks/`. A protected test that seems wrong: stop and report (amendment).
- The code text of a transform is never compiled or run on import (REQ-WFM-053); only `run` executes it (SC-09 accepted: trusted code runs in the MIA process).
- `workflow_library.py` is shared with MODEL and CONVERT: add the kind `transforms`, `set_trust`, `set_lifecycle`, `get_trust`, `get_lifecycle`, `get_meta`, `set_meta` in an own block, touch nothing else; the four workflow states stay. The table `transform_meta` goes into `record_tables.py` (TC-IF-302-09 real variant) and the table list of the storage layer.
- No new dependency (`jsonschema` is pinned already). Prefer simple, explicit code matching the surrounding module; comments say why.
- Every finding gets a failing test first (a protected one needs the owner). Same test failing after 3 serious attempts, a needed new part or interface, or files outside the task: stop and report.
- Each task: tests green, the stage 1 and 2 steps of `stages.yaml`, `python3 -I tools/check_sysml_model.py .`, then one commit: `git add <paths>` and `git commit -m "feat(toolbox): ... (REQ-WFM-...)" -- <paths>` with the Co-Authored-By line; never `git add -A`. Log findings and deviations in `specs/mia/goals/G-V2.TOOLBOX/implementation-log.md` (create it). Do not push; the owner pushes.
- Decisions go to the owner as a questionnaire (AskUserQuestion, recommended option first). Do not edit approved requirement or check text.

Start with T-01: show me the plan for it (files, tests, what you will not touch) before you write code.
