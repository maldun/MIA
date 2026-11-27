# Handover: G-V4.GRAPHSTORE.TRANSFER Commit drafted, the owner merges next (2026-11-27)

Replaces `handover-2026-11-27-g-v4-transfer-reverified.md`. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer`. Only the owner pushes (`git push -4`).

## Done
- The owner's ticks were confirmed in the report (lines "Verified by the owner" and "Re-verify accepted by the owner").
- `goal/v4` was merged in at `7eb2749b` (docs only, no conflict). The checks are green: unit 2649 OK, the five transfer acceptance files OK with PostgreSQL, `test_storage_postgres.py` OK, IF-102 on PostgreSQL 12/12, JS 233/233, model OK; traceability 585 as at Verify.
- The merge steps (`9e06633b`): requirements, checks and scenarios are in the node files N-3.1, N-2.1 and N-5. The model texts are updated (V-6) and the model is regenerated (699). AC witnesses are filled. D-551 holds the specification points.
- The test requirements are staged in `e96c136a`, for the owner script `tools/apply_merge_g_v4_transfer.sh`.
- The merge request is in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/merge-request.md`. The history is unchanged (as for RULES and VIEW).

## Waits for the owner
The steps are under "What the owner runs" in the merge request: the owner script `--do`, the 33 requirements set to Verified in Emacs, the commit, `git push -4`, and the merge into `goal/v4` (`git merge --no-ff goal/v4.graphstore.transfer`).

## Open points, not TRANSFER's to decide
- G-V4's gate: 31 new GL2 errors of `goal_check.py` in G-V4. These are the moved requirements whose parent is a goal-local HR item (the same pattern as VIEW and RULES). Also the IF-102 row of G-V4's Frozen table, whose reason is overtaken.
- The Status of the 33 requirements stays Approved until the owner sets Verified. REQ-SLY-009 went from Verified (G-V1) to Approved because its text changed.

## After the merge
1. Check that the merge is on `goal/v4` (`git log goal/v4 --merges -1`) and that the owner script commit is in it (`specs/mia/test-requirements.md` has the section "G-V4.GRAPHSTORE.TRANSFER").
2. On `goal/v4`: traceability 584 with none about TRANSFER; model checks; the five transfer acceptance files; `tests/test_storage_postgres.py`; `tools/contract_postgres.sh`. If RUN or BUILDER merged before, also the unit suite and every acceptance script one at a time.
3. Set the goal's Phases row Commit to `done` with the merge commit, tick nothing (the "Merge" box in `merge-request.md` is the owner's), and write a G-V4 line handover on `goal/v4`.
4. Deploy (`deploy-phase` + `agent-app-deploy`): SMOKE-TRANSFER-001 on the throw-away database `mia_smoke` only (D-460 (1)), with SMOKE-RULES-001 (D-462), through `tools/smoke_in_stack.sh`. Start `mia_db_1` with `podman start` only after the owner says yes. Never run `deploy/up.sh` from a worktree without `deploy/.env`, because it writes a new one. Moving the owner's data to the database is a later owner gate after `tools/backup.sh`. Before the smoke run, look at `ListAgents` (the database and podman are shared).
5. Validate stays parked (G-V5, D-386). The questions for it are in the merge request ("Notes for Deploy and Validate").

## Start prompt for the next session
> Finish the Commit of G-V4.GRAPHSTORE.TRANSFER and run its Deploy. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer`. Read `CLAUDE.md`, `specs/mia/handover-2026-11-27-g-v4-transfer-commit-drafted.md`, `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/merge-request.md` and the goal's `goal.md`; load `dev-workflow`, `commit-phase`, `agent-app`, `agent-app-commit`, then `deploy-phase` and `agent-app-deploy`. First confirm that the owner merged the branch into `goal/v4` with the owner script and the Verified statuses in it. If not, stop and say what is missing. Then do "After the merge" steps 1 to 3, and Deploy as step 4 says (smoke run on `mia_smoke` only, ask before starting the database). Do not merge or push yourself; hand the owner the commands.

## Next free numbers (TRANSFER)
Decisions D-552 (block to D-559); amendments A-198 (block to A-199); checks TC-API-068, TC-SLY-041; test requirements TR-TRANSFER-012.
