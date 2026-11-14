# Requirements: Record tables (N-3.3, low level)

**Parent:** `specs/mia/nodes/N-3-database/requirements.md` (N-3)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The 14 record tables of IF-302 (history, which also holds the summaries and the chat log, memory, votes, tasks, memos, accounts, presets, gestures, run results, trust values, cases, behaviours, workflow lifecycles and reports), with their schemas and rules for deletion. Provides IF-302. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-RTB-001 – Shared state held
- Level: low   Subject: Persistence
- Text: The Record tables shall define the 15 tables of IF-302 v8: history, memory, votes, tasks, memos, accounts, presets, gestures, runs (run results), source_trust (trust values of sources), cases, behaviours, workflow_meta, reports and skill_runs (the run records of the Skill run view, REQ-RTB-007); summaries and the chat log are records of history.
- Rationale: refines REQ-DB-002
- Parent: REQ-DB-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a record of each kind is written and read back identically
- Verified by: TC-RTB-001
- Status: Approved
- History: 2026-10-31 D-161: the 14 tables of IF-302 v5 listed (it named summaries and a chat log, which are records of history, and missed six tables)
- History (cont.): A-141 (G-V3.PANEL, approved 2026-11-08, D-302): 15 tables, skill_runs added after reports (REQ-RTB-007); applied in Implement of G-V3.PANEL T-01 (2026-11-08, owner's ruling on the conflict with the unit test); Verified again after the next verification

### REQ-RTB-002 – Run results
- Level: low   Subject: Persistence
- Text: The Record tables shall define the table of run results with the required fields workflow, workflow_version, model_pin and benchmark_version and refuse a record that lacks one.
- Rationale: refines REQ-DB-010
- Parent: REQ-DB-010
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: each stored result carries the three versions
- Verified by: TC-RTB-002
- Status: Verified
- History: –

### REQ-RTB-003 – Votes stored
- Level: low   Subject: Persistence
- Text: The Record tables shall define the table of votes with the required fields user, subject, category (one of four) and value (1 or -1); the time of a vote is that of its version.
- Rationale: refines REQ-DB-012
- Parent: REQ-DB-012
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-18: 100 % of scripted votes read back complete
- Verified by: TC-RTB-003
- Status: Verified
- History: –

### REQ-RTB-004 – Memory records
- Level: low   Subject: Persistence
- Text: The Record tables shall define the table of memory records with the required fields text and source, as deletable records.
- Rationale: refines REQ-DB-013
- Parent: REQ-DB-013
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-24: a deleted record is gone (exact)
- Verified by: TC-RTB-004
- Status: Verified
- History: –

### REQ-RTB-005 – Tasks and memos exact
- Level: low   Subject: Persistence
- Text: The Record tables shall define the tables of tasks and memos with the required field text, as deletable records, and validate a document without changing it.
- Rationale: refines REQ-DB-014
- Parent: REQ-DB-014
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12: 50 of 50 items read back identical (exact)
- Verified by: TC-RTB-005
- Status: Verified
- History: –

### REQ-RTB-006 – Source trust stored
- Level: low   Subject: Persistence
- Text: The Record tables shall define the table of the trust values of sources as versioned records that are not deletable.
- Rationale: refines REQ-DB-015
- Parent: REQ-DB-015
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-3: an edited trust value survives a restart
- Verified by: TC-RTB-006
- Status: Approved
- History: –

### REQ-RTB-007 – Skill runs stored
- Level: low   Subject: Persistence
- Text: The Record tables shall define the table skill_runs with the required fields run, skill, skill_version, account, started and state, as versioned records that are deletable.
- Rationale: refines REQ-DB-002; one record per skill run for the Skill run view, A-141 (FR-46)
- Parent: REQ-DB-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: definitions() names skill_runs as versioned and deletable; a run record lacking one of the six fields is rule schema with that field as detail; a complete one is accepted (exact)
- Verified by: TC-RTB-007
- Status: Draft
- History: A-141 (proposed 2026-11-08, G-V3.PANEL), new; owner 2026-11-08: a new table skill_runs, REQ-RTB-007

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
- Verified by: TC-IF-302-01..07
- Status: Verified
- History: v0, amendment 5/7 (2026-10-25); 2026-10-31 A-61 (D-161): IF-302 v6; Verified by names TC-IF-302-01..07 (it said 01..03); 2026-10-31 A-67 (D-170): IF-302 v7, deletable are exactly history, memory, tasks, memos
