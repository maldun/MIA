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

## After the merge
Phases row Commit `done` with the merge commit. Then Deploy: the smoke run on `mia_smoke` only (D-460 (1)), with SMOKE-RULES-001 (D-462).

## Next free numbers (TRANSFER)
Decisions D-552 (block to D-559); amendments A-198 (block to A-199); checks TC-API-068, TC-SLY-041; test requirements TR-TRANSFER-012.
