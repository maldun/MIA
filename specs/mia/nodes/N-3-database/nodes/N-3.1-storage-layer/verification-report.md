# Verification report: Storage layer (N-3.1)

**Goal:** G-V1 (iteration), supervised; node N-3.1 (leaf) verified as a black box with the mocks of its neighbours and on both backends (files, PostgreSQL)
**Branch:** goal/v1 @ f3636bc (node files identical to 6be0b49 and to 53c6766 except 0c5959f, b6427d8)   **Parent line of work:** master   **Plan baseline:** plan-baseline-it1
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed:** 9f6adc7 (T-01, T-02), 211ded7 (T-03), 58f266d (T-04, T-05), 5834a1b (T-06), 61c7ed0 (T-07), 0ab5a09 (T-08), all on master before 53c6766; later on goal/v1: 0c5959f (test compares the db image by name, D-139), b6427d8 (comment line of `tools/backup.sh`, N-4.2 T-05). Scope: REQ-SLY-001..012, IF-102 (provided). IF-301 and IF-302 are provided by N-3.2 and N-3.3, not by this node.

## Verdict (proposal)
**Verified with findings.** Every requirement has a test that passes on the backends it names, and the IF-102 contract suite passes on the mock, the file backend and PostgreSQL (16/16 each). The findings are robustness gaps the requirements do not test (F1 to F4), one partly met requirement that is already known and assigned elsewhere (F5: REQ-SLY-007 covers only the new tables, D-67), and small gaps in the stages, docs and the model. None blocks the merge. F1, F2 and F3 are implementation defects to fix in Phase 3, each with a failing test first.

## Automated checks (local runs, not CI)
| Check | Result |
|---|---|
| Node tests in the image (`tools/run_in_image.sh`) | test_storage 12, test_accounts 5, test_storage_copy 6, test_migrate 5, IF-102 suite 16: OK. test_storage_postgres (2 classes) and test_backup skip (no psycopg or podman in the image), test_database_stack 3 OK, 1 class skipped: expected |
| PostgreSQL tests on the host (venv mia312, own throwaway `postgres:16`, never pulled) | test_storage_postgres 17 OK in 48 s; test_backup 3 OK in 12 s. **2 psycopg ResourceWarnings** in TC-SLY-007 (F4) |
| IF-102 contract suite | mock 8/8, real on the file backend 8/8; real on PostgreSQL (`MIA_TEST_DATABASE_URL` to my own container) 8/8, with 7 ResourceWarnings from the adapter (F4) |
| N-3 integration steps 0 to 3 | 4/4 OK on the real parts (READY has N-3.2, N-3.3, N-3.1, N-3); step 3 also OK on PostgreSQL |
| TC-SLY-010, TC-SLY-011 container tests (`DatabaseContainer`) | **not run by me**: they run two of my containers at once (stack db plus a client or the "alone" container), which this session's rules forbid. The compose-file tests (3) pass; evidence for the container part is the implementation log (5 tests green, 24 s) |
| Protected IF-102 material vs. amendments | `test_if_102_storage.py`, `tests/integration/N-3/*`, `mocks/errors.py`: unchanged since the plan gate (fe819ca). `mocks/if_102_storage.py`: changed only by A-08 and A-15 (tables). `_StorageAdapter` and the IF-102 branch of `real_subject` in `tests/helpers/contract.py` equal the A-02 draft (e02992c); `integration.py` equals its draft. `contract.py` differs from its draft only by A-51 (IF-104, installed, draft not refreshed: not this node) |
| trace_check (whole spec) | exit 1 from other parts (93 errors, none for REQ-SLY); for this node one warning: REQ-SLY-012 has no `req` marker (its evidence is the IF-102 suite, marked `IF-102`). Also: `test-requirements.md` has no TR items (M41, project-wide) |
| test_doc_check (the 7 test files of the node) | 75 errors (T1 17, T2 24, T3 34): the tests predate the readable-test rule (F11) |
| Mutation checks (scratch copy of HEAD, removed) | 14 mutations, 14 caught (table below) |
| Static, security, licence | no linter configured (CLAUDE.md); manual review only. psycopg[binary] 3 is the approved dependency (D-54), only in `requirements-db.txt`, imported only by `storage_postgres.py` |
| Usability with bad inputs (`migrate.py`, `tools/restore.sh`) | missing archive and missing options: clear message, exit 1/2. Unreachable database: raw psycopg traceback. A typo in `--data`: "copied 0 records", exit 0 (F10) |

### Mutation checks
| Mutation | Caught by |
|---|---|
| `storage.py` validation skipped | test_storage |
| version `current + 2` | test_storage |
| delete allowed on every table | test_storage |
| `expected_version` ignored | test_storage |
| the origin filter of remote notices removed (own subscribers told twice on PostgreSQL) | test_storage_postgres (`PostgresStorage`); **not** by `SharedDatabase` or the file tests |
| `quote(id, safe="/")` (an id leaves its folder) | test_storage |
| fixed salt | test_accounts |
| `verify` always true | test_accounts |
| copy conflict check removed | test_storage_copy, test_migrate |
| dry run writes | test_migrate |
| only the first planned record copied | test_storage_copy, test_migrate |
| `UniqueViolation` not turned into `conflict` | test_storage_postgres |
| restore drops the safety copy | test_backup |
| backup without `data.tar` | test_backup |

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-SLY-001 PostgreSQL in a container behind IF-102 | Test, inspection | IF-102 suite on PostgreSQL 8/8 (my run); `test_the_schema_is_applied_once...`; `deploy/compose.yaml` service `db` | Pass (component). The app itself still uses the file backend (compose comment, D-139: "nothing in MIA reads it yet"); that wiring is N-2's | yes |
| REQ-SLY-002 shared state held | Test | TC-SLY-002 on files and PostgreSQL: one record of each of the 12 tables of the test (now 16 tables exist; `cases`, `behaviours`, `workflow_meta`, `reports` are covered by the IF-302 suite, not by TC-SLY-002) | Pass | yes |
| REQ-SLY-003 immutable versions | Test (statistical: 500 seeds) | TC-SLY-003 on both backends, 0 failures over seeds 1..500; two instances never share a version (PostgreSQL) | Pass; but a seeded or migrated record can break it (F1) | yes (deterministic code) |
| REQ-SLY-004 validation on write | Test | TC-SLY-004 on both backends, IF-102 suite (all five graph rules), refused edit consumes no version | Pass for `put`; seed and migrate write without validation (F1) | yes |
| REQ-SLY-005 accounts | Test | TC-SLY-005: no password in the dump, different hashes, scrypt N=2^14 | Pass; `create` can overwrite under a race (F3) | yes |
| REQ-SLY-006 change notification | Test | TC-SLY-006 files (thread) and PostgreSQL (20 writes, second instance hears each once, max <= 2 s); IF-102 TC-06 | Pass; a failing subscriber stops the notices (F2); delete is not notified (F7) | yes |
| REQ-SLY-007 reversible move from files | Test | TC-SLY-007: files to PostgreSQL and back identical (4 records); file side in test_migrate | **Partly**: only the records of the Storage layer's own format; the test does not use "the recorded data folder of the repository" as TC-SLY-007 says; the legacy stores have no importer (F5, D-67) | yes |
| REQ-SLY-008 backup and restore | Test | TC-SLY-008: 51 rows and a data folder come back exactly; safety copy; foreign archive refused | Pass | yes |
| REQ-SLY-009 library export and seed | Test | TC-SLY-009 (test_storage_copy, test_migrate) | Pass; seeding does not validate (F1) | yes |
| REQ-SLY-010 reachable only in the stack | Test, inspection | compose: no `ports`, profile `db` (test passes); container test not run by me | Pass by inspection; container part from the log only | the host and LAN refusals in rootless podman follow from "no published port"; the test cannot fail for another reason, which is fine |
| REQ-SLY-011 own container | Test | compose health check, volume, init schema (tests pass); container test not run by me | Pass by inspection; container part from the log only | – |
| REQ-SLY-012 realise IF-102 | Test | IF-102 suite on file and PostgreSQL backends, 8/8 each | Pass; no stage runs the PostgreSQL side (F6) | yes |

## Test requirements (M41)
`specs/mia/test-requirements.md` has no TR items (trace_check warning, project-wide). Checked against `test-spec.md` instead: TC-SLY-001 (throwaway `postgres:16`, data on tmpfs): met. TC-SLY-003 (seeds 1..500, 0 failures): met. TC-SLY-006 (median and maximum of 20 writes <= 2 s): met. TC-SLY-007 ("the recorded data folder of the repository"): **not met**, a synthetic folder of 4 records (F5). Contract suite against mock and real: met on both backends.

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-SLY-004 "when a record is written" | `seed_library` and `migrate` write raw version lists without validation or a version check (F1) | Phase 3 |
| specified, not done | REQ-SLY-007 / TC-SLY-007 | legacy stores not movable; test data synthetic (F5) | known (D-67, N-2 tasks); owner |
| specified, not done | REQ-SLY-012 in the stages | the PostgreSQL side of the IF-102 suite runs in no stage (F6) | Phase 2 (stages.yaml, protected) |
| done, not specified | `--dry-run` | accepted and ignored by `library-export` / `library-seed`, which then write (F8) | Phase 3 |
| done, not specified | delete | no notice to subscribers; IF-102 says "after every write", REQ-SLY-006 "when a record changes" (F7) | owner decision |
| done, not specified | appending missing versions in `copy_records` | reasonable, documented in the module and the log | none |
| interface text | IF-102 v1 lists 12 tables and "immutable for workflows and context_graphs"; the code follows IF-301/IF-302 (16 tables, deletability from their definitions); accepted as decision 2 of D-67 and named in D-69, not yet applied (F12) | Phase 2 (contract text) |

Human review: the owner decisions F7 and the proposals for F5, F6, F12. No item is marked `Code review: needed`.

## Architecture (check 4)
`architecture.sysml:583-590` still marks `storageLayer` and `database` as `proposed` with no modules (`database` names `deploy/REQUIREMENTS_DB.md`). Built modules: `storage.py`, `storage_files.py`, `storage_postgres.py`, `storage_copy.py`, `migrate.py`, `accounts.py`, `tools/backup.sh`, `tools/restore.sh`, `deploy/db/`, the `db` service (F13). Code dependencies: `storage.py` imports `chat_log.utc_now` (reuse of a helper, no flow in the model; harmless), `graph_tables` and `record_tables` (IF-301, IF-302: modelled).

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap |
|---|---|---|---|---|
| Functional suitability | REQ-SLY-001..012 | matrix above | pass with findings | F1, F5 |
| Performance efficiency | REQ-SLY-006 (2 s) | TC-SLY-006 max <= 2 s | pass | – |
| Compatibility | REQ-SLY-012 | IF-102 suite on mock, files, PostgreSQL | pass | F6 (not staged) |
| Interaction capability | – (owner command line) | bad-input probe | minor | F10 |
| Reliability | REQ-SLY-003, -006, -008 | property test, two-instance race, backup round trip | pass | F2 (one subscriber error stops the notices; the listener is not restarted after a database restart) |
| Security | REQ-SLY-005, -010 | scrypt, salt, no plain password; no published port | pass | F3 |
| Maintainability | – | mutation 14/14; test_doc_check 75 errors | partly | F11, F13 |
| Flexibility | REQ-SLY-007 | files <-> database in one command | partly | F5 |
| Safety | – | not applicable to this node | – | not now |

## Open deferrals (M26)
None for N-3.1. The open deferrals TD-01 to TD-04 (TD-04: REQ-WFM-039) concern other nodes.

## Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | `storage_copy.py:138-161` (seed, export, migrate) writes the version lists of a folder as they are: no validation (REQ-SLY-004) and no check that versions run 1..n. Probe: a folder with a workflow containing a cycle is seeded and stored; a record with versions [1, 3] is seeded, then `get(version=2)` returns version 3 (`storage.py:89` reads by position), and the next `put` writes a **second version 3** on the file backend and is refused with `conflict` forever on PostgreSQL (`storage.py:65`) | Medium | Phase 3: test first (seed of an invalid workflow and of a gapped history is refused with nothing written); fix in `copy_records` (validate each document of the source with the table definitions, require versions 1..n and the entry's `id`); proposal: refuse the whole copy as for a conflict |
| F2 | `storage.py:80-82` and `storage_postgres.py:83-89`: a subscriber that raises stops the rest. File backend: `put` raises after the version is stored, later subscribers are not told and `publish` is not called (`storage.py:71-73`). PostgreSQL: the listener thread dies on the first raising callback and `_listener` stays set, so this instance hears no other instance again (probe: 0 of 3 notices). Same after a database restart: the loop ends on `OperationalError` (`:86`) and nothing listens again | Medium | Phase 3: test first (a raising subscriber; the second subscriber and later notices still arrive; `put` returns); fix: catch and log per listener in `_dispatch`; restart or reconnect the listener |
| F3 | `accounts.py:117-119`: `create` checks `ids` and then `put`s without `expected_version=0`; two creations of one name (two owner commands, two instances) give version 2 with the second password, i.e. a silent password change instead of "the account exists" (probe) | Low (only the owner creates accounts, on the machine) | Phase 3: test first; fix: `expected_version=0` and turn `conflict` into the ValueError |
| F4 | The psycopg ResourceWarning of today's smoke run: `migrate.py:57` opens the PostgreSQL backend and never closes it; `tests/test_storage_postgres.py:169` (TC-SLY-007) calls `migrate.main` twice, so 2 warnings (`tests/smoke/smoke_stack.py:64` runs this file). A second source: `tests/helpers/contract.py:120` (`_StorageAdapter`, protected) opens one backend per test and never closes it (7 warnings in the IF-102 suite on PostgreSQL) | Low | migrate: Phase 3, test first (run `migrate.main` under `warnings.catch_warnings` with ResourceWarning as error, or check that the opened backend is closed), fix with `try/finally: database.close()`. Adapter: amendment of `contract.py` (close via `addCleanup` or a `close()`), owner |
| F5 | REQ-SLY-007 partly met: TC-SLY-007 says "the recorded data folder of the repository (fixtures)"; the test uses 4 synthetic records in the new format. The legacy stores (`chat_log.jsonl`, `memories.json`, presets, gestures, moods) have no `to_records`/`from_records` anywhere (D-67 decision 1 put them into N-2 tasks; not done) | Medium (known) | Owner: accept REQ-SLY-007 as partly met for G-V1 (scope row) or schedule the importers of D-67 with their tests in `tests/test_migrate.py` |
| F6 | No stage sets `MIA_TEST_DATABASE_URL`, so the IF-102 suite never runs on PostgreSQL in `contract-real`; TC-SLY-001 is evidence only from manual runs (implementer's scratch run and mine). `test_storage_postgres.py` runs in `unit` only where psycopg is installed and through the smoke stack | Low | Phase 2 amendment of `stages.yaml` (protected): a stage-3 step that starts the throwaway container and runs the suite with the variable |
| F7 | Delete is not notified to subscribers (`storage.py:102-108`); IF-102 says "after every write", REQ-SLY-006 "when a record changes". A page that lists memos or tasks of another instance keeps a deleted record | Owner decision | Proposal: a delete is a change; notify `{"table","id","version": None,"author"}` and say so in IF-102 (amendment), then test |
| F8 | `migrate.py:52-55`: `--dry-run` is accepted by `library-export` and `library-seed` and ignored; they write (probe) | Low | Phase 3: test first; fix: refuse the option there or honour it with `_Discard` |
| F9 | A text with a NUL character is stored by the file backend but raises `psycopg.errors.UntranslatableCharacter` (not a `StorageError`) on PostgreSQL (`storage_postgres.py:58`): the two backends differ | Low | Phase 3 (test first): refuse NUL in documents in `Storage` (rule `schema`) for both, or translate the error |
| F10 | Usability of `migrate.py`: an unreachable database gives a raw traceback; a typo in `--data` gives "copied 0 records", exit 0, and `db-to-files` creates the misspelt folder | Low | Phase 3 backlog: one line "cannot reach the database: ..." and refuse a missing `--data` folder for `files-to-db` and `library-export` |
| F11 | test_doc_check: 75 errors in the 7 test files of the node (no `Example:` lines, no Given/When/Then); the tests predate the rule | Low | backlog (refactoring commit, M31) |
| F12 | IF-102 contract text is stale: 12 tables (16 exist through IF-301/IF-302 v1..v5) and "immutable for workflows and context_graphs" (deletability follows the table definitions); decided in D-67/D-69, not applied | Low | Phase 2: contract text amendment (no test change) |
| F13 | `architecture.sysml:583-590`: `storageLayer`, `database` still `proposed` without modules | Low | Phase 2 model update (run `tools/check_sysml.sh`) |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| The app's store stays the file backend; the database runs but nothing in MIA reads `MIA_DATABASE_URL` | D-139 (4): plain `up.sh` starts without the database until the store moves; the `storage` option belongs to N-2 | owner (D-139) |
| Run events stay files, not IF-102 | D-107 / A-28 | owner |
| `library.py`'s sqlite3 search index is a cache; the `cases` table of library.sqlite is stored state that moves behind IF-102 when first used | D-147, D-152 | owner |
| TC-SLY-010, TC-SLY-011 container tests: evidence from the implementation log, not re-run here | the reviewer's one-container rule | to be confirmed by the owner (run `python tests/test_database_stack.py` on the host) |

## Notes for Phase 7 (validation)
- Two MIA instances on one database: whether the notices across instances feel immediate (2 s bound) and survive a database restart (F2).
- The move of a real data folder to the database (F5) is the first thing a user with existing data will try.

---

# Re-verification (after v1-n31b and the A-59 install)

**Goal:** G-V1 (iteration), supervised; node N-3.1 (leaf), black box with its neighbours' mocks and on both backends
**Branch:** goal/v1 @ 1f97395   **Plan baseline:** plan-baseline-it1   **Date:** 2026-10-31
**Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed:** v1-n31b (merged in acf1320): 5f9cf58 (F1), 63b1b16 (F2), d4e8fbd (F3), 539a2e8 (F4), 5cbd165 (F7), 3814cd3 (F8, F9, F10), 18fbab6 (F13), 8707a9e and a4ddfff (A-59 draft), 2ae1fc5 and 6ba6322 (`categories()`, D-162), e321546; 849ac36 (A-59, A-60, A-61 installed by the owner). Inputs: D-158, D-162, IF-102 v2, `stages.yaml` step `contract-postgres`, sibling reports N-3.2 and N-3.3.

## Verdict (proposal)
**Verified with accepted deviations.** All 13 earlier findings are closed or decided: F1, F2, F3, F4 (migrate), F7, F8, F9, F10 with tests that fail on a mutant (table below), F6 and F12 by A-59 (installed files equal their drafts), F13 by the model, F5 by D-158 (REQ-SLY-007 partly, goal row), F4 (adapter) by D-158; F11 stays backlog. The D-162 collision is closed: a mutant of the real `graph_rules.py` now fails the `_real` IF-102 case in a full contract run, on files and on PostgreSQL. New findings are low: an untested guard in the listener (R1), a second backend divergence of the F9 kind (R2: NaN and non-string ids), two unspecified behaviours waiting for the owner (R3), and plan text (R4). None blocks the merge.

## Automated checks (local runs, not CI)
| Check | Result |
|---|---|
| Node tests in the image (`tools/run_in_image.sh`, one container at a time) | test_storage 17, test_accounts 6, test_storage_copy 7, test_migrate 10, IF-102 suite 20 (10 mock, 10 real), test_chat_answers 12 (the IF-102 mock test no longer skips): OK. test_database_stack 3 OK + 1 class skipped, test_storage_postgres and test_backup skip (no psycopg or podman in the image): expected |
| PostgreSQL tests on the host (venv mia312, own throwaway `postgres:16`, local image, not pulled) | test_storage_postgres 24 OK in 16 s with `-W always::ResourceWarning`: **0 warnings** (F4 closed for the node's code); test_backup 3 OK |
| Stage step `contract-postgres` (`MIA_DB_PYTHON=…/mia312/bin/python bash tools/contract_postgres.sh`) | 10/10 OK, none skipped, container removed. With a bare `python` that has no psycopg the step fails with "set MIA_DB_PYTHON" (fails loudly, not silently) |
| Full contract run, one process (`unittest discover -s tests/acceptance/contract -p "test_if_*.py"`) | 218 tests, 18 skips (other interfaces: IF-103/404/405 stage 2, IF-201, IF-101 events), OK on files and with `MIA_TEST_DATABASE_URL` on my PostgreSQL. IF-102 on PostgreSQL still gives 10 ResourceWarnings from the protected adapter (accepted, D-158) |
| N-3 integration steps 0–3 | 4/4 OK on the host and in the image; step 3 also OK on PostgreSQL |
| Protected material vs. amendments | `contracts/IF-102-storage-interface.md`, `tests/helpers/mocks/if_102_storage.py`, `tests/acceptance/contract/test_if_102_storage.py`, `mocks/graph_rules.py`, `mocks/errors.py`, IF-301/IF-302 suites and mocks: byte-equal to their A-59/A-60/A-61 drafts. `tests/helpers/contract.py`: `amendments/A-59/real_storage.py` is in it verbatim; the removed lines of 849ac36 are only the old IF-102 adapter imports and the IF-301 real side (A-60). `stages.yaml` +2 lines (the step, A-59). No commit after 849ac36 touches `tests/`, `contracts/` or `stages.yaml`. The look-only run of `tools/apply_amendment_a59.sh` was denied by the session's permission check, so the comparison is by `cmp`, not by the script |
| trace_check (whole spec) | exit 1 from other parts (99 errors); for this node: ERROR `test-spec.md` has no `## Scenarios` section (M39, R4), and WARN TD-02, -03, -06, -07 not listed in this report (listed below now). No REQ-SLY gap; the REQ-SLY-012 marker warning of the first report is gone |
| test_doc_check (7 node test files) | 75 errors (T1 17, T2 24, T3 34), the same as before (F11); every test added by v1-n31b passes the rule |
| `check_sysml_model.py`, `check_sysml.sh specs/mia/architecture.sysml` | OK; `storageLayer` and `database` are `partly` with their modules (F13 closed) |
| Static, security, licence | no linter configured; manual review of the fix commits. No new dependency |

### Mutation checks (scratch copy of HEAD, removed)
| Mutation | Caught by |
|---|---|
| copy: documents not validated (F1) | test_storage_copy, test_migrate |
| copy: versions not required to run 1..n (F1) | test_storage_copy |
| copy: entry id not checked (F1) | test_storage_copy |
| `_dispatch` lets a raising subscriber through (F2) | test_storage (files), test_storage_postgres |
| listener returns on `OperationalError` instead of reconnecting (F2) | test_storage_postgres (`test_the_listener_connects_again...`) |
| `_hear` does not catch a bad notice payload | **survives** (R1) |
| `accounts.create` without `expected_version=0` (F3) | test_accounts |
| `migrate` does not close the database (F4) | test_migrate |
| delete sends no notice (F7) | test_storage, test_storage_postgres, IF-102 suite (files and PostgreSQL) |
| delete notice with version 1 instead of None (F7) | test_storage, IF-102 suite (files and PostgreSQL) |
| dry run ignored (F8) | test_migrate |
| NUL accepted (F9) | test_storage, test_storage_postgres |
| a missing source folder not refused (F10) | test_migrate |
| `categories()` sorted / one missing (D-162) | test_storage, IF-102 suite (files and PostgreSQL); the missing one also test_chat_answers |
| real `graph_rules.py` accepts two adjacent data nodes (D-162 collision), full contract run in one process | IF-102 `test_graph_rules_are_checked_on_write_real` and IF-301 `_real`, on files and on PostgreSQL, also with `-k _real` alone; in a unit discovery (`-s tests`, all modules imported) test_storage (files and PostgreSQL), test_graph_rules, test_graph_api, test_workflow_library |

## Earlier findings
| # | Status | Evidence |
|---|---|---|
| F1 | closed | `storage_copy._check_entries`; tests named in the log; 3 mutants caught |
| F2 | closed | `_dispatch` catches per subscriber; listener loop reconnects; 2 mutants caught (R1 left) |
| F3 | closed | mutant caught |
| F4 | closed (migrate); adapter part accepted (D-158) | 0 ResourceWarnings in test_storage_postgres; 10 remain in the IF-102 suite on PostgreSQL (protected adapter) |
| F5 | decided (D-158): REQ-SLY-007 partly, goal row, importers next iteration (FB-04) | `goals/G-V1/goal.md:72` |
| F6 | closed (A-59) | step `contract-postgres` 10/10 |
| F7 | closed (D-158, A-59) | IF-102 v2 golden 4, TC-IF-102-09; mutants caught |
| F8, F9, F10 | closed | mutants caught |
| F11 | open, backlog | 75 errors, unchanged |
| F12 | closed (A-59) | IF-102 v2 lists the 16 tables; the deletable ones in the text (`history`, `memory`, `tasks`, `memos`) equal the code's |
| F13 | closed | model `partly` with modules; SysML checks OK |

## Verification matrix (changes against the first report only)
| Requirement | Result now |
|---|---|
| REQ-SLY-003, -004, -009 | Pass; seed and migrate now refuse what `put` refuses (F1). Non-finite numbers and non-string ids: R2 |
| REQ-SLY-005 | Pass; the race is closed (F3) |
| REQ-SLY-006 | Pass on both backends, delete included; a raising subscriber and a dropped connection no longer stop the notices. Notices sent while the listener reconnects are lost (R3, unspecified) |
| REQ-SLY-007 | Partly, accepted (D-158) |
| REQ-SLY-010, -011 | unchanged: compose tests pass; container tests not re-run (two containers at once) |
| REQ-SLY-012 | Pass: IF-102 v2 suite on mock, files and PostgreSQL (10/10 each), now staged (stage 3) |
| REQ-SLY-001, -002, -008 | unchanged, pass |

## Specification vs. code (M42), new items
| Direction | Item | Destination |
|---|---|---|
| done, not specified | NUL refused with `invalid`/`schema` on every backend (`storage.py:39-50`); not in the Errors table of IF-102 v2 (`contracts/IF-102-storage-interface.md:22-27`) | R3, owner |
| done, not specified | after a dropped listening connection notices are lost for about 1 s (`storage_postgres.py:84-96`); REQ-SLY-006 does not say what a subscriber may expect across a database restart | R3, owner |
| specified, partly | TC-SLY-007 still names "the recorded data folder of the repository (fixtures)" (`test-spec.md:17`) after D-158 made REQ-SLY-007 partly | R4 |

## Open deferrals (M26)
None belongs to N-3.1. Open in the project: TD-01, TD-02, TD-03 (GUI), TD-04 (REQ-WFM-039), TD-06 (workflow library folder, N-3.2), TD-07 (judge calibrations, N-4.1).

## New findings
| # | Finding | Severity | Destination / proposal |
|---|---|---|---|
| R1 | `storage_postgres.py:98-103` (`_hear`): the guard that keeps the listener alive on a bad notice (anyone who can reach the database may `pg_notify` on `mia_changes`, or an event without `table`) has no test; removing it survives every test, and the thread then dies silently as in F2 | Low | needs test (Phase 3): `SELECT pg_notify('mia_changes', 'not json')` and one `'{}'`, then a write on another instance is still heard |
| R2 | Backend divergence of the F9 kind: a document with `float("nan")` or `inf` is stored by the file backend (`storage_files.py:37`, `json.dump` allows NaN) and gives a raw `psycopg.errors.InvalidTextRepresentation` on PostgreSQL (`storage_postgres.py:62`); a non-string id gives a raw `TypeError` (files) or `UndefinedFunction` (PostgreSQL) instead of a `StorageError` (probes on both backends) | Low | needs test (Phase 3, test first in the `StorageBehaviour` mixin): refuse non-finite numbers and non-string ids/authors with `invalid`/`schema` in `storage.validate`/`put`, like NUL; fold into the R3 Errors row |
| R3 | Two behaviours of the fixes that no requirement or IF-102 line states (open questions of the implementation log, no decision in `review-log.md`): NUL (and R2) refused with `invalid`/`schema`; notices lost while the listener reconnects | Low | owner decision; proposal: an Errors row "a text with NUL or a non-finite number: `invalid`, rule `schema`" in IF-102 at the next contract change with one suite case and the mock; REQ-SLY-006: state "notices sent while the database restarts may be lost" (accept) rather than add catch-up |
| R4 | Plan text: `test-spec.md` of the node has no `## Scenarios` section (trace_check ERROR, M39, same as N-3.2 F8, N-3.3 F8); TC-SLY-007 (`test-spec.md:17`) still names the repository's recorded data folder | Low | amendment (text only): scenarios for TC-SLY-001..011 and TC-SLY-007 reworded to the node's own record format per D-158; with the F11 backlog |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| REQ-SLY-007 partly: no importers of the legacy stores | D-158, FB-04 | owner |
| 10 ResourceWarnings of the protected `_StorageAdapter` on PostgreSQL | D-158 | owner |
| TC-SLY-010, TC-SLY-011 container tests not re-run by the reviewer | one-container rule of this session; evidence from the implementation log | to be confirmed by the owner (`python tests/test_database_stack.py` on the host) |
| the earlier deviations (file backend stays the app's store, run events as files, library sqlite cache) | D-139, D-107, D-147, D-152 | owner |

## Not checked here
- CI: none; all results are local feedback runs.
- The whole test suite (only the node's files, its consumers named above and the contract suites).
- `tools/apply_amendment_a59.sh` look-only run (denied by the permission check; compared with `cmp` instead).
- Process note: one unit discovery (`-s tests -k …`) also ran `test_storage_postgres.py`, which started its own throwaway container for about 16 s while mine was up (two of my containers at once, both removed).

## Notes for Phase 7
- Unchanged: notices across instances after a database restart (R3); moving a real data folder (F5, next iteration).
