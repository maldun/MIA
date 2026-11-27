# Handover: G-V4 line, TRANSFER merged and deployed (smoke only) (2026-11-27, late night)

Supersedes `handover-2026-11-27-g-v4-line-transfer-reverified.md` for the session that picks the next G-V4 step. Everything there still holds except the items below. Worktree of this line: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4`. Read `CLAUDE.md` and this file; load `dev-workflow` and the phase skill of what you pick. Ways of working: ask decisions as a questionnaire, recommended option first; name files by full absolute paths; the owner signs, and the agent never sets Approved; only the owner pushes (`git push -4`).

## What happened since the last line handover
| Item | Result | Record |
|---|---|---|
| TRANSFER Commit | merged by the owner at `f6ccde75`; 33 requirements Verified (`268e54e2`), TR-TRANSFER-001 to 011 installed (`c1e84d8e`) | `goals/G-V4.GRAPHSTORE.TRANSFER/goal.md` Phases, `merge-request.md` |
| Checks on `goal/v4` after the merge | traceability 584 (none about TRANSFER); model checks OK; the five transfer acceptance files OK; `test_storage_postgres.py` 45 OK; `contract_postgres.sh` 12 OK | `goals/G-V4.GRAPHSTORE.TRANSFER/deployment-record.md` |
| TRANSFER Deploy | SMOKE-TRANSFER-001 green on `mia_smoke` only, SMOKE-RULES-001 pass, both through `tools/smoke_in_stack.sh` with `localhost/mia:g-v4-transfer`; `mia_smoke` dropped, `mia_db_1` stopped again; no finding | `deployment-record.md`, D-552 |

## Waiting for the owner
- [ ] RUN A-189: the consumers of IF-301 (VIEW, EDIT, CONTEXT) agree to the joint amendment (D-483 names it open).
- [ ] RUN F-7: the small fix of `IMPORT_OPS` in `toolbox.py`: own task, and in which line.
- [ ] TRANSFER: the two Date fields of the sign-off boxes are empty (optional).
- [ ] The reason "(scoped record IDs, sync)" in the IF-102 row of G-V4's `goal.md` Frozen table is overtaken now that TRANSFER is merged.
- [ ] Later gate (D-460 (1)): move the live store to the database after `tools/backup.sh`; rebuild `localhost/mia:g-v4-transfer` from `goal/v4` first (the current one predates the fix commits, D-552 (2)).

## Next (pick one per session)
- **RUN T-04** (real model runs, about 588 case runs on MP-light): start prompt at the end of `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run/specs/mia/handover-2026-11-27-g-v4-run-t04-next.md`. RUN must merge `goal/v4` (now with TRANSFER) before its Commit. Check `ListAgents` first and message every running session. Ollama is stopped.
- `explore/builder-workflow` (BUILDER waits for RUN and CONTEXT, D-521). For EDIT and CODE, see the notes in `goals/G-V4.VIEW/merge-request.md` and TD-91 to TD-95 (deadline 2026-12-31).
- TRANSFER Validate stays parked (G-V5, D-386).

## State of the host
The live stack `mia`, `mia_db_1` and `ollama` are stopped; `mia-searxng` runs. A throw-away `mia-test-postgres-*` container seen during this session was not started by it. Never overwrite `localhost/mia:latest` (RUN's branch build). Use `-4` for `git fetch` and `git push`. The worktree `goal-v4-transfer` (branch `goal/v4.graphstore.transfer`, fully merged) can be removed by the owner.

## Next free numbers
TRANSFER D-553, A-198, TC-API-068, TC-SLY-041, TR-TRANSFER-012; RUN D-486, A-191, F-8; VIEW D-505, A-178; BUILDER D-522.
