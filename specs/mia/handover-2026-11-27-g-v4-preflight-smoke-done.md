# Handover: G-V4 line, REQ-GA-016 model block, F-2 fixed, smoke runner (2026-11-27, late)

Supersedes `handover-2026-11-27-g-v4-transfer-impl-done.md` for the session that picks the next G-V4 subgoal. Worktree of this line: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4` (pushed by the owner at `33d3244f`; `893240bb` and this handover are not pushed yet). Read `CLAUDE.md` and this file; load `dev-workflow` and the phase skill of what you pick. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; only the owner pushes (`git push -4`).

## What this session did
| Item | Result | Record |
|---|---|---|
| REQ-GA-016 | Approved by the owner (`4f85c406`); model block regenerated (A-176 text), `check_sysml_model.py` OK, `check_sysml.sh` 0 errors | `456d34ce` |
| F-2 of VIEW's Deploy, preflight half | `deploy/preflight.sh` checks a container-side `OLLAMA_URL` (`host.containers.internal`, `host.docker.internal`) through `127.0.0.1` on the same port and says so; test seen red first (`tests/test_preflight.py`, 8/8) | `f384b4cd`, `goals/G-V4.VIEW/deployment-record.md` (F-2) |
| F-2, smoke half | New `tools/smoke_in_stack.sh`: runs a smoke check in a throw-away container on `mia_default` over an export without `.env` files; the database URL goes through the environment only. No protected check changed (the smoke already takes the URL from the environment). Test `tests/test_smoke_in_stack.py` (stub podman, seen red first) | `33d3244f` |
| SMOKE-CORE-001 through the runner | Owner's yes: `mia_db_1` started, `bash tools/smoke_in_stack.sh --image localhost/mia:g-v4-view tests/smoke/smoke_core_graphs.py`: green (4 store checks, files removed, `mia_smoke` dropped; server lists only `mia`, `postgres`, `template0`, `template1`); `mia_db_1` stopped again | `893240bb`, deployment record F-2 |
| `CLAUDE.md` | Names `tools/smoke_in_stack.sh` (owner's yes) | `893240bb` |

## Waiting for the owner
- [ ] Push `goal/v4` (`git push -4`).
- [ ] RUN: REQ-GTB-060 (text changed twice, still Approved) and REQ-GTB-043 (Draft) in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run/specs/mia/goals/G-V4.GRAPHAPI.RUN/requirements.md`; A-189 as a joint amendment of IF-301.

## Next (pick one per session)
- **TRANSFER Verify**, in a fresh session: start prompt at the end of `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer/specs/mia/handover-2026-11-27-g-v4-transfer-verify-next.md`. TRANSFER should merge `goal/v4` first (shared tools, F-2 fix, smoke runner); its SMOKE-TRANSFER-001 can then run through `tools/smoke_in_stack.sh` instead of by hand.
- **RUN T-03** (`goal/v4.graphapi.run`, worktree `goal-v4-run`): `handover-2026-11-25-g-v4-run-t03-next.md` there; raise the packaging of `graph_run.py` at its next planning point (memory `graph-runner-packaging-in-run`). RUN should merge `goal/v4` to get the shared tools.
- `explore/builder-workflow` (BUILDER, waits for RUN and CONTEXT, D-521); EDIT and CODE: notes in `goals/G-V4.VIEW/merge-request.md`, TD-91 to TD-95 (deadline 2026-12-31).
- Small: `deploy/REQUIREMENTS_DB.md` item 7 names an `up.sh migrate` that does not exist (stale docs).

## State of the host
- The live stack `mia` is **stopped** (all `mia_*` containers exited, likely a reboot); `mia_db_1` stopped (started and stopped again for the smoke); the `ollama` container is **stopped** too (`0.0.0.0:11434` when it runs), so a real preflight fails P1 until it is started. `mia-searxng` runs. To start the live stack: `MIA_IMAGE=localhost/mia:g-v4-view` with `deploy/up.sh` in the `goal-v4` worktree (see `goals/G-V4.VIEW/deployment-record.md`); `store: files`.
- Images: `localhost/mia:latest` = RUN's branch build (`9206eeb93719`, never overwrite: `deploy/build.sh` tags `:latest`, so build other lines by hand with their own tag); `localhost/mia:g-v4-view` (`722a3cd0c480`, deployed; has psycopg 3, used by the smoke runner); `localhost/mia:g-v4-transfer` (`2f6de35d4f4c`); rollback `localhost/mia:g-v4-view-pre-theme`, `localhost/mia:v0.2.1`; keep `localhost/mia-view-check:latest`.
- Never build an image in a worktree that holds `deploy/.env` (`.containerignore` does not exclude it): build from a `git archive` export.
- The owner's database server is reached from the host only through a container on `mia_default` (no published port, by design): use `tools/smoke_in_stack.sh`.

## Next free numbers
TRANSFER: D-547 (block D-540 to D-559), A-196 (block A-195 to A-199). RUN: D-485, A-190. VIEW: D-505, A-178. BUILDER: D-522 (block D-520 to D-539). This session took none. Check `specs/mia/amendments/` and the review logs of every branch before taking one.
