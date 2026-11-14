# Start prompt for the third Verify read of G-V2.TOOLBOX (commit ca3d8fa)

Copy everything below the line into a fresh Claude Code session started in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox` (branch `goal/v2.toolbox`). A session that never saw the fix chats; one session at a time in this worktree. Start it in a normal terminal, so that signals reach the tests (the shutdown tests fail in a `nohup` background job).

---

You re-verify G-V2.TOOLBOX (phase 4, Verify, third round) of MIA, supervised, as an independent reviewer. Load `dev-workflow` and `verify-phase` (`agent-app` does not apply). Read `CLAUDE.md`, then the section "Second round" and its findings N1 to N3 in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-toolbox/specs/mia/goals/G-V2.TOOLBOX/verification-report.md`, then `git show ca3d8fa`.

Scope: exactly one commit, `ca3d8fa` (`toolbox.py`, `tests/test_toolbox.py`). It claims to fix N1 (an untrust keeps the reason of an entry that is untrusted already), N2 (a failure of the event store or the library while importing is `ToolboxError("store_failed")`; the orphan event stays, decided) and N3 (test gaps for F4, F3, F1). Not in scope and decided: F6, F7, F8 rest, the order event, allowance clear, save.

What to check:
1. Protected material unchanged: `git diff 84eddb6..HEAD -- tests/acceptance tests/helpers tests/smoke contracts eval benchmarks` is empty. Any change is a finding.
2. Red before green: run `HEAD`'s `tests/test_toolbox.py` against `5c0f2b0:toolbox.py` (a copy in the scratchpad, never in the worktree). The N1 and N2 tests must fail there. The N3 tests are expected to pass on the old code (they pin behaviour that existed); say which tests that are and whether each would fail if the behaviour broke (mutate a copy: for example let `_checked` accept `2.0`, or keep the allowance after a failed save).
3. N1 in `set_trust`: the reason after trusted, then untrusted by the owner, then untrusted again by an account (the second untrust must keep the first reason, N1 asks for that); an untrusted shipped entry; a fresh import untrusted by a guest keeps the import text; trust given back and taken again. Is the `_latest(tid)` call a second read that can disagree with the write (single user: say whether it matters)?
4. N2 in `import_transform`: `except Exception` also catches what is not a store failure. Look for a `ToolboxError` raised inside a `try` and wrapped as `store_failed`, for `KeyboardInterrupt` and `SystemExit` (they are not `Exception`: confirm), for the new-import branch where `save` works and `set_meta` fails (an entry without meta stays, F8 note: is the message honest about it?), and for `why` leaking a path or secret from the library's error text. Check that the allowed codes of the module docstring list `store_failed`.
5. Re-run with `/home/maldun/prog/Python/venvs/mia312/bin/python`: `tests/test_toolbox.py`, `tests/acceptance/test_toolbox.py`, `tests/test_workflow_library.py`, `tests/acceptance/contract/test_if_203_v1_transforms.py`, then the full stage ladder `run_stages.py --upto 2 --keep-going` with the venv `bin` first in PATH, in this terminal (the unit step takes 8 to 15 minutes; do not edit any file in the worktree while it runs, `test_checkout_untouched` fails on a changed file). Expected: `decomposition` fails (F7, known); every other step passes; 17 skips in the real contracts. Anything else is a finding with its failing test as a proposal. Stage 3 needs podman and local images (`postgres:16`): run it only if both are there and say so; stage 4 has no steps.

Rules:
- You do not change code, tests, requirements, contracts or the plan. Findings come with a failing test as a proposal in the report.
- Never run `*.holdout` material; no model, no network, no new dependency.
- Add a section "Third round (ca3d8fa)" to the report with the checks above, replace the Stage log entry with the clean ladder result on `HEAD`, and set the verdict: Verified with accepted deviations (the deviations are F6, F7, F8 rest, and what the owner accepts), or Verified with open findings. Commit only the report: `git add <path>` and `git commit -m "verify(toolbox): ..." -- <path>` with the Co-Authored-By line; never `git add -A`; do not push.
- Findings go to the owner (reviewer name `maldun`) one per question (AskUserQuestion, recommended option first). Tell the owner when the report is ready for the gate.

Start by listing what you will check and in which order, then begin with step 1.
