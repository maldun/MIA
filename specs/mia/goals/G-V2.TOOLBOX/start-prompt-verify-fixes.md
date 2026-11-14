# Start prompt for the re-Verify session of G-V2.TOOLBOX (the fix commits)

Copy everything below the line into a fresh Claude Code session started in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox` (branch `goal/v2.toolbox`). A session that never saw the fix chat; one session at a time in this worktree.

---

You re-verify G-V2.TOOLBOX (phase 4, Verify, second round) of MIA, supervised, as an independent reviewer. Load `dev-workflow` and `verify-phase` (`agent-app` does not apply). Read `CLAUDE.md`, then `specs/mia/goals/G-V2.TOOLBOX/verification-report.md` (first round, 2026-11-12, findings F1 to F8 and the decisions D-229), then the diff of the fix commits only.

Scope: exactly three commits on `goal/v2.toolbox`, `git show 02a4906 33ab9a2 931c53f`:
- `02a4906` plan: text and criterion of REQ-WFM-091 and REQ-WFM-092, TC-WFM-091 in `test-spec.md` (N-2.3-workflow-management).
- `33ab9a2` fix: F1 to F5 in `toolbox.py`, unit tests in `tests/test_toolbox.py` (class `VerifyFindings`, the mock and the real library; the twin test `BaselineChecks` changed with F2).
- `931c53f` fix: F8 (unknown id is `ToolboxError("not_found")`), and the notes for F6 and the rest of F8 in `plan.md`.
Not in scope and decided: F7 (`decomposition` step, known red, parent session), F6 and the rest of F8 (notes only).

What to check (the first round's checks are not repeated unless a fix touches them):
1. Protected material unchanged: `git diff 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks` must be empty. Any change is a finding.
2. Each finding F1 to F5 and F8: does the failing test reproduce the first round's repro (compare with the report's text), and does it fail on the code before the fix (check out `84eddb6:toolbox.py` into a temp copy, never into the worktree) and pass after? A test that passes without the fix is a finding.
3. F1 and F2 in `toolbox.py` (`import_transform`, `set_lifecycle`): look for a path where an allowance still reaches new code, for a lifecycle change that keeps it (retire without `allow_baseline` after an allowance, a second retire), for the order event, allowance clear, save (a failure between the steps may take a permission away but must never keep one), and for `get_meta` on a transform without meta record.
4. F4: the reason text for an untrust by the owner, by an account, and for a shipped entry; `look_up` of a trusted entry shows no reason. F3: other numbers that jsonschema counts as integers (`1e0`, `True` is refused already). F5: the event is recorded and the save then fails: is an event without a replace acceptable (the fix chose it on purpose)?
5. The requirement text of REQ-WFM-091/092 against code and tests (both directions), and that the acceptance tests TC-WFM-091, 092, 095 still read the same behaviour as before.
6. Re-run: the test files of the scope with `/home/maldun/prog/Python/venvs/mia312/bin/python` as scripts, then the stage ladder (`run_stages.py --upto 2 --keep-going`, venv `bin` first in PATH; the full unit suite takes about 8 minutes, in the background). The first round's Stage log is empty; enter the result of unit, contract-mocks, acceptance, contract-real and integration, and say what skipped and why. Stages 4 and 5 of the report's list: say what `stages.yaml` defines and what could run locally.

Rules:
- You do not change code, tests, requirements, contracts or the plan. Findings come with a failing test as a proposal in the report.
- Never run `*.holdout` material; no model, no network, no new dependency.
- Update `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox/specs/mia/goals/G-V2.TOOLBOX/verification-report.md` with a second-round section and the new verdict (Verified, Verified with accepted deviations, Verified with open findings). Commit only the report: `git add <path>` and `git commit -m "verify(toolbox): ..." -- <path>` with the Co-Authored-By line; never `git add -A`; do not push.
- Findings go to the owner (reviewer name `maldun`) one per question (AskUserQuestion, recommended option first). Tell the owner when the report is ready for the gate.

Start by listing what you will check and in which order, then begin with step 1.
