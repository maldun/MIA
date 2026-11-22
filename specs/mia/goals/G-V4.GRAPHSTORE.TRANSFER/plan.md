# Plan: G-V4.GRAPHSTORE.TRANSFER (files and database interchangeable, move and sync)

**Goal:** `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/goal.md`   **Requirements:** `requirements.md` of this folder (29 new, 2 changed; approved 2026-11-22, D-466, D-467; they move into N-3.1 and N-2.1 at the merge)   **Test spec:** `test-spec.md`, `test-requirements.md` (approved 2026-11-22/23, D-468)   **Status:** Draft (2026-11-23, agent on the owner's delegation, D-468)

Line of work `goal/v4.graphstore.transfer` (worktree `../MIA-goal-v4-transfer`), merges into `goal/v4`; supervised. Six tasks as in the high-level spec, pure storage logic: no model step, no prompt, no eval suite, no new dependency, no new part, no new interface version (one new module `graph_store_transfer.py` in N-3.1; IF-102 v9 by A-186 is text only).

## Deployment and feedback (M51)
- Environment for the current-state deployment: the owner's host; SMOKE-TRANSFER-001 (`python tests/smoke/smoke_transfer.py`) on a throw-away database `mia_smoke` on his running PostgreSQL server, started only with his yes (D-460 (1)); SMOKE-RULES-001 runs with it (D-462). MIA itself keeps running on files: the live store switch is a later owner gate.
- Feedback slices: none beyond the tasks; the owner checked the behaviour on the prototype (rounds 02 and 03: AC-004 to AC-008).
- Living prototype (M46): `prototype/g-v4`, `graph_store_move.py` and `graph_store_sync.py` (adapt: the move checks with stored versions and writes members first, the sync cuts back instead of removing the header first, D-466).
- Source of each fact (P26): `requirements.md` of this folder → the generated block of `specs/mia/architecture.sysml` (D-420).

## Before the first task (the owner)
1. `bash tools/apply_amendment_a186.sh --do` (IF-102 v9, text only), commit "plan: A-186 installed".
2. `bash tools/apply_transfer_red_tests.sh --do` (four acceptance files, the helper `transfer_stores.py`, the extended `core_stores.py`, the smoke script), commit "test: TRANSFER acceptance tests (red)", tag `plan-baseline-g-v4-transfer`.
3. Tick the update of 2026-11-22 in `goal.md` (Agreement) and the plan gate below. Then Implement starts in a fresh session on this branch.

## Interface fixed by the red tests
- `graph_store_transfer` (stub in the branch with the names, constants and answers): `move_store(source, target) -> {"copied", "skipped", "added_versions"}`; `move_graph(source, target, graph_id) -> {"graphs": 1, "records": n}`; `lag(live, copy) -> {graph: {"live", "copy", "state", "reason"}}` (only graphs not current); `sync_store(live, copy) -> {"graphs", "records", "set_aside": {graph: {"versions", "file", "reason"}}}`; `copy_lock(root)`; `FORMAT = 1`, `MARKER = "mia-store.json"`, `LOCK = "sync.lock"`, `ASIDE = "aside"`, `CONVERSION_STEP`.
- Refusals: `StorageError("invalid", rule="move_refused", detail={"graphs": {id: [{"rule", "detail"}]}})` (`unknown_member`, `unknown_endpoint`, `unknown_kind` with the kind as detail); `StorageError("conflict", detail={"graph": id})` (one-graph move over the copy's own version); `StorageError("locked", detail={"lock": "sync.lock"})`; `StorageError("invalid", rule="older_format", detail={"table", "id", "conversion"})`; `StorageError("format", detail={"found", "known"})` from `FileBackend(root)`.
- Backends: `cut(table, id, version)` on both backends (keep versions 1 to n); `FileBackend.put_file(path, text)` (durable: fsync, rename, fsync of the folder); `FileBackend.append` writes the marker first into a set without one and flushes as REQ-SLY-023 says.
- Aside file (JSON): `{"graph", "set_aside_at", "reason", "header": [entries], "members": {"<table>|<id>": [entries]}}` (prototype format).
- `python -m MIA.migrate lag|sync --data DIR | --database-url URL --copy DIR`: `lag` prints one line per graph not current, `"%-40s live %-3d copy %-3d %s %s"`; `sync` prints `synced N records, set aside M graphs`; a refusal is one line, exit 1. (The stubs answer "not built yet", exit 1.)
- Not fixed yet: the backend side of TC-API-060 to 064. Their red tests are written when VIEW is merged into `goal/v4`; they come with their own owner script before T-06 (D-469). Agreed with VIEW (D-470): `graph_api_v2.create_app(backend, accounts_store, store, allowed_origins, *, live=None)`, keyword-only so VIEW's positional calls cannot shift; with `live=None` nothing changes (REQ-API-022). The start-up probe is TRANSFER's own helper `tests/helpers/web_app_probe.py`, a copy of VIEW's `WebAppProbe` and `checkout_with`; TRANSFER's tests never import `tests/acceptance/test_view_backend.py` (protected, TR-VIEW-015).

## State at the red commit
Scratch runs of 2026-11-23 from `red-tests/` against the stubs: every TRANSFER check fails by assertion (none by an import error or a crash), except TC-SLY-022, green from the start and to be kept green (CORE already answers alike on both backends), and TC-SLY-030, skipped until VIEW's side tables exist (TR-TRANSFER-010; green before Verify). CORE's save checks (`tests/acceptance/test_core_save.py`) stay green with the extended `FailingBackend`. The interruption checks fail on the write count first, so a run that writes nothing cannot pass (TR-TRANSFER-004).

Regression set: after every task the unit suite (`discover -s tests`) and every acceptance script one by one are green except the TRANSFER checks of later tasks and the known reds of `goal/v4`; the IF-102 contract suite unchanged and green.

## Tasks
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Move integrity and order | REQ-SLY-016 to 021, REQ-SLY-009 (changed), REQ-GA-008 (changed) | TC-SLY-016 to 020, TC-SLY-009; the move half of TC-SLY-021 | red tests installed |
| T-02 Durable files, cut back, the same answers | REQ-SLY-022, 023; the backend operations of REQ-SLY-038 | TC-SLY-022 (kept), TC-SLY-023 | T-01 |
| T-03 Lag, sync, aside, lock, commands | REQ-SLY-024 to 028, 038, 039 | TC-SLY-024 to 028, TC-SLY-038, TC-SLY-039, TC-SLY-021 whole | T-02 |
| T-04 Side records, one-graph move, interruptions | REQ-SLY-030, 031, 029, 036 | TC-SLY-031, TC-SLY-029, TC-SLY-036; TC-SLY-030 once VIEW is merged | T-03 |
| T-05 Portable sets | REQ-SLY-032 to 035, 037 | TC-SLY-032 to 035, TC-SLY-037 | T-03 |
| T-06 Copy setting, AutoSync, store answer, smoke | REQ-API-060 to 064; HR-004, HR-006 whole | TC-API-060 to 064 (red tests first, D-469); SMOKE-TRANSFER-001 on the branch | T-04, T-05, VIEW merged into `goal/v4` |

### T-01: Move integrity and order
- Implements: REQ-SLY-016 to REQ-SLY-021; the changes of REQ-SLY-009 and REQ-GA-008
- Tests to turn green: TC-SLY-016 to 020 and TC-SLY-009 (`tests/acceptance/test_transfer_move.py`); the move half of TC-SLY-021 (its sync half needs T-03)
- Touches: `graph_store_transfer.py` (`move_store`: the check of every graph against the source's members and kinds first, then all tables, graph group members first and headers last); `storage_copy.py` (`copy_records` keeps the conflict and record checks; export and seed take the graph group, members first); `migrate.py` (`files-to-db`, `db-to-files` go through `move_store`); unit tests
- Reuses: prototype `graph_store_move.py` (`move_store`, `_problems`, `GRAPH_TABLES`), adapted to the answers above and to `graph_rule_set.kinds()` for the kind
- Must not touch: protected material; `graph_tables.py`, `graph_rule_set.py`, `graph_model.py`
- Demonstrator after this task: `python -m MIA.migrate files-to-db` on a store with a damaged header names the graph and writes nothing
- Done when: the listed tests green, the regression set holds; the defects "each record checked alone" (TC-SLY-017, 018) and "headers before context steps" (TC-SLY-019) make their checks fail (logged, TR-TRANSFER-008)

### T-02: Durable files, cut back, the same answers
- Implements: REQ-SLY-022, REQ-SLY-023; `cut` on both backends and `FileBackend.put_file` (used by REQ-SLY-026, 032, 038)
- Tests to turn green: TC-SLY-023; TC-SLY-022 stays green (`tests/acceptance/test_transfer_sync.py`, class SameBehaviour)
- Touches: `storage_files.py` (fsync of the file, rename, fsync of the folder; `cut`; `put_file`), `storage_postgres.py` (`cut`: delete the versions above n in one statement); unit tests of both backends
- Must not touch: protected material; `storage.py` (no IF-102 operation), `graph_store_transfer.py` beyond calling the new operations
- Demonstrator after this task: a backend cut back to version 2 lists versions 1 and 2, on files and on the database
- Done when: the listed tests green; the defect "no flush" makes TC-SLY-023 fail (logged)

### T-03: Lag, sync, aside, lock, commands
- Implements: REQ-SLY-024 to REQ-SLY-028, REQ-SLY-038, REQ-SLY-039
- Tests to turn green: TC-SLY-024 to 028 (`test_transfer_sync.py`), TC-SLY-038 (`test_transfer_interrupt.py`), TC-SLY-039 (`test_transfer_sets.py`, class Commands), TC-SLY-021 whole
- Touches: `graph_store_transfer.py` (`lag`, `sync_store`: aside file through `put_file`, then cut back header first, then members, then the live versions members first; a graph only on the copy removed header first after its aside file; `copy_lock` with `fcntl.flock`); `migrate.py` (`lag`, `sync`); unit tests
- Reuses: prototype `graph_store_sync.py` (`lag`, `_set_aside`, `sync_store`), with the cut back of D-466 instead of `_remove_from` for a differing graph
- Must not touch: protected material; IF-102
- Demonstrator after this task: AC-006 and AC-007 by hand with `python -m MIA.migrate lag` and `sync`
- Done when: the listed tests green; the defects "removal before the aside file" (TC-SLY-026) and "header removed first" (TC-SLY-038) make their checks fail (logged)

### T-04: Side records, one-graph move, interruptions
- Implements: REQ-SLY-030, REQ-SLY-031, REQ-SLY-029, REQ-SLY-036
- Tests to turn green: TC-SLY-031 (`test_transfer_sync.py`), TC-SLY-029 and TC-SLY-036 (`test_transfer_interrupt.py`); TC-SLY-030 stays skipped until VIEW is merged and must then be green before Verify
- Touches: `graph_store_transfer.py` (`move_graph`: the lacking versions, members, `graph_changes`, `arrangements`, header last; `conflict` over the copy's own version; the side tables by the explicit list `GRAPH_GROUP`, present only where defined); unit tests
- Must not touch: protected material; VIEW's modules
- Demonstrator after this task: a new live version of `cp2.multi` reaches a copy alone with `move_graph`
- Done when: the listed tests green; the defect "one-graph move overwrites" makes TC-SLY-031 fail (logged)

### T-05: Portable sets
- Implements: REQ-SLY-032 to REQ-SLY-035, REQ-SLY-037
- Tests to turn green: TC-SLY-032 to 035 and TC-SLY-037 (`test_transfer_sets.py`, class Sets)
- Touches: `storage_files.py` (marker written before the first record into a set without one; a newer format refused when opened), `graph_store_transfer.py` (a set without a marker with an unscoped graph-group record refused naming `CONVERSION_STEP`); unit tests
- Must not touch: protected material; MIGRATION's conversion (not built here)
- Demonstrator after this task: a copied folder opens elsewhere with the same graphs; a folder with `{"format": 2}` is refused by name
- Done when: the listed tests green; the regression set holds (every write into a files store now adds the marker: the unit tests that compare folders file by file are checked, TC-SLY-007 stays green)

### T-06: Copy setting, AutoSync, store answer, smoke
- Implements: REQ-API-060 to REQ-API-064; HR-004 and HR-006 as a whole
- Before the code: the red tests of TC-API-060 to 064 are written on the then-merged VIEW (keyword-only `live=None` on `graph_api_v2.create_app`, D-470), with the new helper `tests/helpers/web_app_probe.py` (a copy of VIEW's probe), staged with their own owner script and installed by the owner (protected)
- Tests to turn green: TC-API-060 to 064; `python tests/smoke/smoke_transfer.py` passes on the branch against a throw-away server
- Touches: `graph_api_v2.py` (the `live` keyword and the real store fields), `web_app.py` and `__main__.py` (the configuration keys `copy` and `autosync`; the start steps and the stop list split out of `__main__` into two functions it calls, TR-TRANSFER-009; AutoSync before the first answer and in the stop list before the database is closed); unit tests
- Must not touch: protected material; the owner's live data; VIEW's requirements
- Depends on: T-04, T-05, VIEW merged into `goal/v4`
- Demonstrator after this task: MIA on a copy with AutoSync on shows `shown: copy` and the lag in `GET /api/v2/store`
- Done when: every TRANSFER check green (TC-SLY-030 included), the regression set holds with no known red of TRANSFER left

## At the merge (Commit phase, not a task)
- Move the 29 new requirements into the node files: REQ-SLY-016 to 039 into N-3.1, REQ-API-060 to 064 into N-2.1; replace REQ-SLY-009 in N-3.1 and REQ-GA-008 in N-5 with the approved changes; checks, scenarios and the smoke row into the node test specs; TR-TRANSFER-001 to 011 into `specs/mia/test-requirements.md` (owner script).
- Fill the Witness column of AC-004 to AC-008 and AC-033 in `specs/mia/goals/G-V4/accepted-cases.md` (test spec, first paragraph).
- G-V4 `goal.md` Frozen table, row IF-102: the reason "(scoped record IDs, sync)" is overtaken (no IF-102 change but A-186's text); the owner decides at G-V4's gate.

## Plan gate
- [ ] Plan package approved by maldun (owner): goal, high-level spec, requirements, checks and test code (red tests staged in `red-tests/`, A-186 staged). Date:
