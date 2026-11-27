# Handover: G-V4 line, TRANSFER through Implement, shared tools on goal/v4 (2026-11-27, evening)

Supersedes `handover-2026-11-27-g-v4-view-deploy-done.md` for the session that picks the next G-V4 subgoal. Worktree of this line: `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4` (pushed by the owner at `902219c4`). Read `CLAUDE.md` and this file; load `dev-workflow` and the phase skill of what you pick. Ways of working: decisions as a questionnaire, recommended option first; full absolute paths; the owner signs, the agent never sets Approved; only the owner pushes (`git push -4`).

## What this session did
| Line | Result | Record |
|---|---|---|
| TRANSFER (`goal/v4.graphstore.transfer`, worktree `goal-v4-transfer`) | `goal/v4` (VIEW) merged in; red tests TC-API-060 to 064 (owner-installed `943b8dac`); T-06 (copy setting, AutoSync, store answer) `92f7aa46`; SMOKE-TRANSFER-001 green on the owner's server; F-1 of VIEW's Deploy fixed `76df87c4`; V-3 of VIEW's verification fixed `3c2f39a1`; amendment A-195 (REQ-API-064 changed, 065, 066 new) installed and approved; image `localhost/mia:g-v4-transfer` (`2f6de35d4f4c`); **Implement done** | `goals/G-V4.GRAPHSTORE.TRANSFER/implementation-log.md`, `handover-2026-11-27-g-v4-transfer-verify-next.md` (on the TRANSFER branch), D-540 to D-546 |
| `goal/v4` | `tools/regress.sh` (regression set, one run per worktree) and `tools/plant_defects.py` (deliberate defects, restore byte for byte, bytecode removed around each run) with `tests/test_plant_defects.py`; both named in `CLAUDE.md` (owner's yes) | `803e8088`, `5f1ba2e3`, `902219c4` |
| Owner's decision | Packaging `graph_run.py` for re-use belongs to G-V4.GRAPHAPI.RUN; ask there what "re-use" means (memory `graph-runner-packaging-in-run`) | chat, 2026-11-27 |

Lesson behind the tools: a deliberate defect restored with the same size within the same second left stale bytecode, so later checks ran the defect (TRANSFER T-06 finding). Use `tools/plant_defects.py` instead of hand-made sed and copy scripts.

## Waiting for the owner
- [x] REQ-GA-016: approved by the owner (`4f85c406`); model block regenerated and checked (`456d34ce`). The goal copy in `goals/G-V4.VIEW/requirements.md` holds only the group table row, no status.
- [ ] RUN: REQ-GTB-060 (text changed twice, still Approved) and REQ-GTB-043 (Draft) in `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-run/specs/mia/goals/G-V4.GRAPHAPI.RUN/requirements.md`; A-189 as a joint amendment of IF-301.

## Next (pick one per session)
- **TRANSFER Verify**, in a fresh session: start prompt at the end of `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer/specs/mia/handover-2026-11-27-g-v4-transfer-verify-next.md`.
- **RUN T-03** (`goal/v4.graphapi.run`, worktree `goal-v4-run`): `handover-2026-11-25-g-v4-run-t03-next.md` there; raise the packaging of `graph_run.py` at its next planning point. RUN should merge `goal/v4` to get the shared tools.
- ~~F-2 of VIEW's Deploy~~: fixed on `goal/v4` (`f384b4cd`), recorded in `goals/G-V4.VIEW/deployment-record.md`. The smoke half (`db` of `MIA_DATABASE_URL` resolves only on the stack network): `bash tools/smoke_in_stack.sh --image localhost/mia:g-v4-view tests/smoke/smoke_core_graphs.py` (the stack's `db` must run); no protected check changed.
- `explore/builder-workflow` (BUILDER, waits for RUN and CONTEXT, D-521); EDIT and CODE: notes in `goals/G-V4.VIEW/merge-request.md`, TD-91 to TD-95 (deadline 2026-12-31).
- `deploy/REQUIREMENTS_DB.md` item 7 names an `up.sh migrate` that does not exist (stale; whoever owns the deploy docs).

## State of the host
- The live stack `mia` is **stopped** (all `mia_*` containers exited about 13 hours before this session; likely a reboot); `mia-searxng` runs; `mia_db_1` stopped (started and stopped again for the smoke). To start the live stack again: `MIA_IMAGE=localhost/mia:g-v4-view` with `deploy/up.sh` in the `goal-v4` worktree (see `goals/G-V4.VIEW/deployment-record.md`); `store: files`.
- Images: `localhost/mia:latest` = RUN's branch build (`9206eeb93719`, never overwrite: `deploy/build.sh` tags `:latest`, so build other lines by hand with their own tag); `localhost/mia:g-v4-view` (`722a3cd0c480`, deployed); `localhost/mia:g-v4-transfer` (`2f6de35d4f4c`); rollback `localhost/mia:g-v4-view-pre-theme`, `localhost/mia:v0.2.1`; keep `localhost/mia-view-check:latest`.
- Never build an image in a worktree that holds `deploy/.env` (`.containerignore` does not exclude it): build from a `git archive` export.
- The owner's database server is reached from the host only through a container on `mia_default` (no published port, by design).

## Next free numbers
TRANSFER: D-547 (block D-540 to D-559), A-196 (block A-195 to A-199). RUN: D-485, A-190. VIEW: D-505, A-178. BUILDER: D-522 (block D-520 to D-539). Check `specs/mia/amendments/` and the review logs of every branch before taking one.
