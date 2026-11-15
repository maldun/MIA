# Start prompt for the fourth Verify read of G-V2.TOOLBOX (commit bf253ce)

Copy everything below the line into a fresh Claude Code session started in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox` (branch `goal/v2.toolbox`). A session that never saw the finding or the fix chats; one session at a time in this worktree.

---

You re-verify G-V2.TOOLBOX (phase 4, Verify, fourth round) of MIA, supervised, as an independent reviewer. Load `dev-workflow` and `verify-phase` (`agent-app` does not apply). Read `CLAUDE.md`, then the section "Third round (ca3d8fa)" and finding N4 in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox/specs/mia/goals/G-V2.TOOLBOX/verification-report.md`, then `git show bf253ce`.

Scope: exactly one commit, `bf253ce` (`toolbox.py`, `tests/test_toolbox.py`, `implementation-log.md`). It claims to fix N4: in `import_transform`, a failing `set_meta` after a successful first save raises `ToolboxError("store_failed")` with a message that says the entry was stored without its meta record; a failing first `save` still says "was not stored". The orphan entry stays (decided by the owner, maldun). Not in scope and decided: F6, F7, F8 rest, the order event, allowance clear, save, N1 to N3 (verified in round 3).

What to check:
1. Protected material unchanged: `git diff 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks` is empty; `git show --stat bf253ce` touches only the three files named above. Any other change is a finding.
2. Red before green: run `HEAD`'s `tests/test_toolbox.py` against `ca3d8fa:toolbox.py` (a copy made with `git archive` in the scratchpad, never in the worktree). The test for a failing `set_meta` must fail there, on mock and real. The test for a failing first `save` is expected to pass on the old code: say whether it would fail if the behaviour broke.
3. Mutations on a copy of `HEAD` (each must make a test fail; a survivor is a finding): (a) the bare `raise` instead of the `ToolboxError` in the `set_meta` branch; (b) the old text "was not stored" in the `set_meta` branch; (c) the "stored without its meta record" text in the `save` branch; (d) the code `store_failed` changed to another code in either branch; (e) the replace branch (version 2) left unchanged: confirm it is not touched by the split.
4. Read the new code of the new-id branch: does the split keep every case of round 3 (a `ToolboxError` inside is not lost, `KeyboardInterrupt` and `SystemExit` pass through, no entry is deleted, no library method added, the replace branch is unchanged)? Is the message honest for the real library and the mock (entry at version 1, untrusted, empty reason: `look_up` it and compare with the text)? Does the text name the reason as empty only where `look_up` shows it empty? Does the module docstring still say what the code does?
5. Behaviour only in the code: is anything done in `bf253ce` that no requirement or finding states (a new default, an extra output, a retry or cleanup)? That is a gap to report, not to fix.
6. Re-run with `/home/maldun/prog/Python/venvs/mia312/bin/python`: `tests/test_toolbox.py` (45 tests expected), `tests/acceptance/test_toolbox.py` (17), `tests/test_workflow_library.py` (13), `tests/acceptance/contract/test_if_203_v1_transforms.py` (10). The full ladder ran clean on `ca3d8fa` (only `decomposition` fails, F7, known) and `bf253ce` changes no file outside the three: do not repeat it unless `git diff ca3d8fa..HEAD --stat` shows another file.

Rules:
- You do not change code, tests, requirements, contracts or the plan. Findings come with a failing test as a proposal in the report.
- Never run `*.holdout` material; no model, no network, no new dependency.
- Add a section "Fourth round (bf253ce)" to the report with the checks above and set the verdict at the top: Verified with accepted deviations (the deviations are F6, F7, F8 rest, and what the owner accepts), or Verified with open findings. The Stage log keeps the clean ladder of `ca3d8fa`; add one line that `bf253ce` touches no file outside the three. Commit only the report: `git add <path>` and `git commit -m "verify(toolbox): ..." -- <path>` with the line `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`; never `git add -A`; do not push.
- Findings go to the owner (reviewer name `maldun`) one per question (AskUserQuestion, recommended option first). Tell the owner when the report is ready for the gate.

Start by listing what you will check and in which order, then begin with step 1.
