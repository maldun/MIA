# High-Level Specification: G-V4.GRAPHSTORE.TRANSFER – files and database interchangeable, move and sync

**Status:** Approved (2026-11-22), written by the agent on its own recommendations (D-423); decisions by delegation D-460 (survey points) and D-463 (this spec); owner D-464 (A-186)
**Top-level spec:** `../G-V4.GRAPHSTORE/top-level-spec.md` (items FR-58, FR-59, FR-93, NFR-15 and the move and sync part of NFR-16 are this subgoal's; NFR-8 and REQ-GA-008 of the product spec)   **Owner:** Stefan Reiterer   **Date:** 2026-11-22
**Basis:** prototype rounds 02 (CP2, CP3, CP9) and 03 (CP13 to CP15) on `prototype/g-v4` (`graph_store_move.py`, `graph_store_sync.py`); the accepted cases AC-004 to AC-008, AC-027, AC-033 (`../G-V4/accepted-cases.md`); CORE and RULES as merged into `goal/v4` (`ceb7097a`); VIEW's IF-104 v2 store route (A-171) and IF-302 v15 side tables (A-172) on `goal/v4.view`; the read-only survey of 2026-11-22.

## 1. Big parts and technology
TRANSFER adds no node and no interface version. It adds one module to the storage layer that moves the graph group between two `Storage` objects and keeps a copy in sync, fixes the existing whole-store move, and wires a copy setting and a sync at start and stop into the web server.

| Part (node) | Purpose | Technology | New / existing | Decided in |
|---|---|---|---|---|
| N-3.1 Storage layer | the whole-store move (files ↔ PostgreSQL) with a check of every graph against what the move brings along; the lag; the one-way sync with the aside folder; the one-graph move; the format marker; durable writes on files | a new module `graph_store_transfer.py` (Python 3.12, adapted from the prototype's `graph_store_move.py` and `graph_store_sync.py`), on top of `storage.Storage`; `storage_copy.py` and `migrate.py` changed; `storage_files.py` gets fsync before rename | new module; existing modules changed | D-460, prototype CP2, CP3, CP15 |
| N-3.2 Workflows and context graphs | the record check with the versions the move carries (`check_record(..., stored=...)`); the registry of kinds for the unknown-kind refusal (`graph_rule_set.kinds()`, IF-301 v4) | existing functions, called, not changed | existing | CORE, RULES |
| N-3.3 Record tables | VIEW's side tables `arrangements` and `graph_changes` (IF-302 v15) are carried with their graph | an explicit table list in the transfer module; no contract change | existing (VIEW) | D-460 |
| N-2.1 API and accounts | the copy setting; AutoSync at start and at an orderly stop; the real values of `GET /api/v2/store` (`shown`, `live_reachable`, `lag`) | `__main__.py` start and `graceful_shutdown` list, `web_app.py` storage construction; the route of IF-104 v2 written by VIEW | existing, changed | D-460 (2), A-171 |

### Key decisions and alternatives
| Decision | Alternatives considered | Rationale | Record |
|---|---|---|---|
| The move checks every graph header against the members it finds in the source (the same `check_record` with `stored` built from the source), refuses the whole move naming each damaged graph, and writes members first, headers last | check each record alone (today); trust the source | AC-005: "a store with a step version missing is refused, nothing written"; members first means an interrupted move leaves no header without its steps (NFR-16, prototype CP15) | D-460 |
| The integrity check stays structural (record checks with stored versions); the eight rules of RULES are not asked during a move or sync | run the rule report on every graph | a move must carry what the store holds, also a graph that breaks a rule today; refusing it would lose data (FR-59 "without loss") | D-460 |
| Scope of the move: all tables, as `migrate` does today; scope of the sync: the graph group (`graphs`, `graph_nodes`, `graph_edges`, `context_nodes`, `context_edges`, `skills`) plus the side tables `arrangements`, `graph_changes` | sync everything | FR-58 "the live store holds everything, the copy keeps graphs"; FR-93 is about versions of graphs; the other tables (accounts, memory, runs) have no "live wins" meaning yet. **Reading of FR-58 shown in the plan review** | D-460 |
| The sync is one way, live → copy; a graph whose copy history differs from the live one gets the live history; the copy's differing versions are written first to `<copy root>/aside/<graph>__<stamp>.json` (fsync, rename) and only then removed from the copy | two-way merge; discard the copy's versions | FR-93: live is the master, nothing only on the copy is lost; AC-007 | D-460, prototype CP3 |
| Removing or cutting back on the copy is a backend operation of N-3.1 (`remove` exists on both backends; cutting a record back to version n is added, header before members, so an interrupted sync leaves an earlier complete version, never a missing graph), used only by the sync after its aside file is durable; IF-102 stays as it is (`delete` refuses graph tables) | an IF-102 amendment with a "remove" operation; removing the header first (prototype) | no consumer outside N-3.1 needs it; the contract keeps graph records immutable for everyone else; NFR-16 (D-406) | D-460, D-466 |
| A format marker `mia-store.json` (`{"format": 1}`) in the root of a set of files; a set without one is format 0: read when it holds only stored-form graphs, else refused naming MIGRATION's conversion step | a version in every record | NFR-15 "an older set is read completely or converted by a stated step"; the conversion of the document form is MIGRATION's | D-460 |
| A graph of a kind the registry does not know stops the whole move or sync with `unknown_kind` naming it; the lag lists it as `refused` with its kind | let MIGRATION refuse it; skip it | a later MIA's kind must not be half-carried by an older one; RULES' registry is the one list (Q-7 of RULES) | D-460 |
| Files backend: fsync of the temporary file before `os.replace`, and of the folder after it | rename only (today) | an aside file and a moved record must survive a power cut before the copy's versions are removed (NFR-16) | this spec |
| Copy setting on top of VIEW's store setting: the live store is the database (`MIA_DATABASE_URL`), the copy is a folder; AutoSync at start and at an orderly stop, **off by default**; an unreachable live store gives a report, not a failed start; one sync at a time (lock file `<copy root>/sync.lock`) | always on; sync on every write | D-460 (1): until the owner's later gate MIA runs on files; a sync must never block the start or overwrite a running sync | D-460 |
| `migrate.py` keeps its four commands; `files-to-db` and `db-to-files` call the new move; `library-export` and `library-seed` refine REQ-GA-008 as storage commands | a page function in the graph app | REQ-GA-008 moved here (D-367); re-parented to FR-59. **Shown in the plan review** | D-460 |
| No prototype round 05 | a round for PostgreSQL as live side, side tables, older sets, start/stop hook | rounds 02 and 03 cover the mechanisms; the four gaps are plain code paths tested in Plan's red tests. A deviation from D-401, recorded here | D-460 |

## 2. Dependencies
| ID | Kind | What | Pin / version | Why we need it | If it fails or changes | Used by | Update policy | Contract tests (what we rely on) |
|---|---|---|---|---|---|---|---|---|
| DEP-1 | tool | Python | 3.12 (venv `/home/maldun/prog/Python/venvs/mia312`) | runs storage, move and sync | as CORE | HR-001 to HR-008 | compatible range 3.12 to < 3.15 | the whole test suite on 3.12 |
| DEP-2 | library | psycopg 3 | as in `requirements-db.txt` | the PostgreSQL backend | the PostgreSQL tests skip; the files path works | HR-002, HR-005 | as CORE | `tests/test_storage_postgres.py`, IF-102 contract suite |
| DEP-3 | service | PostgreSQL | `postgres:16` image, local, never pulled by tests | the live store in tests and the smoke | the database tests skip | HR-002, HR-005, SMOKE | as CORE | `tools/contract_postgres.sh` |
| DEP-4 | data | prototype sample stores and checks of rounds 02 and 03 | commit of `prototype/g-v4` | the golden cases of the move, lag and sync (cp2, cp3, cp15) | re-made from the cases | HR-004 to HR-008 | exact | the cases become fixtures |

No new dependency is added.

## 3. High-level requirements
Hard bounds: **none**. No top-level outcome names a time; a sync at start that takes long is a report in the low-level spec (budget there, plausibility from the prototype), not a hard bound.

The kinds `rule` and `measure` follow CORE's and RULES' approved high-level specs (owner, D-416).

### HR-001 – One move for the graph group
- Kind: rule
- Parent: FR-59
- Text: The Storage layer shall move graphs between two stores only through one transfer function that checks every graph against the records it brings along before it writes anything, and writes a graph's members before its header.
- Rationale: today the move checks records alone and writes headers before context steps (survey, `storage_copy.py:48`, `migrate.py:77`); AC-005.
- Depends on: DEP-1
- Status: Approved

### HR-002 – Same answers on both backends
- Kind: rule
- Parent: FR-58
- Text: Every storage operation on graphs shall give the same answer, versions, authors, times and refusals on the files backend and on the PostgreSQL backend.
- Rationale: FR-58 and NFR-8; AC-004.
- Depends on: DEP-1, DEP-2, DEP-3
- Status: Approved

### HR-003 – One-way sync, live wins, nothing lost
- Kind: rule
- Parent: FR-93
- Text: The sync shall bring the copy to the live store's history of every graph and shall write every version that exists only on the copy durably to the aside folder before removing it from the copy.
- Rationale: FR-93; AC-006, AC-007.
- Depends on: DEP-1
- Status: Approved

### HR-004 – Measure: move without loss (OC-3)
- Kind: measure
- Parent: FR-59
- Text: A whole-store move from files to the database and back, and again, shall leave every graph with all versions, authors and times unchanged, add no record the second time, and refuse a store with one damaged graph with that graph named and nothing written.
- Method: the sample store of AC-005 (several versions per graph, one context graph, one graph with a loop-controlling step, D-374), and the same store with one step version removed.
- Metric: 0 differences after the round trip; 0 records added by the repeat; 0 records written by the refused move.
- Rationale: OC-3.
- Reference: Fedora host, Python 3.12, PostgreSQL 16 in a throw-away container.
- Detail in: the test requirements of this subgoal.
- Status: Approved

### HR-005 – Measure: the same answers (OC-1)
- Kind: measure
- Parent: FR-58
- Text: The same sequence of saves, changes, reads, lists and refused saves shall give identical answers on files and on the database.
- Method: the sequence of AC-004 (`cp2_check.py` 1 and 2) plus the refusals of CORE (`schema_break`, `conflict`).
- Metric: 0 differences.
- Rationale: OC-1.
- Reference: as HR-004.
- Detail in: the test requirements of this subgoal.
- Status: Approved

### HR-006 – Measure: lag and sync (OC-2)
- Kind: measure
- Parent: FR-93
- Text: The lag shall name every graph that is behind, differs or is refused before a sync, the sync shall make the copy equal the live store, and a second sync shall add no record.
- Method: the cases of AC-006 and AC-007, with live store on files and on the database.
- Metric: lag states as in the cases; 0 differences after the sync; 0 records added by the second sync; every copy-only version in an aside file with its author.
- Rationale: OC-2.
- Reference: as HR-004.
- Detail in: the test requirements of this subgoal.
- Status: Approved

### HR-007 – Measure: interrupted move or sync (OC-5)
- Kind: measure
- Parent: NFR-16
- Text: A move or sync interrupted at any one write shall leave every graph entirely as before, entirely new or at an earlier complete version of the live history, and running it again shall finish it.
- Method: fault injection at every write of a move, a one-graph move and a sync (prototype CP15), on both backends.
- Metric: 0 graphs with a header that names a missing member; 0 differences after the rerun.
- Rationale: OC-5 and NFR-16 (D-406 wording).
- Reference: as HR-004.
- Detail in: the test requirements of this subgoal.
- Status: Approved

### HR-008 – Measure: portable sets (OC-4)
- Kind: measure
- Parent: NFR-15
- Text: A set of files copied to another folder shall list every graph with the same versions and content, hold no path of where it was made, and a set without a format marker shall be read or refused naming the conversion step.
- Method: AC-008; a format-0 set with stored-form graphs only and one with a document-form workflow.
- Metric: 0 differences; 0 absolute paths in the set; the document-form set refused naming MIGRATION's step.
- Rationale: OC-4.
- Reference: as HR-004.
- Detail in: the test requirements of this subgoal.
- Status: Approved

## 4. Split proposal
### Nodes (decomposition)
No new node, no new interface version. Within N-3.1 one new module. N-2.1 consumes it inside the backend process (no cross-node interface: the server and the storage layer run in one process and N-2.1 already consumes IF-102). The one-graph move after a keep (FR-95, FR-81) is called by VIEW's and EDIT's backend code in the same process; its signature is agreed with VIEW in step 1b: `move_graph(source, target, graph_id) -> {"graphs": 1, "records": n}`, members, then `graph_changes`, then the header (prototype CP2).

### Goals and subgoals
| Proposed goal / subgoal | Outcome it delivers | Top-level items | Why this cut | How it is checked |
|---|---|---|---|---|
| TRANSFER (this) | move, same answers, sync, portable sets, safe interruption | FR-58, FR-59, FR-93, NFR-15, NFR-16 (part) | keep together (goal.md Split check): one module, one check | HR-004 to HR-008 |

Expected cut into tasks (six, step 5): T-01 move integrity (the two defects, test first); T-02 the same answers on files and PostgreSQL, fsync; T-03 lag, one-way sync, aside, rerun after an interruption; T-04 side records and the one-graph move; T-05 portability and the format marker; T-06 copy setting, AutoSync, lock, unknown kind, real store route, SMOKE-TRANSFER-001.

## 5. Integration with the existing system
- New: `graph_store_transfer.py` (move, one-graph move, lag, sync, aside, format marker; about 300 lines from the prototype). Changed: `storage_copy.py` (`copy_records` checks with the stored versions of the source, writes members first), `migrate.py` (calls the transfer for the graph group, table order), `storage_files.py` (fsync), `__main__.py` and `web_app.py` (copy setting, AutoSync, store route values). Contracts: IF-102 v9 by A-186, text only (the table list names the IF-301 record tables; no operation, behaviour or suite change; D-464); unchanged: IF-301 v4, IF-302 v15, IF-104 v2.
- Protected tests: `tests/acceptance/contract/test_if_102_storage.py` stays green unchanged; TC-SLY-007 and TC-SLY-009 (`test_migrate.py`, `test_storage_copy.py`) are checked in step 1b: a test that expects the old order or the per-record check needs an amendment.
- Requirement amendments expected: REQ-SLY-007/009 (the move checks graphs as a whole, members first); REQ-GA-008 re-parented to FR-59.
- PostgreSQL tests and smoke name the database `mia_smoke` and refuse any other target (as TR-CORE-009); the owner's database is started only with his yes and never removed (CORE Deploy lessons).

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| VIEW's store setting, store route and side tables are not merged yet (contracts only on `goal/v4.view`) | T-04 and T-06 cannot run against real code | tests that need them skip while the tables or the route are missing; TRANSFER writes the backend choice from `MIA_DATABASE_URL` itself if VIEW has not (agreed with VIEW by message) |
| IF-102 v8's table list does not name the graph tables (`graphs`, `graph_nodes`, …) although `table_definitions()` has them | the contract under-describes what is moved | **decided (D-464):** text-only amendment A-186 to IF-102 v9 (draft `specs/mia/amendments/A-186/`, owner script `tools/apply_amendment_a186.sh`); no behaviour change, not needed for TRANSFER's tests |
| TC-SLY-007/009 may expect today's order | a protected test may need an amendment | checked in step 1b; amendment by the owner's script if needed |
| An interrupted multi-version catch-up stops at an earlier complete version (prototype ASM-6) | the copy is behind, not broken | accepted by the D-406 wording of NFR-16; the rerun finishes it (HR-007) |
| AutoSync at start against a slow or unreachable database | slow start | off by default; an unreachable live store is a report; a time budget in the low-level spec |

## Approval
Reviewed item by item with the owner (review log: `review-log.md`). The approval of the whole document is the owner's: tick the box (in Emacs `C-c C-c` on the line) or say so in the chat; the agent then sets the status to Approved and never before.

- [X] Approved by maldun (owner). Date:
