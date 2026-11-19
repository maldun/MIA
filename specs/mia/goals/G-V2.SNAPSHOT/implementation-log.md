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

## Owner of the snapshots in the app (2026-11-19, owner decision: use `owner_account` from the config)
- `constants.OWNER_ACCOUNT_KEY = "owner_account"`; `accounts.owner_check(cfg)` gives `account -> bool`, true only for the account the entry names; a missing, empty or non-text entry names nobody. `web_app.py` builds `WorkflowLibrary(_votes_store, is_owner=accounts.owner_check(cfg))`. Before this every snapshot call in the running app was `forbidden`.
- The entry `owner_account` is named by the hint of `first_account.py` and `tools/accounts_cli.py`, but is not in `setup_cfg.example.json`; nothing else read it before.
- Test: `tests/test_owner_account.py` 5 (the key, the check, nobody without an entry, the real library follows the config, the wiring line of `web_app.py` read as text because the module cannot be imported in a test). `test_accounts`, `test_accounts_api`, `test_first_account`, IF-203 v2 green; `web_app.py` compiles.
- Not done: `pins` is still not given to the library in the app, so a snapshot stores `pins: {}`; the source of "the model pins in force" is undecided. No HTTP route calls the snapshot operations yet.

## Owner default: the first account (2026-11-19, owner decision: the first account is the owner by default, the setting can change it)
- Replaces the "nobody without an entry" rule above. `accounts.owner_check(cfg, store)`: a text `owner_account` wins (also when no such account exists: a typo makes nobody the owner, it does not hand the rights over); without a usable entry the owner is `accounts.first_account(store)`, the account whose first version is the oldest (a tie in the same second goes to the smaller name; accounts are not deletable). The owner is looked up at each call, so an account made after the start counts and a later account never takes over. `web_app.py` passes `_votes_store`.
- Test: `tests/test_owner_account.py` 7; `test_accounts`, `test_accounts_api`, `test_first_account`, `test_library_snapshots`, IF-203 v2 green.
- Known limit: the time has a resolution of one second (`utc_now`), so two accounts made in the same second are ordered by name, not by creation.
- Changing the owner means editing `owner_account` in `setup_cfg.json` (or `setup_cfg.local.json`) and restarting; no route or command changes it. REQ-WFM-066 says "the account that creates accounts": the first account satisfies it for a single owner.

## Pins of a snapshot from the config (2026-11-19, owner decision: build what was suggested)
- `workflow_library.pins_from_config(cfg)`: `{"MP-light": cfg["version_light"], "MP-full": cfg["version"]}`; an entry that is missing, empty or not a text leaves its pin out. No digests (deployment record) and no call to the model server, so a snapshot never fails because Ollama is down. Keys `MODEL_KEY`, `MODEL_LIGHT_KEY` in `constants.py`. `web_app.py`: `WorkflowLibrary(..., pins=lambda: pins_from_config(cfg))`. Shape as the contract and its mock: `{pin id: model name}`, no contract change.
- Test: `tests/test_model_pins.py` 5; `test_owner_account`, `test_library_snapshots`, `test_workflow_library`, IF-203 v0 and v2 green; `web_app.py` compiles.
- Limit: `cfg` is read once at start, so a changed model setting counts after a restart; the function form only keeps the library free of a stale copy.
- Still open: no HTTP route calls the snapshot operations.

## Verify round 2: F-08 and F-09 (2026-11-19)
- F-08 (medium, a regression of the owner commits): `owner_account` was read by the code but missing in `setup_cfg.example.json`, so `tests/test_config.py::Example::test_every_option_the_code_reads_is_in_the_example` failed. I had not run the whole suite after that commit. Fix: `"owner_account": ""` in the example (empty means the first account) and a paragraph "The owner" in `deploy/README.md` (login section). The existing test is the regression test (red before, green after).
- F-09 (low): `test_f09_every_kind_of_malformed_stored_snapshot_is_refused_and_changes_nothing` (7 shapes: items not a list or missing, unknown kind, id not a text, version a text or a boolean, item not a mapping). The four survivors of the round (kind, id type, version type, list check) each fail it now.
- Not changed: F-10 (reword of REQ-WFM-066 "the account that creates accounts", owner decision), F-11 (allowed by REQ-WFM-064), F-01, F-02, F-05, F-06, F-07.
- The full run after F-08 (2497 tests) showed one more failure caused by the same option: `tests/test_deploy.py::test_the_config_of_the_stack_lists_every_option_of_the_example` wants every option of the example in `deploy/setup_cfg.compose.json`. Fix: `"owner_account": ""` there too (test_deploy 19, test_config green). The two `test_task_files_browser` failures are the known ones of master.

## Verify round 2: F-01 fixed (2026-11-19, owner decision: fix F-01, accept F-02, F-05, F-06, F-07, F-10, F-11)
- F-01: a snapshot is written with `expected_version=0` in `WorkflowLibrary._put` (kind `snapshots` only), so the Storage refuses a second version atomically with `conflict`, also when two writers passed the name check together. Test (red before): `test_f01_a_snapshot_is_written_once_even_when_the_name_check_is_passed_by_a_second_writer` hides the existing name from `list_ids` and expects `conflict` and a history of one version; `test_f01_a_new_version_of_an_ordinary_item_is_still_allowed` keeps the other kinds as they are. IF-203 v0, v1, v2, TC-WFM-061 to 066 and the module tests green.
- Not fixed, accepted by the owner: F-02, F-05, F-06, F-07, F-10, F-11. The race between the `expected_version` check and the put for ordinary items (documented) is unchanged.
