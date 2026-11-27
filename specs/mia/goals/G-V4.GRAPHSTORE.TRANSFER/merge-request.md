# Merge request: G-V4.GRAPHSTORE.TRANSFER, files and database interchangeable, move and sync

**Goal:** G-V4.GRAPHSTORE.TRANSFER (subgoal of G-V4.GRAPHSTORE, supervised)   **Branch:** `goal/v4.graphstore.transfer` → `goal/v4` (no version, no tag: a subgoal merge)
**Accepted by:** Stefan Reiterer (owner)   **Merged by:** the owner (agents hold no integration rights)
**TLS:** `specs/mia/goals/G-V4.GRAPHSTORE/top-level-spec.md` (FR-58, FR-59, FR-93, NFR-15, the move and sync part of NFR-16)   **HLS:** `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/high-level-spec.md` (HR-001 to HR-008)
**Goal record:** `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/goal.md`   **Plan:** `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/plan.md`
**Verification report:** `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/verification-report.md` (verified with accepted deviations; first Verify `1246c849` (D-547), re-verify of the fix commits `7607cca9`; both boxes ticked by the owner 2026-11-27, `3748d0c3`, `5b8e77ff`)
**Implementation log:** `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/implementation-log.md`
**Interfaces:** IF-102 v9 (A-186, text only; no IF-102 change otherwise), IF-104 v2 unchanged (VIEW's fixed store fields made real, REQ-API-064)
**Drafted:** 2026-11-27 by the agent (Commit phase); Merge: [ ] the owner

## What TRANSFER delivers
- **Move of the whole store** (`python -m MIA.migrate files-to-db` / `db-to-files`, `graph_store_transfer.move_store`): every record of every table arrives with its versions, authors and times. Each graph is checked with what the move brings, members go before their header, a damaged graph or one of an unknown kind stops the whole move (named, nothing written), and moving again changes nothing. Library export and seed carry the graph group (REQ-SLY-009).
- **Same behaviour on files and the database:** the same answers for the same saves, and durable file writes (fsync before replace).
- **Lag and one-way sync of a copy** (`migrate lag --copy DIR`, `sync --copy DIR`): the live store wins. The copy's own versions go to an aside file before a graph is cut back, and the answer names that file. One sync runs at a time (the copy's lock, also for a whole-store move into a copy). A rerun finishes an interrupted move or sync. Records no graph names are synced like a graph (A-196).
- **Side records and the one-graph move:** `graph_changes` and `arrangements` travel with their graph. `move_graph(source, target, graph_id)` is there for EDIT's keep (no caller in TRANSFER).
- **Portable sets:** the format marker `mia-store.json`. An older set without unscoped IDs is read; one with them is refused, naming MIGRATION's conversion; a newer set is refused. Both checks run on the source and the target. No absolute path of the machine is written into a set.
- **Copy setting in the backend** (`copy`, `autosync` in the configuration): graphs are read from the copy and written to the live store. A copy of a newer format falls back to the live store with a log line. AutoSync runs at start and at an orderly stop, and an unreachable live store is logged, not fatal. `GET /api/v2/store` gives the real `shown`, `live_reachable` and `lag`.
- **Handed over from VIEW:** F-1 (a file that is not a list of versions is refused in one line, not a traceback) and V-3 (a dropped PostgreSQL connection is opened again; MIA starts while the database is down).

## Commits per task
| Task / item | Commit(s) | Requirements |
|---|---|---|
| Plan: goal update, high-level spec, requirements by group, checks, A-186 (owner-installed `fbce1924`), seam with VIEW | `723f0f49` to `4cf5e5d0`, `fbce1924` | – |
| Red tests, tag `plan-baseline-g-v4-transfer` | `eb0030d9` | – |
| T-01 Move integrity and order | `bc2b100a` | REQ-SLY-016..021, REQ-SLY-009, REQ-GA-008 |
| T-02 Durable files, cut back | `dc373458` | REQ-SLY-022, 023, 038 |
| T-03 Lag, sync, aside, lock, commands | `901d7763` | REQ-SLY-024..028, 038, 039 |
| T-04 Side records, one-graph move, interruptions | `355c8826`, follow-up after VIEW's merge `5af24dc0` | REQ-SLY-029..031, 036, 030 |
| T-05 Portable sets | `73a32730` | REQ-SLY-032..035, 037 |
| VIEW brought in (`goal/v4` merged; T-06 unblocked) | `b18ec97a` | – |
| API red tests TC-API-060 to 064 (owner-installed) | `6750b808`, `943b8dac` | – |
| T-06 Copy setting, AutoSync, store answer | `92f7aa46`, stack configuration `4dd8f7b4` | REQ-API-060..064 |
| F-1 and V-3 of VIEW (handed over, D-501, D-503) | `76df87c4`, `3c2f39a1` | REQ-SLY-007; REQ-API-021, 050 |
| A-195 (REQ-API-064 changed, 065, 066 new; D-543 to D-546) | `52d3705d`, installed `d3024c15`, approved `ac8be86a` | REQ-API-064..066 |
| Verify, owner's answers | `1246c849`, `871e19f5` (D-547, D-548) | – |
| Fix V-1, V-3 after Verify | `a844df90`, `761de3a5` | REQ-SLY-028, 007; REQ-SLY-034 |
| A-196, A-197 (V-2, V-4) drafted, installed, implemented | `9ffbed95`, `5fd14c6d`, `7956272f`, model `dfb069cd` | REQ-SLY-024..027, 037 |
| Re-verify, signed off | `7607cca9`, `3748d0c3`, `5b8e77ff` | – |
| Commit phase: `goal/v4` merged in (docs only: `deploy/REQUIREMENTS_DB.md`, two line handovers) | `7eb2749b` | – |
| Commit phase: requirements and checks moved into the node files; model texts (V-6); D-551 | `9e06633b` | all 33 |
| Commit phase: test requirements staged, owner script | `e96c136a` | TR-TRANSFER-001..011 |

The history stays as it is, as for RULES and VIEW. The fix commits after Verify are separate `fix(storage)` commits naming their finding (`Task: ... Verify fix V-n`). Folding them in would rewrite history across six `goal/v4` merges and need a force push of the pushed branch. Nothing is squashed or rebased. The handover and plan commits are documents. **Content proof:** `git diff 5b8e77ff HEAD` (the signed-off state against now) touches no code, test, contract or eval file. It changes only `specs/`, `deploy/REQUIREMENTS_DB.md` (from `goal/v4`) and the new `tools/apply_merge_g_v4_transfer.sh`.

## Requirements implemented
33 requirements, all with the Status Approved (they were approved in Plan, and A-195, A-196 and A-197 were approved later). The owner sets **Verified**, because that is a gate status (see "What the owner runs", step 2). From this merge on, the node files are the source:
- `specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/requirements.md`: REQ-SLY-016 to 039 (groups MV, SB, SY, SR, PT and REQ-SLY-039 of AS; terms and groups in the section "Iteration 4 (goal G-V4.GRAPHSTORE.TRANSFER ...)"); REQ-SLY-009 changed in place (it was Verified in G-V1 and is Approved now in its changed form)
- `specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md`: REQ-API-060 to 066 (AS)
- `specs/mia/nodes/N-5-graph-app/requirements.md`: REQ-GA-008 changed in place (superseded by REQ-SLY-009, verified by inspection with TC-SLY-009); TC-GA-008 is retired

The checks, edge inputs, SMOKE-TRANSFER-001 and the scenarios are in the node test specs of N-3.1 and N-2.1 (stage 2, `tests/acceptance/test_transfer_*.py`). The witnesses of AC-004 to AC-008 and AC-033 are filled in `specs/mia/goals/G-V4/accepted-cases.md`. VAL-TRANSFER-01 stays in the goal record.

## Plan amendments
A-186 (IF-102 v9, text only), A-195 (the copy setting's behaviour: REQ-API-064 changed, 065, 066 new), A-196 (records no graph names synced like a graph, TC-SLY-040), A-197 (TC-SLY-037 searches every folder it made). All were installed by the owner. No frozen requirement was changed: `goal_check.py --spec-dir specs/mia --parent-ref goal/v4` reports no changed frozen item. Its 4 GL5 lines are old G-V2 items.

## Specification points written at the merge (D-551)
- V-6: the model texts of `WebApplication` and `storageLayer` now name what T-06, the fixes and A-196 built.
- REQ-SLY-039 gets a Detail line with the command texts: `lag` prints nothing when the copy is current; `sync` prints one more line per item set aside; a refusal prints one `refused: ... (nothing was written)` line and exits 1.
- The rationale of REQ-SLY-025 says what `lag.graphs` counts. The rationale of REQ-SLY-028 records D-549's reading of "the copy".
- The History lines say "changed" (A-195, A-196, A-197, the plan gate). The `In force:` lines are dropped in the node files.

## Agent changes (agent-app)
None. No skill, pipeline, prompt, eval suite, baseline or model pin is touched (`git diff goal/v4...HEAD -- skills library eval` is empty), so the quick eval subset does not apply and there is no new baseline.

## Checks on the merged branch (2026-11-27, venv `mia312`, after `7eb2749b`)
| Check | Result |
|---|---|
| Update with the target | `goal/v4` (`70dad886`, 4 docs-only commits) merged in at `7eb2749b`, no conflict |
| Unit suite | Ran 2649 in 474 s, OK (5 skipped, 2 expected failures) |
| Transfer acceptance files (`test_transfer_move`, `_sync`, `_sets`, `_interrupt`, `_backend`) | all OK; the PostgreSQL halves ran (no skip) |
| `tests/test_storage_postgres.py` | OK, none skipped |
| IF-102 contract suite on PostgreSQL 16 (`tools/contract_postgres.sh`) | 12/12 OK |
| `tests/js/*.test.mjs` | 233/233 |
| Model | after the move: 699 node requirements; `check_sysml_model.py` OK; `check_sysml.sh` 0 errors, 0 warnings |
| Unit tests that read spec files (`test_gen_node_requirements_model`, `test_amendment_report` and 4 more) | OK after the move |
| Traceability, before the move | 585 ERROR lines, the same as at Verify and the re-verify; none names a TRANSFER item |
| Traceability, after the move | 619: the 34 moved checks wait for their test requirements |
| Traceability, after the owner's script | **584**, shown on a scratch copy: TC-SLY-009 now has a test requirement too; none names a TRANSFER item |
| `goal_check.py` | 129 errors against 98 on `HEAD` before the move. The 31 new ones are GL2 in G-V4: moved requirements whose Parent is a goal-local HR item (for example REQ-SLY-016 → HR-004). This is the same pattern as VIEW's 16 and RULES'; G-V4's scope is decided at G-V4's gate |
| Siblings | `git merge-tree` against `goal/v4.graphapi.run` and `explore/builder-workflow`: no conflict today |

## What the owner runs
In this worktree (`/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-transfer`, branch `goal/v4.graphstore.transfer`):
1. `bash tools/apply_merge_g_v4_transfer.sh` to look at the diff (`--report` for the readable form), then `bash tools/apply_merge_g_v4_transfer.sh --do`. It prints how many trace errors name a TRANSFER check; expected: 0.
2. Set the 33 requirements to Verified in Emacs (`requirement-sign-all`, or `C-c r S` per item): REQ-SLY-009, REQ-SLY-016 to 039 (N-3.1), REQ-API-060 to 066 (N-2.1), REQ-GA-008 (N-5).
3. `git add specs/mia/test-requirements.md specs/mia/nodes && git commit -m "plan: TRANSFER test requirements installed, requirements Verified"`
4. `git push -4` (the branch tracks `origin/goal/v4.graphstore.transfer`).

In the parent's worktree (`/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4`, branch `goal/v4`):

5. `git status` (clean), then `git merge --no-ff goal/v4.graphstore.transfer`, then `git push -4`
6. Tick "Merge" above and record the merge commit in the goal's Phases row Commit (`done`, merge commit). The agent can do the record on request.

## Checks after the merge (on `goal/v4`)
- `python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests`: 584
- `python3 -I tools/check_sysml_model.py .` and `bash tools/check_sysml.sh`
- the five transfer acceptance files, `tests/test_storage_postgres.py`, `tools/contract_postgres.sh`
- whoever merges second among TRANSFER, RUN and BUILDER: the unit suite and every acceptance script one at a time

## Known issues / accepted deviations
- **D-549's lock limit:** a whole-store move takes the copy's lock only when the target already holds `sync.lock`. A folder never synced is not locked while its first sync and a move start at once.
- **R-1:** TC-SLY-037 doesn't search a record's aside file (new with A-196) for paths. By inspection, `_set_aside_record` writes no path.
- **R-2:** a graph ID with `|` is not forbidden by any rule; it could share a lag key with a record. No such ID exists today. This is a note for MIGRATION or the next goal that touches graph IDs.
- **`library-seed`** has no per-graph check (REQ-SLY-009 does not ask for it). The seed keeps put's record checks and the members-first order.
- G-V4 `goal.md` Frozen table, row IF-102: the reason "(scoped record IDs, sync)" is overtaken (TRANSFER needed no IF-102 change beyond A-186's text). This is the owner's decision at G-V4's gate.

## Notes for Deploy and Validate
- **Deploy:** only the smoke run on the throw-away database `mia_smoke` (D-460 (1)), with SMOKE-RULES-001 (D-462). SMOKE-TRANSFER-001 runs through `tools/smoke_in_stack.sh`. Don't run `deploy/up.sh` from a worktree without `deploy/.env`, because it writes a new one; start `mia_db_1` with `podman start`. Moving the owner's data to the database is a separate later owner gate after `tools/backup.sh`.
- **Validate** (G-V5, parked): with a copy that lacks skills, `lag.graphs` counts those skill records too; does the owner read that number as "graphs"? A save shows on the copy only after the next sync. Are AutoSync's refusal lines noticed?
