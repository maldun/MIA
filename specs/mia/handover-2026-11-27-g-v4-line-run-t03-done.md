# Handover: G-V4 line, RUN T-03 done, TRANSFER verified with fixes under way (2026-11-27, late)

Supersedes `handover-2026-11-27-g-v4-db-docs-done.md` for the session that picks the next G-V4 step; everything there still holds except the items below. Worktree of this line: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4` (pushed by the owner up to `b259b533`; this handover comes on top). Read `CLAUDE.md` and this file; load `dev-workflow` and the phase skill of what you pick. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; only the owner pushes (`git push -4`).

## What this session did
| Item | Result | Record |
|---|---|---|
| TRANSFER Verify (background agent, fresh context) | report drafted: proposal "verified with accepted deviations" after fixes; checks rerun (unit 2645 OK, PostgreSQL 45/45, IF-102 12/12, SMOKE-TRANSFER-001 4 PASS); findings V-1 to V-6 | `goal/v4.graphstore.transfer` `1246c849` (D-547) |
| Owner's answers to TRANSFER Verify | V-1, V-3 Phase 3 fixes; V-2 amendment A-196; V-4 amendment A-197; V-6 and the verdict after the fixes | `871e19f5` (D-548), handover with start prompt `3561bdb8` |
| V-5 (docs here) | `deploy/REQUIREMENTS_DB.md` item 7 now `--data MIA/data/db` (`MIA/data` is what the F-1 fix refuses); not run in the container | `b259b533` |
| TRANSFER fixes handed over | the owner started session `goal-v4-7b`; it got the decisions by message and has drafted A-196, A-197 (`9ffbed95`) | – |
| RUN: merge of `goal/v4`, A-190, T-03 | merge conflict in `architecture.sysml` resolved by keeping both sides; A-190: REQ-RUN-046 (answer step of a stored graph) and REQ-RUN-047 (graph run imports only stdlib, networkx and the rule set: "re-use = module boundary only"); T-03 committed after a green regression (unit 2610 OK, acceptance 73/75, red only the known two) | `goal/v4.graphapi.run` `9983b896`, `e12d5d94` (D-485), `551c414b`, handover `1109858e` |

## Waiting for the owner
- [ ] RUN: approve REQ-RUN-046, 047 (Draft, A-190); REQ-GTB-060 back to Draft and approve again, REQ-GTB-043 (Draft); A-189 as a joint amendment of IF-301 (VIEW, EDIT, CONTEXT agree).
- [ ] TRANSFER: install A-196, A-197 when the fix session stages them; then the re-verify of the fix commits and the sign-off box in `verification-report.md`.
- [ ] RUN F-7: say whether the small fix of `IMPORT_OPS` in `toolbox.py` (thin code takes the toolbox's own `common_operations`) gets its own task, and in which line.

## Next (pick one per session)
- **RUN T-04** (real model runs, about 588 case runs on MP-light): start prompt at the end of `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run/specs/mia/handover-2026-11-27-g-v4-run-t04-next.md`. `ListAgents` first and a message to every running session (the TRANSFER fix session was promised one); Ollama is stopped.
- **TRANSFER**: runs in session `goal-v4-7b` (fixes, A-196, A-197), then a fresh re-verify of the fix commits only, then Commit into `goal/v4`.
- `explore/builder-workflow` (BUILDER, waits for RUN and CONTEXT, D-521); EDIT and CODE: notes in `goals/G-V4.VIEW/merge-request.md`, TD-91 to TD-95 (deadline 2026-12-31).
- Optional, small: the rest of `deploy/REQUIREMENTS_DB.md` (stages, decisions) is still written as a plan.

## State of the host
Live stack `mia`, `mia_db_1` and `ollama` stopped; `mia-searxng` runs. The TRANSFER verifier started `mia_db_1` with `podman start` for the smoke and stopped it again. No image was built this session; never overwrite `localhost/mia:latest` (RUN's branch build). `git fetch` over IPv6 hung once this evening (moved to the background after 120 s): use `-4`.

## Next free numbers
TRANSFER D-549, A-198 (A-196, A-197 taken by the fix session); RUN D-486, A-191, F-8; VIEW D-505, A-178; BUILDER D-522.
