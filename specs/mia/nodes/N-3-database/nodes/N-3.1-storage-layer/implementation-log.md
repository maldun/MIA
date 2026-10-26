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
