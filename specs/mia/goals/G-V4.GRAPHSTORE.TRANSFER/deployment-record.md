# Deployment record: G-V4.GRAPHSTORE.TRANSFER → reference host (maldun's workstation)

**Kind:** subgoal (no version, no tag), smoke-only Deploy (D-460 (1), D-462)   **Commit:** `goal/v4` @ a1518a5a (TRANSFER merged at f6ccde75)   **Date:** 2026-11-27
**Goal:** G-V4.GRAPHSTORE.TRANSFER   **Deployed by:** Claude session, the owner chose each step (D-552)
**Runtime image:** `localhost/mia:g-v4-transfer`, id `2f6de35d4f4c40a81eeb11fea2ba797cffcef4aae964bb577172f8e77717793c` (built 2026-11-27 13:26 UTC from a clean export of the branch, before the fix commits). It differs from `goal/v4` in `graph_store_transfer.py` (the fixes), `deploy/preflight.sh` (F-2 fix) and two docs. `tools/smoke_in_stack.sh` runs the scripts of a read-only export of this checkout, so the smokes ran the merged code; the image supplies only Python 3.12 and psycopg 3. Not rebuilt (owner, D-552 (2)): rebuild from `goal/v4` when the live store moves to the database.
**Target:** Fedora (kernel 6.18), podman 5.7.1, network `mia_default`, stack database `mia_db_1` (PostgreSQL 16). The live stack `mia` stays down and on files; no model is involved.
**Configuration:** the worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4` with its `deploy/.env` (git-ignored; only its `MIA_DATABASE_URL`, passed through the environment). Database part replaced by `mia_smoke` by the smoke itself.

## Checks on `goal/v4` before Deploy (handover step 2)
| Check | Result |
|---|---|
| Traceability | 584 errors, as expected; none names a TRANSFER item |
| `tools/check_sysml_model.py`, `tools/check_sysml.sh` | OK; 4 files, 0 errors |
| `tests/acceptance/test_transfer_{backend,interrupt,move,sets,sync}.py` | all OK |
| `tests/test_storage_postgres.py` | 45 OK |
| `tools/contract_postgres.sh` | 12 OK |

RUN and BUILDER are not merged, so the unit suite and the other acceptance scripts were not rerun (handover step 2).

## Preflight
| Check | Result |
|---|---|
| network `mia_default`, image present | yes (`smoke_in_stack.sh` checks both) |
| `mia_db_1` | started with `podman start` after the owner's yes (D-552 (1)), healthy |
| Models (`preflight_agent.py`) | not run: TRANSFER changes no prompt, skill, pipeline or pin, and the smokes make no model call |

## Smoke tests
| Test | Result |
|---|---|
| SMOKE-TRANSFER-001 `smoke_transfer.py` (TR-TRANSFER-003, -007), through `tools/smoke_in_stack.sh --image localhost/mia:g-v4-transfer` | **green**, rc 0: round trip files → `mia_smoke` → files keeps every history; the lag names `cp2.multi` behind and `sample.code` differing, nothing else; after the sync the copy equals `mia_smoke`; the sync names one aside file that exists |
| SMOKE-RULES-001 `smoke_rules.py` (D-462), same way | **pass**, rc 0: the 15 skills `ready`; `sample.broken` refused naming `e2`, no step run |
| After the run | `mia_db_1` lists only `mia`, `postgres`, `template0`, `template1` (`mia_smoke` dropped); `mia_db_1` stopped again |

## Rollback
Nothing was installed: the live stack was not started and MIA's own database and files store were not written. The rollback of the live stack stays as in `specs/mia/goals/G-V4.VIEW/deployment-record.md` (`localhost/mia:g-v4-view`, `localhost/mia:v0.2.1`).

## Findings
None.

## Known issues
- The live store switch (owner's volume `mia-data` to the database, MIA on "live database + files copy") is a separate later owner gate after `tools/backup.sh` (D-460 (1)); it needs a rebuilt image (see above).
- Accepted deviations of Verify: D-549's lock limit, R-1, R-2.
- Questions for Validate (G-V5, parked, D-386): see "Notes for Deploy and Validate" in `merge-request.md`.

## Readiness for validation
Validate stays parked (G-V5, D-386).
