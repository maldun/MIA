# Start prompt for the fifth Verify read of G-V2.TOOLBOX (commit 9d11152)

Copy everything below the line into a fresh Claude Code session started in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox` (branch `goal/v2.toolbox`). A session that never saw the finding or the fix chats; one session at a time in this worktree.

---

You re-verify G-V2.TOOLBOX (phase 4, Verify, fifth round) of MIA, supervised, as an independent reviewer. Load `dev-workflow` and `verify-phase` (`agent-app` does not apply). Read `CLAUDE.md`, then the section "Fourth round (bf253ce)" and finding N5 in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox/specs/mia/goals/G-V2.TOOLBOX/verification-report.md`, then `git show 9d11152`.

Scope: exactly one commit, `9d11152` (`tests/test_toolbox.py`, `implementation-log.md`; no change of `toolbox.py` is expected). It claims to fix N5: the test for a failing `set_meta` after a first save now pins the message ("stored without its meta record", "its reason is empty") and checks with the real `set_meta` restored that `look_up(id)["reason"]` is empty. Owner decision (maldun): pin the text and the reason clause. Not in scope and decided: F6, F7, F8 rest, N1 to N4 (verified in rounds 3 and 4).

What to check:
1. Protected material unchanged: `git diff 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks` is empty; `git show --stat 9d11152` touches only the two files named above, and `toolbox.py` is identical to `bf253ce` (`git diff bf253ce..HEAD -- toolbox.py` is empty). Any other change is a finding.
2. Red before green: the new asserts must fail on a code that lacks them. Make a copy of `HEAD` with `git archive` in the scratchpad (never in the worktree) and apply, one at a time, to `toolbox.py`: (a) drop " (its reason is empty)" from the `set_meta` message; (b) shorten "was stored without its meta record" to "was stored"; (c) the old text "was not stored" in the `set_meta` branch; (d) a bare `raise` there; (e) the code `store_failed` changed in either branch; (f) the "stored without its meta record" text in the `save` branch. Each must make a test fail, on mock and real (a survivor is a finding). Also run the test of `HEAD` against `ca3d8fa:toolbox.py`: the `set_meta` test still fails.
3. Read the changed test: `del self.library.set_meta` removes the instance override and restores the class method on mock and real; the `look_up` check then reads the state the failed import left (version 1, untrusted, reason ""). Does the test still mirror the scenario of N4 and N5 (Given / When / Then in its docstring), and does it leave no state that could affect another test (a fresh library per test)? A docstring that no longer matches what the code checks is a finding.
4. Behaviour only in the code or the test: anything in `9d11152` that no finding states (another assertion, a changed helper, a changed test name)? That is a gap to report, not to fix.
5. Re-run with `/home/maldun/prog/Python/venvs/mia312/bin/python`: `tests/test_toolbox.py` (45 tests expected), `tests/acceptance/test_toolbox.py` (17), `tests/test_workflow_library.py` (13), `tests/acceptance/contract/test_if_203_v1_transforms.py` (10). The full ladder ran clean on `ca3d8fa` (only `decomposition` fails, F7, known) and no code file changed since: do not repeat it unless `git diff ca3d8fa..HEAD --stat` shows a file outside `toolbox.py`, `tests/test_toolbox.py`, the goal folder.

Rules:
- You do not change code, tests, requirements, contracts or the plan. Findings come with a failing test as a proposal in the report.
- Never run `*.holdout` material; no model, no network, no new dependency.
- Add a section "Fifth round (9d11152)" to the report with the checks above and set the verdict at the top: Verified with accepted deviations (the deviations are F6, F7, F8 rest, and what the owner accepts), or Verified with open findings. The Stage log keeps the clean ladder of `ca3d8fa`; add one line that `9d11152` touches no file outside the two. Commit only the report: `git add <path>` and `git commit -m "verify(toolbox): ..." -- <path>` with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; never `git add -A`; do not push.
- Findings go to the owner (reviewer name `maldun`) one per question (AskUserQuestion, recommended option first). Tell the owner when the report is ready for the gate.

Start by listing what you will check and in which order, then begin with step 1.
