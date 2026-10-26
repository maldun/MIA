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
- Status: Approved
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
- Status: Approved
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
- Status: Approved
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
- Status: Approved
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
- Status: Approved
- History: –

### REQ-SLY-006 – Change notification
- Level: low   Subject: Persistence
- Text: When a record changes, the Storage layer shall tell every subscriber of the storage interface.
- Rationale: refines REQ-DB-006
- Parent: REQ-DB-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a second subscriber is notified within 2 s
- Verified by: TC-SLY-006
- Status: Approved
- History: –

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
- Status: Approved
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
- Status: Approved
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
- Status: Approved
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
- Status: Approved
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
- Status: Approved
- History: –
