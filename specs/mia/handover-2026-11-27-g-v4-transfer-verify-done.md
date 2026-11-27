# Handover: G-V4.GRAPHSTORE.TRANSFER Verify drafted, the owner's answers next (2026-11-27)

Replaces `handover-2026-11-27-g-v4-transfer-verify-next.md`. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer` (`goal/v4` @ 6a39dce3 merged in, 658f0141). Only the owner pushes (`git push -4`).

## State
- Report draft: `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verification-report.md` (D-547). Proposal: **verified with accepted deviations after V-1 (and V-3) are fixed**; sign-off box empty.
- Reproductions: `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verify-repro/` (`repro_sync_edges.py CHECKOUT` for V-1 to V-3, `defects.json` for `tools/plant_defects.py`, D1 NOT CAUGHT = V-4).
- Checks rerun by Verify: unit suite 2645 OK; acceptance red only `test_decide_guard.py`, `test_judge_calibration.py` (known); `test_storage_postgres.py` 45/45; IF-102 contract 12/12; JS 233/233; SMOKE-TRANSFER-001 4 PASS; traceability 585 ERROR lines, identical to `goal/v4`.

## Findings (details and options in the report)
- V-1 medium, Phase 3: `move_store` into a files copy takes no copy lock (REQ-SLY-028 names "a move into the copy").
- V-2 low, Phase 2: graph-group records that no graph names: a copy-only one stays after the sync, a differing one refuses the whole sync while the lag says current.
- V-3 low: a sync or move into an older set with unscoped IDs marks it format 1 (REQ-SLY-034 is checked on the source only).
- V-4 low: TC-SLY-037 misses an absolute path outside home (amendment A-196 proposed; protected test).
- V-5 medium, `goal/v4` docs: `deploy/REQUIREMENTS_DB.md` item 7 says `--data MIA/data`; the store is `MIA/data/db` (F-1 refuses the documented command).
- V-6 low: `architecture.sysml` text still says T-06 planned (fix at Commit).

## Next
1. Done 2026-11-27 (D-548, `871e19f5`): V-1 Phase 3 fix; V-2 amendment A-196 (records no graph names synced like a graph, `lag` lists them); V-3 Phase 3 fix (`check_format` on the target too); V-4 amendment A-197 (TC-SLY-037 searches every folder root the check made); V-5 fixed on `goal/v4` (`b259b533`). Verdict and V-6 after the fixes.
2. With 2(a)/3(a): a fresh Implement session on this branch fixes V-1 (and V-3), each with a failing unit test first; with 1(a)/4(a) the amendments come first (A-196 and up, owner scripts).
3. Re-verify of the fix commits only (a fresh session), then the owner ticks the sign-off; then Commit into `goal/v4`.
4. V-5 is a docs commit on `goal/v4` (another session's line).

## Start prompt for the fix session
> Continue G-V4.GRAPHSTORE.TRANSFER after Verify: fix V-1 and V-3 and stage amendments A-196 (V-2) and A-197 (V-4) as decided in D-548. Work in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md`, `specs/mia/handover-2026-11-27-g-v4-transfer-verify-done.md` and the findings in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verification-report.md` (repro in `verify-repro/`); load `dev-workflow`, `implement-phase` and `plan-phase` (amendments: drafts staged by a script outside the repo, the owner installs). Merge `goal/v4` first (V-5 fix). Each fix with a failing unit test first; then hand over to a fresh re-verify of the fix commits only.

## Host state
`mia_db_1` stopped again (started only for the smoke with `podman start`; `deploy/up.sh` was not run, it would write a `deploy/.env` into the worktree). No image built; `localhost/mia:latest` untouched (the smoke used `localhost/mia:g-v4-transfer` as runtime).

## Next free numbers (TRANSFER)
Decisions D-548 (block to D-559); amendments A-196 (block to A-199); checks TC-API-068, TC-SLY-040; test requirements TR-TRANSFER-012.
