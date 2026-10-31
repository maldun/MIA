# Implementation log: Storage layer (N-3.1)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Storage interface and file backend | done | `feat(storage)` | `tests/test_storage.py` (12 tests: TC-SLY-002, TC-SLY-003 with 500 seeds, TC-SLY-006 files, IF-102 errors, odd ids and text, parallel writers); IF-102 contract suite with `Storage(FileBackend)` as real provider (scratch run, 16 tests, no skip) | one commit with T-02 |
| T-02 Validation hook | done | `feat(storage)` | same file: TC-SLY-004 and the refused edit that consumes no version | validation is the table definitions of IF-301 and IF-302 |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| The file backend must not let an id such as `..` or `a/b` leave its table folder | T-01 | `test_ids_with_odd_characters_and_text_byte_for_byte` |
| Two threads writing one record could get the same version number | T-01 | `test_parallel_writers_never_get_the_same_version` (a lock around read-modify-write) |
| The delete rule must follow the definitions of IF-301 and IF-302 (votes and accounts are not deletable), not only "workflows and context_graphs" as the text of IF-102 says | T-01 | `test_only_the_tables_that_allow_it_can_be_deleted`; the IF-102 spec text is narrower than REQ-RTB-001: no conflict in the suite, noted for the owner |

## Reuse check (owner rule: use existing code)
- Reused: `chat_log.utc_now()` for the time of a version, the atomic write pattern of `content_store.py` (temporary file, then rename), `graph_tables` and `record_tables` for tables, deletability and validation.
- New: `storage.py` (the rules), `storage_files.py` (the file backend). The old stores (`chat_log.py`, `preset_store.py`, `gesture_store.py`, `skill_store.py`) are not changed; they move behind the Storage layer in the N-2 tasks.

## Plan amendments
None.

## Decisions
- `Storage` raises its own `StorageError(code, rule, detail)`. The contract suite expects the class of the mock (`tests/helpers/mocks/errors.py`); the adapter of the integration step translates it (the scratch run used a ten-line adapter). Production code does not import from `tests/`.
- The lock is per process. Several instances on one folder are what the PostgreSQL backend is for (T-06); the file backend stays single-process.

## Open questions for Phase 4 and the integration step
- Real provider for the IF-102 suite: an amendment of `tests/helpers/contract.py` at integration step 3 of N-3 (owner), with the error translation above.
- Text of IF-102: "immutable for workflows and context_graphs" should read "for the tables that are not deletable (IF-301, IF-302)". Proposal for an amendment of the spec text, no test changes.

## T-03 Accounts (added)
- Done: `accounts.py` (scrypt of the standard library, N=2^14, r=8, p=1, a random salt per account, the parameters stored with the hash) and `tests/test_accounts.py` (5 tests: TC-SLY-005, a password change is a new version, empty input and duplicates refused, non-ASCII passwords). No existing account code in the repository (reuse check: nothing to reuse). Unknown accounts cost one hash, so a login attempt does not reveal which names exist by timing. Reported green: 5 tests. Who may create accounts is REQ-BE-011 (Backend), throttling REQ-API-004.

## T-04 Library export and seed, T-05 Migration command (added)
- Done: `storage_copy.py` (`copy_records`, `export_library`, `seed_library`), `migrate.py` (one command per direction and for the library), `tests/test_storage_copy.py` (6 tests) and `tests/test_migrate.py` (5 tests): TC-SLY-009, TC-SLY-007 file side (a to b to c identical file by file in canonical JSON), idempotent second run, appending only missing versions, a different history is a conflict that writes nothing, dry run, usage errors. Reported green: 11 tests.
- Design: export, seed and both migration directions are one operation on the raw version lists, so a copy is identical to its source (authors and times included) and nothing is renumbered. The database side of `migrate.py` imports `storage_postgres` only when it is used (T-06); the tests use the file backend as a stand-in through `open_db`.
- Plan said T-04 touches `storage.py` and a `tools/` script: the logic lives in `storage_copy.py` and the command in `migrate.py` (one command for both), `storage.py` stays unchanged. No plan change needed.
- Reuse check: the library "as it is today" (`library/nodes`, `library/pipelines`, content-addressed files with a status file) is the old pipeline format and is not part of the new `workflows` table; seeding the five example workflows is root task T-10. Nothing to reuse here.

## Gap for the owner (not covered by any N-3 task)
- The legacy file stores (`data/chat_log.jsonl`, `memories.json`, `feedback_log.jsonl`, presets and gestures as one JSON file per name, `moods.json`) have their own formats. Moving their content into the new tables (and back, so that "the data folder identical file by file" also holds for a real MIA data folder) needs an importer per store. The plan puts "moving the old stores behind the Storage layer" in later N-2 tasks; the importers for the migration command are not named there. Proposal: add them as part of those N-2 tasks (each store gets `to_records` and `from_records` next to its code, tested with the fixtures) and add one test per store to `tests/test_migrate.py`.

## T-06 PostgreSQL backend (added)
- Done: `storage_postgres.py` (one `records` table of versions, `deploy/db/001_records.sql` applied once by number, LISTEN/NOTIFY notices), `requirements-db.txt` (`psycopg[binary]>=3.2,<4`, approved D-54), `tests/test_storage_postgres.py` (17 tests on a throwaway `postgres:16` container with data on tmpfs). The behaviour tests of the file backend are a mixin (`StorageBehaviour` in `tests/test_storage.py`) and run unchanged on both backends: TC-SLY-002, -003 (500 seeds), -004, the IF-102 errors; plus TC-SLY-006 (20 writes, second instance hears each once, median and maximum at most 2 s), TC-SLY-007 (files to database and back through `migrate`), two instances writing one record never share a version, the schema is applied once. The IF-102 contract suite with `Storage(PostgresBackend)` as real provider (scratch adapter): 16 of 16 tests, TC-SLY-001 reported green.
- Reuse: the entries and all rules are the code of T-01 (`Storage`); the backend only stores and reads entries. `migrate.py` opens it by name (`storage_postgres`) as planned.
- The tests run with the python that has psycopg (a scratch venv from `requirements.txt` plus `requirements-db.txt` on Python 3.12). They skip with a reason without psycopg, podman or the image; the skip is not a weakening.

| Finding | Task | Covered by test |
|---|---|---|
| The contract suite (TC-IF-102-06) expects the notice when `put` returns; a database notice arrives a moment later (within the 2 s bound). The writer's own subscribers are therefore told at once and the channel carries the notice to the other instances only, tagged with an origin id | T-06 | `test_a_subscriber_is_told_once_per_write...` (files) and the contract suite on PostgreSQL; `test_a_write_on_one_connection_is_heard_on_the_other_within_2_s` |
| Two instances can race on the next version number; the primary key refuses the second and the loser gets `conflict` with the current version | T-06 | `test_two_instances_writing_the_same_record_never_share_a_version` |
| A listener thread must end quietly when the server goes away | T-06 | observed while stopping the container; the loop catches `OperationalError` |

## T-07 Backup and restore (added)
- Done: `tools/backup.sh` and `tools/restore.sh` (scripts, not a list of steps) and `tests/test_backup.py` (3 tests, TC-SLY-008): 50 records with an extra version plus a data folder with a subfolder and non-ASCII text; backup; wipe both; restore: the same rows (table, id, version, author, time, document) and the same files. The archive holds `db.dump` (pg_dump custom format) and `data.tar`. A restore first checks the archive (a foreign archive changes nothing), then saves the state before it as `mia-before-restore-<time>.tar.gz`, the same convention as `deploy/up.sh restore`. Reported green: 3 tests.
- Reuse: the safety copy before a restore and the naming follow `deploy/up.sh backup|restore` (which keeps covering the compose data volume); the throwaway database of `test_storage_postgres.py` is the test fixture.

## T-08 Container, network and compose service (added)
- Done: service `db` in `deploy/compose.yaml` (profile `db`, `postgres:16`, volume `pgdata`, health check `pg_isready`, no published port, the schema of `deploy/db/` mounted as the init script, password from `.env`), `deploy/up.sh db` (also the database; makes `POSTGRES_PASSWORD` and `MIA_DATABASE_URL` once in `.env`) and `deploy/up.sh db-only` (only the database, returns at once), `MIA_DATABASE_URL` passed to the `mia` service, `tests/test_database_stack.py` (5 tests: 3 on the compose file, 2 with real containers). Reported green: 5 tests in 24 s, no skips.
- TC-SLY-010: no port is published; connections from `127.0.0.1`, the LAN address and the container address are refused; a container on another network gets no answer; a container of the stack connects as `db`. TC-SLY-011: a container started alone with the same settings and the stack give the same tables (`records`, `schema_version`), both ready, the health check passes.
- The stack without the profile is unchanged (test). `up.sh db` and `db-only` were tried in a scratch copy of `deploy/` (project `mia-test-upsh`), not on the real project: password and URL made, database healthy, port not published; the scratch stack was removed.
- Reuse: the `ollama` profile pattern of `up.sh`/compose, the `.env` handling and the project name `MIA_PROJECT`. New: the service, the `db`/`db-only` arguments.
- Not done here (belongs to the N-2 wiring): the `storage` option in `config.py` that picks the database from `MIA_DATABASE_URL`.

## Hand-over of N-3.1
All eight tasks are done; every task has a commit and tests. Open for the integration step of N-3 (owner, amendments): the real providers in `tests/helpers/contract.py` for IF-301, IF-302 and IF-102 (error class translation), and the text of IF-102.

## Verify findings (verification-report.md, decisions D-158), branch v1-n31b
Each fix is test-first: the new test was red before the change and green after (reported, not verified).

| Finding (report) | Fix | Covered by test (red before) |
|---|---|---|
| F1 seed and migrate wrote without validation or version check | `storage_copy.copy_records` checks every version of the source before the first write: the entry's `id` is the record's, versions run 1..n, each document passes `storage.validate` (the function `put` uses, now module level). A refused record refuses the whole copy with `invalid` (rule, `detail.table`, `detail.id`); `migrate.py` prints "refused: table/id (rule: detail) (nothing was written)", exit 1 | `test_storage_copy.test_a_seed_with_an_invalid_document_or_a_gap_in_the_versions_is_refused_and_writes_nothing`, `test_migrate.test_a_record_that_put_would_refuse_is_named_and_nothing_is_moved` |
| F2 a raising subscriber stopped the notices; the PostgreSQL listener died on it and on a dropped connection | `Storage._dispatch` catches and logs (logger `storage`) per subscriber, so the others, the write and `publish` go on. `PostgresBackend` listens in a loop that opens the connection again 1 s after the server drops it (a database restart); the notices sent in that gap are lost (no catch-up: REQ-SLY-006 says nothing about it, open question below); a notice that fails is logged, not fatal | `test_storage.test_a_raising_subscriber_does_not_stop_the_others_or_the_write` (files and PostgreSQL), `test_storage.test_a_raising_subscriber_does_not_stop_the_notice_to_the_other_instances`, `test_storage_postgres.test_a_raising_subscriber_does_not_end_the_listener`, `test_storage_postgres.test_the_listener_connects_again_when_the_server_drops_it` (the server ends the LISTEN connection with `pg_terminate_backend`) |
| F3 `accounts.create` could overwrite an account under a race | `create` writes with `expected_version=0` and turns `conflict` into the ValueError "the account exists" | `test_accounts.test_a_second_create_that_lost_the_race_is_refused_and_keeps_the_first_password` (a store with a stale list of ids) |
| F4 `migrate.py` never closed the database (psycopg ResourceWarning in TC-SLY-007) | `main` closes the opened database in `finally`, also after a refused copy; `FileBackend.close()` (nothing to release) so every backend can be closed. The protected `_StorageAdapter` of `tests/helpers/contract.py` stays as it is (D-158); its 7 warnings on PostgreSQL remain | `test_migrate.test_the_database_is_closed_after_a_run_and_after_a_refused_one`; `test_storage_postgres.SharedDatabase` with `-W always::ResourceWarning`: 0 warnings |
| F7 a delete sent no notice (D-158: it does, as IF-102 says) | `Storage.delete` tells its subscribers and the shared channel `{"table","id","version": None,"author"}` after the record is removed, through the same `_tell` as `put`, so the file and the PostgreSQL backend behave the same; a refused delete tells nothing. The shape (version None) was the verification's proposal; A-59 puts it into IF-102 and the mock (draft, not installed) | `test_storage.test_a_delete_is_a_change_and_is_told_with_version_none` (files red before; PostgreSQL through the mixin), `test_storage_postgres.test_a_delete_on_one_instance_is_heard_on_the_other` |
| F8 `--dry-run` ignored by `library-export` and `library-seed` | the four commands share one path (`_copy`), so the dry run writes nothing for all of them; `migrate.py` no longer goes through `export_library`/`seed_library` (they stay for the library code and its tests) | `test_migrate.test_a_dry_run_of_the_library_commands_writes_nothing` |
| F9 a NUL character: stored by the file backend, a raw `psycopg.errors.UntranslatableCharacter` on PostgreSQL | `storage.refuse_nul` refuses NUL in the document (keys included), the id and the author with `invalid`, rule `schema`, on every backend; `copy_records` checks the same | `test_storage.test_a_nul_character_is_refused_on_every_backend` (files and PostgreSQL) |
| F10 (the user-facing part of F8 to F9) raw traceback for an unreachable database, "copied 0 records" for a misspelt folder | `migrate.py`: "cannot open the database: <first line>" (also without psycopg), "no such folder: X" for a missing source folder (`files-to-db`, `library-export`: `--data`; `library-seed`: `--folder`), exit code 1 each | `test_migrate.test_a_missing_source_folder_or_an_unreachable_database_is_one_line_and_exit_code_1`, `test_migrate.test_the_real_database_opener_turns_a_refused_connection_into_one_line` |

Not done: the 75 test_doc_check errors of F11 (the new tests follow the rule; the old ones are backlog), F12 and F13 go into A-59.

### Open questions (unspecified behaviour, M42)
- NUL is now refused on the file backend too (it stored it before). No requirement or IF-102 line says it; proposal: an Errors row in IF-102 at the next contract change, with a suite case and the mock refusing it.
- After a dropped listening connection the PostgreSQL listener reconnects within about 1 s; notices sent in that gap are lost (no catch-up). REQ-SLY-006 does not say what a subscriber may expect across a database restart.
- The delete notice carries `version: None` (the verification's proposal); A-59 writes it into IF-102.

## Amendment A-59 (draft, not installed; D-158)
- Drafts: `specs/mia/amendments/A-59/IF-102-storage-interface.md` (IF-102 v2: the delete notice with version None, golden 4; tables and the delete rule follow IF-301/IF-302: F7, F12), `specs/mia/contract-drafts/tests/helpers/mocks/if_102_storage.py` (delete tells the subscribers), `specs/mia/contract-drafts/tests/acceptance/contract/test_if_102_storage.py` (TC-IF-102-09). `stages.yaml` (stage-3 step `contract-postgres`, F6) and the TC-IF-102-09 row of `specs/mia/test-spec.md` are made from the installed files at install time.
- New, not protected: `tools/contract_postgres.sh` (the step: a throwaway `postgres:16` on tmpfs, never pulled, the real side of the IF-102 suite with `MIA_TEST_DATABASE_URL`, a skip counts as a failure; `MIA_DB_PYTHON` names a python with psycopg).
- Install: `bash tools/apply_amendment_a59.sh --do` on goal/v1 after this branch is merged.
- Checked on a scratch copy of this branch (removed): install, then the IF-102 suite 18/18 (mock 9, files 9), `tools/contract_postgres.sh` 9/9 on PostgreSQL, the tests that use the mock in the image (test_api_events, test_api_sessions, test_accounts_api, test_api_storage_imports, IF-104 and IF-203 suites) green; a second run of the script changes nothing.
- F13: `architecture.sysml` `storageLayer` and `database` are `partly` with their modules (model file, edited directly; check_sysml and check_sysml_model OK).
- Full run at the end, each `tests/test_*.py` in the image (`tools/run_in_image.sh`): 160 of 162 files OK; the 2 known failures (test_amendment_report, test_harness rt_edit). On the host (venv mia312): test_storage_postgres 23 OK, the IF-102 suite on PostgreSQL 8/8 (installed suite) and 9/9 (A-59 on a scratch copy).

## Owner decision D-162 (after the Verify fixes), branch v1-n31b
| Item | Change | Covered by test (red before) |
|---|---|---|
| IF-102 `categories()` | `Storage.categories()` gives the vote categories of the record tables (`record_tables.CATEGORIES`, the four of IF-302 in their order) as a list, the same on every backend. The coordinator's wording was "memory categories"; D-162 and `chat_service.py` mean the vote categories, which are the only categories IF-302 defines | `test_storage.test_the_vote_categories_are_an_operation_of_the_storage` (files and PostgreSQL) |
| `chat_service.py` takes the categories from the storage | `vote` and `score` ask `self._votes.categories()` (the IF-102 storage); the import of `record_tables.CATEGORIES` is gone (N-2.2 imports nothing of N-3's tables). Every caller passes the real Storage layer; the IF-102 mock gets `categories()` with A-59, so the test on the mock skips until then (as N-3.3 did in df6ca82) | `test_chat_answers.test_the_chat_service_takes_the_vote_categories_from_the_storage` (a storage that lists only `service`), `test_chat_answers.test_the_chat_service_votes_on_the_if_102_mock` (skips until A-59) |
| A-59 extended (D-162) | `categories()` in the IF-102 v2 text (golden 5), the mock and TC-IF-102-10; the `_real` side of IF-102 loads the Storage layer by file path with the real graph rules (`specs/mia/amendments/A-59/real_storage.py`; `contract.py` built from the installed file, so A-59 and A-60 install in either order). Note: `specs/mia/amendments/A-59/A-59-note.md` | Finding shown on a scratch copy: a mutant of the real `graph_rules.py` survived all 94 tests of the IF-101/102/301/302 suites in one process before (the real side ran the mock rules); with A-59 and A-60 installed (both orders) it fails only the `_real` graph-rule cases of IF-102 and IF-301, on files and PostgreSQL; unmutated 100 OK (3 IF-101 skips, no flask) |

## Re-verification findings (decisions D-168), branch v1-n31c
| Finding | Change | Covered by test |
|---|---|---|
| R1 the guard of `_hear` (a bad notice on `mia_changes`) had no test | test only, no code change | `test_storage_postgres.test_a_bad_notice_on_the_channel_does_not_end_the_listener` (`pg_notify` with `not json` and `{}`, then a write is heard). With the guard removed (scratch edit, reverted) it fails: the listener thread dies on the JSONDecodeError |
