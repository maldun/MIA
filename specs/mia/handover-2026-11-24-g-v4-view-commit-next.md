# Handover: G-V4.VIEW re-verify done; next Commit (2026-11-24)

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-view`, branch `goal/v4.view` (tracks `origin/goal/v4.view`; the owner pushes, with `git push -4`). Start a fresh session. Read `CLAUDE.md`, this file, and from `specs/mia/goals/G-V4.VIEW/`: `verification-report.md` (findings V-1 to V-15, "Owner's decisions" D-501, "Re-verify of the fixes"), `goal.md`, `plan.md` (its Commit points). Then load `dev-workflow` and `commit-phase`. VIEW has no model step, so `agent-app-commit` does not apply. This file supersedes `handover-2026-11-24-g-v4-view-reverify-next.md`.

## Before Commit starts (the owner)
- [ ] Tick both boxes in `verification-report.md`: "Verified by the owner" (Verdict) and "Re-verify accepted by the owner" (end of the file). Proposal: **verified with accepted deviations**.
- [ ] The close look at the page in Firefox, by the list in the report's "Notes for Commit, Deploy and Validate". It can also wait for Deploy, with `store: database`; the owner decides.

Commit starts only after the boxes are ticked. Then set the Verify row in `goal.md` to done.

## State
| Item | State | Where |
|---|---|---|
| Implement | T-01 to T-12 done; the fixes after Verify done (D-501), one commit per reopened task | `implementation-log.md` |
| Verify | report plus re-verify (`59af1a91`): V-1, V-2, V-4, V-5 (narrowed), V-8, V-9, V-10, V-13, V-15 closed; no new findings | `verification-report.md` |
| Accepted deviations | V-3 (handed to G-V4.GRAPHSTORE.TRANSFER), V-6, V-7, V-11, V-12, V-14 | D-501 (3) |
| Image | keep the tag `mia-view-check` until the merge (V-15) | D-501 (4) |
| Reviewer's repro scripts | `verify-repro/repro_f1.py`, `repro_f2.py` (cannot show V-9, it blocks the login cookie), `repro_f2_storage.py` (V-9, storage only), `repro_f3.py` | report |

## Commit (a subgoal: merge into `goal/v4`, no version, no tag)
1. **Update the branch with `goal/v4`.** `goal/v4` has 8 commits since the merge base, docs only (D-472 to D-474, the RUN split, SWITCH; 7 files). Expect conflicts only in shared spec files (`review-log.md`, `goals/G-V4/goal.md`).
2. **Rerun the automated checks on the updated branch**, one at a time (they share `mia.log`), with the venv `mia312`. The list is the re-verify table in the report: VIEW's acceptance files, the IF-104 v2 contract (33, PostgreSQL), the page and browser checks (browser three times), `tests/js`, the unit suite, every acceptance script, the model checks, trace (549 expected) and goal check (82 expected). Known reds outside VIEW: `test_decide_guard.py`, `test_judge_calibration.py` (G-V3.REPORT F-3). `test_delivery_on_stack` runs only while Ollama answers; otherwise it skips.
3. **Specification work at Commit** (`plan.md`, D-501 (3)):
   - Move VIEW's 70 requirements, its checks and TR-VIEW-001 to TR-VIEW-021 from `goals/G-V4.VIEW/` into the node files. The goal's trace errors are expected to go away with this; check that the count drops and that no new error appears.
   - Fill the Witnesses of AC-009 to AC-016 and AC-035.
   - Write into the specification: **V-7** (which text binds for a value of the wrong type: REQ-API-048's `invalid` or IF-104 v2's codes), **V-11** (errors other than 401 and 503 show nothing), the **V-14 items** (report section "Specification vs. code", items 1 to 12 plus the list the owner kept), and the **V-5 question** together with V-7 (whether every wrong form of a step or connection is `invalid` instead of `rules_broken`; today only a connection without a text `id` is `invalid`). These are owner decisions: ask them as one questionnaire, then write them.
   - The model is done (V-13, `976348e4`); run `bash tools/check_sysml.sh` again after the spec moves.
4. **Clean the history**: one commit per task, with requirement IDs, by the commit-phase rules. The fix commits belong to their tasks (T-04, T-06, T-07, T-08, T-10, T-12).
5. **Draft the merge request** into `goal/v4`: scope, the accepted deviations, the evidence (report), and the V-3 hand-over to TRANSFER. A person merges; the agent never merges or pushes.
6. After the merge: Commit row done in `goal.md`; the line about V-3 in TRANSFER's record is written by the session that works on TRANSFER (D-501 (2)).

## Then
Deploy: SMOKE-VIEW-001 (image with `psycopg`, `store: database`) and SMOKE-VIEW-002 (opening time, measured); the owner's look with `store: database` (exit criterion). Validate as the goal record says (NFR-10 first use without help, light and dark, the 220 px layers on large graphs).

## Shared state
- No model calls in VIEW's checks. The PostgreSQL tests start their own throwaway `postgres:16` under podman.
- Another branch, `explore/builder-workflow` (worktree `.claude/worktrees/builder-workflow`), carries D-520 (the BUILDER TLS amendment) off `goal/v4`. It touches `review-log.md` and `high-level-spec.md`, so whichever merges into `goal/v4` second has a small conflict there.

Next free numbers: D-502 (VIEW's block D-500 to D-519; BUILDER has D-520 to D-539), A-176, TC-API-026, TR-VIEW-022, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003. REQ-API for VIEW stays at or below 059.
