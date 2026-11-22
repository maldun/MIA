# Requirements: G-V4.GRAPHSTORE.TRANSFER (low level, new and changed items)

**Top-level spec:** `specs/mia/goals/G-V4.GRAPHSTORE/top-level-spec.md` (FR-58, FR-59, FR-93, NFR-15, NFR-16 move and sync part)   **High-level spec:** `specs/mia/goals/G-V4.GRAPHSTORE.TRANSFER/high-level-spec.md` (HR-001 to HR-008, approved 2026-11-22)   **Status:** Draft (2026-11-22, agent by delegation D-423; the owner reviews group by group)   **Plan baseline:** –

<!-- The requirements this subgoal adds, and the proposed wording changes of requirements in force.
     Basis: the approved high-level spec, the decisions D-460, D-463, D-464, prototype rounds 02 and 03 (`graph_store_move.py`, `graph_store_sync.py`,
     cp2, cp3, cp9, cp15 on `prototype/g-v4`), the survey of 2026-11-22, the accepted cases AC-004 to AC-008, AC-027, AC-033.
     Where the requirements go at the merge: groups MV, SB, SY, SR, PT into N-3.1
     (`specs/mia/nodes/N-3-database/nodes/N-3.1-storage-layer/requirements.md`, REQ-SLY-016 and up); group AS into N-2.1
     (`specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md`, REQ-API-060 and up: VIEW keeps REQ-API-018 to 059).
     Requirements in force that stay as they are: REQ-SLY-002, 003 (versions never change), 004 (record checks on write), 007 (round trip gives identical files: every
     write into a set without a marker writes one, REQ-SLY-032, so both sides of TC-SLY-007 hold it), 008 (backup), 012 (realise IF-102);
     VIEW's REQ-API-018 to 021 (the store setting: TRANSFER adds the copy on top of it); REQ-API-022 is replaced by REQ-API-064 once a copy is set.
     28 new and 2 changed requirements (30, above the split hint of 25; goal.md Split check, the owner confirms in the review). -->

## Terms
| Term | Meaning |
|---|---|
| live store | the store that VIEW's store setting names (REQ-API-018): the master; graphs are changed only there (FR-95 of EDIT) |
| copy | a set of files in a folder that the copy setting names; MIA reads graphs from it while it is set; it follows the live store by sync |
| set of files | a folder written by the files backend: one file per record, `<table>/<id>.json`, plus the format marker |
| graph group | the tables `graphs`, `graph_nodes`, `graph_edges`, `context_nodes`, `context_edges`, `skills`, and VIEW's side tables `arrangements` and `graph_changes` (IF-302 v15) where they exist |
| members (of a graph) | the step and connection records its header names, at the versions it names; with them go its record of changes (`graph_changes`) and its arrangement (`arrangements`) |
| move (of the whole store) | copying every record of every table from a source store to a target store with versions, authors and times unchanged |
| one-graph move | copying the missing versions of one graph with its members from one store to another (called after a keep, FR-95, FR-81) |
| lag | per graph of the graph group: the number of versions of its header in the live store and in the copy, and its state `current`, `behind`, `differs`, `copy_only` or `refused` with a reason |
| differs | the copy holds a version of the graph, or of one of its members, that is not the same entry as the live store's version of that number, or a version beyond the live store's newest |
| aside folder | `<copy root>/aside/`; an aside file `<graph id, / as _>__<UTC stamp>[_n].json` holds the copy's differing versions of one graph and its members with their authors and times, and the reason |
| format marker | the file `mia-store.json` in the root of a set of files, `{"format": n}`; a set without it is format 0 |
| AutoSync | the sync run by the backend at its start and at its orderly stop, while the copy setting asks for it |
| scoped record | a record of `graph_nodes`, `graph_edges`, `context_nodes` or `context_edges` whose ID is `<graph id>/<local id>` (IF-301 v3, A-167) |

## Groups
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | MV | Moving the whole store: everything arrives, damaged graphs refused, members before headers, a repeat changes nothing (FR-59, HR-001, HR-004) | REQ-SLY-016, REQ-SLY-017, REQ-SLY-018, REQ-SLY-019, REQ-SLY-020, REQ-SLY-021, REQ-SLY-009 (changed), REQ-GA-008 (changed) |
| 2 | SB | The same behaviour on files and the database, durable file writes (FR-58, HR-002, HR-005, NFR-16) | REQ-SLY-022, REQ-SLY-023 |
| 3 | SY | Lag and one-way sync: live wins, the copy's own versions set aside, one sync at a time, rerun after an interruption (FR-93, HR-003, HR-006, HR-007) | REQ-SLY-024, REQ-SLY-025, REQ-SLY-026, REQ-SLY-027, REQ-SLY-028, REQ-SLY-029, REQ-SLY-036, REQ-SLY-038 |
| 4 | SR | Side records and the one-graph move (AC-033, FR-95 and FR-81 mechanisms) | REQ-SLY-030, REQ-SLY-031 |
| 5 | PT | Portable sets: the format marker, older and newer sets, no paths (NFR-15, HR-008) | REQ-SLY-032, REQ-SLY-033, REQ-SLY-034, REQ-SLY-035, REQ-SLY-037 |
| 6 | AS | The copy setting in the backend: reading the copy, AutoSync at start and stop, the real store answer (FR-58, FR-93, D-460) | REQ-API-060, REQ-API-061, REQ-API-062, REQ-API-063, REQ-API-064 |

## Requirements

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP2)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: survey defect 2, D-460)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: survey defect 1, prototype CP2)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP2, CP14)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (survey)

### REQ-SLY-024 – The lag of every graph
- Level: low   Subject: Persistence
- Group: SY
- Text: When the owner asks for the lag, the Storage layer shall list every graph that is not current, with its versions in the live store and the copy, its state and its reason.
- Rationale: refines HR-006 and FR-93 "MIA shows how far the copy lags before a sync"; the states and the line format follow the prototype (`graph_store_sync.lag`)
- Parent: HR-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-006: `cp2.multi` is listed as live 6, copy 4, `behind`; AC-007: `sample.code` is listed as `differs`; a graph of kind `swarm` is listed as `refused` with reason `unknown_kind`; no other graph is listed (exact)
- Verified by: TC-SLY-024
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP3)

### REQ-SLY-025 – The sync brings the copy to the live store
- Level: low   Subject: Persistence
- Group: SY
- Text: When the owner runs the sync, the Storage layer shall make the history of every record of the graph group in the copy equal to its history in the live store.
- Rationale: refines HR-003, HR-006 and FR-93 "the copy receives the missing versions and equals the live store"; the sync covers the graph group only (D-460; reading of FR-58 shown in the plan review)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-006 and AC-007 with the live store on files and on the database: after the sync every record of the graph group has the same history in both stores; a second sync adds 0 records (exact)
- Verified by: TC-SLY-025
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP3)

### REQ-SLY-026 – The copy's own versions set aside before they go
- Level: low   Subject: Persistence
- Group: SY
- Text: If a graph differs or exists only on the copy, then the Storage layer shall write the copy's differing versions of the graph and its members durably to an aside file before removing them.
- Rationale: refines HR-003 and FR-93 "the copy's differing versions are saved aside and named to the owner, not discarded"; removing on the copy is a backend operation of N-3.1, not of IF-102 (D-460)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-007: the aside file holds the copy's version 2 of `sample.code` with its author and time; with a fault injected between the aside write and the first removal, the copy still holds version 2 and the aside file is complete (exact)
- Verified by: TC-SLY-026
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP3, CP15)

### REQ-SLY-027 – The sync names what it set aside
- Level: low   Subject: Persistence
- Group: SY
- Text: When a sync has set versions aside, the Storage layer shall name in its answer each such graph with its versions and the path of its aside file relative to the copy.
- Rationale: refines HR-003, FR-93 "named to the owner"; AC-007 "the sync names version 2 and the aside file"
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-007: the answer's `set_aside` holds `sample.code` with versions `[2]` and a file `aside/sample.code__<stamp>.json` that exists (exact)
- Verified by: TC-SLY-027
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new

### REQ-SLY-028 – One sync at a time
- Level: low   Subject: Persistence
- Group: SY
- Text: If a sync or a move into the copy is running, then the Storage layer shall refuse a second one on the same copy and name the copy's lock.
- Rationale: refines HR-003; D-460: one sync at a time; the lock is an operating-system lock on `<copy root>/sync.lock`, released when its process ends, so a crashed sync leaves no stale lock
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: while one process holds the lock, a sync from a second process ends refused naming `sync.lock` and the copy is unchanged; after the first process is killed, a sync runs (exact)
- Verified by: TC-SLY-028
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP15)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP15)

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
- Status: Approved
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (owner D-466, finding in the SY review)

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
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

### REQ-SLY-031 – The one-graph move
- Level: low   Subject: Persistence
- Group: SR
- Text: When the backend asks to move one graph, the Storage layer shall copy the versions of the graph and its members that the target lacks, header last, leaving other graphs unchanged.
- Rationale: refines HR-001 and HR-003; the mechanism of AC-027 (FR-95: a keep reaches the copy at once) and AC-033 (FR-81); signature `move_graph(source, target, graph_id)` proposed to VIEW (D-464 (2))
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: after a new version of `cp2.multi` in the live store, the one-graph move adds exactly that version and its new members to the copy, and every other record of the copy is unchanged (exact)
- Verified by: TC-SLY-031
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype CP2)

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
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

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
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

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
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

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
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new

### REQ-SLY-037 – No path of the machine in a set
- Level: low   Subject: Persistence
- Group: PT
- Text: The Storage layer shall write no absolute file path of the machine into a set of files.
- Rationale: refines HR-008 and NFR-15 "a set made on one machine works on another"; AC-008 "no file holds a path of where it was made"; aside paths in answers are relative to the copy (REQ-SLY-027)
- Parent: HR-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-008: after a move, a sync with an aside file and a copy of the folder to another place, no file of either folder contains the source folder's absolute path or the home folder (exact)
- Verified by: TC-SLY-037
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new

### REQ-API-060 – Graphs read from the copy
- Level: low   Subject: WebApplication
- Group: AS
- Text: Where the configuration names a copy folder, the API and accounts shall read the graphs of IF-104 v2 from the copy.
- Rationale: refines HR-002 and FR-58 "so that MIA can run daily on the copy"; on top of VIEW's store setting (REQ-API-018); writes go to the live store (FR-95 of EDIT, not here)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: with a live store and a copy holding a different version of one graph, `GET` of that graph through IF-104 v2 answers the copy's version (exact)
- Verified by: TC-API-060
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

### REQ-API-061 – AutoSync off unless asked
- Level: low   Subject: WebApplication
- Group: AS
- Text: Where the configuration does not switch AutoSync on, the API and accounts shall run no sync at start or stop.
- Rationale: refines HR-003; D-460: AutoSync is off by default, until the owner's later gate MIA runs on files (D-460 (1))
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: start and orderly stop with a copy set and no AutoSync setting leave the copy unchanged while the live store has a newer version (exact)
- Verified by: TC-API-061
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

### REQ-API-062 – AutoSync at start and at an orderly stop
- Level: low   Subject: WebApplication
- Group: AS
- Text: While AutoSync is switched on, the API and accounts shall run the sync before it answers the first request and after it has answered the last one at an orderly stop.
- Rationale: refines HR-003 and FR-93 "when MIA starts or stops in an orderly way"; the stop hook is the `graceful_shutdown` list (survey: `__main__.py:104`), before the database is closed
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: with AutoSync on, a newer live version is in the copy before the first answer, and a version written to the live store while running is in the copy after the orderly stop (exact)
- Verified by: TC-API-062
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (basis: prototype `AutoSync`)

### REQ-API-063 – An unreachable live store does not stop the start
- Level: low   Subject: WebApplication
- Group: AS
- Text: If the live store does not answer when AutoSync runs, then the API and accounts shall go on with the copy and report that the sync did not run, naming the live store.
- Rationale: refines HR-003; D-460 "an unreachable live store is a report, not a failure"; the editor is then read-only (FR-95, EDIT)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: with AutoSync on and the live store's address unreachable, the backend starts, answers graphs from the copy, and its log holds one line naming the live store and "sync not run" (exact)
- Verified by: TC-API-063
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460)

### REQ-API-064 – The store answer while a copy is set
- Level: low   Subject: WebApplication
- Group: AS
- Text: While a copy is set, the API and accounts shall answer the store with `shown` copy, `live_reachable` as the live store answers now, and the lag of the copy.
- Rationale: refines HR-006 and FR-93 "MIA shows how far the copy lags"; the lag in IF-104 v2 terms: `graphs` = the number of graphs not current, `since` = the time of the oldest live version the copy lacks, null when none; makes VIEW's fixed fields of IF-104 v2 real without a new version (D-460 (2), REQ-API-022)
- Parent: HR-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-006 before the sync: `GET /api/v2/store` gives `shown: "copy"`, `live_reachable: true`, `lag: {"graphs": 1, "since": <time of live version 5 of cp2.multi>}`; after the sync `lag: {"graphs": 0, "since": null}` (exact)
- Verified by: TC-API-064
- Status: Draft
- History: G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, new (D-460 (2))

## Changed requirements (proposed; the approved text in `In force:` stays in force until the owner approves the change, M8)

### REQ-SLY-009 – Library export and seed
- Level: low   Subject: Persistence
- Group: MV
- In force (Verified, G-V1): "The Storage layer shall export library entries to files and seed them from files with identical entries."
- Text: The Storage layer shall export the library entries and the graph group to a set of files and seed them from one with identical entries, as commands of the storage tool.
- Rationale: refines REQ-DB-009 and REQ-GA-008 (moved here, D-367, D-460); the stored graphs are part of the library since CORE; a command, not a page function
- Parent: REQ-DB-009
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: export then seed gives identical entries, now also for every record of the graph group of the sample store, with members before headers (exact)
- Verified by: TC-SLY-009
- Status: Approved
- History: G-V1, verified; G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, change proposed (graph group, REQ-GA-008)

### REQ-GA-008 – Library export and seed
- Level: high   Subject: GraphApp
- Group: MV
- In force (Approved, G-V1, out of G-V1 by D-177): "The Graph app shall offer the export of the library to files and the seed from files."
- Text: The Graph app shall leave the export and the seed of the library to the commands of the Storage layer (superseded by REQ-SLY-009).
- Rationale: D-367 moved export and seed from the graph app to GRAPHSTORE; D-460 re-parents it to FR-59 as a storage command (shown in the plan review); the Graph app keeps no export button
- Parent: FR-22
- Priority: Could
- Verification method: Inspection
- Acceptance criterion: the Graph app's page has no export or seed control, and REQ-SLY-009's check covers export and seed (exact)
- Verified by: TC-SLY-009
- Status: Approved
- History: G-V1, approved, out (D-177); G-V4.GRAPHSTORE.TRANSFER Plan step 1b, 2026-11-22, superseded by REQ-SLY-009 (proposed)

## Notes for other subgoals (not requirements of TRANSFER)
- VIEW: REQ-API-022 (fixed fields) holds while no copy is set; REQ-API-064 gives the real values. VIEW builds the backend choice (config `store` = `files` | `database`, address from `MIA_DATABASE_URL`; VIEW D-440 (4), commit `3f0bc69a` on `goal/v4.view`); the copy setting of REQ-API-060 lies on top of it. VIEW agreed to `move_graph(source, target, graph_id) -> {"graphs": 1, "records": n}` with the order members, `graph_changes`, `arrangements`, header; no VIEW requirement calls it (VIEW's save route writes the live store only), so the call site belongs to EDIT.
- EDIT: writes go to the live store; with the live store unreachable the editor is read-only (FR-95); TRANSFER only reports `live_reachable`.
- MIGRATION: the conversion step named by REQ-SLY-034; the document form and its tables stay movable as plain tables until MIGRATION retires them.
- Deploy: tests and SMOKE-TRANSFER-001 name the database `mia_smoke` and refuse any other target (a test requirement like TR-CORE-009); SMOKE-RULES-001 runs with it (D-462).
