# Verification report: G-V4.GRAPHSTORE.TRANSFER (files and database interchangeable, move and sync)

**Goal:** G-V4.GRAPHSTORE.TRANSFER (subgoal of G-V4.GRAPHSTORE), supervised, accepted by Stefan Reiterer (owner)
**Branch:** `goal/v4.graphstore.transfer` @ 658f0141 (`goal/v4` @ 6a39dce3 merged in first, no conflict)   **Plan baseline:** `plan-baseline-g-v4-transfer` (eb0030d9); API red tests 943b8dac; A-195 installed d3024c15, approved ac8be86a
**Date:** 2026-11-27   **Reviewer:** an independent AI reviewer (Opus 5.5, fresh context, never saw the implementation chat; no subagents). No person has read this report yet.
**Decision record:** D-547 (this verification, `specs/mia/review-log.md`). The owner's answers to the questions below get the next free numbers (D-548 and up; amendments A-196 and up).

## Verdict
**Proposal: verified with accepted deviations, after one small fix (V-1) and the owner's answers on V-2 to V-5.** Every one of the 31 requirements in scope has a green check that I ran myself. Each check ran under its test requirements, with one gap in the path search (V-4). The protected material differs from the baseline only by the red API tests (943b8dac) and A-195 (d3024c15). Both match their staged drafts byte for byte. SMOKE-TRANSFER-001 is green on the owner's server. F-1 and V-3, handed over from VIEW, are fixed and stay fixed: a planted regression of either fails a check.

What remains:
- **V-1 (medium, Phase 3):** a whole-store move into a copy folder (`migrate db-to-files` / `files-to-db` with a files target) does not take the copy's lock. REQ-SLY-028 says "a sync or a move into the copy".
- **V-2 to V-4 (low, Phase 2 questions):** these are edge cases the plan does not decide. They cover graph-group records that no graph names (the open question of T-03), writing into an older set, and the path search of TC-SLY-037.
- **V-5 (medium for the owner, docs on `goal/v4`):** the migration command that `deploy/REQUIREMENTS_DB.md` item 7 now documents uses `--data MIA/data`. That is exactly the folder that F-1 now refuses. The store's folder is `MIA/data/db`.
- **V-6 (low):** the model's text still calls T-06 "planned".

- [ ] Verified by the owner (verdict, and the answers to the questions in "Owner's decisions" below). Date:

## Automated checks (all run by me, 2026-11-27, Python 3.12 venv `mia312`, node; scratch output under `/tmp/claude-1000/-home-maldun-prog-Python-MIA--claude-worktrees-goal-v4/05424c0e-29dd-4d3e-a583-210a12d5482a/scratchpad/`)
| Check | Result |
|---|---|
| Merge of `goal/v4` (6a39dce3) into the branch | clean, no conflict (658f0141) |
| Regression set `bash tools/regress.sh --out <scratch>/regress --base 943b8dac` (bytecode removed first, one run in this worktree) | unit suite **2645 tests OK** (skipped 5, expected failures 2). Acceptance scripts (76): red only the known `test_decide_guard.py` and `test_judge_calibration.py` (`behaviour.FUNCTIONS`, G-V3.REPORT F-3, red at the base too). Compared with 943b8dac, only `test_transfer_backend.py` (5 failures → OK) and `test_rules_rule_set.py` (red in the export only: it asks git) differ. All five TRANSFER acceptance files are OK. `test_skill_run_view_browser.py` is OK, and `test_sandbox` is OK inside the unit suite |
| `tests/test_storage_postgres.py` (throw-away postgres:16) | **45/45 OK**, none skipped (the V-3 reconnect check included) |
| IF-102 contract suite `MIA_DB_PYTHON=... bash tools/contract_postgres.sh` | **12/12 OK** on a throw-away postgres:16 |
| JavaScript tests `node --test "tests/js/*.test.mjs"` | 233/233 pass |
| SMOKE-TRANSFER-001 through `tools/smoke_in_stack.sh --image localhost/mia:g-v4-transfer --env-file <main checkout>/deploy/.env tests/smoke/smoke_transfer.py` | **4 PASS, exit 0**. `mia_db_1` was started with `podman start` (not `deploy/up.sh db`, which would have written a new `deploy/.env` into this worktree) and stopped again afterwards. The image was only the Python runtime; the code came from an export of this worktree. No image was built and `localhost/mia:latest` was not touched. I could not list the server's databases afterwards (no `postgres` role); the smoke drops `mia_smoke` by name and refuses any other name (TR-TRANSFER-007, inspected) |
| Traceability `trace_check.py --spec-dir specs/mia --tests-dir tests` | 585 ERROR lines, **line-for-line identical to `goal/v4`** (export at 6a39dce3); none names a TRANSFER item. The TRANSFER requirements show as WARN "in architecture.sysml but not in requirements.md" until the merge moves them into the node files (plan, "At the merge") |
| Model `check_sysml_model.py` / `check_sysml.sh specs/mia/architecture.sysml` | OK / 0 errors, 0 warnings |
| Lint, types, SAST | none configured (CLAUDE.md); security by inspection below |
| Real model runs | none (TRANSFER has no model step, no eval path) |

## Protected material (check 2)
- `git diff goal/v4 HEAD` on `tests/acceptance`, `tests/helpers`, `tests/smoke`, `tests/contract`, `benchmarks`, `eval`: the five `test_transfer_*.py`, `core_stores.py`, `transfer_stores.py`, `web_app_probe.py`, `smoke_transfer.py`. Nothing else.
- Seven of them are byte-identical to `red-tests/` (eb0030d9 for T-01 to T-05, 943b8dac for the probe). `test_transfer_backend.py` and the goal's `test-requirements.md` are byte-identical to `specs/mia/amendments/A-195/`, installed by the owner in d3024c15 and approved in ac8be86a. A-195 removed only docstring lines of TC-API-060 to 064 and changed none of their code.
- `skip` in the acceptance files: TC-SLY-030 (only while VIEW's side tables are missing; it ran, VIEW is merged) and TC-API-063/067 (only without psycopg; they ran). The PostgreSQL halves skip only without podman or the image; none skipped here.
- Count: the test spec has 33 checks plus SMOKE-TRANSFER-001. The acceptance files hold 32 test functions, because TC-SLY-029 and 036 are one function per run kind. All are present.

## Verification matrix
All methods are Test except REQ-GA-008 (Inspection). "Mine" = green in my regression run above; PG = the PostgreSQL half ran.

| Requirement | Check | Evidence | Result |
|---|---|---|---|
| REQ-SLY-016 | TC-SLY-016 | `test_transfer_move.py`, files and PG | pass |
| REQ-SLY-017 | TC-SLY-017 | `test_transfer_move.py` | pass |
| REQ-SLY-018 | TC-SLY-018 | `test_transfer_move.py`, files and PG | pass |
| REQ-SLY-019 | TC-SLY-019 | `test_transfer_move.py` | pass |
| REQ-SLY-020 | TC-SLY-020 | `test_transfer_move.py` | pass |
| REQ-SLY-021 | TC-SLY-021 | `test_transfer_move.py` (move and sync) | pass |
| REQ-SLY-009 (changed) | TC-SLY-009 | `test_transfer_move.py` | pass |
| REQ-GA-008 (changed) | inspection + TC-SLY-009 | `graph_app/` has no export or seed control (grep of `index.html` and the page scripts: no export or seed route or button) | pass |
| REQ-SLY-022 | TC-SLY-022 | `test_transfer_sync.py`, files and PG | pass |
| REQ-SLY-023 | TC-SLY-023 | `test_transfer_sync.py` | pass |
| REQ-SLY-024 | TC-SLY-024 | `test_transfer_sync.py`, files and PG | pass (see V-2b: a lone differing record is not listed) |
| REQ-SLY-025 | TC-SLY-025 | `test_transfer_sync.py`, files and PG; SMOKE-TRANSFER-001 | pass (see V-2a: a copy-only record outside every graph stays) |
| REQ-SLY-026 | TC-SLY-026 | `test_transfer_sync.py` | pass |
| REQ-SLY-027 | TC-SLY-027 | `test_transfer_sync.py` | pass |
| REQ-SLY-028 | TC-SLY-028 | `test_transfer_sync.py` (separate process, SIGKILL) | pass for the sync; **V-1**: a whole-store move ignores the lock |
| REQ-SLY-029, 036 | TC-SLY-029, 036 | `test_transfer_interrupt.py`, every write position, move / one-graph move / sync, files and PG | pass |
| REQ-SLY-038 | TC-SLY-038 | `test_transfer_interrupt.py`, files and PG | pass |
| REQ-SLY-030 | TC-SLY-030 | `test_transfer_sync.py` (VIEW's tables defined, not skipped) | pass |
| REQ-SLY-031 | TC-SLY-031 | `test_transfer_sync.py` | pass |
| REQ-SLY-032 | TC-SLY-032 | `test_transfer_sets.py` | pass |
| REQ-SLY-033 | TC-SLY-033 | `test_transfer_sets.py` | pass |
| REQ-SLY-034 | TC-SLY-034 | `test_transfer_sets.py` | pass (as source; **V-3** as target) |
| REQ-SLY-035 | TC-SLY-035 | `test_transfer_sets.py` | pass |
| REQ-SLY-037 | TC-SLY-037 | `test_transfer_sets.py`; inspection: aside file = graph, stamp, reason, header, members; marker = format only | pass; **V-4**: the check misses an absolute path outside home |
| REQ-SLY-039 | TC-SLY-039 | `test_transfer_sets.py` (class Commands) | pass |
| REQ-API-060 | TC-API-060 | `test_transfer_backend.py` (start and stop through `MIA.__main__`) | pass |
| REQ-API-061 | TC-API-061 | same | pass |
| REQ-API-062 | TC-API-062 | same | pass |
| REQ-API-063 | TC-API-063 | same (database address on a closed port) | pass |
| REQ-API-064 (changed, A-195) | TC-API-064, TC-API-067 | same | pass |
| REQ-API-065 | TC-API-065 | same | pass |
| REQ-API-066 | TC-API-066 | same | pass |

F-1 (VIEW Deploy) is held by `tests/test_migrate.py::test_a_file_that_is_no_history_is_one_line_not_a_traceback`. V-3 (VIEW Verify) is held by `tests/test_storage_postgres.py::test_a_dropped_connection_is_opened_again_on_the_next_call` (a real server-side drop with `pg_terminate_backend`) and `tests/test_web_app_live_store.py`. Both are green and both catch their planted regression (D10 to D12 below).

## Test requirements (M41)
| TR | Applies to | How I verified it | Met |
|---|---|---|---|
| TR-TRANSFER-001 exact values | 27 checks | read the assertions: whole histories, dicts and lists compared with `assertEqual`; no "contains" on results | yes |
| TR-TRANSFER-002 both backends, visible skips | 8 checks | the PostgreSQL halves ran (no skip lines); `core_stores.fresh_backend` skips with a reason | yes |
| TR-TRANSFER-003 sample store from fixtures | 14 checks | `transfer_stores.sample_store`: 15 converted graphs, `sample.code`, `context.cp13`, `cp2.multi` with four authors | yes |
| TR-TRANSFER-004 every write position, injector fires | TC-SLY-026, 029, 036, 038 | the counted writes are compared with an uninterrupted run (test code); the implementer's defects "header first", "removed first" failed, and my D9 also fails the sync checks | yes |
| TR-TRANSFER-005 times | 6 checks | copied times compared exactly; fixed clock where two saves are compared | yes |
| TR-TRANSFER-006 lock across processes | TC-SLY-028, 039 | `transfer_stores.hold_lock` is a separate process killed with SIGKILL | yes |
| TR-TRANSFER-007 throw-away only | 13 checks + smoke | temporary folders, `mia-core-test-<pid>` containers, `mia_smoke` only (smoke refuses other names) | yes |
| TR-TRANSFER-008 able to fail | 8 checks | implementer's mutation runs logged for T-01 to T-04; I re-planted equivalents for 023, 024/025/026, 028, 030 (D3, D4, D8, D9): all caught | yes |
| TR-TRANSFER-009 real start and stop | TC-API-060 to 067 | `web_app_probe.run_main` imports `MIA.__main__` of a checkout copy and calls `start_backend()` / `stop_list()` | yes |
| TR-TRANSFER-010 VIEW's parts | TC-SLY-030, TC-API-060 to 064 | VIEW merged; none skipped | yes |
| TR-TRANSFER-011 path search | TC-SLY-037 | **partly**: the named mutation ("an aside answer with an absolute path") is caught by TC-SLY-027, not by TC-SLY-037. An absolute path of the copy written into an aside file is caught by no check (D1). No TR-011 mutation run is logged in the implementation log | **V-4** |

### My deliberate defects (`verify-repro/defects.json`, run with `python tools/plant_defects.py`; every file restored, `git status` clean afterwards)
| Defect | Failing checks |
|---|---|
| D1 aside file holds the copy's absolute folder (REQ-SLY-037) | **NOT CAUGHT** (V-4) |
| D2 aside answer names an absolute path | TC-SLY-027 only |
| D3 side records not carried (REQ-SLY-030) | TC-SLY-030 |
| D4 sync without the copy lock (REQ-SLY-028) | TC-SLY-028, TC-SLY-039 |
| D5 a newer set opened (REQ-SLY-035) | TC-SLY-035, TC-API-065 |
| D6 an older set not refused (REQ-SLY-034) | TC-SLY-034 |
| D7 writes go to the copy (REQ-API-066) | TC-API-066 |
| D8 no folder fsync (REQ-SLY-023) | TC-SLY-023 |
| D9 "differs" read as "behind" (REQ-SLY-024) | TC-SLY-024, 025, 026, 027 |
| D10 F-1 regression | `test_migrate` F-1 check |
| D11 V-3 regression: no reconnect | `test_storage_postgres` V-3 check |
| D12 V-3 regression: live store opened at import | `test_web_app_live_store`, TC-API-063, TC-API-067 |
| D13 the stop sync after "close the database" | not caught; immaterial: `close_database(_votes_store)` closes the accounts store, not the graph backend the sync uses (note only) |
| D14 `since` = newest (REQ-API-064) | unit check "since over all lagging graphs" |

### Reproductions of V-1 to V-3 (`verify-repro/repro_sync_edges.py CHECKOUT`, files backend, throw-away folders; output on 658f0141)
```
V-1 move_store into a locked copy: written {'copied': 26, 'skipped': 0, 'added_versions': 0}
V-2a sync: {'graphs': 0, 'records': 0, 'set_aside': {}} lag after: {} orphan still on the copy: True graph group equal: False
V-2b lag before the sync: {}
V-2b sync refused: conflict {'table': 'graph_nodes', 'id': 'lonely.g/z'}
V-3 sync into an older copy: written {'graphs': 3, 'records': 32, 'set_aside': {}} marker now 1
V-3 move from it afterwards: refused invalid record_identity {'table': 'graph_nodes', 'id': 'n1', 'detail': 'id'}
```

## Goal acceptance (supervised goal: for information)
OC-1 (same answers): TC-SLY-022. OC-2 (sync on command, at start and at stop, nothing only-on-copy lost): TC-SLY-024 to 028, 039, TC-API-062. V-2a is an edge where the copy keeps a record, so nothing is lost, but the copy does not equal the live store. OC-3 (move both ways, repeat, damaged graph refused): TC-SLY-016 to 021. OC-4 (portable, older and newer sets): TC-SLY-032 to 035, 037. OC-5 (interruptions): TC-SLY-029, 036, 038. Nothing outside the goal's parts was touched by the task commits. The only exceptions are the follow-up commits named in the log (`deploy/setup_cfg.compose.json`, `README.md`, `setup_cfg.example.json`) and the shared tools from `goal/v4`. No stop condition was hit.

## Code against the architecture
- The one new module `graph_store_transfer.py` is listed under `Persistence.storageLayer` (N-3.1). `storage_files.py`, `storage_postgres.py`, `storage_copy.py` and `migrate.py` were already there. The web side (`web_app.py`, `graph_api_v2.py`, `__main__.py`) belongs to the web application.
- Dependencies: `graph_api_v2` → `graph_store_transfer.lag_summary` and `web_app` → `AutoSync` are the API → storage-layer direction that exists already (the web app uses IF-102). `graph_store_transfer` → `graph_rule_set.kinds()` is the registry of IF-301 v4, as the plan says. `storage_copy` does not import `graph_store_transfer` (`GRAPH_GROUP` moved there). No new flow is needed.
- IF-102 is unchanged (`cut` and `put_file` are backend operations beside it, A-186 text only). The fields of IF-104 v2 `GET /store` are unchanged in shape (REQ-API-022 with `live=None`; `create_app(..., *, live=None)` is keyword-only, D-470).
- **V-6:** the model's text is behind the code. `WebApplication` still says "G-V4.GRAPHSTORE.TRANSFER (planned) ... (REQ-API-060 to 064)". It names neither REQ-API-065 and 066 nor that T-06 is built. The `storageLayer` text ends at T-05 and does not name `lag_summary`, `AutoSync` or the reconnect of V-3.

## Specification vs. code (M42)
**Specified, not (fully) built:**
- V-1: REQ-SLY-028 "a sync or a move into the copy". `move_store` takes no lock. Only `sync_store` and `move_graph` do.
- V-2a: REQ-SLY-025 "every record of the graph group in the copy equal to its history in the live store". A record only on the copy that no header names and that is not in `live.ids` is left as it is, and the sync answers 0 graphs.
- V-3: REQ-SLY-034 "refuse to move or sync the set". The code checks the set only as the source. A sync or move into an older set writes the format-1 marker over it, and from then on the set is no longer recognised as older.

**Built, not specified (each already listed in the implementation log as unspecified behaviour; my proposal):**
- `sync` prints one line per set-aside graph; `lag` prints nothing when the copy is current. Proposal: add these command texts to REQ-SLY-039 at the merge (additive; no amendment of the check).
- The `refused:` line of a move names every graph. Same: command text under REQ-SLY-039 / REQ-SLY-007.
- `cut(…, 0)` removes the record; `put_file` takes a path relative to the root; `move_graph` locks only a files target. Internal, consistent with REQ-SLY-022, 027, 028: no item needed.
- The sync answer's `graphs` counts the graphs that were not current before the sync. Proposal: one sentence in REQ-SLY-025's rationale at the merge.
- A lone differing graph-group record refuses the whole sync (`conflict`). This is V-2b, an open question.
- `library-seed` keeps `copy_records`' checks without the per-graph check of REQ-SLY-017. REQ-SLY-009 does not ask for it; accept (open question 2).

**Tests mirror their scenarios:** I read TC-SLY-026, 028, 030, 031, 034, 037, 039 and TC-API-062, 063, 066 against `test-spec.md`. Each follows its Given / When / Then. The T-03 unit tests were written after the code (a logged deviation from test-first). The acceptance checks were red before, so I accept it.

**Security (inspection):** the aside file name comes from a graph ID that the record rules already checked, with `/` replaced, under `aside/` of the copy. The lock is `fcntl.flock` on `<copy>/sync.lock`. No subprocess or shell. The database URL is never printed (the AutoSync log names `host:port/db` without the password, `_live_name`). Writes with a copy set go to the live store and are guarded by the owner check as before. No finding.

**Usability (bad inputs, by inspection and the checks):** a non-history file, a newer set, an older set, a held lock, a missing folder and an unreachable database each give one line and exit code 1 in `migrate` (TC-SLY-039, the F-1 check). The `--data` help text "the data folder of the file storage" is what led to F-1. It still does not say that the store's folder is `accounts_dir` (default `data/db`). See V-5.

## Quality evidence per characteristic (M32, the goal's share)
| Characteristic | Evidence |
|---|---|
| Functional suitability | matrix above (31/31 green) |
| Performance efficiency | not in scope (no bound in the plan); the regression shows no slowdown that matters |
| Compatibility | TC-SLY-022 (same answers on files and PostgreSQL 16), TC-SLY-032 to 035 (format marker), IF-104 v2 contract suite green |
| Interaction capability | the store answer (TC-API-064, 067); the command lines (TC-SLY-039); V-5 (documented command) |
| Reliability | TC-SLY-023, 029, 036, 038 (durable writes, interruptions); V-3 reconnect; TC-API-063 (start without the live store) |
| Security | inspection above; no new trust boundary |
| Maintainability | one module per part, model consistent; V-6 (model text) |
| Flexibility | the backend choice and the copy setting are configuration only |
| Safety | `not now` (Q-2) |

## Open deferrals (M26)
None in TRANSFER. Out of scope by the goal: the live store switch (a later owner gate, D-460 (1)); the editor's view of a save under a copy (EDIT, FR-95).

## Review findings
| ID | Severity | Finding | Destination (proposal) |
|---|---|---|---|
| V-1 | medium | `move_store` (whole-store move, `migrate files-to-db` / `db-to-files`) into a files folder that is a copy does not take the copy's lock. A move during a running sync (or a sync during a move) is not refused. REQ-SLY-028 names "a move into the copy". TC-SLY-028 checks only the sync. Repro V-1 | Phase 3: a failing unit test first, then `move_store` under `_lock_of(target)`. Note for the fix: the lock file `sync.lock` then appears in every files target; check it against REQ-SLY-007's identical files (TC-SLY-007) |
| V-2 | low | Graph-group records that no header names (the open question of T-03). (a) A copy-only one stays after the sync: copy ≠ live (REQ-SLY-025), and the lag says current. (b) A differing one refuses the whole sync with `conflict`, while the lag lists nothing, so the owner sees "current" and a sync that fails (and AutoSync logs a refusal at every start and stop). They arise only from hand edits or foreign copies, because the copy is written only by the sync (REQ-API-066). Repro V-2a, V-2b | Phase 2 (owner question 1) |
| V-3 | low | A sync or move *into* an older set (no marker) with an unscoped record writes the marker `{"format": 1}`. A later move from that set then names `invalid`/`record_identity` instead of MIGRATION's conversion step (REQ-SLY-034 is checked on the source only, TC-SLY-034 likewise). Unscoped IDs existed only before A-167 (CORE development). Repro V-3 | Phase 2 (owner question 3) |
| V-4 | low | TC-SLY-037 searches only for the source folder's token and the home folder. An absolute path of the copy (under `/tmp`) written into an aside file passes (D1). The mutation that TR-TRANSFER-011 names is caught only by TC-SLY-027, and its run is not logged. The code itself writes no path (inspection) | Phase 2: amendment A-196 (protected test: TC-SLY-037 also searches for every folder root of the check), or accept with the inspection (owner question 4) |
| V-5 | medium (the owner would run it) | `deploy/REQUIREMENTS_DB.md` item 7 (fixed on `goal/v4` in cd12668a, answering the handover's open question) now documents `python -m MIA.migrate files-to-db --data MIA/data ...`. `MIA/data` is MIA's data folder. The store is `MIA/data/db` (`accounts_dir`), and since F-1 this command is refused at `presets/`. The `--data` help in `migrate.py` says only "the data folder of the file storage" | `goal/v4` line (docs commit, not TRANSFER's file): `--data MIA/data/db`; TRANSFER may sharpen the `--data` help when V-1 is fixed (owner question 5) |
| V-6 | low | `architecture.sysml` text: `WebApplication` still says T-06 "(planned)" and REQ-API-060 to 064 only; `storageLayer` does not name T-06 (`lag_summary`, `AutoSync`) or the V-3 reconnect | Commit (the merge updates the model text) |

Notes, no finding: the two flaky checks of the log were green in my one full run (`test_skill_run_view_browser.py` as an acceptance script, `test_sandbox` in the unit suite). `test_sandbox` counts `mia-sandbox-*` folders in the shared `/tmp`, so it can fail while another session runs; that belongs to the test-isolation backlog of `goal/v4`, not to TRANSFER. D13: the order "sync the copy" before "close the database" is not checked and does not matter today (different stores).

## Answers to the handover's open questions
1. The sync refuses a differing record that no graph names: V-2, owner question 1.
2. `library-seed` without the per-graph check: accept as built (REQ-SLY-009 does not ask; the seed keeps put's record checks and members-first order).
3. The extra `sync` line per set-aside graph: accept; write it into REQ-SLY-039's command texts at the merge (additive, the check stays).
4. V-3 checked with `pg_terminate_backend` (a real server-side drop): accept. My run of `test_storage_postgres.py` covers it, and D11 shows that the check fails without the reconnect. A stopped real container is the same event for the client (the connection closed by the server); the smoke ran on a freshly started `mia_db_1`.
5. A save is seen on the copy only after the next sync: as specified (REQ-API-066); the editor's view is EDIT's (FR-95). Note for Validate.
6. `deploy/REQUIREMENTS_DB.md` item 7: the missing `up.sh migrate` is fixed on `goal/v4` (merged here), but the new text has the wrong `--data` folder: V-5.
7. The two flaky checks: green in my run; see the notes above.

## Accepted-deviation candidates
V-2, V-3 and V-4 if the owner chooses "accept" in questions 1, 3 and 4; question 2 of the open questions (`library-seed`).

## Owner's decisions (prepared; batched by group, recommended option first)
**Group MV/SY (move and sync):**
1. *V-2, records no graph names:* (a) **recommended:** Phase 2 amendment. The sync treats such a record like a graph: the copy's own versions go to an aside file, then the record is cut back to the live history (removed if the record is only on the copy). The lag lists it as a row `records` with the record's ID. Then Phase 3. (b) Accept as a deviation, with one sentence in REQ-SLY-025 ("records named by a graph or a side record") and the lag listing lone differing records, so that a refused sync is not a surprise. (c) Accept as built.
2. *V-1, the lock of a whole-store move:* (a) **recommended:** Phase 3 fix (`move_store` under the copy's lock for a files target), with a failing unit test first. (b) Narrow REQ-SLY-028 to "a sync or a one-graph move" by amendment.

**Group PT (portable sets):**
3. *V-3, writing into an older set:* (a) **recommended:** Phase 3 under the existing REQ-SLY-034 (it says "move or sync the set"). `check_format` runs on the target of a move or sync too, before the first write. One unit test, no protected change. (b) Accept: no store of the owner holds unscoped IDs; MIGRATION notes it.
4. *V-4, the path search:* (a) **recommended:** amendment A-196. TC-SLY-037 also searches for the absolute roots of every folder the check made (protected test, owner script); D1 must then fail it. (b) Accept with my inspection of the code (aside and marker contents hold no path).

**Group AS / docs:**
5. *V-5:* (a) **recommended:** a docs commit on `goal/v4`: item 7 reads `--data MIA/data/db`, and the `--data` help of `migrate.py` says "the store's folder (`accounts_dir`, default data/db)" (the help text with V-1's fix on TRANSFER). (b) Leave it until Deploy of the live store switch.
6. *Verdict:* (a) **recommended:** verified with accepted deviations after V-1 (and V-3 if 3(a)) are fixed and re-verified on the fix commits only. (b) Verified with accepted deviations now, V-1 into the backlog.

## Notes for Commit, Deploy and Validate
- Commit: move the 31 requirements, checks and TR-TRANSFER-001 to 011 into the node files (plan, "At the merge"); update the model text (V-6); the command texts of REQ-SLY-039 (open question 3 above).
- Deploy: SMOKE-TRANSFER-001 is green on `mia_db_1` through `tools/smoke_in_stack.sh` (an image is needed only as a runtime with psycopg). Do not run `deploy/up.sh` from a worktree without `deploy/.env`: it writes a new one.
- Validate: what the owner sees after a save while a copy is shown (the save appears only after the next sync); whether AutoSync log lines are noticed when a sync is refused.
