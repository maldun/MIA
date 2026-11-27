# Requirements: Storage layer (N-3.1, low level)

**Parent:** `specs/mia/nodes/N-3-database/requirements.md` (N-3)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The PostgreSQL database and the one door to it (IF-102): immutable versions, accounts, change notification, migration from files, backup and restore, the container. Consumes the table definitions of IF-301 and IF-302. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-SLY-001 – PostgreSQL in a container
- Level: low   Subject: Persistence
- Text: The Storage layer shall be one PostgreSQL database in a container behind the storage interface IF-102.
- Rationale: refines REQ-DB-001
- Parent: REQ-DB-001
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15, AC-29: the container starts alone and passes the contract suite of IF-102
- Verified by: TC-SLY-001
- Status: Verified
- History: –

### REQ-SLY-002 – Shared state held
- Level: low   Subject: Persistence
- Text: The Storage layer shall hold every table of the shared state (history, summaries, chat log, feedback, presets, gestures, library entries and accounts) as the definitions of IF-301 and IF-302 describe them.
- Rationale: refines REQ-DB-002
- Parent: REQ-DB-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a record of each kind is written and read back identically
- Verified by: TC-SLY-002
- Status: Verified
- History: –

### REQ-SLY-003 – Immutable versions
- Level: low   Subject: Persistence
- Text: When a versioned record is edited, the Storage layer shall store the edit as a new version with author and time and keep the former version unchanged.
- Rationale: refines REQ-DB-003
- Parent: REQ-DB-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: version n is unchanged after version n+1 is written (exact)
- Verified by: TC-SLY-003
- Status: Verified
- History: –

### REQ-SLY-004 – Schema validation on write
- Level: low   Subject: Persistence
- Text: When a record is written, the Storage layer shall have it validated through IF-301 or IF-302 and refuse an invalid one with the broken rule named.
- Rationale: refines REQ-DB-004
- Parent: REQ-DB-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16, AC-27: each of the rules (identity, adjacent data nodes, cycle, session stopping criterion) is refused with its name; protects against TB-edit
- Verified by: TC-SLY-004
- Status: Verified
- History: –

### REQ-SLY-005 – Accounts
- Level: low   Subject: Persistence
- Text: The Storage layer shall store accounts with a salted slow password hash and no plain password.
- Rationale: refines REQ-DB-005
- Parent: REQ-DB-005
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: no plain password is stored; two accounts with the same password have different hashes (exact)
- Verified by: TC-SLY-005
- Status: Verified
- History: –

### REQ-SLY-006 – Change notification
- Level: low   Subject: Persistence
- Text: When a record changes, the Storage layer shall tell every subscriber of the storage interface. Notices sent while an instance's listening connection to the database is being opened again (a database restart) may be lost.
- Rationale: refines REQ-DB-006; a catch-up after a restart is not worth its cost for a personal assistant (D-168)
- Parent: REQ-DB-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a second subscriber is notified within 2 s
- Verified by: TC-SLY-006
- Status: Verified
- History: 2026-10-31 D-168: notices sent during a reconnect may be lost (N-3.1 re-verification R3b)

### REQ-SLY-007 – Reversible move from files
- Level: low   Subject: Persistence
- Text: When the owner starts the move from files to the database or back, the Storage layer shall perform it with one command and give identical files after the round trip.
- Rationale: refines REQ-DB-007
- Parent: REQ-DB-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: files to database and back give identical files (exact)
- Verified by: TC-SLY-007
- Status: Approved
- History: –

### REQ-SLY-008 – Backup and restore
- Level: low   Subject: Persistence
- Text: The Storage layer shall allow backup and restore together with the other data of MIA.
- Rationale: refines REQ-DB-008
- Parent: REQ-DB-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7, AC-15: backup and restore round-trip returns the same records (exact)
- Verified by: TC-SLY-008
- Status: Verified
- History: –

### REQ-SLY-009 – Library export and seed
- Level: low   Subject: Persistence
- Text: The Storage layer shall export the library entries and the graph group to a set of files and seed them from one with identical entries, as commands of the storage tool.
- Rationale: refines REQ-DB-009 and REQ-GA-008 (moved here, D-367, D-460); the stored graphs are part of the library since CORE; a command, not a page function
- Parent: REQ-DB-009
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: export then seed gives identical entries, now also for every record of the graph group of the sample store, with members before headers (exact)
- Verified by: TC-SLY-009
- Status: Verified
- History: G-V1, verified; G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, changed (graph group, REQ-GA-008; plan gate 2026-11-23); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-010 – Reachable only inside the host network
- Level: low   Subject: Persistence
- Text: The Storage layer shall accept connections only from the other containers of the stack.
- Rationale: refines REQ-DB-016
- Parent: REQ-DB-016
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-5: a connection from the LAN is refused (exact)
- Verified by: TC-SLY-010
- Status: Verified
- History: –

### REQ-SLY-011 – Own container
- Level: low   Subject: Persistence
- Text: The Storage layer shall start as its own container alone and by the compose stack.
- Rationale: refines REQ-DB-017
- Parent: REQ-DB-017
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: starts alone and in the stack with the same configuration file
- Verified by: TC-SLY-011
- Status: Verified
- History: –

### REQ-SLY-012 – Realise IF-102
- Level: low   Subject: Persistence
- Text: The Storage layer shall realise the storage interface IF-102 as specified in contracts/IF-102-storage-interface.md.
- Rationale: refines IF-102
- Parent: IF-102
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: the contract suite test_if_102_storage.py passes against the Storage layer (stage 2)
- Verified by: TC-SLY-001
- Status: Verified
- Frozen: G-V4
- History: –

### REQ-SLY-013 – Depth of a document
- Level: low   Subject: Persistence
- Text: If a document that is put is nested deeper than 200 levels, then the Storage layer shall refuse it as invalid.
- Rationale: refines REQ-SLY-004 and REQ-GTB-027; one limit for every table, so that the refusal does not depend on the recursion limit of the interpreter or on how deep the caller is in the call stack (F-20 of the fifth Verify run of G-V2.STORE, A-100); the deepest real document in library, skills and eval has 19 levels
- Parent: REQ-SLY-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: a document whose deepest value (an object, a list or a scalar; the document is level 1 and every value below it is one level deeper than its parent) is at level 200 is stored, one whose deepest value is at level 201, 600 or 990 is refused as StorageError `invalid` and nothing is stored, for a graph table (rule `schema_break`, detail `data`) and for another table (rule `schema`, detail `nested too deep`), on the file backend and on PostgreSQL (exact)
- Verified by: TC-SLY-012
- Status: Verified
- History: G-V2.STORE Verify F-20, 2026-11-08, new (A-100, proposed)

### REQ-SLY-014 – A document that contains itself
- Level: low   Subject: Persistence
- Text: If a document that is put contains itself, then the Storage layer shall refuse it as invalid within one second.
- Rationale: refines REQ-SLY-004; a hang is worse than the RecursionError it replaced (F-19 of the fifth Verify run of G-V2.STORE, A-100); only Python callers can build such a document, JSON has no cycles
- Parent: REQ-SLY-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: a list or dict that contains itself, also twice in one dict, is refused as StorageError `invalid` within one second for a graph table and for another table, on the file backend and on PostgreSQL, and nothing is stored (exact, time limit 1 s)
- Verified by: TC-SLY-013
- Status: Verified
- History: G-V2.STORE Verify F-19, 2026-11-08, new (A-100, proposed)

### REQ-SLY-015 – Size of a document
- Level: low   Subject: Persistence
- Text: If a document that is put has more than 100,000 values, counting a value once for every path that reaches it, then the Storage layer shall refuse it as invalid.
- Rationale: refines REQ-SLY-004 and REQ-GTB-028; a document that shares sub-objects can have an exponential number of paths and the backend would have to serialise all of them (F-22 of the Verify of G-V2.STORE, A-102); 100,000 is about 190 times the largest stored document in the repository (529 values)
- Parent: REQ-SLY-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: a document with 100,000 values is stored, one with 100,001 is refused as StorageError `invalid` and nothing is stored, for a graph table (rule `schema_break`, detail `data`) and for another table (rule `schema`, detail `too large`); a document that names the same child twice on 30 levels is refused within one second, on the file backend and on PostgreSQL (exact, time limit 1 s)
- Verified by: TC-SLY-014
- Status: Verified
- History: G-V2.STORE Verify F-22, 2026-11-08, new (A-102, proposed)

## Iteration 4 (goal G-V4.GRAPHSTORE.TRANSFER, files and database interchangeable, move and sync; moved at the merge 2026-11-27)
Requirements of the subgoal G-V4.GRAPHSTORE.TRANSFER (goal record `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/`: plan, test requirements TR-TRANSFER-001 to 011, verification report). Verified 2026-11-27 (both boxes ticked by the owner); Verify findings decided in D-548 and D-549: V-1 and V-3 fixed, V-2 and V-4 by the amendments A-196 and A-197, V-5 fixed on `goal/v4`, V-6 at the merge; R-1, R-2 and D-549's lock limit accepted. The specification points of the merge in D-551. The texts are those of the goal file with the approved changes in force (A-195, A-196, A-197, the plan gate); the Status lines stay Approved until the owner sets Verified. REQ-SLY-009 is changed in place above; REQ-API-060 to 066 of group AS are in `specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md`, REQ-GA-008 in `specs/mia/nodes/N-5-graph-app/requirements.md`.

## Terms of G-V4.GRAPHSTORE.TRANSFER
| Term | Meaning |
|---|---|
| live store | the store that VIEW's store setting names (REQ-API-018): the master; graphs are changed only there (FR-95 of EDIT) |
| copy | a set of files in a folder that the copy setting names; MIA reads graphs from it while it is set; it follows the live store by sync |
| set of files | a folder written by the files backend: one file per record, `<table>/<id>.json`, plus the format marker |
| graph group | the tables `graphs`, `graph_nodes`, `graph_edges`, `context_nodes`, `context_edges`, `skills`, and VIEW's side tables `arrangements` and `graph_changes` (IF-302 v15) where they exist |
| members (of a graph) | the step and connection records its header names, at the versions it names; with them go its record of changes (`graph_changes`) and its arrangement (`arrangements`) |
| move (of the whole store) | copying every record of every table from a source store to a target store with versions, authors and times unchanged |
| one-graph move | copying the missing versions of one graph with its members from one store to another (called after a keep, FR-95, FR-81) |
| lag | per graph of the graph group: the number of versions of its header in the live store and in the copy, and its state `current`, `behind`, `differs`, `copy_only` or `refused` with a reason; per record no graph names, under `<table>|<record ID>`: the number of its versions in each store and its state (A-196) |
| record no graph names | a record of the graph group that no header version of any graph names in either store and that is no side record of a graph: every skill, and a step or connection left by a hand edit or a foreign copy (A-196) |
| differs | the copy holds a version of the graph, or of one of its members, that is not the same entry as the live store's version of that number, or a version beyond the live store's newest |
| aside folder | `<copy root>/aside/`; an aside file `<graph id, / as _>__<UTC stamp>[_n].json` holds the copy's differing versions of one graph and its members with their authors and times, and the reason; for a record no graph names `<table>_<record ID, / as _>__<UTC stamp>[_n].json` holds `record`, `set_aside_at`, `reason` and its `versions` (A-196) |
| format marker | the file `mia-store.json` in the root of a set of files, `{"format": n}`; a set without it is format 0 |
| AutoSync | the sync run by the backend at its start and at its orderly stop, while the copy setting asks for it |
| scoped record | a record of `graph_nodes`, `graph_edges`, `context_nodes` or `context_edges` whose ID is `<graph id>/<local id>` (IF-301 v3, A-167) |

## Groups of G-V4.GRAPHSTORE.TRANSFER
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | MV | Moving the whole store: everything arrives, damaged graphs refused, members before headers, a repeat changes nothing (FR-59, HR-001, HR-004) | REQ-SLY-016, REQ-SLY-017, REQ-SLY-018, REQ-SLY-019, REQ-SLY-020, REQ-SLY-021, REQ-SLY-009 (changed), REQ-GA-008 (changed) |
| 2 | SB | The same behaviour on files and the database, durable file writes (FR-58, HR-002, HR-005, NFR-16) | REQ-SLY-022, REQ-SLY-023 |
| 3 | SY | Lag and one-way sync: live wins, the copy's own versions set aside, one sync at a time, rerun after an interruption (FR-93, HR-003, HR-006, HR-007) | REQ-SLY-024 (changed, A-196), REQ-SLY-025 (changed, A-196), REQ-SLY-026 (changed, A-196), REQ-SLY-027 (changed, A-196), REQ-SLY-028, REQ-SLY-029, REQ-SLY-036, REQ-SLY-038 |
| 4 | SR | Side records and the one-graph move (AC-033, FR-95 and FR-81 mechanisms) | REQ-SLY-030, REQ-SLY-031 |
| 5 | PT | Portable sets: the format marker, older and newer sets, no paths (NFR-15, HR-008) | REQ-SLY-032, REQ-SLY-033, REQ-SLY-034, REQ-SLY-035, REQ-SLY-037 (changed, A-197) |
| 6 | AS | The copy setting in the backend: reading the copy, AutoSync at start and stop, the real store answer (FR-58, FR-93, D-460) | REQ-SLY-039, REQ-API-060, REQ-API-061, REQ-API-062, REQ-API-063, REQ-API-064 (changed, A-195), REQ-API-065, REQ-API-066 |

### REQ-SLY-016 – Whole store moved unchanged
- Level: low   Subject: Persistence
- Group: MV
- Text: When the owner moves the whole store between a set of files and the database, the Storage layer shall copy every record of every table with its versions, authors and times unchanged.
- Rationale: refines HR-004 and FR-59 "every graph arrives with all its versions, authors and times unchanged and numbered as before"; D-460: the move takes all tables, as `migrate` does today
- Parent: HR-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-005: the sample store (several versions per graph, a context graph, a graph with a loop-controlling step) moved files → database → files gives every record's history entry by entry equal to the source (exact)
- Verified by: TC-SLY-016
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP2); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-017 – Every graph checked with what the move brings
- Level: low   Subject: Persistence
- Group: MV
- Text: When a move starts, the Storage layer shall check every graph header of the source against the member versions and connection ends found in the source before it writes any record.
- Rationale: refines HR-001; survey: `copy_records` checks each record alone (`storage_copy.py:48`), so `unknown_member` and `unknown_endpoint` are never asked during a move; the check is structural (IF-301 `check_record` with `stored`), never the eight rules (D-460)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: a source whose header names step version 3 of which only versions 1 and 2 exist is found before the first write; a graph that breaks only one of the eight rules (a cycle) is moved (exact)
- Verified by: TC-SLY-017
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: survey defect 2, D-460); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-018 – A damaged graph stops the whole move
- Level: low   Subject: Persistence
- Group: MV
- Text: If the check before a move finds a header naming a missing member version or connection end, then the Storage layer shall write nothing and name every such graph with its missing parts.
- Rationale: refines HR-001 and FR-59 "if one graph cannot be moved, nothing is moved and that graph is named"; AC-005
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-005 damaged store: the move ends refused with rule `move_refused`, the detail names the graph and the missing member, and every table of the target has the same records as before (exact)
- Verified by: TC-SLY-018
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new; verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-019 – Members before the header
- Level: low   Subject: Persistence
- Group: MV
- Text: When the Storage layer moves or syncs a graph, it shall write each member version before the header version that names it.
- Rationale: refines HR-001 and NFR-16 "never a missing step or connection"; survey defect 1: `migrate` copies `graphs` before `context_nodes` and `context_edges` (`migrate.py:77`), so an interrupted move can leave a context graph header without its steps
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: in a recorded write order of a move of a workflow and a context graph, every header version comes after each member version it names (exact)
- Verified by: TC-SLY-019
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: survey defect 1, prototype CP2); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-020 – Moving again changes nothing
- Level: low   Subject: Persistence
- Group: MV
- Text: When a move is run onto a target that already holds the same histories, the Storage layer shall add no record and report the number of records it skipped.
- Rationale: refines HR-004 and FR-59 "moving again changes nothing"; AC-005
- Parent: HR-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-005: the second move reports 0 records copied, 0 versions added and as many skipped as the first move copied (exact)
- Verified by: TC-SLY-020
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new; verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-021 – A graph of an unknown kind stops a move or sync
- Level: low   Subject: Persistence
- Group: MV
- Text: If a graph of the source names a kind that the registry of kinds does not list, then the Storage layer shall refuse the whole move or sync and name the graph with `unknown_kind`.
- Rationale: refines HR-001; D-460: a later MIA's kind is not half-carried by an older one; the registry is RULES' `kinds()` (IF-301 v4); RULES Q-7 left the listing of such a graph to TRANSFER
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: a source with one graph of kind `swarm` (written directly through the backend) gives a refusal naming that graph and `unknown_kind`, and the target is unchanged (exact)
- Verified by: TC-SLY-021
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-022 – The same answers on files and the database
- Level: low   Subject: Persistence
- Group: SB
- Text: The Storage layer shall give the same answer to every operation on the graph group, including versions, authors, order of IDs and refusals, on the files backend and on the PostgreSQL backend.
- Rationale: refines HR-002, HR-005, FR-58 and NFR-8; AC-004
- Parent: HR-005
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-004: the sequence of `cp2_check.py` 1 and 2 plus a refused save (`schema_break`) and a stale save (`conflict`), run on both backends with a fixed clock, gives identical answer lists (exact)
- Verified by: TC-SLY-022
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP2, CP14); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-023 – A record file is on disk before it counts
- Level: low   Subject: Persistence
- Group: SB
- Text: When its files backend replaces a record file, the Storage layer shall flush the new file to disk before the replacement and flush the folder after it.
- Rationale: refines NFR-16; survey: `storage_files.py` renames without fsync, so after a power cut an aside file or a moved version may be empty while the copy's own version is already removed
- Parent: HR-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: a test that records the calls of `os.fsync` and `os.replace` around one append sees fsync of the file, then replace, then fsync of the folder (exact)
- Verified by: TC-SLY-023
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (survey); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-024 – The lag of every graph
- Level: low   Subject: Persistence
- Group: SY
- Text: When the owner asks for the lag, the Storage layer shall list every graph, and every record no graph names, that is not current, with its versions in both stores, its state and its reason.
- Rationale: refines HR-006 and FR-93 "MIA shows how far the copy lags before a sync"; the states and the line format follow the prototype (`graph_store_sync.lag`); records no graph names (Terms) are synced like a graph, so the copy equals the live store for every record of the graph group and the lag says so (V-2 of Verify, D-548)
- Parent: HR-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-006: `cp2.multi` is listed as live 6, copy 4, `behind`; AC-007: `sample.code` is listed as `differs`; a graph of kind `swarm` is listed as `refused` with reason `unknown_kind`; no other graph is listed; TC-SLY-040: a step `lonely.g/z` no header names, different in the two stores, is listed as `graph_nodes|lonely.g/z` live 1, copy 1, `differs`; `orphan.g/x` only on the copy as live 0, copy 1, `copy_only`; `fresh.g/y` only in the live store as live 1, copy 0, `behind`; each with reason null (exact)
- Verified by: TC-SLY-024, TC-SLY-040
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP3); Verify, 2026-11-27, changed by A-196 (D-548, D-550); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-025 – The sync brings the copy to the live store
- Level: low   Subject: Persistence
- Group: SY
- Text: When the owner runs the sync, the Storage layer shall make the history of every record of the graph group in the copy equal to its history in the live store.
- Rationale: refines HR-003, HR-006 and FR-93 "the copy receives the missing versions and equals the live store"; the sync covers the graph group only (D-460; reading of FR-58 shown in the plan review); records no graph names (Terms) are synced like a graph, so the copy equals the live store for every record of the graph group and the lag says so (V-2 of Verify, D-548); the lag lists a record no graph names as a row of its own, so `lag.graphs` of the store answer (REQ-API-064) counts such rows too, every skill the copy lacks among them (A-196, D-550; checked in Validate whether the owner reads it as graphs)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-006 and AC-007 with the live store on files and on the database: after the sync every record of the graph group has the same history in both stores; a second sync adds 0 records; TC-SLY-040 on both backends: after the sync the copy's graph group equals the live store's, `orphan.g/x` is gone from the copy, and a second sync adds 0 records and sets nothing aside (exact)
- Verified by: TC-SLY-025, TC-SLY-040
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP3); Verify, 2026-11-27, changed by A-196 (D-548, D-550); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-026 – The copy's own versions set aside before they go
- Level: low   Subject: Persistence
- Group: SY
- Text: If a graph or a record no graph names differs or exists only on the copy, then the Storage layer shall write the copy's differing versions of it, and of a graph's members, durably to an aside file before removing them.
- Rationale: refines HR-003 and FR-93 "the copy's differing versions are saved aside and named to the owner, not discarded"; removing on the copy is a backend operation of N-3.1, not of IF-102 (D-460); records no graph names (Terms) are synced like a graph, so the copy equals the live store for every record of the graph group and the lag says so (V-2 of Verify, D-548)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-007: the aside file holds the copy's version 2 of `sample.code` with its author and time; with a fault injected between the aside write and the first removal, the copy still holds version 2 and the aside file is complete; TC-SLY-040: the aside file of `graph_nodes|lonely.g/z` and that of `graph_nodes|orphan.g/x` each hold the copy's version 1 with its author and time (exact)
- Verified by: TC-SLY-026, TC-SLY-040
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP3, CP15); Verify, 2026-11-27, changed by A-196 (D-548, D-550); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-027 – The sync names what it set aside
- Level: low   Subject: Persistence
- Group: SY
- Text: When a sync has set versions aside, the Storage layer shall name in its answer each such graph or record with its versions and the path of its aside file relative to the copy.
- Rationale: refines HR-003, FR-93 "named to the owner"; AC-007 "the sync names version 2 and the aside file"; records no graph names (Terms) are synced like a graph, so the copy equals the live store for every record of the graph group and the lag says so (V-2 of Verify, D-548)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-007: the answer's `set_aside` holds `sample.code` with versions `[2]` and a file `aside/sample.code__<stamp>.json` that exists; TC-SLY-040: `set_aside` holds `graph_nodes|lonely.g/z` with versions `[1]`, reason "the live store won" and a file `aside/graph_nodes_lonely.g_z__<stamp>.json`, and `graph_nodes|orphan.g/x` with versions `[1]` and reason "the record exists only on the copy"; both files exist (exact)
- Verified by: TC-SLY-027, TC-SLY-040
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new; Verify, 2026-11-27, changed by A-196 (D-548, D-550); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-028 – One sync at a time
- Level: low   Subject: Persistence
- Group: SY
- Text: If a sync or a move into the copy is running, then the Storage layer shall refuse a second one on the same copy and name the copy's lock.
- Rationale: refines HR-003; D-460: one sync at a time; the lock is an operating-system lock on `<copy root>/sync.lock`, released when its process ends, so a crashed sync leaves no stale lock; "the copy" of a move is a folder that already holds `sync.lock` (D-549): a whole-store move into any other folder takes no lock and writes no lock file (REQ-SLY-007's identical round trip), so a folder never synced is not locked while its first sync and a move start at once (accepted limit, D-549)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: while one process holds the lock, a sync from a second process ends refused naming `sync.lock` and the copy is unchanged; after the first process is killed, a sync runs (exact)
- Verified by: TC-SLY-028
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-029 – An interrupted move or sync leaves complete graphs
- Level: low   Subject: Persistence
- Group: SY
- Text: If a move or a sync stops at any write, then the Storage layer shall leave every graph of the target at a complete version.
- Rationale: refines HR-007 and NFR-16 (D-406 wording: entirely as before, entirely new or at an earlier complete version of the live history); members before headers (REQ-SLY-019) is how
- Parent: HR-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: for every write position of a move, a one-graph move and a sync, on both backends (prototype CP15): after the stop no header in the target names a missing member (exact)
- Verified by: TC-SLY-029
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP15); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-030 – Side records travel with their graph
- Level: low   Subject: Persistence
- Group: SR
- Text: Where the tables `arrangements` and `graph_changes` exist, the Storage layer shall carry each graph's records of them in every move, one-graph move and sync.
- Rationale: refines HR-004 and HR-006; AC-033 "every entry arrives unchanged"; D-460: the side tables of VIEW (A-172) are carried by an explicit list in the transfer module, no contract change; the checks skip while the tables are missing (until VIEW merges)
- Parent: HR-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-033: a graph with two recorded changes and an arrangement, moved and synced, has the same `graph_changes` and `arrangements` records at the destination; a version kept without its record of changes (VIEW REQ-API-040, `logged` false) arrives without one, and no record is made up (exact)
- Verified by: TC-SLY-030
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-031 – The one-graph move
- Level: low   Subject: Persistence
- Group: SR
- Text: When the backend asks to move one graph, the Storage layer shall copy the versions of the graph and its members that the target lacks, header last, leaving other graphs unchanged.
- Rationale: refines HR-001 and HR-003; the mechanism of AC-027 (FR-95: a keep reaches the copy at once) and AC-033 (FR-81); signature `move_graph(source, target, graph_id)` agreed with VIEW (D-465), the call site is EDIT's; a target whose history of the graph differs is refused with `conflict`, because only the sync may set aside, cut back or remove on the copy (owner, D-467)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: after a new version of `cp2.multi` in the live store, the one-graph move adds exactly that version and its new members to the copy, and every other record of the copy is unchanged; with a copy that holds a version 5 of its own, the move ends with `conflict` naming `cp2.multi` and the copy is unchanged (exact)
- Verified by: TC-SLY-031
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP2); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-032 – The format marker
- Level: low   Subject: Persistence
- Group: PT
- Text: When the Storage layer writes into a set of files that has no format marker, it shall first write the marker with the format it knows.
- Rationale: refines HR-008 and NFR-15 "a set made by an older version is read completely or converted by a stated step"; without a marker a later MIA cannot tell what it opens (D-460)
- Parent: HR-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: a move into an empty folder leaves `mia-store.json` holding `{"format": 1}` (exact)
- Verified by: TC-SLY-032
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-033 – An older set without unscoped records is read
- Level: low   Subject: Persistence
- Group: PT
- Text: Where a set of files has no format marker and every graph-group record in it is scoped, the Storage layer shall read it as the format it knows.
- Rationale: refines HR-008; the sets written by CORE and RULES have no marker yet but are already in the stored form; library documents (`workflows`, `context_graphs`) are a current table, not an older format
- Parent: HR-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: a set written by today's code without a marker, holding scoped graphs and `workflows` documents, is moved and synced like a format-1 set (exact)
- Verified by: TC-SLY-033
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-034 – An older set with unscoped records is refused
- Level: low   Subject: Persistence
- Group: PT
- Text: If a set of files without a format marker holds an unscoped graph-group record, then the Storage layer shall refuse to move or sync the set, naming the record and MIGRATION's conversion step.
- Rationale: refines HR-008 and NFR-15 "converted by a stated step"; the conversion is G-V4.GRAPHSTORE.MIGRATION's (D-460); IDs before A-167 were plain
- Parent: HR-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: a set holding `graph_nodes/n1` (no slash) gives a refusal naming `graph_nodes`, `n1` and the conversion step, and nothing is written (exact)
- Verified by: TC-SLY-034
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-035 – A newer set is refused
- Level: low   Subject: Persistence
- Group: PT
- Text: If the format marker of a set of files names a format greater than the one the Storage layer knows, then the Storage layer shall refuse to open the set and name both formats.
- Rationale: refines HR-008; an older MIA must not write into a set it cannot read completely (NFR-16)
- Parent: HR-008
- Priority: Should
- Verification method: Test
- Acceptance criterion: a set with `{"format": 2}` is refused naming 2 and 1, and no file in it changes (exact)
- Verified by: TC-SLY-035
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new; verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-036 – A rerun finishes an interrupted move or sync
- Level: low   Subject: Persistence
- Group: SY
- Text: When a move or a sync that stopped at a write is run again, the Storage layer shall finish it so that the target holds the same records as after an uninterrupted run.
- Rationale: refines HR-007 and NFR-16 "an interrupted move or sync can be run again to finish"
- Parent: HR-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: for every write position of REQ-SLY-029's runs: after the rerun the target equals the result of an uninterrupted run, record by record (exact)
- Verified by: TC-SLY-036
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP15); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-037 – No path of the machine in a set
- Level: low   Subject: Persistence
- Group: PT
- Text: The Storage layer shall write no absolute file path of the machine into a set of files.
- Rationale: refines HR-008 and NFR-15 "a set made on one machine works on another"; AC-008 "no file holds a path of where it was made"; aside paths in answers are relative to the copy (REQ-SLY-027); the folders a check makes lie under the system's temporary folder, outside home and without the source's token, so each is searched too (V-4 of Verify, D-548)
- Parent: HR-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-008: after a move, a sync with an aside file and a copy of the folder to another place, no file of either folder contains the source folder's absolute path, the absolute path of any folder the check made, or the home folder (exact)
- Verified by: TC-SLY-037
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new; Verify, 2026-11-27, changed by A-197 (D-548, D-550); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-038 – A differing graph is cut back, never removed first
- Level: low   Subject: Persistence
- Group: SY
- Text: When the sync replaces a differing graph on the copy, the Storage layer shall cut its header back to the last version both stores share before cutting back its members.
- Rationale: refines HR-007 and NFR-16 (D-406: never missing, at worst an earlier complete version); the prototype removed the header first, so an interrupted sync left the graph missing from the copy until a rerun (owner, D-466). Cutting back is a backend operation of N-3.1 on both backends (files: the version list rewritten atomically; PostgreSQL: the versions above n deleted), used only by the sync after the aside file is durable (REQ-SLY-026); no IF-102 change. After the cut the live versions follow members first (REQ-SLY-019). A graph only on the copy has no shared version and is removed, header first
- Parent: HR-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-007 with a fault injected at every write of the sync, on both backends: after each stop `sample.code` is listed on the copy at version 1 (the shared one), at the copy's version 2 or at the live version 2, never missing, and every header names only existing members (exact)
- Verified by: TC-SLY-038
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (owner D-466, finding in the SY review); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27

### REQ-SLY-039 – Lag and sync on command
- Level: low   Subject: Persistence
- Group: AS
- Text: The Storage layer shall offer the lag and the sync of a copy as commands of its storage tool, next to the move commands.
- Rationale: refines HR-006 and FR-93 "when the owner runs the sync" (OC-2 "on command"); `python -m MIA.migrate lag --copy DIR` and `sync --copy DIR`, the live store from the store setting; it may run while MIA runs, the lock (REQ-SLY-028) keeps one sync at a time; no API route, which would need a new IF-104 version (owner, D-467)
- Parent: HR-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-006: `lag --copy` prints the line of `cp2.multi` (live 6, copy 4, behind) and exits 0; `sync --copy` then reports the records added and exits 0; a refused sync (lock held) is one line and exit code 1 (exact)
- Detail: `lag` prints one line per graph, or record no graph names, that is not current (`<id> live <n> copy <n> <state> [<reason>]`) and nothing when the copy is current; `sync` prints `synced <n> records, set aside <n> graphs` (the count takes in records no graph names) and one more line `  <id>: versions [...] set aside in <copy folder>/<aside file> (<reason>)` for each graph or record it set aside; a refused lag, sync or move prints one line `refused: ... (nothing was written)` and exits 1 (a stale target `conflict: ...`, a missing folder `no such folder: ...`, an unopened database `cannot open the database: ...`).
- Verified by: TC-SLY-039
- Status: Verified
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (owner D-467, finding in the AS review); verified (G-V4.GRAPHSTORE.TRANSFER verification report and re-verify of the fix commits, both boxes ticked by the owner 2026-11-27) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/requirements.md` at the merge (plan.md, "At the merge"); the Status stays as approved until the owner sets Verified.; Verified confirmed in Emacs on 2026-11-27
