# Handover: G-V4 line, stale DB docs fixed (2026-11-27, night)

Supersedes `handover-2026-11-27-g-v4-preflight-smoke-done.md` for the session that picks the next G-V4 subgoal; everything there still holds except the items below. Worktree of this line: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4` (pushed by the owner up to `22f3c127`; `cd12668a` and this handover are not pushed yet). Read `CLAUDE.md` and this file; load `dev-workflow` and the phase skill of what you pick. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; only the owner pushes (`git push -4`).

## What this session did
| Item | Result | Record |
|---|---|---|
| Stale DB docs (owner's pick) | `deploy/REQUIREMENTS_DB.md` no longer names the missing `deploy/up.sh migrate`: item 7 gives the real command, `deploy/up.sh exec mia sh -c 'python -m MIA.migrate files-to-db --data MIA/data --database-url "$MIA_DATABASE_URL" --dry-run'` (database up with `deploy/up.sh db`; `db-to-files` back); the status line names what has been built since (storage layer, `db` service, `deploy/db/`, `migrate.py`). Checked in `localhost/mia:g-v4-view`: module and data path resolve (stops only at the missing `--database-url`). No real copy run (stack and `mia_db_1` stopped). | `cd12668a` |

## Waiting for the owner
- [ ] Push `goal/v4` (`git push -4`).
- [ ] RUN: REQ-GTB-060 (text changed twice, still Approved) and REQ-GTB-043 (Draft) in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run/specs/mia/goals/G-V4.GRAPHAPI.RUN/requirements.md`; A-189 as a joint amendment of IF-301.

## Next (pick one per session)
- **TRANSFER Verify**, in a fresh session: start prompt at the end of `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer/specs/mia/handover-2026-11-27-g-v4-transfer-verify-next.md`. Merge `goal/v4` there first (shared tools, F-2 fix, smoke runner); SMOKE-TRANSFER-001 can then run through `tools/smoke_in_stack.sh`.
- **RUN T-03** (`goal/v4.graphapi.run`, worktree `goal-v4-run`): `handover-2026-11-25-g-v4-run-t03-next.md` there; raise the packaging of `graph_run.py` at its next planning point (memory `graph-runner-packaging-in-run`). Merge `goal/v4` first.
- `explore/builder-workflow` (BUILDER, waits for RUN and CONTEXT, D-521); EDIT and CODE: notes in `goals/G-V4.VIEW/merge-request.md`, TD-91 to TD-95 (deadline 2026-12-31).
- Optional, small: the rest of `deploy/REQUIREMENTS_DB.md` (stages, decisions) is still written as a plan; only the migration lines and the status line were corrected.

## State of the host
Unchanged from `handover-2026-11-27-g-v4-preflight-smoke-done.md`: live stack `mia`, `mia_db_1` and `ollama` stopped; `mia-searxng` runs. Images as listed there (never overwrite `localhost/mia:latest`; build from a `git archive` export). This session only ran a throw-away `localhost/mia:g-v4-view` container (`--rm`).

## Next free numbers
Unchanged: TRANSFER D-547, A-196; RUN D-485, A-190; VIEW D-505, A-178; BUILDER D-522. This session took none.
