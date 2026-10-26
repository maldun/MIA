# Requirements: Graph tables (N-3.2, low level)

**Parent:** `specs/mia/nodes/N-3-database/requirements.md` (N-3)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The tables of workflows and context graphs and the graph rules that every write of such a record must pass (the second line of defence for TB-edit). Provides IF-301. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-GTB-001 – Shared state held
- Level: low   Subject: Persistence
- Text: The Graph tables shall define the tables of workflows (library entries) and context graphs.
- Rationale: refines REQ-DB-002
- Parent: REQ-DB-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a record of each kind is written and read back identically
- Verified by: TC-GTB-001
- Status: Approved
- History: –

### REQ-GTB-002 – Schema validation on write
- Level: low   Subject: Persistence
- Text: When asked to validate a workflow, the Graph tables shall report the first broken rule of node identity, adjacent data nodes, adjacent process nodes, session stopping criterion and cycle (IF-301).
- Rationale: refines REQ-DB-004
- Parent: REQ-DB-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16, AC-27: each of the rules (identity, adjacent data nodes, cycle, session stopping criterion) is refused with its name; protects against TB-edit
- Verified by: TC-GTB-002, TC-GTB-003
- Status: Approved
- History: –

### REQ-GTB-003 – Context graphs stored
- Level: low   Subject: Persistence
- Text: The Graph tables shall define the table of context graphs as versioned records that are not deletable and are validated by the graph rules; the Storage layer keys them by workflow id or by chat.
- Rationale: refines REQ-DB-011
- Parent: REQ-DB-011
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: a context graph edit creates a new version
- Verified by: TC-GTB-004
- Status: Approved
- History: –

### REQ-GTB-004 – Example workflows as seed data
- Level: low   Subject: Persistence
- Text: The Graph tables shall ship the example workflows lookup, verify and review, the search command and method transfer (off by default) as seed entries of the library, with their specifications, context graphs and benchmark references.
- Rationale: refines REQ-DB-018
- Parent: REQ-DB-018
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-9, AC-10: after a seed from files the library holds the five entries; export then seed gives identical entries (exact)
- Verified by: TC-GTB-005
- Status: Approved
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-301 – Graph table definitions and validation
- Level: low   Subject: Persistence
- Text: The Graph tables shall provide the Storage layer with the definitions of the tables of workflows and context graphs and their validation IF-301 as specified in contracts/IF-301-graph-tables.md.
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-DB-004, REQ-DB-011
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: the contract suite test_if_301_graph_tables.py passes against the mock (stage 1) and the Graph tables (stage 2)
- Verified by: TC-IF-301-01..03
- Status: Approved
- History: v0, amendment 5/7 (2026-10-25)
