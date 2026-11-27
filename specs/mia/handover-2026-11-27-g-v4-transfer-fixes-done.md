# Handover: G-V4.GRAPHSTORE.TRANSFER fixes after Verify done, amendments staged (2026-11-27)

Replaces `handover-2026-11-27-g-v4-transfer-verify-done.md`. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer`. Only the owner pushes (`git push -4`).

## Done
- `goal/v4` merged in (de1c8064, the V-5 docs fix b259b533).
- V-1 fixed, a844df90: `move_store` takes the copy's lock for a files target that already holds `sync.lock`. D-549: always locking broke REQ-SLY-007 (identical files) and the F-1 checks. Known limit: a folder never synced, while its first sync and a move start at once.
- V-3 fixed, 761de3a5: `check_formats(source, target)` in `move_store`, `move_graph` and `sync_store`, before the first write.
- A-196 (V-2) and A-197 (V-4) drafted, 9ffbed95 (D-550): note `specs/mia/amendments/A-196-197-note.md`, script `tools/apply_amendment_a196_a197.sh`. Trial implementation of A-196 on local branch `wip/transfer-a196-trial` (697badea); it is not on the line of work.
- Checks (my runs, feedback only): transfer acceptance files and `test_migrate.py` OK; full unit suite 2648 OK (one flake in the first run, logged); traceability 585 ERROR lines as before, plus WARNs for the five changed requirements (the same pattern as REQ-API-064 under A-195).

- A-196 and A-197 installed (5fd14c6d) and approved by the owner in Emacs; A-196 implemented test-first (7956272f), model block regenerated (dfb069cd), `wip/transfer-a196-trial` deleted. Full unit suite 2649 OK, `test_storage_postgres.py` OK, every transfer acceptance file OK (TC-SLY-040 on both backends).

## Next
1. Fresh re-verify of the fix commits only: a844df90 (V-1), 761de3a5 (V-3), 9ffbed95 and 5fd14c6d (A-196, A-197 drafts and install; compare the installed files with `specs/mia/amendments/A-196-197/`), 7956272f (A-196 code), dfb069cd (model block). Then V-6 and the verdict; the owner ticks the sign-off.
2. Then Commit into `goal/v4`.

## Start prompt for the re-verify
> Re-verify G-V4.GRAPHSTORE.TRANSFER: only the fix commits after Verify (a844df90, 761de3a5, 9ffbed95, 5fd14c6d, 7956272f, dfb069cd) in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer` (branch `goal/v4.graphstore.transfer`). Read `CLAUDE.md`, `specs/mia/handover-2026-11-27-g-v4-transfer-fixes-done.md`, the findings V-1 to V-6 in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verification-report.md` and the section "Fixes after Verify" of its `implementation-log.md`; load `dev-workflow` and `verify-phase`. Rerun the repro and the planted defects (`verify-repro/`), decide V-6, and add the result and the verdict to the report; the sign-off box stays empty for the owner.

## For the re-verify
- `verify-repro/repro_sync_edges.py .`: V-1 now `refused locked`, V-3 `refused older_format` twice; V-2a/b change only with A-196.
- `verify-repro/defects.json` D4 no longer applies as written: its `old` text `check_format(live)` is now `check_formats(live, copy)`.
- D1 must fail TC-SLY-037 now (A-197 installed).
- V-2: repro V-2a gives the orphan set aside and removed (graph group equal), V-2b a set-aside and a sync instead of `conflict`.

## Next free numbers (TRANSFER)
Decisions D-551 (block to D-559); amendments A-198 (block to A-199); checks TC-API-068, TC-SLY-041; test requirements TR-TRANSFER-012.
