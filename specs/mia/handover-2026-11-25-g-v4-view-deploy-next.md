# Handover: G-V4.VIEW Commit done, merged into `goal/v4`; next Deploy (2026-11-25)

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4` (tracks `origin/goal/v4`; the owner pushes, with `git push -4`). VIEW's own branch `goal/v4.view` is merged and pushed; it gets no more commits. Start a fresh session. Read `CLAUDE.md`, this file, and from `specs/mia/goals/G-V4.VIEW/`: `goal.md` (exit criterion, Phases), `plan.md` ("Deployment and feedback"), `verification-report.md` ("Notes for Commit, Deploy and Validate"), `merge-request.md` ("Known issues"). Then load `dev-workflow` and `deploy-phase`. VIEW has no model step, so `agent-app-deploy` does not apply. This file supersedes `handover-2026-11-24-g-v4-view-commit-next.md`.

## Before Deploy starts (the owner)
- [ ] `git push -4` in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`: this handover commit is not pushed yet (`8a6f658a`, the Commit row, is).

## State
| Item | State | Where |
|---|---|---|
| Commit | done: merged by the owner at `34fb0534`; TR-VIEW-001 to 021 and TD-91 to TD-95 installed and signed off (`abf2db5f`) | `goal.md` Phases, `merge-request.md` |
| Checks on `goal/v4` after the merge | trace 585 (as expected), `check_sysml_model.py` OK, `check_sysml.sh` 0 errors, VIEW acceptance 9/9 and 2/2, IF-104 v2 contract 33/33 (mock, files, PostgreSQL 16, none skipped), Firefox 7/7, JS 26 pass / 11 `[real]` skipped as planned | `goal.md` Commit row |
| Full unit suite and every acceptance script | not rerun after the merge: VIEW merged first of VIEW, TRANSFER and BUILDER, so the second one runs them | `merge-request.md` |
| Requirements | the node files are the source now (N-2.1, N-3.3, N-4.2, N-5); REQ-GA-045 Deferred (TD-91) | `merge-request.md` |
| Image | `localhost/mia-view-check:latest` still present; keep it until the Deploy smoke checks have passed, then the owner may remove it (V-15) | D-501 (4) |

## Deploy (a subgoal: no version, no tag)
The environment is the owner's host with the compose stack and Caddy (`/graph/` to the graph app, D-133). Steps by `deploy-phase`:
1. **Preflight** on the host: podman, the compose stack, Caddy route `/graph/`, `deploy/.env` with `MIA_DATABASE_URL`, the PostgreSQL container running, Firefox for the owner's look. Facts from the machine, not from this file.
2. **Install** from `goal/v4` with the scripted build (`deploy/build.sh`, as for v0.2.1; record in `specs/mia/deployment/deployment-record.md`). Ask the owner before replacing the running stack, and name the rollback (the previous image `localhost/mia:v0.2.1`).
3. **SMOKE-VIEW-001** `tests/smoke/smoke_view_image.py` (TR-VIEW-016): image built from `deploy/`, `store: database`, only `import psycopg` and `GET /api/v2/store` as the owner, writes nothing.
4. **SMOKE-VIEW-002** `tests/smoke/smoke_view_open_time.py` (TR-VIEW-017): opening time of `chain.fifty`, five openings after one warm-up, median and range in ms, measured only, no pass or fail.
5. **The owner's look in Firefox with `store: database`** (the exit criterion; the close look moved here from Commit, owner 2026-11-25). The list is in the report's "Notes for Commit, Deploy and Validate": keyboard only (V-1), drag then dark (V-2), log out then History and Previous (V-8), store stopped (V-10), MIA stopped and a click (V-11, now TD-91), `sample.broken` missing vs untrusted (TD-92 trigger), `chain.fifty` after `fit`, an empty store. Also the same graphs listed and drawn from files and from the database (exit criterion, OC-7).
6. Deployment record, then the Deploy row in `goal.md` (done, with the smoke results and the owner's look).

## Watch out
- **V-3 (handed to TRANSFER):** a PostgreSQL store never reconnects, and MIA doesn't start while the database is down. MIA runs on files until TRANSFER's gate (D-460). So the `store: database` runs here are for the smoke check and the owner's look; afterwards the stack goes back to `store: files` unless the owner decides otherwise. Ask before leaving it on the database. For the V-10 step (store stopped), expect no recovery after the database comes back: that is V-3, not a new finding.
- If the owner's look finds something: every finding gets a failing test first, then the fix, on a new branch off `goal/v4` (not `goal/v4.view`). If it is TD-92's mix-up, TD-92's trigger fires.
- Before a stack restart, check `ListAgents`: other sessions (TRANSFER, BUILDER, RUN) may use the same host.

## Then
Validate as the goal record says, in G-V5 (parked, D-386): VAL-VIEW-01, NFR-10 (first use without help), light and dark readability, the 220 px layers on large graphs.

## Shared state
- Other open subgoal branches off `goal/v4`: `goal/v4.graphstore.transfer` (carries V-3, `arrangements` and `graph_changes`, REQ-API-022's live fields), `goal/v4.graphapi.run`, `explore/builder-workflow` (D-520, small conflict in `review-log.md` and `high-level-spec.md` possible; keep both rows, ordered by decision number).
- Notes for EDIT and CODE are in `merge-request.md` ("Notes for other subgoals"): TD-91 to TD-94 trigger at EDIT's Plan, TD-95 belongs to CODE; deadline 2026-12-31 for all.

Next free numbers: D-503 (VIEW's block D-500 to D-519), A-176 (VIEW's block A-171 to A-184), TD-96, TR-VIEW-022, TC-API-026, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003.
