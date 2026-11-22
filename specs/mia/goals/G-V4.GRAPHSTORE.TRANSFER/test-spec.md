# Test specification: G-V4.GRAPHSTORE.TRANSFER

**Requirements:** `requirements.md` (REQ-SLY-016 to 039, REQ-API-060 to 064; changes of REQ-SLY-009 and REQ-GA-008; all approved 2026-11-22, D-466, D-467)   **High-level spec:** HR-004 to HR-008 (measures)   **Status:** Draft (2026-11-22, agent by delegation D-423; the owner reviews the scenarios)

All checks are exact: every expected value is a record history, an ID, a state, a count, an order of calls or an equality, so no statistical check is needed; the high-level spec has no hard bound, so no benchmark. The accepted cases (`specs/mia/goals/G-V4/accepted-cases.md`) are witnessed by TC-SLY-022 (AC-004), TC-SLY-016, TC-SLY-018, TC-SLY-020 (AC-005), TC-SLY-024, TC-SLY-025 (AC-006), TC-SLY-026, TC-SLY-027 (AC-007), TC-SLY-037 (AC-008), TC-SLY-030 (AC-033) and TC-SLY-031 (the mechanism of AC-027).

Stores: every check that names "both backends" runs on a new files folder and on a new database in a throw-away `postgres:16` container, as CORE's `tests/helpers/core_stores.py` does (TR-TRANSFER-002). The sample store (TR-TRANSFER-003) is the 15 converted skill graphs, `cp2.multi` with four versions by four authors, `sample.code` (a code step, a loop-controlling step, hostile names) and the context graph `context.cp13`, all from `tests/fixtures/graphs/`. "Live" and "copy" in a scenario are two such stores; the copy is always a files folder.

Protected tests in force: TC-SLY-007 and TC-SLY-009 (`tests/test_migrate.py`, `tests/test_storage_copy.py`, unit level, not protected) keep passing; the IF-102 contract suite (`tests/acceptance/contract/test_if_102_storage.py`) is unchanged and stays green (A-186 is text only).

## Test cases
| Test ID | Verifies | Level | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|
| TC-SLY-016 | REQ-SLY-016, HR-004 | component | the sample store on files; moved to an empty database, then to an empty files folder | every record of every table has, entry by entry, the same versions, authors, times and documents as in the source | exact |
| TC-SLY-017 | REQ-SLY-017 | component | the sample store plus a header of `cp2.multi` naming step version 3 of which only 1 and 2 exist; separately a graph that breaks only the cycle rule | the damaged header is found before the first write (0 writes counted); the cycle graph is moved | exact |
| TC-SLY-018 | REQ-SLY-018, HR-004 | component | the damaged store of TC-SLY-017 plus `sample.broken` (a connection to a missing step); target a database holding one unrelated graph | refused with `move_refused`; the detail names `cp2.multi` with the missing member and `sample.broken` with `e2`; the target holds exactly its one graph | exact |
| TC-SLY-019 | REQ-SLY-019 | component | the sample store moved through a recording backend that logs every append | for every header version in the log, each member version it names appears earlier in the log | exact |
| TC-SLY-020 | REQ-SLY-020, HR-004 | component | the move of TC-SLY-016, run a second time onto the same target | copied 0, versions added 0, skipped equal to the first move's copied; the target unchanged | exact |
| TC-SLY-021 | REQ-SLY-021 | component | the sample store plus a graph `alien` of kind `swarm` written through the backend; a move, and a sync with that store as the live store | both refused naming `alien` and `unknown_kind`; target and copy unchanged | exact |
| TC-SLY-022 | REQ-SLY-022, HR-005 | component | the save sequence of `cp2_check.py` 1 and 2, a refused save (`schema_break`), a stale save (`conflict`), on both backends with a fixed clock | the two answer lists (versions, authors, times, ID lists, refusals with rule and detail) are equal | exact |
| TC-SLY-023 | REQ-SLY-023 | unit | one append on a files backend with `os.fsync` and `os.replace` recorded | the calls are: fsync of the temporary file, replace, fsync of the table folder | exact order |
| TC-SLY-024 | REQ-SLY-024, HR-006 | component | AC-006 (live has two more versions of `cp2.multi`), AC-007 (`sample.code` with a copy version 2 and a different live version 2), `alien` on the live store; live on files and on the database | the lag lists exactly `cp2.multi` (live 6, copy 4, `behind`), `sample.code` (`differs`) and `alien` (`refused`, `unknown_kind`) | exact |
| TC-SLY-025 | REQ-SLY-025, HR-006 | component | AC-006 and AC-007 (without `alien`); sync, then sync again; live on files and on the database | after the first sync every graph-group record has the same history on both sides; the second sync adds 0 records | exact |
| TC-SLY-026 | REQ-SLY-026, HR-003 | component | AC-007; once plain, once with a fault after the aside file is written and before the first removal or cut | the aside file holds the copy's version 2 of `sample.code` and its members with author and time; after the fault the copy still holds version 2 and the aside file is complete JSON | exact |
| TC-SLY-027 | REQ-SLY-027 | component | AC-007, sync | the answer's `set_aside` is exactly `{"sample.code": {"versions": [2], "file": "aside/sample.code__<stamp>.json", ...}}`; the path is relative and the file exists | exact |
| TC-SLY-028 | REQ-SLY-028 | component | a copy; process A holds its lock (a helper process that takes the lock and waits); process B runs a sync; then A is killed and B runs again | B's first sync is refused naming `sync.lock` and the copy is unchanged; after A is killed B's sync runs | exact |
| TC-SLY-029 | REQ-SLY-029, HR-007 | component | a move of the sample store, a one-graph move of `cp2.multi` and the sync of AC-006 plus AC-007, each interrupted at every write position; both backends | after every stop no header in the target names a missing member | 0 positions failing |
| TC-SLY-036 | REQ-SLY-036, HR-007 | component | every stopped run of TC-SLY-029, run again | the target equals, record by record, the target of an uninterrupted run (aside files may be two) | 0 differences |
| TC-SLY-038 | REQ-SLY-038, HR-007 | component | the sync of AC-007 interrupted at every write position; both backends for the live side | after each stop `sample.code` is listed on the copy at the shared version 1, at the copy's version 2 or at the live version 2, never missing; every header names only existing members | 0 positions failing |
| TC-SLY-030 | REQ-SLY-030 | component | a graph with two `graph_changes` records, a version kept without one and an `arrangements` record; move, one-graph move and sync (skipped while the tables are missing) | the destination has the same side records; the version without a record has none | exact |
| TC-SLY-031 | REQ-SLY-031 | component | live and copy equal; a new live version of `cp2.multi`; then a copy with a version 5 of its own | the one-graph move adds that version and its new members, every other record unchanged; with the copy's own version 5 the move ends with `conflict` naming `cp2.multi` and the copy is unchanged | exact |
| TC-SLY-032 | REQ-SLY-032 | component | a move into an empty folder; a plain save into an empty folder | each folder holds `mia-store.json` = `{"format": 1}` | exact |
| TC-SLY-033 | REQ-SLY-033 | component | a set written by today's code without a marker (scoped graphs and `workflows` documents) | moved and synced like a format-1 set; the move result equals that of TC-SLY-016 for those records | exact |
| TC-SLY-034 | REQ-SLY-034 | component | a set without a marker holding `graph_nodes/n1` (no slash) | move and sync refused naming `graph_nodes`, `n1` and MIGRATION's conversion step; nothing written | exact |
| TC-SLY-035 | REQ-SLY-035 | component | a set with `mia-store.json` = `{"format": 2}` | opening it is refused naming 2 and 1; no file in it changes (byte compare) | exact |
| TC-SLY-037 | REQ-SLY-037, HR-008 | component | the sample store in a folder with a unique name under a temporary folder; moved to another folder, synced with an aside file, the copy folder copied elsewhere | no file of the target, the copy or the copied folder contains the source folder's absolute path or the home folder; the copied folder lists the same graphs and versions | exact |
| TC-SLY-039 | REQ-SLY-039 | component | AC-006 on files; `python -m MIA.migrate lag --copy DIR`, then `sync --copy DIR`, then `sync` while a helper holds the lock | `lag` prints the line of `cp2.multi` (live 6, copy 4, behind), exit 0; `sync` reports the records added, exit 0; the locked sync is one line, exit 1 | exact |
| TC-SLY-009 | REQ-SLY-009, REQ-GA-008 | component | the sample store; `library-export` to a new folder, `library-seed` into an empty store | every library entry and every graph-group record arrives identical; in the seed's write log members come before headers | exact |
| TC-API-060 | REQ-API-060 | component | the backend app with `store` files (live) and `copy` set to a folder holding a different version of `cp2.multi` | `GET` of `cp2.multi` through IF-104 v2 answers the copy's version | exact |
| TC-API-061 | REQ-API-061 | component | `copy` set, no `autosync`; the live store has a newer version; start and orderly stop of the backend | the copy is unchanged after start and after stop | exact |
| TC-API-062 | REQ-API-062 | component | `copy` set, `autosync` true; the live store has a newer version; a version written to the live store while running; orderly stop | the newer version is on the copy before the first answer; the version written while running is on the copy after the stop | exact |
| TC-API-063 | REQ-API-063 | component | `copy` set, `autosync` true, `store` database with an address on a closed port | the backend starts and answers graphs from the copy; the log holds one line naming the live store and `sync not run` | exact |
| TC-API-064 | REQ-API-064 | component | AC-006 with `copy` set; `GET /api/v2/store` before and after a sync | before: `shown` `copy`, `live_reachable` true, `lag` `{"graphs": 1, "since": <time of live version 5 of cp2.multi>}`; after: `lag` `{"graphs": 0, "since": null}` | exact |

## Edge inputs (per operation: empty, missing, at and past the limit)
| Operation | Edge | Check |
|---|---|---|
| move | empty source; empty target; target with the same histories; target with a different history of one record | TC-SLY-016, TC-SLY-020, and the existing `conflict` of TC-SLY-007 (unit) |
| lag | copy equal to live (no line); graph only on the copy (`copy_only`); unknown kind (`refused`) | TC-SLY-024, TC-SLY-025 (second lag empty) |
| sync | nothing to do; versions only behind; differing; only on the copy; interrupted; locked | TC-SLY-025, 026, 029, 036, 038, 028 |
| one-graph move | target lacks the graph; target behind; target with its own version | TC-SLY-031 |
| format marker | none with scoped records; none with an unscoped record; format 1; format 2 | TC-SLY-032 to 035 |
| AutoSync | off; on with live reachable; on with live unreachable | TC-API-061 to 063 |

## Statistical checks (M19)
None: no result of this subgoal is random or noisy.

## Benchmarks and baselines
None: no hard bound and no time budget (high-level spec section 3).

## Smoke tests (run in Phase 6, target environment)
| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-TRANSFER-001 | REQ-SLY-016, REQ-SLY-025, REQ-SLY-026, HR-004, HR-006 | the owner's host, the installed release, the owner's running PostgreSQL server (started only with his yes) | a new files folder with the sample store; a new database `mia_smoke`; move files → `mia_smoke` → a second new folder; a version only on the second folder, a new version in `mia_smoke`; lag, sync | the round trip gives equal histories; the lag names the two graphs; the sync makes the folder equal `mia_smoke` and names the aside file; both throw-away stores dropped by name; MIA's own data untouched |

## Validation criteria (checked in Phase 7)
| ID | Criterion | How we check | Who | Agreement (if numeric): margin, mean or single values, method |
|---|---|---|---|---|
| VAL-TRANSFER-01 | FR-58, FR-59, FR-93 and NFR-15 hold for the deployed version as they held in the prototype (AC-004 to AC-008) | the owner repeats the steps of AC-004 to AC-008 on the deployed version, on throw-away stores | Stefan Reiterer (owner) | single values: every line passes |

## Scenarios
<!-- one block per check of the tables above, in plain language, approved before the check is built -->

### TC-SLY-016 – The whole store goes to the database and back unchanged
- Verifies: REQ-SLY-016, HR-004
- Given: the sample store on files; an empty database; an empty second folder
- When: the whole store is moved to the database, and from there to the second folder
- Then: every record of every table in the database and in the second folder has the same versions, authors, times and documents as in the source, entry by entry
- And: `cp2.multi` has its four versions by its four authors in the order they were written

### TC-SLY-017 – A damaged graph is found before anything is written
- Verifies: REQ-SLY-017
- Given: the sample store plus a header of `cp2.multi` that names version 3 of a step that has only versions 1 and 2; separately, a store with one graph that has a cycle but is otherwise sound
- When: each store is moved to an empty target through a backend that counts writes
- Then: the damaged store is refused with 0 writes counted
- And: the graph with the cycle is moved: the move checks records, not the eight rules

### TC-SLY-018 – One damaged graph stops the whole move and is named
- Verifies: REQ-SLY-018, HR-004
- Given: the damaged store of TC-SLY-017 plus `sample.broken` (a connection `e2` to a missing step); a target database that already holds one unrelated graph
- When: the store is moved
- Then: the move is refused with `move_refused`, naming `cp2.multi` with its missing step version and `sample.broken` with `e2`
- And: the target holds exactly its one graph, as before

### TC-SLY-019 – Steps and connections are written before the header that names them
- Verifies: REQ-SLY-019
- Given: the sample store, with a workflow graph and the context graph; a target that logs every write
- When: the store is moved
- Then: for every header version in the log, each step and connection version it names was written earlier

### TC-SLY-020 – Moving again changes nothing
- Verifies: REQ-SLY-020, HR-004
- Given: the source and the target after the move of TC-SLY-016
- When: the same move is run again
- Then: it reports 0 copied, 0 versions added and as many skipped as the first move copied
- And: the target is unchanged

### TC-SLY-021 – A graph of an unknown kind stops a move and a sync
- Verifies: REQ-SLY-021
- Given: the sample store plus a graph `alien` of kind `swarm`, written straight through the backend (the graph model would refuse it)
- When: the store is moved to an empty target, and synced as the live store to a copy
- Then: both are refused naming `alien` and `unknown_kind`
- And: the target and the copy are unchanged

### TC-SLY-022 – Files and database give the same answers
- Verifies: REQ-SLY-022, HR-005
- Given: an empty files store and an empty database, both with the same fixed clock
- When: the save sequence of the prototype's check 1 and 2, a save that breaks the schema and a save with a stale version are run on each
- Then: the two lists of answers are equal: versions, authors, times, ID lists, and the refusals with their rule and detail

### TC-SLY-023 – A record file is on disk before it replaces the old one
- Verifies: REQ-SLY-023
- Given: a files store, with the calls to flush and to replace recorded
- When: one version is appended
- Then: the calls are, in this order: flush of the new file, replacement, flush of the table folder

### TC-SLY-024 – The lag names what is behind, what differs and what is refused
- Verifies: REQ-SLY-024, HR-006
- Given: a live store and a copy made equal; then two new live versions of `cp2.multi`; a version 2 of `sample.code` on the copy and a different version 2 in the live store; `alien` of kind `swarm` added to the live store; the live store once on files, once on the database
- When: the owner asks for the lag
- Then: it lists exactly three graphs: `cp2.multi` live 6, copy 4, `behind`; `sample.code` `differs`; `alien` `refused` with `unknown_kind`
- And: no other graph is listed

### TC-SLY-025 – The sync makes the copy equal the live store
- Verifies: REQ-SLY-025, HR-006
- Given: the stores of TC-SLY-024 without `alien`
- When: the sync runs, and then runs again
- Then: after the first sync every record of the graph group has the same history in both stores
- And: the second sync adds 0 records and a lag lists nothing

### TC-SLY-026 – The copy's own version is set aside before it goes
- Verifies: REQ-SLY-026, HR-003
- Given: the case of AC-007: `sample.code` with a version 2 only on the copy and a different version 2 in the live store
- When: the sync runs once without a fault, and once (from the same start) with a fault after the aside file is written and before the first cut or removal on the copy
- Then: the aside file holds the copy's version 2 of `sample.code` and of its changed steps, each with author and time
- And: after the fault the copy still holds its version 2 and the aside file is complete, readable JSON

### TC-SLY-027 – The sync says what it set aside and where
- Verifies: REQ-SLY-027
- Given: the case of AC-007
- When: the sync runs
- Then: its answer names `sample.code` with versions `[2]` and the file `aside/sample.code__<stamp>.json`, relative to the copy
- And: that file exists in the copy

### TC-SLY-028 – Only one sync at a time, and a crashed one does not block
- Verifies: REQ-SLY-028
- Given: a copy; a helper process that takes the copy's lock and waits
- When: a second process runs a sync; then the helper is killed and the second process syncs again
- Then: the first attempt is refused naming `sync.lock` and the copy is unchanged
- And: after the kill the sync runs

### TC-SLY-029 – A stop at any write leaves complete graphs
- Verifies: REQ-SLY-029, HR-007
- Given: a move of the sample store, a one-graph move of `cp2.multi` and the sync of AC-006 plus AC-007; the target on files and on the database
- When: each is stopped at its first write, its second write, and so on to its last
- Then: after every stop, no header in the target names a step or connection version that is not there

### TC-SLY-036 – Running it again finishes the work
- Verifies: REQ-SLY-036, HR-007
- Given: every stopped run of TC-SLY-029
- When: the same move or sync is run again
- Then: the target equals, record by record, the target of the same run done without a stop
- And: a sync stopped after its aside file may leave a second aside file with the same versions; nothing is lost

### TC-SLY-038 – A differing graph never disappears from the copy
- Verifies: REQ-SLY-038, HR-007
- Given: the case of AC-007; the live store on files and on the database
- When: the sync is stopped at each of its writes in turn
- Then: after each stop `sample.code` is listed on the copy, at version 1 (the version both share), at the copy's version 2 or at the live version 2
- And: every header on the copy names only steps and connections that are there

### TC-SLY-030 – Recorded changes and the arrangement travel with their graph
- Verifies: REQ-SLY-030
- Given: a graph with two recorded changes, a version kept without a record of changes, and an arrangement (the side tables of VIEW; the check is skipped, visibly, while they do not exist)
- When: the store is moved, the graph is moved alone, and the copy is synced
- Then: at each destination the graph has the same recorded changes and the same arrangement
- And: the version kept without a record of changes still has none; no record is made up

### TC-SLY-031 – One graph moves alone, and never over the copy's own version
- Verifies: REQ-SLY-031
- Given: a live store and a copy that are equal; a new live version of `cp2.multi`
- When: `cp2.multi` is moved alone from the live store to the copy; then, with a copy that holds a version 5 of its own, it is moved again
- Then: the first move adds exactly the new version and its new steps and connections; every other record of the copy is unchanged
- And: the second move ends with `conflict` naming `cp2.multi` and the copy is unchanged (the next sync sets the copy's version aside)

### TC-SLY-032 – A set of files gets its format marker
- Verifies: REQ-SLY-032
- Given: two empty folders
- When: the sample store is moved into the first, and one graph is saved into the second
- Then: each folder holds `mia-store.json` with `{"format": 1}`

### TC-SLY-033 – Today's sets without a marker still work
- Verifies: REQ-SLY-033
- Given: a set written by today's code (scoped graphs and `workflows` documents) without a marker
- When: it is moved and synced
- Then: it behaves as a set with format 1: the records arrive as in TC-SLY-016

### TC-SLY-034 – An older set with plain step IDs is refused by name
- Verifies: REQ-SLY-034
- Given: a set without a marker holding a step record `graph_nodes/n1` (no graph ID in front)
- When: it is moved, and synced
- Then: both are refused naming `graph_nodes`, `n1` and MIGRATION's conversion step
- And: nothing is written

### TC-SLY-035 – A set from a newer MIA is not opened
- Verifies: REQ-SLY-035
- Given: a set whose marker says `{"format": 2}`
- When: the Storage layer opens it
- Then: it is refused naming format 2 and format 1
- And: every file of the set is byte for byte as before

### TC-SLY-037 – A set holds no path of the machine
- Verifies: REQ-SLY-037, HR-008
- Given: the sample store in a folder with a unique name under a temporary folder
- When: it is moved to a second folder, that folder is used as a copy and synced with one aside file, and the copy is copied to a third place
- Then: no file of the three folders contains the first folder's absolute path or the home folder
- And: the third folder lists the same graphs and versions as the source

### TC-SLY-039 – Lag and sync are commands
- Verifies: REQ-SLY-039
- Given: the case of AC-006 on files
- When: the owner runs `lag --copy <folder>`, then `sync --copy <folder>`, then `sync` again while a helper holds the lock
- Then: `lag` prints the line of `cp2.multi` with live 6, copy 4, behind and exits 0
- And: `sync` reports the records added and exits 0; the locked sync prints one line and exits 1

### TC-SLY-009 – Export and seed carry the stored graphs
- Verifies: REQ-SLY-009, REQ-GA-008
- Given: the sample store
- When: the library is exported to a new folder and seeded from it into an empty store that logs its writes
- Then: every library entry and every record of the graph group arrives identical
- And: in the log every step and connection version comes before the header version that names it

### TC-API-060 – MIA reads graphs from the copy
- Verifies: REQ-API-060
- Given: the backend with the live store on files and `copy` set to a folder holding a different version of `cp2.multi`
- When: `cp2.multi` is read through the graph interface
- Then: the answer is the copy's version

### TC-API-061 – Without AutoSync nothing is synced
- Verifies: REQ-API-061
- Given: `copy` set, no `autosync`; the live store has a newer version of `cp2.multi`
- When: the backend starts and stops in an orderly way
- Then: the copy is unchanged after the start and after the stop

### TC-API-062 – AutoSync at start and at an orderly stop
- Verifies: REQ-API-062
- Given: `copy` set, `autosync` true; the live store has a newer version of `cp2.multi`
- When: the backend starts, a new version is written to the live store while it runs, and the backend stops in an orderly way
- Then: the newer version is on the copy before the first answer
- And: the version written while running is on the copy after the stop

### TC-API-063 – An unreachable live store is reported, not fatal
- Verifies: REQ-API-063
- Given: `copy` set, `autosync` true, `store` database with an address on a port where nothing listens
- When: the backend starts
- Then: it starts and answers graphs from the copy
- And: its log holds one line naming the live store and "sync not run"

### TC-API-064 – The store answer tells how far the copy lags
- Verifies: REQ-API-064
- Given: the case of AC-006 with `copy` set
- When: `GET /api/v2/store` is asked before and after a sync
- Then: before: `shown` is `copy`, `live_reachable` true, `lag` `{"graphs": 1, "since": <time of live version 5 of cp2.multi>}`
- And: after: `lag` is `{"graphs": 0, "since": null}`

### SMOKE-TRANSFER-001 – Move and sync on the owner's server, throw-away only
- Verifies: REQ-SLY-016, REQ-SLY-025, REQ-SLY-026, HR-004, HR-006
- Given: the owner's host with the installed release; the owner's PostgreSQL server running (started only with his yes); a new folder with the sample store; a new database `mia_smoke`
- When: the store is moved to `mia_smoke` and back to a second new folder; one version is added only on that folder and a new one in `mia_smoke`; the lag is asked and the sync is run
- Then: the round trip gives equal histories; the lag names the two graphs; after the sync the folder equals `mia_smoke` and the answer names the aside file
- And: `mia_smoke` and both folders are dropped by name; MIA's own data is not written
