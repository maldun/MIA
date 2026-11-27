# Handover: G-V4.GRAPHSTORE.TRANSFER re-verified, Commit into goal/v4 next (2026-11-27)

Replaces `handover-2026-11-27-g-v4-transfer-fixes-done.md`. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer`. Only the owner pushes (`git push -4`).

## Done
- Re-verify of the fix commits (a844df90, 761de3a5, 9ffbed95, 5fd14c6d, 7956272f, dfb069cd), committed 7607cca9: section "Re-verify of the fix commits" in `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verification-report.md`. Proposal: **verified with accepted deviations**, no blocker.
- Evidence: full unit suite 2649 OK; all five transfer acceptance files OK with the PostgreSQL halves (TC-SLY-040 on both backends); `test_storage_postgres.py` 45/45; model checks OK; traceability 585 ERROR lines as before, none for TRANSFER. Protected changes are only the A-196/A-197 install, byte-identical to `specs/mia/amendments/A-196-197/`.
- Repro and planted defects: `verify-repro/repro_sync_edges.py` gives the expected answers for V-1, V-2a, V-2b and V-3. `verify-repro/defects-reverify.json` (D1 to D21): D1 is now caught (V-4 closed); D15 to D19 (the regressions of the fixes) are caught. Not caught: D13 (immaterial), D20 (R-1), D21 (equivalent mutant, R-2).
- V-6 decided: not a blocker, a fixed item of Commit (model texts).

## Waits for the owner
- Tick the box "Re-verify accepted by the owner" in the report (verdict; V-6 to Commit; R-1, R-2 accepted). The first sign-off box of the first Verify is still empty too. Without the ticks, Commit does not start.
- Push the branch: `git -C /home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer push -4` (one commit ahead of the remote, two with this handover).

## Commit into goal/v4 (to do)
1. Before you start: the owner's ticks in the report. The goal's Phases table: Verify `done` (report, D-547, re-verify 7607cca9). `goal/v4` is two docs commits ahead (3b86d000, 909d1dfa, line handovers only). Merge it into the branch first, then run the automated checks again: unit suite, transfer acceptance files, `test_storage_postgres.py`, IF-102 contract suite, model checks, `trace_check.py`.
2. Plan "At the merge" (`plan.md`, section 93 ff.), updated by the amendments:
   - Move the requirements into the node files. REQ-SLY-016 to 039 go to N-3.1, and REQ-API-060 to 066 to N-2.1 (065 and 066 were added by A-195). Replace REQ-SLY-009 (N-3.1) and REQ-GA-008 (N-5) with the approved changes. REQ-SLY-024 to 027 and 037 go in with their A-196/A-197 texts. Their `History` lines say "changed by A-196/A-197", no longer "proposed", and the `In force:` lines are dropped.
   - Checks, scenarios and the smoke row go into the node test specs, TC-SLY-040 included. TR-TRANSFER-001 to 011 go into the protected `specs/mia/test-requirements.md` through an owner script, as A-195 and A-196 did.
   - Fill the Witness column of AC-004 to AC-008 and AC-033 in `specs/mia/goals/G-V4/accepted-cases.md`.
   - G-V4 `goal.md` Frozen table, row IF-102: the reason is overtaken. This is the owner's decision at G-V4's gate, so only name it.
3. Items from Verify:
   - V-6: update the model texts. `WebApplication` (`architecture.sysml` about line 292) still says "planned" and names only REQ-API-060 to 064. `storageLayer` should also name `lag_summary`, `AutoSync`, the reconnect (V-3 of VIEW) and the records no graph names (A-196). Run `bash tools/check_sysml.sh` afterwards.
   - REQ-SLY-039: add the command texts (the extra `sync` line per set-aside item, `lag` printing nothing when current, the `refused:` line of a move). REQ-SLY-025 rationale: what `graphs` counts. REQ-SLY-028 rationale: D-549's reading of "the copy" (optional).
   - Known limitations for the merge request: D-549's lock limit, R-1, R-2, and `library-seed` without the per-graph check.
4. History: one commit per task with requirement IDs (commit-phase). Draft the merge request into `goal/v4`. No version and no tag, because this is a subgoal. A person merges; `merge_gate.py --approved-by` is the owner's.
5. Afterwards: Phases table Commit `done`. Deploy is the smoke on `mia_smoke` only (D-460 (1)), together with SMOKE-RULES-001 (D-462).

## Notes
- Do not run `deploy/up.sh` from a worktree without `deploy/.env`: it writes a new one. Start `mia_db_1` with `podman start`.
- Flaky checks seen before (`test_skill_run_view_browser.py`, `test_sandbox`, once `test_graph_api_v2.py` `CopySet`): all green in the re-verify run. Re-run once before you judge a failure.

## Next free numbers (TRANSFER)
Decisions D-551 (block to D-559); amendments A-198 (block to A-199); checks TC-API-068, TC-SLY-041; test requirements TR-TRANSFER-012.

## Start prompt for the Commit
> Commit G-V4.GRAPHSTORE.TRANSFER into `goal/v4`: worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer`. Read `CLAUDE.md`, `specs/mia/handover-2026-11-27-g-v4-transfer-reverified.md`, the goal's `goal.md`, `plan.md` (section "At the merge"), the "Re-verify of the fix commits" section and the "Notes for Commit, Deploy and Validate" of `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verification-report.md`; load `dev-workflow`, `commit-phase`, `agent-app` and `agent-app-commit`. First confirm the owner's ticks in the report. Merge `goal/v4` into the branch and run the automated checks again. Then do the merge steps of the handover (node files, test requirements by owner script, accepted cases, model texts for V-6, command texts), clean the history, and draft the merge request into `goal/v4`. Do not merge or push yourself; hand the owner the commands.
