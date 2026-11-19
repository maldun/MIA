# Implementation log G-V2.SNAPSHOT (T-SN-01, formerly T-CV-05 of G-V2.CONVERT)

Branch `goal/v2.snapshot` from master `c939cc51` (protected tests of A-121 installed). Owner decision 2026-11-18 (Stefan Reiterer): the real provider is part of the task.

## Done
| Part | Commit | Result |
|---|---|---|
| `snapshot_store.py`: take, read, list, restore with the former state kept as `before restore of <name>` (suffix ` (2)` ...), pointer moves, trust and lifecycle written back with evidence `restore of <name>`, rollback of the items already changed, owner only (`Refused`), `Conflict`, `NotFound`, empty name `ValueError` | `007695aa` | `tests/acceptance/test_skill_snapshots.py` 8 of 8 (TC-WFM-061 to 066); new `tests/test_snapshot_store.py` 3 |
| `record_tables.py`: table `current_versions` (IF-302 v13): versioned, not deletable, `version` an integer >= 1, other fields kept | `9cb43b9a` | TC-IF-302-11 real variant green; `tests/test_record_tables.py` updated (the set of tables changed, one new test) |
| `workflow_library.py`: pointer (`set_current_version`, read without version = current, save = max+1 moving the pointer, `expected_version` against the current version, no pointer record = newest version), kind `skills` | `9b2d783b` | new `tests/test_library_pointer.py` 7 (real Storage, files); IF-203 v0 and v1 suites unchanged green |
| IF-102 v7 backend side | – | no code: both backends are generic (one `records` table with `tbl`, one folder per table, ids quoted), `Storage` takes its tables from `record_tables.definitions()`; `tests/test_storage_postgres.py` 43 of 43 on a throwaway postgres:16 |

## Not done: stopped, owner decisions needed
1. **The real variants of `test_if_203_v2_snapshots.py` cannot go green with the protected suite as written** (7 errors, 1 skip, all `invalid: record_identity`). Reasons, each checked:
   - The suite saves mock-shaped documents: a skill `{"name": i}` (IF-301 v2 wants `{"id", "data": {command, workflow_graph_id, context_graph_id}}`), a workflow `{"nodes": ["lookup"], "edges": []}` (nodes must be objects with `id` and `kind`; refused with `node_identity`). The real Storage refuses them, as it must. The suite needs documents valid for both providers (protected: needs an amendment by the owner).
   - **There is no table `snapshots`**: neither IF-302 v13 nor IF-301 v2 defines it, `Storage` answers `unknown_table`. The IF-203 v2 text says "writes one `snapshots` record" but no table holds it. A new table is a contract change (IF-302 v14 or IF-301), not mine to add.
   - **The owner is not known to the real library.** The adapter `_WorkflowLibraryAdapter` in `tests/helpers/contract.py` (protected) builds `WorkflowLibrary(Storage(...))` and passes no owner; the suite expects `anna` to be the owner and `ben` `forbidden`. Nothing in the production code names the owner (`owner_account` of `setup_cfg.json` is read nowhere; `Toolbox` takes `is_owner` from outside). The library needs an injected `is_owner` and the adapter must pass it.
   - `pins()` has no source in the real library (IF-203 says "the model pins in force (`eval-spec.md`)"; no module holds them as data).
2. **TC-IF-203-17 real (rollback) stays a skip**: the adapter proxies attribute reads to the library, but an assignment `lib.fail_set_current_version_at = 3` lands on the adapter, not on the library, so a seam on the library cannot be reached from the suite; adding the attribute would turn the skip into a false red. Left as it is.
3. **Two layers for the same operations.** The contract puts `snapshot`, `read_snapshot`, `list_snapshots`, `restore_snapshot` on the library (IF-203 v2); the acceptance tests (TC-WFM-061 to 066) test `SnapshotStore` on top of a library with the kind `snapshots`. `SnapshotStore` is built; the library-level operations are not (blocked by item 1). Once the table and the owner source are decided, the library methods can delegate to `SnapshotStore` (or the other way round): one decision for the owner.

## Decisions to see
- `expected_version` is checked against the current version (A-121), then the put runs without it; a concurrent writer between the two could be missed (the library has one process per Storage lock only). Accepted for now, same as the rest of the file backend.
- The pointer record carries `reason` (`save` or `set_current_version`); the author of a move is the author of the version record.
- `tests/test_record_tables.py` (not protected) changed: the exact set of tables now contains `current_versions`.
- The kind `skills` joined `KINDS` of the library; a skill record is a record of IF-301 v2 (`{"id", "data"}`).

## Tests run (venv mia312)
`test_skill_snapshots` 8, `test_snapshot_store` 3, `test_library_pointer` 7, `test_record_tables` 18, `test_workflow_library` 13, `test_converted_isolation` 2, `test_core_converted` 11, `test_conversion_record` 10, `test_convert_verify_fixes` 14, `test_harness` 30 (1 expected failure), `test_converted_tools` 11, `test_pipeline` 26, `test_checks` 48, `test_run_workflow` 12, `test_toolbox` 45 and acceptance 17, `test_skill_record_storage` 32, `test_skill_history` 5, `test_storage` 35, `test_storage_copy` 7, `test_storage_copy_semantics` 11, `test_library` 37, acceptance `test_common_operations` 6, `test_skill_conversion` 11, contract IF-203 v0 8, IF-203 v1 10, IF-102 24, IF-302 22, IF-301 8, `test_storage_postgres` 43: all green. `test_if_203_v2_snapshots` real variants: 7 red, 1 skip (item 1 and 2).

## Production fork (2026-11-19, branch `goal/v2.snapshot-prod`)
- `record_tables.py`: table `snapshots` (IF-302 v14, versioned, not deletable; name a non-empty text, time, author, items a list, pins a mapping; other fields kept). TC-IF-302-12 real green.
- `workflow_library.py`: `snapshot`, `read_snapshot`, `list_snapshots`, `restore_snapshot` delegate to `SnapshotStore` and map its errors to `conflict`, `forbidden`, `not_found`, `invalid/schema`; constructor `WorkflowLibrary(storage, costs=None, meta=None, is_owner=None, pins=None)` (no `is_owner`: nobody is the owner); `pins()`; seam `fail_set_current_version_at` (the n-th pointer move of a restore fails once with `unavailable`, then the way back works). `snapshots` is an internal kind (not in `KINDS`, so the graph API does not offer it).
- Contract: `test_if_203_v2_snapshots` 16 of 16 (TC-IF-203-17 real no longer skipped), `test_if_302_record_tables` 24 of 24. New `tests/test_library_snapshots.py` 6; `tests/test_record_tables.py` set of tables updated.
- Full unittest run: 2474 tests; failures only the two of `test_task_files_browser` (they fail on master too) and the table set, fixed here. `tests/test_storage_postgres.py` not yet run on this branch (slow podman start): the verifier runs it.
- Open: the race between the `expected_version` check and the put (see above) is unchanged.

## Verify round 1, F-03 and F-04 (2026-11-19, owner decision: fix F-03 and F-04, accept F-01)
- F-03: new test `test_f03_the_list_is_oldest_first_by_time_not_by_name` (snapshot "b" before "a", fake clock) kills the mutant that sorts by name. No code change.
- F-04: `InvalidName` (a `ValueError`) is the only error the library maps to `invalid/schema/name`; other `ValueError`s pass through. A stored snapshot is checked before the first write (`Malformed`: items not a list, kind unknown, id, version, a transform without trust or lifecycle): `invalid/schema/snapshot`, no automatic snapshot, nothing moved. A failure while changing items back is logged and the original error is raised.
- Tests: `tests/test_snapshot_store.py` 7, `tests/test_library_snapshots.py` 8; IF-203 v2 16, TC-WFM-061 to 066 8, `test_library_pointer` 7, `test_record_tables` 18 green.
- Not changed: F-01 (accepted candidate, same race class as the documented one), F-02, F-05, F-06, F-07 (left for the owner's decision in the report).
