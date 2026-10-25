# Requirements: Record tables (N-3.3, low level)

**Parent:** `specs/mia/nodes/N-3-database/requirements.md` (N-3)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The tables of the history, summaries, chat log, memory, votes, tasks, memos, presets, gestures, run results and trust values, with their schemas and rules for deletion. Provides IF-302. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-RTB-001 – Shared state held
- Level: low   Subject: Persistence
- Text: The Record tables shall define the tables of the history, summaries, chat log, votes, memory, tasks, memos, presets, gestures and run results.
- Rationale: refines REQ-DB-002
- Parent: REQ-DB-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a record of each kind is written and read back identically
- Verified by: –
- Status: Draft
- History: –

### REQ-RTB-002 – Run results
- Level: low   Subject: Persistence
- Text: The Record tables shall store the run results with workflow version, model pin and benchmark version.
- Rationale: refines REQ-DB-010
- Parent: REQ-DB-010
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: each stored result carries the three versions
- Verified by: –
- Status: Draft
- History: –

### REQ-RTB-003 – Votes stored
- Level: low   Subject: Persistence
- Text: The Record tables shall store each vote with user, time, subject and category.
- Rationale: refines REQ-DB-012
- Parent: REQ-DB-012
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-18: 100 % of scripted votes read back complete
- Verified by: –
- Status: Draft
- History: –

### REQ-RTB-004 – Memory records
- Level: low   Subject: Persistence
- Text: The Record tables shall store memory records with their source and delete a record when asked.
- Rationale: refines REQ-DB-013
- Parent: REQ-DB-013
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-24: a deleted record is gone (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-RTB-005 – Tasks and memos exact
- Level: low   Subject: Persistence
- Text: The Record tables shall store the text of tasks and memos without change.
- Rationale: refines REQ-DB-014
- Parent: REQ-DB-014
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12: 50 of 50 items read back identical (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-RTB-006 – Source trust stored
- Level: low   Subject: Persistence
- Text: The Record tables shall keep the users' edits of the trust of a source.
- Rationale: refines REQ-DB-015
- Parent: REQ-DB-015
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-3: an edited trust value survives a restart
- Verified by: –
- Status: Draft
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-302 – Record table definitions and validation
- Level: low   Subject: Persistence
- Text: The Record tables shall provide the Storage layer with the definitions of the record tables and their validation IF-302 as specified in contracts/IF-302-record-tables.md.
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-DB-002, REQ-DB-012
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-18, AC-24: the contract suite test_if_302_record_tables.py passes against the mock (stage 1) and the Record tables (stage 2)
- Verified by: TC-IF-302-01..03
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)
