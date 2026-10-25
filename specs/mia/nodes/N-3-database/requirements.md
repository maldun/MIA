# Requirements: Database (N-3, high level)

**Parent:** `specs/mia/requirements.md` (top level N-0)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

Workflows, memories, history, user feedback, context graphs and accounts behind the storage layer. Provides IF-102. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-DB-001 – PostgreSQL in a container
- Level: high   Subject: Persistence
- Text: The Database shall be one PostgreSQL database in a container behind the storage interface IF-102.
- Rationale: refines NFR-8, CON-7, NFR-9
- Parent: NFR-8, CON-7, NFR-9
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15, AC-29: the container starts alone and passes the contract suite of IF-102
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-002 – Shared state held
- Level: high   Subject: Persistence
- Text: The Database shall hold the history, summaries, chat log, feedback, presets, gestures, library entries and accounts.
- Rationale: refines NFR-8
- Parent: NFR-8
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a record of each kind is written and read back identically
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-003 – Immutable versions
- Level: high   Subject: Persistence
- Text: When a versioned record is edited, the Database shall store the edit as a new version with author and time and keep the former version unchanged.
- Rationale: refines FR-7, FR-22
- Parent: FR-7, FR-22
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: version n is unchanged after version n+1 is written (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-004 – Schema validation on write
- Level: high   Subject: Persistence
- Text: If a workflow or graph does not match its schema or violates a graph rule, then the Database shall refuse to store it and name the broken rule.
- Rationale: refines FR-22, FR-7
- Parent: FR-22, FR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16, AC-27: each of the rules (identity, adjacent data nodes, cycle, session stopping criterion) is refused with its name; protects against TB-edit
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-005 – Accounts
- Level: high   Subject: Persistence
- Text: The Database shall store accounts with a salted slow password hash and let only the owner's request create one.
- Rationale: refines FR-21
- Parent: FR-21
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: no plain password is stored (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-006 – Change notification
- Level: high   Subject: Persistence
- Text: When a record changes, the Database shall tell every subscriber of the storage interface.
- Rationale: refines NFR-8, FR-5
- Parent: NFR-8, FR-5
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a second subscriber is notified within 2 s
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-007 – Reversible move from files
- Level: high   Subject: Persistence
- Text: When the owner starts the move from files to the database or back, the Database shall perform it with one command and give identical files after the round trip.
- Rationale: refines NFR-8
- Parent: NFR-8
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: files to database and back give identical files (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-008 – Backup and restore
- Level: high   Subject: Persistence
- Text: The Database shall allow backup and restore together with the other data of MIA.
- Rationale: refines FR-19, NFR-8
- Parent: FR-19, NFR-8
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7, AC-15: backup and restore round-trip returns the same records (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-009 – Library export and seed
- Level: high   Subject: Persistence
- Text: The Database shall export library entries to files and seed them from files with identical entries.
- Rationale: refines FR-22
- Parent: FR-22
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: export then seed gives identical entries (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-010 – Run results
- Level: high   Subject: Persistence
- Text: The Database shall store the run results with workflow version, model pin and benchmark version.
- Rationale: refines FR-26
- Parent: FR-26
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: each stored result carries the three versions
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-011 – Context graphs stored
- Level: high   Subject: Persistence
- Text: The Database shall store one context graph per workflow and one for the chat as versioned records.
- Rationale: refines FR-30
- Parent: FR-30
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: a context graph edit creates a new version
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-012 – Votes stored
- Level: high   Subject: Persistence
- Text: The Database shall store each vote with user, time, subject and category.
- Rationale: refines FR-27
- Parent: FR-27
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-18: 100 % of scripted votes read back complete
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-013 – Memory records
- Level: high   Subject: Persistence
- Text: The Database shall store memory records with their source and delete a record when asked.
- Rationale: refines FR-14
- Parent: FR-14
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-24: a deleted record is gone (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-014 – Tasks and memos exact
- Level: high   Subject: Persistence
- Text: The Database shall store the text of tasks and memos without change.
- Rationale: refines FR-28
- Parent: FR-28
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12: 50 of 50 items read back identical (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-015 – Source trust stored
- Level: high   Subject: Persistence
- Text: The Database shall keep the users' edits of the trust of a source.
- Rationale: refines FR-12
- Parent: FR-12
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-3: an edited trust value survives a restart
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-016 – Reachable only inside the host network
- Level: high   Subject: Persistence
- Text: The Database shall accept connections only from the other containers of the stack.
- Rationale: refines NFR-5, NFR-6
- Parent: NFR-5, NFR-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-5: a connection from the LAN is refused (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-DB-017 – Own container
- Level: high   Subject: Persistence
- Text: The Database shall start as its own container alone and by the compose stack.
- Rationale: refines NFR-9
- Parent: NFR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: starts alone and in the stack with the same configuration file
- Verified by: –
- Status: Draft
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-102 – Storage interface
- Level: high   Subject: Persistence
- Text: The Database shall provide the Backend with the storage interface IF-102 as specified in contracts/IF-102-storage-interface.md (put as a new immutable version, get, history, ids, delete where allowed, subscribe, and refusal of an invalid workflow with the broken rule named).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: NFR-8, CON-7, FR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15, AC-27: the contract suite test_if_102_storage.py passes against the mock (stage 1) and the Database (stage 2)
- Verified by: TC-IF-102-01..07
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)
