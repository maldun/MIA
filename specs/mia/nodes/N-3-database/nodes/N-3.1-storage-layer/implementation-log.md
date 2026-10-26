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
