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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Relaxed: TD-06
- Target: the five seed entries in `library/workflows` pass validate(workflows, ...) and TC-GTB-005, rewritten for the entry format of FB-03, runs green
- History: A-66 (2026-10-31): Relaxed TD-06 (D-160, D-169)

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
- Verified by: TC-IF-301-01..04
- Frozen: G-V2
- Status: Verified
- History: v0, amendment 5/7 (2026-10-25); v1, A-60 (2026-10-31): session limit and malformed parts

## Iteration 2 (goal G-V2, skill rework: foundation)

## Groups
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | NR | Node and edge records: graphs as records (FR-40) | REQ-GTB-005, REQ-GTB-006, REQ-GTB-007, REQ-GTB-008 |
| 2 | TY | Types: rebuilding data classes from type IDs, schemas (FR-40) | REQ-GTB-009, REQ-GTB-010, REQ-GTB-011, REQ-GTB-012 |
| 3 | VR | Versions and round trip: edits as versions, stored equals rebuilt (FR-40) | REQ-GTB-013, REQ-GTB-014 |
| 4 | CP | Compatibility: the document form during the transition (FR-40) | REQ-GTB-015 |

### REQ-GTB-005 – Node records
- Level: low   Subject: Persistence
- Text: The Graph tables shall store each node of a workflow or context graph as a record of an ID and a JSON field that holds a fixed type.
- Rationale: refines FR-40; amends IF-301 (A-89, conflict 2)
- Parent: FR-40
- Group: NR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a node written and read has the same ID and JSON field, the type is present (exact)
- Verified by: TC-GTB-005
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-006 – Edge records
- Level: low   Subject: Persistence
- Text: The Graph tables shall store each edge as a record of an ID, a start node, an end node and a JSON field.
- Rationale: refines FR-40
- Parent: FR-40
- Group: NR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: an edge read back has the same four fields (exact)
- Verified by: TC-GTB-006
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-007 – Fields of transform nodes
- Level: low   Subject: Persistence
- Text: The Graph tables shall hold the toolbox ID of its transform in the JSON field of a transform node.
- Rationale: refines FR-40 ('the extended JSON fields of transform and master nodes')
- Parent: FR-40
- Group: NR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a transform node read back names the same toolbox ID (exact)
- Verified by: TC-GTB-007
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-008 – Fields of master nodes
- Level: low   Subject: Persistence
- Text: The Graph tables shall hold the definition of its task and its stopping criterion in the JSON field of a master node.
- Rationale: refines FR-40; the definition itself is a record only until goal D
- Parent: FR-40
- Group: NR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a master node read back has the same definition and stopping criterion (exact)
- Verified by: TC-GTB-008
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-009 – Class from type ID
- Level: low   Subject: Persistence
- Text: When a stored node is read, the Graph tables shall rebuild its data class from the stored type ID.
- Rationale: refines FR-40
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a node of each type is rebuilt with that class and equal values (exact)
- Verified by: TC-GTB-009
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-010 – Unknown type
- Level: low   Subject: Persistence
- Text: If a stored or written node has a type ID that no registered data class has, then the Graph tables shall refuse it and name the type ID.
- Rationale: refines FR-40; unhandled type IDs would otherwise be rebuilt wrongly or lost Suggestion of the agent, not in the HLS text; the owner decides at review.
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a node with the type ID 'x.unknown' is refused with that ID (exact)
- Verified by: TC-GTB-010
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-011 – Types as schemas
- Level: low   Subject: Persistence
- Text: The Graph tables shall check the JSON field of each node and edge on write against the JSON schema of its type.
- Rationale: refines FR-40 and REQ-GTB-002
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a node whose field breaks its schema is refused naming the path of the field (exact)
- Verified by: TC-GTB-011
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-012 – No language-specific serialisation
- Level: low   Subject: Persistence
- Text: The Graph tables shall not use a language-specific serialisation to store or rebuild a graph.
- Rationale: refines FR-40; no pickle
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-31: no module of the Graph tables imports pickle, marshal or shelve (inspection, exact)
- Verified by: TC-GTB-012
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-013 – Versions kept
- Level: low   Subject: Persistence
- Text: When a node, an edge or a graph is edited, the Graph tables shall store the edit as a new version and keep every earlier version.
- Rationale: refines FR-40 and REQ-SLY-003
- Parent: FR-40
- Group: VR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: after an edit versions n and n+1 both exist and version n is unchanged (exact)
- Verified by: TC-GTB-013
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-014 – Rebuilt equals stored
- Level: low   Subject: Persistence
- Text: When a stored graph is read and rebuilt, the Graph tables shall give a graph equal to the one that was stored.
- Rationale: refines FR-40
- Parent: FR-40
- Group: VR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: property test on generated graphs: write, read, rebuild, equal (exact)
- Verified by: TC-GTB-014
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new

### REQ-GTB-015 – Document form during the transition
- Level: low   Subject: Persistence
- Text: While IF-301 v1 and IF-203 v0 are in use, the Graph tables shall return a stored workflow also in the document form of those interfaces.
- Rationale: refines FR-40; owner decision 2026-11-05 (conflict 2): the document form stays readable during the transition
- Parent: FR-40
- Group: CP
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: the contract suites of IF-301 v1 and IF-203 v0 still pass unchanged on converted skills (exact)
- Verified by: TC-GTB-015
- Status: Draft
- History: G-V2 Plan step 1 (2026-11-07), new; 2026-11-07 review: IF-203 v1 corrected to v0, the old interface, consistent with A-90 (owner approved)

