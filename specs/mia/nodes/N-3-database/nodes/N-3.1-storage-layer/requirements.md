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
- Text: The Storage layer shall export library entries to files and seed them from files with identical entries.
- Rationale: refines REQ-DB-009
- Parent: REQ-DB-009
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: export then seed gives identical entries (exact)
- Verified by: TC-SLY-009
- Status: Verified
- History: –

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
- History: –

### REQ-SLY-013 – Depth of a document
- Level: low   Subject: Persistence
- Text: If a document that is put is nested deeper than 200 levels, then the Storage layer shall refuse it as invalid.
- Rationale: refines REQ-SLY-004 and REQ-GTB-027; one limit for every table, so that the refusal does not depend on the recursion limit of the interpreter or on how deep the caller is in the call stack (F-20 of the fifth Verify run of G-V2.STORE, A-100); the deepest real document in library, skills and eval has 19 levels
- Parent: REQ-SLY-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: a document nested 200 levels (the document is level 1) is stored, one nested 201, 600 and 990 levels is refused as StorageError `invalid` and nothing is stored, for a graph table (rule `schema_break`, detail `data`) and for another table (rule `schema`, detail `nested too deep`), on the file backend and on PostgreSQL (exact)
- Verified by: TC-SLY-012
- Status: Draft
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
- Status: Draft
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
- Status: Draft
- History: G-V2.STORE Verify F-22, 2026-11-08, new (A-102, proposed)
