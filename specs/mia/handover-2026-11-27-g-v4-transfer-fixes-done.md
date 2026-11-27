# Handover: G-V4.GRAPHSTORE.TRANSFER fixes after Verify done, amendments staged (2026-11-27)

Replaces `handover-2026-11-27-g-v4-transfer-verify-done.md`. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer`. Only the owner pushes (`git push -4`).

## Done
- `goal/v4` merged in (de1c8064, the V-5 docs fix b259b533).
- V-1 fixed, a844df90: `move_store` takes the copy's lock for a files target that already holds `sync.lock`. D-549: always locking broke REQ-SLY-007 (identical files) and the F-1 checks. Known limit: a folder never synced, while its first sync and a move start at once.
- V-3 fixed, 761de3a5: `check_formats(source, target)` in `move_store`, `move_graph` and `sync_store`, before the first write.
- A-196 (V-2) and A-197 (V-4) drafted, 9ffbed95 (D-550): note `specs/mia/amendments/A-196-197-note.md`, script `tools/apply_amendment_a196_a197.sh`. Trial implementation of A-196 on local branch `wip/transfer-a196-trial` (697badea); it is not on the line of work.
- Checks (my runs, feedback only): transfer acceptance files and `test_migrate.py` OK; full unit suite 2648 OK (one flake in the first run, logged); traceability 585 ERROR lines as before, plus WARNs for the five changed requirements (the same pattern as REQ-API-064 under A-195).

## Next
1. Owner: `bash tools/apply_amendment_a196_a197.sh` (look), then `--do`, commit "plan: A-196, A-197 installed"; in Emacs set REQ-SLY-024 to 027 and 037 to Draft, review, approve. Read the consequences in the note (skills count as records no graph names; `lag.graphs` counts them).
2. Implement A-196 test-first: rewrite the unit check `Sync.test_a_differing_record_outside_every_graph_is_a_conflict_before_any_write`, then take the trial from `wip/transfer-a196-trial`; TC-SLY-040 green on both backends; regenerate the model text block (as 52681d67 after A-195); delete the wip branch.
3. Fresh re-verify of the fix commits only (a844df90, 761de3a5, the A-196/A-197 commits), then V-6 and the verdict, then the owner ticks the sign-off; then Commit into `goal/v4`.

## For the re-verify
- `verify-repro/repro_sync_edges.py .`: V-1 now `refused locked`, V-3 `refused older_format` twice; V-2a/b change only with A-196.
- `verify-repro/defects.json` D4 no longer applies as written: its `old` text `check_format(live)` is now `check_formats(live, copy)`.
- D1 must fail TC-SLY-037 after A-197 is installed.

## Next free numbers (TRANSFER)
Decisions D-551 (block to D-559); amendments A-198 (block to A-199); checks TC-API-068, TC-SLY-041; test requirements TR-TRANSFER-012.
