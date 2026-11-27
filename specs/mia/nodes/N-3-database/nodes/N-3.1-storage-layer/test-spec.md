# Test specification: Storage layer (N-3.1)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/requirements.md   **Status:** Draft (Plan for node N-3.1, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: the file backend runs in the commit stage, the PostgreSQL backend in a throwaway container in the acceptance stage. The interface IF-102 is tested by its contract suite against the mock and the real part and uses IF-301 and IF-302 (as mocks until their nodes are integrated). Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-SLY-001 | REQ-SLY-001, REQ-SLY-012 | Contract (real) | 3 | the contract suite test_if_102_storage.py with the real provider: the PostgreSQL backend in a throwaway container (`postgres:16`, data on tmpfs; stage-3 step `contract-postgres`, A-59) | every test of the suite passes; the step fails, never skips, where podman, the local image or psycopg is missing | exact |
| TC-SLY-002 | REQ-SLY-002 | Component | 1 | one record of each of the 10 record tables and of workflows and context_graphs, written and read back; file backend (stage 1) and PostgreSQL backend (stage 3) | every record reads back equal (deep equality) on both backends | exact |
| TC-SLY-003 | REQ-SLY-003 | Property | 1 | 500 random sequences (seeds 1 to 500) of put, get(version), history on both backends | versions run 1..n without gap; get(version=k) returns what put number k stored; no earlier version ever changes | 0 failures over 500 seeds |
| TC-SLY-004 | REQ-SLY-004 | Component | 1 | the Storage layer with the mocks of IF-301 and IF-302: a workflow with a cycle, an edge between two data nodes, a vote with category mood, a valid workflow | the three invalid documents are refused with the rule named and nothing is stored (ids and versions unchanged); the valid one is stored as version 1 | exact |
| TC-SLY-005 | REQ-SLY-005 | Component | 1 | create two accounts with the same password; dump the whole store; verify the right and a wrong password | the dump contains neither password; the two hashes differ (salt); the right password verifies, the wrong one does not; the hash function is scrypt or stronger from the standard library | exact |
| TC-SLY-006 | REQ-SLY-006 | Component | 3 | two subscribers on two connections (two threads on the file backend, two database connections on PostgreSQL); a write on the first | the second subscriber is notified once with table, id, version and author; the delay is at most 2 s; after unsubscribe nothing arrives | median of 20 writes <= 2 s, maximum <= 2 s |
| TC-SLY-007 | REQ-SLY-007 | Component | 3 | a data folder in the Storage layer's own record format (workflows with two versions, a memo with a slash in its id and non-ASCII text, an account) moved to the database and back with `python -m MIA.migrate files-to-db` and `db-to-files`; the legacy stores and their importers are out of G-V1 (D-158, FB-04) | the folder after the round trip is identical file by file (byte for byte after canonical JSON); each direction is one command | exact |
| TC-SLY-008 | REQ-SLY-008 | Component | 3 | a database with 50 records; the backup command; the database wiped; the restore command | the same 50 records with all versions; the backup also contains the other data of MIA (the data folder) | exact |
| TC-SLY-009 | REQ-SLY-009, REQ-GA-008 | component | 2 | the sample store; `library-export` to a new folder, `library-seed` into an empty store | every library entry and every graph-group record arrives identical; in the seed's write log members come before headers | exact |
| TC-SLY-010 | REQ-SLY-010 | System | 3 | the stack with the database; a connection attempt from the host LAN address and from a container outside the stack network | both are refused; a connection from a container of the stack succeeds | exact |
| TC-SLY-011 | REQ-SLY-011 | System | 3 | the container started alone with the configuration file, then by the compose stack with the same file | healthy in both cases; the same tables exist | exact |
| TC-SLY-012 | REQ-SLY-013 | Component | 1 | a document nested 200, 201, 600 and 990 levels, for `graph_nodes` and for another table | the 200-level one is stored as version 1; the others are refused as invalid and nothing is stored | exact |
| TC-SLY-013 | REQ-SLY-014 | Component | 1 | a list that contains itself, a dict that contains itself twice, as the value of a graph node and as a document of another table | each is refused as invalid within one second and nothing is stored | exact, 1 s |
| TC-SLY-014 | REQ-SLY-015 | Component | 1 | a task document {"text": "t", "numbers": [...]} with 99,997 and with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3), the same as the value of a graph node (99,995 and 99,996 numbers); a document that names the same child twice on 30 levels | the 100,000-value document is stored; the others are refused as invalid and nothing is stored, the last within one second | exact, 1 s |

Contract test cases of IF-102: TC-IF-102-01 to the last of the suite (listed in the root `test-spec.md`).

## Scenarios

### TC-SLY-001 – IF-102 on PostgreSQL
- Verifies: REQ-SLY-001, REQ-SLY-012
- Given: a throwaway `postgres:16` container with its data on tmpfs, and `MIA_TEST_DATABASE_URL` pointing at it
- When: the real side of the IF-102 contract suite runs (`tools/contract_postgres.sh`)
- Then: every test passes and none is skipped

### TC-SLY-002 – every table holds its records
- Verifies: REQ-SLY-002
- Given: an empty store on the file backend, and one on PostgreSQL
- When: one record of each table is written and read back
- Then: each record reads back equal, as version 1 with its author and id

### TC-SLY-003 – versions never change
- Verifies: REQ-SLY-003
- Given: 500 random sequences of put, get(version) and history (seeds 1 to 500) on each backend
- When: each sequence runs
- Then: versions run 1..n without a gap, get(version=k) returns what put number k stored, and no earlier version changes (0 failures)

### TC-SLY-004 – validation on write
- Verifies: REQ-SLY-004
- Given: a workflow with a cycle, a context graph with two adjacent data nodes, a vote of category `mood` and a valid workflow
- When: each is put
- Then: the three invalid ones are refused with their rule and nothing is stored; the valid one is version 1

### TC-SLY-005 – accounts keep no password
- Verifies: REQ-SLY-005
- Given: two accounts with the same password
- When: the whole store is dumped and both passwords are verified, the right one and a wrong one
- Then: the dump holds neither password, the hashes differ, the right password verifies and the wrong one does not

### TC-SLY-006 – change notices
- Verifies: REQ-SLY-006
- Given: a subscriber on a second thread (files) or a second database connection (PostgreSQL)
- When: 20 writes are made on the first
- Then: each is heard once with table, id, version and author, median and maximum delay at most 2 s; after unsubscribe nothing arrives

### TC-SLY-007 – reversible move from files
- Verifies: REQ-SLY-007
- Given: a data folder in the Storage layer's own record format (D-158: the legacy stores are out of G-V1)
- When: it is moved to the database with `migrate files-to-db` and back into an empty folder with `migrate db-to-files`
- Then: the two folders are identical file by file in canonical JSON

### TC-SLY-008 – backup and restore
- Verifies: REQ-SLY-008
- Given: a database with 50 records and extra versions, and a data folder
- When: `tools/backup.sh` runs, both are wiped and `tools/restore.sh` runs
- Then: the same rows and files come back, and the state before the restore is kept as a safety copy

### TC-SLY-009 – Export and seed carry the stored graphs
- Verifies: REQ-SLY-009, REQ-GA-008
- Given: the sample store
- When: the library is exported to a new folder and seeded from it into an empty store that logs its writes
- Then: every library entry and every record of the graph group arrives identical
- And: in the log every step and connection version comes before the header version that names it

### TC-SLY-010 – reachable only in the stack
- Verifies: REQ-SLY-010
- Given: the stack with the database service
- When: a connection is tried from the host's LAN address, from a container outside the stack network and from a container of the stack
- Then: the first two are refused, the last one connects

### TC-SLY-011 – its own container
- Verifies: REQ-SLY-011
- Given: the database configuration file
- When: the container is started alone, then by the compose stack
- Then: it is healthy both times and has the same tables

### TC-SLY-012 – depth of a document
- Verifies: REQ-SLY-013
- Given: a document nested 200 levels (the document is level 1) and others nested 201, 600 and 990 levels, once as the value of a graph node and once as a document of a table that is not a graph table
- When: each is put
- Then: the 200-level document is stored as version 1; the others are refused as invalid
- And: the refusals store nothing; graph tables name `schema_break` and `data`, other tables `schema` and `nested too deep`; the same on the file backend and on PostgreSQL

### TC-SLY-013 – a document that contains itself
- Verifies: REQ-SLY-014
- Given: a list that contains itself and a dict that contains itself twice, once as the value of a graph node and once as a document of another table
- When: each is put, with a time limit of one second
- Then: each is refused as invalid within the limit
- And: nothing is stored; the same on the file backend and on PostgreSQL

### TC-SLY-014 – size of a document
- Verifies: REQ-SLY-015
- Given: a task document `{"text": "t", "numbers": [...]}` with 99,997 numbers and one with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3; documents of the tables other than graph tables are mappings), a data node whose value is a list of 99,995 and one of 99,996 numbers as records of a graph table, and a document that names the same child twice on 30 levels
- When: each is put, with a time limit of one second
- Then: the documents with 100,000 values are stored as version 1; the ones with 100,001 values are refused as invalid
- And: the 2**30-path document is refused within the limit; the refusals store nothing; graph tables name `schema_break` and `data`, other tables `schema` and `too large`; the same on the file backend and on PostgreSQL

## Test cases of G-V4.GRAPHSTORE.TRANSFER (moved at the merge 2026-11-27)
Unchanged from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/test-spec.md` (TC-SLY-040 by A-196, the path search of TC-SLY-037 by A-197); their test requirements TR-TRANSFER-001 to 011 are in `specs/mia/test-requirements.md`. All checks are exact and run in stage 2 (`tests/acceptance/test_transfer_*.py`); the PostgreSQL half needs podman, the local `postgres:16` image and psycopg 3. Witnesses of the accepted cases: TC-SLY-022 (AC-004), TC-SLY-016, 018, 020 (AC-005), TC-SLY-024, 025 (AC-006), TC-SLY-026, 027 (AC-007), TC-SLY-037 (AC-008), TC-SLY-030 (AC-033). VAL-TRANSFER-01 stays in the goal record.

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|---|
| TC-SLY-016 | REQ-SLY-016, HR-004 | component | 2 | the sample store on files; moved to an empty database, then to an empty files folder | every record of every table has, entry by entry, the same versions, authors, times and documents as in the source | exact |
| TC-SLY-017 | REQ-SLY-017 | component | 2 | the sample store plus a header of `cp2.multi` naming step version 3 of which only 1 and 2 exist; separately a graph that breaks only the cycle rule | the damaged header is found before the first write (0 writes counted); the cycle graph is moved | exact |
| TC-SLY-018 | REQ-SLY-018, HR-004 | component | 2 | the damaged store of TC-SLY-017 plus `sample.broken` (a connection to a missing step); target a database holding one unrelated graph | refused with `move_refused`; the detail names `cp2.multi` with the missing member and `sample.broken` with `e2`; the target holds exactly its one graph | exact |
| TC-SLY-019 | REQ-SLY-019 | component | 2 | the sample store moved through a recording backend that logs every append | for every header version in the log, each member version it names appears earlier in the log | exact |
| TC-SLY-020 | REQ-SLY-020, HR-004 | component | 2 | the move of TC-SLY-016, run a second time onto the same target | copied 0, versions added 0, skipped equal to the first move's copied; the target unchanged | exact |
| TC-SLY-021 | REQ-SLY-021 | component | 2 | the sample store plus a graph `alien` of kind `swarm` written through the backend; a move, and a sync with that store as the live store | both refused naming `alien` and `unknown_kind`; target and copy unchanged | exact |
| TC-SLY-022 | REQ-SLY-022, HR-005 | component | 2 | the save sequence of `cp2_check.py` 1 and 2, a refused save (`schema_break`), a stale save (`conflict`), on both backends with a fixed clock | the two answer lists (versions, authors, times, ID lists, refusals with rule and detail) are equal | exact |
| TC-SLY-023 | REQ-SLY-023 | unit | 2 | one append on a files backend with `os.fsync` and `os.replace` recorded | the calls are: fsync of the temporary file, replace, fsync of the table folder | exact order |
| TC-SLY-024 | REQ-SLY-024, HR-006 | component | 2 | AC-006 (live has two more versions of `cp2.multi`), AC-007 (`sample.code` with a copy version 2 and a different live version 2), `alien` on the live store; live on files and on the database | the lag lists exactly `cp2.multi` (live 6, copy 4, `behind`), `sample.code` (`differs`) and `alien` (`refused`, `unknown_kind`) | exact |
| TC-SLY-025 | REQ-SLY-025, HR-006 | component | 2 | AC-006 and AC-007 (without `alien`); sync, then sync again; live on files and on the database | after the first sync every graph-group record has the same history on both sides; the second sync adds 0 records | exact |
| TC-SLY-026 | REQ-SLY-026, HR-003 | component | 2 | AC-007; once plain, once with a fault after the aside file is written and before the first removal or cut | the aside file holds the copy's version 2 of `sample.code` and its members with author and time; after the fault the copy still holds version 2 and the aside file is complete JSON | exact |
| TC-SLY-027 | REQ-SLY-027 | component | 2 | AC-007, sync | the answer's `set_aside` is exactly `{"sample.code": {"versions": [2], "file": "aside/sample.code__<stamp>.json", ...}}`; the path is relative and the file exists | exact |
| TC-SLY-028 | REQ-SLY-028 | component | 2 | a copy; process A holds its lock (a helper process that takes the lock and waits); process B runs a sync; then A is killed and B runs again | B's first sync is refused naming `sync.lock` and the copy is unchanged; after A is killed B's sync runs | exact |
| TC-SLY-029 | REQ-SLY-029, HR-007 | component | 2 | a move of the small store (`cp2.multi`, `sample.code`, `context.cp13`), a one-graph move of `cp2.multi` and the sync of AC-006 plus AC-007, each interrupted at every write position; both backends | after every stop no header in the target names a missing member | 0 positions failing |
| TC-SLY-030 | REQ-SLY-030 | component | 2 | a graph with two `graph_changes` records, a version kept without one and an `arrangements` record; move, one-graph move and sync (skipped while the tables are missing) | the destination has the same side records; the version without a record has none | exact |
| TC-SLY-031 | REQ-SLY-031 | component | 2 | live and copy equal; a new live version of `cp2.multi`; then a copy with a version 5 of its own | the one-graph move adds that version and its new members, every other record unchanged; with the copy's own version 5 the move ends with `conflict` naming `cp2.multi` and the copy is unchanged | exact |
| TC-SLY-032 | REQ-SLY-032 | component | 2 | a move into an empty folder; a plain save into an empty folder | each folder holds `mia-store.json` = `{"format": 1}` | exact |
| TC-SLY-033 | REQ-SLY-033 | component | 2 | a set written by today's code without a marker (scoped graphs and `workflows` documents) | moved and synced like a format-1 set; the move result equals that of TC-SLY-016 for those records | exact |
| TC-SLY-034 | REQ-SLY-034 | component | 2 | a set without a marker holding `graph_nodes/n1` (no slash) | move and sync refused naming `graph_nodes`, `n1` and MIGRATION's conversion step; nothing written | exact |
| TC-SLY-035 | REQ-SLY-035 | component | 2 | a set with `mia-store.json` = `{"format": 2}` | opening it is refused naming 2 and 1; no file in it changes (byte compare) | exact |
| TC-SLY-036 | REQ-SLY-036, HR-007 | component | 2 | every stopped run of TC-SLY-029, run again | the target equals, record by record, the target of an uninterrupted run (aside files may be two) | 0 differences |
| TC-SLY-037 | REQ-SLY-037, HR-008 | component | 2 | the sample store in a folder with a unique name under a temporary folder; moved to another folder, synced with an aside file, the copy folder copied elsewhere | no file of the target, the copy or the copied folder contains the source folder's absolute path, the absolute path of any folder the check made (A-197) or the home folder; the copied folder lists the same graphs and versions as the folder it was copied from | exact |
| TC-SLY-038 | REQ-SLY-038, HR-007 | component | 2 | the sync of AC-007 interrupted at every write position; both backends for the live side | after each stop `sample.code` is listed on the copy at the shared version 1, at the copy's version 2 or at the live version 2, never missing; every header names only existing members | 0 positions failing |
| TC-SLY-039 | REQ-SLY-039 | component | 2 | AC-006 on files; `python -m MIA.migrate lag --copy DIR`, then `sync --copy DIR`, then `sync` while a helper holds the lock | `lag` prints the line of `cp2.multi` (live 6, copy 4, behind), exit 0; `sync` reports the records added, exit 0; the locked sync is one line, exit 1 | exact |
| TC-SLY-040 | REQ-SLY-024, REQ-SLY-025, REQ-SLY-026, REQ-SLY-027 (A-196) | component | 2 | the sample store equal on both sides plus three steps no header names: `lonely.g/z` different in the two stores, `orphan.g/x` only on the copy, `fresh.g/y` only in the live store; lag, sync, sync again; live on files and on the database | the lag lists exactly `graph_nodes|lonely.g/z` (1, 1, `differs`), `graph_nodes|orphan.g/x` (0, 1, `copy_only`), `graph_nodes|fresh.g/y` (1, 0, `behind`); the sync names the first two in `set_aside` with versions `[1]`, their reasons and relative aside files holding the copy's version 1; afterwards the graph group is equal, `orphan.g/x` is gone, the second sync adds 0 and the lag is empty | exact |

## Edge inputs of G-V4.GRAPHSTORE.TRANSFER (per operation: empty, missing, at and past the limit)
| Operation | Edge | Check |
|---|---|---|
| move | empty source; empty target; target with the same histories; target with a different history of one record | TC-SLY-016, TC-SLY-020, and the existing `conflict` of TC-SLY-007 (unit) |
| lag | copy equal to live (no line); graph only on the copy (`copy_only`); unknown kind (`refused`); a record no graph names, differing, only on the copy, only live (A-196) | TC-SLY-024, TC-SLY-025 (second lag empty), TC-SLY-040 |
| sync | nothing to do; versions only behind; differing; only on the copy; interrupted; locked; a record no graph names (A-196) | TC-SLY-025, 026, 029, 036, 038, 028, 040 |
| one-graph move | target lacks the graph; target behind; target with its own version | TC-SLY-031 |
| format marker | none with scoped records; none with an unscoped record; format 1; format 2 | TC-SLY-032 to 035 |

## Smoke tests of G-V4.GRAPHSTORE.TRANSFER (run in Phase 6, target environment)
| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-TRANSFER-001 | REQ-SLY-016, REQ-SLY-025, REQ-SLY-026, HR-004, HR-006 | the owner's host, the installed release, the owner's running PostgreSQL server (started only with his yes) | a new files folder with the sample store; a new database `mia_smoke`; move files → `mia_smoke` → a second new folder; a version only on the second folder, a new version in `mia_smoke`; lag, sync | the round trip gives equal histories; the lag names the two graphs; the sync makes the folder equal `mia_smoke` and names the aside file; both throw-away stores dropped by name; MIA's own data untouched |

## Scenarios (G-V4.GRAPHSTORE.TRANSFER, approved 2026-11-22, D-468; TC-SLY-040 by A-196)

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
- Given: a move of the small store (`cp2.multi` with its versions, `sample.code` with its loop step, the context graph `context.cp13`: every kind of graph, about 60 writes), a one-graph move of `cp2.multi` and the sync of AC-006 plus AC-007; the target on files and on the database
- When: each is stopped at its first write, its second write, and so on to its last
- Then: after every stop, no header in the target names a step or connection version that is not there

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
- And: the set is made by today's save path and its `mia-store.json` deleted afterwards, the stand-in for a set written before this version (every write now adds the marker)

### TC-SLY-034 – An older set with plain step IDs is refused by name
- Verifies: REQ-SLY-034
- Given: a set without a marker holding a step record `graph_nodes/n1` (no graph ID in front), its record file written straight into the folder as a set before A-167 held it
- When: it is moved, and synced
- Then: both are refused naming `graph_nodes`, `n1` and MIGRATION's conversion step
- And: nothing is written

### TC-SLY-035 – A set from a newer MIA is not opened
- Verifies: REQ-SLY-035
- Given: a set whose marker says `{"format": 2}`
- When: the Storage layer opens it
- Then: it is refused naming format 2 and format 1
- And: every file of the set is byte for byte as before

### TC-SLY-036 – Running it again finishes the work
- Verifies: REQ-SLY-036, HR-007
- Given: every stopped run of TC-SLY-029
- When: the same move or sync is run again
- Then: the target equals, record by record, the target of the same run done without a stop
- And: a sync stopped after its aside file may leave a second aside file with the same versions; nothing is lost

### TC-SLY-037 – A set holds no path of the machine
- Verifies: REQ-SLY-037, HR-008
- Given: the sample store in a folder with a unique name under a temporary folder
- When: it is moved to a second folder, that folder is used as a copy and synced with one aside file, and the copy is copied to a third place
- Then: no file of the three folders contains the first folder's absolute path, the absolute path of any folder the check made, or the home folder (A-197)
- And: the third folder lists the same graphs and versions as the folder it was copied from

### TC-SLY-038 – A differing graph never disappears from the copy
- Verifies: REQ-SLY-038, HR-007
- Given: the case of AC-007; the live store on files and on the database
- When: the sync is stopped at each of its writes in turn
- Then: after each stop `sample.code` is listed on the copy, at version 1 (the version both share), at the copy's version 2 or at the live version 2
- And: every header on the copy names only steps and connections that are there

### TC-SLY-039 – Lag and sync are commands
- Verifies: REQ-SLY-039
- Given: the case of AC-006 on files
- When: the owner runs `lag --copy <folder>`, then `sync --copy <folder>`, then `sync` again while a helper holds the lock
- Then: `lag` prints the line of `cp2.multi` with live 6, copy 4, behind and exits 0
- And: `sync` reports the records added and exits 0; the locked sync prints one line and exits 1

### TC-SLY-040 – Records no graph names are listed, set aside and synced like a graph (A-196)
- Verifies: REQ-SLY-024, REQ-SLY-025, REQ-SLY-026, REQ-SLY-027
- Given: the sample store, equal in the live store and the copy; then three steps that no header names, each version 1: `lonely.g/z` written by `live-writer` in the live store and by `copy-writer` on the copy, `orphan.g/x` only on the copy, `fresh.g/y` only in the live store; the live store once on files, once on the database
- When: the owner asks for the lag, runs the sync, and runs it again
- Then: the lag lists exactly `graph_nodes|lonely.g/z` (live 1, copy 1, `differs`), `graph_nodes|orphan.g/x` (live 0, copy 1, `copy_only`) and `graph_nodes|fresh.g/y` (live 1, copy 0, `behind`), each with reason null
- And: the sync's `set_aside` names exactly `graph_nodes|lonely.g/z` (versions `[1]`, "the live store won") and `graph_nodes|orphan.g/x` (versions `[1]`, "the record exists only on the copy"), each with a file `aside/<table>_<record ID, / as _>__<stamp>.json` relative to the copy that holds `record`, `reason` and the copy's version 1 with author and time
- And: afterwards the graph group is equal in both stores and `orphan.g/x` is gone from the copy
- And: the second sync adds 0 records and sets nothing aside, and the lag lists nothing

### SMOKE-TRANSFER-001 – Move and sync on the owner's server, throw-away only
- Verifies: REQ-SLY-016, REQ-SLY-025, REQ-SLY-026, HR-004, HR-006
- Given: the owner's host with the installed release; the owner's PostgreSQL server running (started only with his yes); a new folder with the sample store; a new database `mia_smoke`
- When: the store is moved to `mia_smoke` and back to a second new folder; one version is added only on that folder and a new one in `mia_smoke`; the lag is asked and the sync is run
- Then: the round trip gives equal histories; the lag names the two graphs; after the sync the folder equals `mia_smoke` and the answer names the aside file
- And: `mia_smoke` and both folders are dropped by name; MIA's own data is not written

## Assumptions (checked in validation)

- ASM-N3-001: podman is installed on the development host and can pull `postgres:16`; the PostgreSQL tests are skipped, never weakened, where it is not.
- ASM-N3-002: the standard library has `hashlib.scrypt`; no new dependency is needed for the password hash.
- ASM-N3-003: the PostgreSQL driver is `psycopg` 3, kept in `requirements-db.txt` and imported only when the storage is `postgres` (design of `deploy/REQUIREMENTS_DB.md`); approved by the owner on 2026-10-25 (D-54).
