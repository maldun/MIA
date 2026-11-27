# Handover: G-V4 line, TRANSFER re-verified and signed off, Commit into goal/v4 next (2026-11-27, night)

Supersedes `handover-2026-11-27-g-v4-line-run-t03-done.md` for the session that picks the next G-V4 step. Everything there still holds except the items below. Worktree of this line: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4`, pushed up to `088ebc6b`; this handover comes on top. Read `CLAUDE.md` and this file; load `dev-workflow` and the phase skill of what you pick. Ways of working: ask decisions as a questionnaire, recommended option first; name files by full absolute paths; the owner signs, and the agent never sets Approved; only the owner pushes (`git push -4`).

## What happened since the last line handover
| Item | Result | Record |
|---|---|---|
| `deploy/REQUIREMENTS_DB.md` | says what is built (storage layer, db service, migrate, backup) and what is still a plan; the optional item of the last handover is done | `goal/v4` `088ebc6b` |
| TRANSFER re-verify (fresh session, fix commits only) | proposal: verified with accepted deviations. Unit 2649 OK; transfer acceptance OK on files and PostgreSQL (TC-SLY-040 on both); `test_storage_postgres.py` 45/45; model checks OK; traceability unchanged (585, none for TRANSFER). Protected changes are byte-identical to the A-196/197 drafts. Repro as promised. Planted defects: D1 now caught (V-4 closed); the fixes' regressions D15 to D19 are caught. V-6 (model texts) goes to Commit. R-1 (a record's aside file is not path-searched; inspected, writes no path) and R-2 (`\|` in a graph ID) are low and accepted | `goal/v4.graphstore.transfer` `7607cca9`, section "Re-verify of the fix commits" of `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verification-report.md`; `verify-repro/defects-reverify.json` |
| TRANSFER sign-off | both boxes ticked by the owner (first Verify and re-verify); pushed | `3748d0c3`, `5b8e77ff` |
| TRANSFER handover for Commit | steps and start prompt for the Commit into `goal/v4` | `a598e716`, `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer/specs/mia/handover-2026-11-27-g-v4-transfer-reverified.md` |

## Waiting for the owner
- [ ] RUN: approve REQ-RUN-046, 047 (Draft, A-190). Set REQ-GTB-060 back to Draft and approve it again, and approve REQ-GTB-043 (Draft). A-189 is a joint amendment of IF-301 (VIEW, EDIT and CONTEXT agree).
- [ ] RUN F-7: decide whether the small fix of `IMPORT_OPS` in `toolbox.py` gets its own task, and in which line.
- [ ] TRANSFER: the two Date fields of the sign-off boxes are empty (optional).
- [ ] At TRANSFER's merge (G-V4's gate): the reason "(scoped record IDs, sync)" in the IF-102 row of G-V4's `goal.md` Frozen table is overtaken.

## Next (pick one per session)
- **TRANSFER Commit into `goal/v4`**, in a fresh session. Start prompt at the end of `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer/specs/mia/handover-2026-11-27-g-v4-transfer-reverified.md`. First merge `goal/v4` into the TRANSFER branch, because `goal/v4` moved on: 3b86d000, 909d1dfa, 088ebc6b and this handover, all docs. Then do the "At the merge" steps, V-6 and the command texts, and draft the merge request. The owner merges. After that, TRANSFER Deploy runs the smoke on `mia_smoke` only, together with SMOKE-RULES-001 (D-460 (1), D-462).
- **RUN T-04** (real model runs, about 588 case runs on MP-light): start prompt at the end of `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run/specs/mia/handover-2026-11-27-g-v4-run-t04-next.md` (RUN unchanged since `1109858e`). Check `ListAgents` first and message every running session. Ollama is stopped.
- `explore/builder-workflow` (BUILDER waits for RUN and CONTEXT, D-521). For EDIT and CODE, see the notes in `goals/G-V4.VIEW/merge-request.md` and TD-91 to TD-95 (deadline 2026-12-31).

## State of the host
The live stack `mia`, `mia_db_1` and `ollama` are stopped; only `mia-searxng` runs. The re-verify built no image and started no stack container; its PostgreSQL checks used throw-away postgres:16 containers. Never overwrite `localhost/mia:latest` (RUN's branch build). Use `-4` for `git fetch` and `git push`.

## Next free numbers
TRANSFER D-551, A-198, TC-API-068, TC-SLY-041, TR-TRANSFER-012; RUN D-486, A-191, F-8; VIEW D-505, A-178; BUILDER D-522.
