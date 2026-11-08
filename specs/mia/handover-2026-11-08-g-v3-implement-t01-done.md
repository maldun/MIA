# Hand-over for the next G-V3 session (written 2026-11-08, night): Plan gate passed, Implement started, PANEL T-01 done

For the session that continues **G-V3** (subgoals G-V3.PANEL and G-V3.CHAT) in the phase **Implement**, supervised, on branch `goal/v3` in the worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3` (the plans name `goal/v3.panel` and `goal/v3.chat`; those branches were not created, the owner works on `goal/v3`). Start with `CLAUDE.md`, then `specs/mia/goals/G-V3.PANEL/plan.md` and `specs/mia/goals/G-V3.PANEL/implementation-log.md` (or the CHAT pair), then this file. Load the skills `dev-workflow`, `agent-app`, `implement-phase`, `agent-app-implement` (CHAT tasks with a model step), `decomposition` only if a node cycle asks for it. The earlier hand-over `handover-2026-11-08-g-v3-red-tests-and-plans.md` has the history of the Plan phase and the commit list; its "Open" list is superseded by this file. Nothing is pushed (the push and the merge are the owner's, and `git push` is denied).

## State
- **Plan gate passed.** Every requirement, check, test requirement and goal record of G-V3 is reviewed and approved in `specs/mia/review-log.md` (rows D-300 to D-309 and the marks). Both plans are approved (D-307 PANEL, D-308 CHAT). The tags **`plan-baseline-it2-panel`** and **`plan-baseline-it2-chat`** are on commit `756b142`.
- **Implement started:** PANEL **T-01 done** (commits `39bf66b` code and unit test, `caedc6f` requirement change, implementation log, Phases table). Everything else is open.
- **Red tests are in place and red on purpose:** TC-WFM-130..138 (`test_skill_runs.py`, `test_skill_run_observer.py`), TC-CHA-040..068 (`test_chat_skill_turns.py`, `test_digest_score.py`, `tests/integration/G-V3/test_run_end_to_end.py`), the JS model (`tests/js/skill-run-model.test.mjs`), the browser checks (`test_skill_run_view_browser.py`, `test_skill_run_view_restart.py`), the real variants of the contract suites for IF-101 v17, IF-201 v3. Stubs that raise NotImplementedError: `skill_runs.py`, `skill_run_observer.py`, `skill_digest.py`, `digest_score.py`, `Harness._digest`, `ChatService.skill_turn` / `model_history` and the `digest`, `declared_phases`, `recorder` arguments, `templates/static/chat/skill-run-model.js` (throws). TC-RTB-007 and the `skill_runs` parts of TC-IF-302-01/-08 and TC-IF-102-12 are green since T-01.
- **Checks (last run):** `goal_check` GL1 only (D-271); `trace_check` 545 old errors, none of G-V3; `agent_check` 6 errors (REQ-WFM-059 A2, THR-011 A8), none of G-V3; `req_plausibility` 40 errors, none of G-V3; `req_review` shows TC-WFM-047 and TR-MODEL-003 (another goal's) as changed; full unit suite (`unittest discover -s tests`, about 8 minutes, the red acceptance tests are not in it): 2071 tests, one error, `test_tailscale` (`remote.sh up` times out after 30 s, not G-V3, not checked on master).

## What you may and may not touch (the guards are real)
`.claude/settings.json` denies edits of `eval/suites`, `eval/baselines`, `tests/acceptance`, `tests/helpers`, `tests/smoke`, `benchmarks`, `contracts`, `tests/integration`, `eval/labels`, `specs/mia/test-requirements.md`, `stages.yaml`, `plausibility.yaml`, `deferred.md`, `decomposition.yaml`, reading the holdout, `git push`, `ollama pull` and `ollama rm`. The permission classifier also blocks bash commands that edit or copy those paths. A change there is a plan amendment: describe it, get the owner's approval, build it in a sandbox in the scratchpad, store it as a payload with an `install.py` (examples: `specs/mia/goals/G-V3/contract-change*/`, `.../red-tests/`) and let the owner run `python3 -I <path>/install.py --do`. Never run a script that opens `eval/suites/*.holdout/`. Editable: the code of the tasks, `tests/test_*.py` unit tests (a change of an old one needs the owner's ruling when a requirement is involved, as with REQ-RTB-001), the goal records' Phases tables, `implementation-log.md`, `review-log.md` (append), the handover files.

## The next tasks (see the plans for the full text)
- **PANEL T-02, run recorder** (depends on T-01, now unblocked): replace the stub `skill_runs.py`; green when TC-WFM-130..135, 137, 138 (`tests/acceptance/test_skill_runs.py`). API fixed by `goals/G-V3.PANEL/run-recorder-interface.md`: `SkillRunRecorder(storage, emit, clock, now)` with start, phase, report, answer, file, end, record, shown; the constructor subscribes to the table `history`, a notice with `version: None` deletes the run records of the account named in `author`; `elements` is stored (A-143). May add an optional `elements` argument to `TaskMonitor.update` (owner decision D-309, `task_monitor.py`); `tests/test_task_monitor.py` must stay green. Fakes: `tests/helpers/skill_runs_fakes.py`.
- **PANEL T-06, JS model** (independent, can run any time): replace the stub `templates/static/chat/skill-run-model.js`; green when `node --test tests/js/skill-run-model.test.mjs` (7 tests). Eight exports, see `skill-run-view-interface-note.md`.
- **PANEL T-04 after T-02** (the observer `SkillRunObserver`, the review's manifest `phases` field and aligned phase strings, exact phase-name match; green when TC-WFM-136), **T-05** (IF-101 v16/v17 on the real backend; the real variants of TC-IF-101-30, -31, -34..39), **T-07 to T-10** (the page; browser scenarios), see the plan.
- **CHAT T-01** (the digest step, fake model, no Ollama needed) first, then T-02, T-03 (the one call in `communicator.py` is allowed, nothing else there), T-04 (harness target and scorer; the owner sets the target line in the two `suite.json` and creates `eval/labels/` afterwards), T-05 (dev runs and prompt tuning, needs Ollama with `gemma4:12b-it-qat`; never the holdout), T-06 (integration, after both subgoals are merged).
- **Loop per task** (`implement-phase`): fresh context, only the task's inputs, red-green in small steps, run the task's tests after every step, tidy, **one commit per task** with `Task:` and `Requirements:` lines and the attribution line, a row in the `implementation-log.md`, finding to a test, stop and escalate on the listed conditions (the first stop of this phase was T-01: a requirement and a test contradicted the plan; the owner ruled).

## Open for the owner (not blocking T-02 and T-06)
1. VAL-012 and VAL-013 (validation criteria for real use) are not rows in the review log; settle them at the gate or in Validate.
2. `goal_check` GL11 on G-V3.CHAT (29 requirements in scope, no subgoals): known, the Split check says keep together.
3. The merge to master with the G-V2 session's work: collisions to expect are listed in `handover-2026-11-08-g-v3-plan-review.md` ("Collisions to expect"); `plausibility.yaml` and its proposal/decision files were merged by hand and will probably conflict textually with the main checkout's uncommitted changes.
4. REQ-RTB-001 changed after its verification (Approved now): Verify re-verifies it with TC-RTB-001.
5. The branches `goal/v3.panel` and `goal/v3.chat` named in the plans do not exist; decide at the merge whether to create them or to change the plans' line-of-work text.

## Environment and commands
```
cd /home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3
/home/maldun/prog/Python/venvs/mia312/bin/python -m unittest -q tests.acceptance.contract.test_if_302_record_tables      # contract suites: mock and real variants
MIA_DB_PYTHON=/home/maldun/prog/Python/venvs/mia312/bin/python bash tools/contract_postgres.sh                           # IF-102 on a throwaway postgres:16 (image must be local)
/home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/test_skill_run_view_browser.py                          # 12 browser tests, 3 minutes, needs podman, localhost/mia and localhost/mia-browser
python3 -I specs/mia/goals/G-V3/red-tests/install.py                                                                      # lists nothing as new or changed
python3 ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests
python3 ~/.claude/skills/plan-phase/scripts/req_review.py --spec-dir specs/mia --tests-dir tests status
python3 ~/.claude/skills/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval
python3 -I tools/gen_node_requirements_model.py . && python3 -I tools/check_sysml_model.py . && bash tools/check_sysml.sh
node --test "tests/js/*.test.mjs"                                                                                         # the 7 new tests fail until T-06
```
Podman needs `:z` on a bind mount of a host folder (SELinux on Fedora), `:O` for the checkout. The browser and restart tests mount the checkout read-only as an overlay and use `--network container:<name>`; stop containers with `podman rm -f -t 0 <name>` (none should be left: `podman ps -a | grep g-v3`).

## Pitfalls met (keep)
- A bare `!` before a command in a normal terminal negates the exit status; it is for the Claude Code prompt only.
- Running a test from a payload folder leaves `__pycache__` there and `install.py` would copy it: remove it (`find specs/mia/goals/G-V3 -name __pycache__ -prune -exec rm -rf {} +`) before an install.
- A Scenarios section in the root `specs/mia/test-spec.md` switches on the scenario rule for every old root check (150 new trace errors): new checks go into a node's test-spec.
- `tools/apply_plausibility.py` is not run (it would drop 39 hand-added ratings); `req_review.py next` starts with the old goal G-V1: present G-V3 items by id.
- Changing the text of an approved item sends it back into review (fingerprint): say so, ask the owner, mark by id; goal Status values are Proposed, Agreed, In progress, Verified, Validated, Closed, Dropped.
- A stub must not make a test pass (the stub of `skill_digest.py` has no `tools` and `prompt` attribute on purpose); the throwaway reference implementations used to check the red tests lived in the scratchpad and are not in the repository.
- `specs/mia/eval-drafts/skill_turns.jsonl.bak` is an untracked backup of the drafts file; delete or ignore it.

## Not touched
The voice path, TD-11, A-130, FR-43, the graph editor, everything of G-V2, master, the holdout suites, `deferred.md` (TD-01 stays on REQ-CLV-023 until PANEL T-10 retires it).
