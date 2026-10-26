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
