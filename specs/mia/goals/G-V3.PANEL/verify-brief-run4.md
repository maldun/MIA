# Brief for the fourth Verify run of G-V3.PANEL (to be pasted as the prompt of a fresh reviewer agent)

Prepared 2026-11-14 after the third report (`verification-report-run3.md`, `5fb1991`, verdict Not verified: F-18 and F-19, low, plus paperwork). Use this text unchanged. It is a **very narrow** run: it checks only the fix of F-18 and F-19. Read `verify-brief.md` (rules), `verify-brief-run3.md` and `verification-report-run3.md` first; the earlier findings are closed and are not re-probed.

---

You are a fresh Verify-phase reviewer for goal G-V3.PANEL, fourth run (no memory of earlier sessions). Work ONLY in /home/maldun/prog/Python/MIA/.claude/worktrees/goal-v3 (branch goal/v3); never cd to /home/maldun/prog/Python/MIA. Follow CLAUDE.md there; Python for every test: /home/maldun/prog/Python/venvs/mia312/bin/python; foreground only, never `nohup`, never two full suites at once. Load `dev-workflow` and `verify-phase`; probes and scratch copies under your scratchpad, mutants only in a scratch COPY made by `git archive`. You are a reviewer: edit nothing but the report, do not push, do not run `install.py` files.

**What changed since the third report (`5fb1991`):** `git log --oneline 5fb1991..HEAD`.
| Finding | Fix | Commit |
|---|---|---|
| F-18 the log line in the `except` of `_emit_status` can raise for a payload that is not a dict | the id is read before the `try`, only from a dict payload | `054d382` (`chat_service.py`, 3 lines) |
| F-19 four surviving mutants (no note at load for a dead link, click on a dead link notifies, healthy recorder logs nothing, log call before the `try`) | tests added: `tests/js/skill-run-start.test.mjs` (now 3 tests of the start and click), `tests/test_emit_status_storage_error.py` (now 4 tests) | `054d382` |
| TD-82 to TD-84 | signed off by the owner (2026-11-14), `Sign-off: maldun, 2026-11-14`; the decision row D-338 is still pending | the commit after `054d382` |

**Tasks.**
1. Close F-18 and F-19 with your own probes: `_emit_status` with a dict, a non-dict (str, None, list), a payload without `id`, a recorder that raises, a recorder that works; the log call count and text in each case. Re-run your own M3, M3b, M3c and M5 mutants of the third run against the new tests; report survivors with a reason and a proposed test.
2. Look hard at the new diff (`git diff 5fb1991..HEAD -- chat_service.py tests templates`): a regression from this round is the usual pattern. Check that `run` is not used before it is defined, that the `isinstance` does not change which payloads get the record lookup (the lookup still reads `payload["id"]` inside the `try`), and that the tests do not depend on test order or on a leaked patch of `chat_service.logger`.
3. Regression, once each: JS tests (167 expected), `test_emit_status_storage_error`, `test_chat_tasks`, `test_skill_runs_race`, `test_skill_run_gaps`, the browser checks (12 tests, three runs, no flip) and the restart test, the full unit suite once (2078 tests expected: one known error `test_tailscale`), the contract suites IF-101 (78, 2 skips), IF-302, IF-102, `check_sysml_model.py`, `test_doc_check` (no new error), the protected diff against `plan-baseline-it2-panel` (nothing new since the third report).
4. `deferred.md`: only the three `Sign-off` lines changed since the third report; nothing else in `specs/` except this brief.

**Known before you start (facts, not findings).** `trace_check` has 553 errors (545 at the tag): two TD-81, six TD-82 to TD-84, to be linked in one amendment later (owner's choice). The decision row D-338 that accepts F-15, F-16, F-17 (TD-82 to TD-84) in `review-log.md` is pending: the verdict 'Verified with accepted deviations' needs it, say so and list what it must name. The branch has not merged master; `goal/v3.chat` is a separate line. The look of the character in the changed box is VAL-012.

**Verdict.** 'Verified', 'Verified with accepted deviations' or 'Not verified', with the exact remaining reasons. Write ONLY `specs/mia/goals/G-V3.PANEL/verification-report-run4.md` (finding ids continue at F-20), commit only that file with `git add` of its path and `git commit -m "docs: G-V3.PANEL verification report, fourth run" -- <path>`, message ending with `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
