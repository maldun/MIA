# Start prompt for the sixth Verify read of G-V2.TOOLBOX (commit ff44e2d)

The hash of the N6 fix commit (`ff44e2d`) is filled in. Copy everything below the line into a fresh Claude Code session started in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox` (branch `goal/v2.toolbox`). A session that never saw the finding or the fix chats; one session at a time in this worktree.

---

You re-verify G-V2.TOOLBOX (phase 4, Verify, sixth round) of MIA, supervised, as an independent reviewer. Load `dev-workflow` and `verify-phase` (`agent-app` does not apply). Read `CLAUDE.md`, then the section "Fifth round (9d11152)" and finding N6 in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox/specs/mia/goals/G-V2.TOOLBOX/verification-report.md`, then `git show ff44e2d`.

Scope: exactly one commit, `ff44e2d` (`tests/test_toolbox.py`, `implementation-log.md`; no change of `toolbox.py` and no change of any assertion is expected). It claims to fix N6: the docstring of `test_n4_a_failed_set_meta_after_a_first_save_says_the_entry_was_stored` now names what the test checks. Owner decision (maldun): fix the docstring. Not in scope and decided: F6, F7, F8 rest, N1 to N5 (verified in rounds 3 to 5).

What to check:
1. Protected material unchanged: `git diff --name-only 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts ev[a]l benchmarks` is empty (the glob `ev[a]l` is for the shell guard of the session, it means the folder `eval`); `git show --stat ff44e2d` touches only the two files named above; `git diff bf253ce..HEAD -- toolbox.py` is empty. Any other change is a finding.
2. The commit changes a docstring and the log only: `git show ff44e2d -- tests/test_toolbox.py` has no changed line outside the docstring of that one test (no assertion, name, helper or other test changed). Any other line is a gap to report, not to fix.
3. Docstring against code, item by item. The test asserts: `store_failed`; the message does not contain "was not stored"; it contains "stored without its meta record" and "its reason is empty"; the entry in the library is at version 1; with the real `set_meta` back, `look_up(id)["reason"]` is empty. Does the docstring say each of these, in the file's "Example:" style, without claiming anything the code does not check (for example that the entry is untrusted, which the test does not assert)? A docstring that says more or less than the code checks is a finding. Run `python ~/.claude/skills/dev-workflow/scripts/test_doc_check.py` on the test file if it applies, and say what it reports.
4. Behaviour only in the commit: anything that no finding states (another docstring changed, a changed log entry that does not match the diff)? A gap to report, not to fix.
5. Re-run with `/home/maldun/prog/Python/venvs/mia312/bin/python`: `tests/test_toolbox.py` (45 tests expected) and `tests/acceptance/test_toolbox.py` (17). The full ladder ran clean on `ca3d8fa` (only `decomposition` fails, F7, known) and no code file changed since: do not repeat it unless `git diff ca3d8fa..HEAD --stat` shows a file outside `toolbox.py`, `tests/test_toolbox.py` and the goal folder.

Rules:
- You do not change code, tests, requirements, contracts or the plan. Findings come with a failing test or a proposed text as a proposal in the report.
- Never run `*.holdout` material; no model, no network, no new dependency.
- Add a section "Sixth round (ff44e2d)" to the report with the checks above and set the verdict at the top. If nothing is open: Verified with accepted deviations (the deviations are F6, F7, F8 rest, and what the owner accepts); otherwise Verified with open findings. The Stage log keeps the clean ladder of `ca3d8fa`; add one line that `ff44e2d` touches no file outside the two. Commit only the report: `git add <path>` and `git commit -m "verify(toolbox): ..." -- <path>` with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; never `git add -A`; do not push.
- Findings go to the owner (reviewer name `maldun`) one per question (AskUserQuestion, recommended option first). Tell the owner when the report is ready for the gate.

Start by listing what you will check and in which order, then begin with step 1.
