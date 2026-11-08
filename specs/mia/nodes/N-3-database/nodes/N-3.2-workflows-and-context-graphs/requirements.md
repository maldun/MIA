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
| 2 | TY | Types: rebuilding data classes from type IDs, schemas (FR-40) | REQ-GTB-009, REQ-GTB-010, REQ-GTB-011, REQ-GTB-012, REQ-GTB-022, REQ-GTB-027, REQ-GTB-028 |
| 3 | VR | Versions and round trip: edits as versions, stored equals rebuilt (FR-40) | REQ-GTB-013, REQ-GTB-014, REQ-GTB-016 |
| 4 | CP | Compatibility: the document form during the transition (FR-40) | REQ-GTB-015 |
| 5 | HD | Graph header and skill record: which members make a graph version, the skill table (FR-40, FR-36) | REQ-GTB-017, REQ-GTB-018, REQ-GTB-019, REQ-GTB-020, REQ-GTB-021 |
| 6 | CX | Context graph tables: where the nodes and edges of a context graph are kept and what is checked (FR-40, FR-41) | REQ-GTB-023, REQ-GTB-024, REQ-GTB-025, REQ-GTB-026 |

### REQ-GTB-005 – Node records
- Level: low   Subject: Persistence
- Text: The Graph tables shall store each node of a workflow or context graph as a record of an ID and a JSON field that holds a fixed type.
- Rationale: refines FR-40; amends IF-301 (A-89, conflict 2)
- Parent: FR-40
- Group: NR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a node written and read has the same ID and JSON field, the type is present (exact)
- Verified by: TC-GTB-016
- Status: Verified
- History: G-V2 Plan step 1 (2026-11-07), new; Step 3 (2026-11-07): Verified by TC-GTB-016 instead of TC-GTB-005, which is the existing check of REQ-GTB-004 (ID collision)

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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
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
- Status: Verified
- History: G-V2 Plan step 1 (2026-11-07), new; 2026-11-07 review: IF-203 v1 corrected to v0, the old interface, consistent with A-90 (owner approved)

### REQ-GTB-016 – A refused edit changes nothing
- Level: low   Subject: Persistence
- Text: If an edit of a node, an edge or a graph is refused by a check, then the Graph tables shall keep the stored version unchanged and create no new version.
- Rationale: refines FR-40 and REQ-GTB-013; asked for by the owner at the review of TC-GTB-013, 2026-11-07
- Parent: FR-40
- Group: VR
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: after a refused edit the latest version number is the one before the edit and its content is unchanged (exact)
- Verified by: TC-GTB-017
- Status: Verified
- History: G-V2.STORE Plan step 3 review (2026-11-07), new

### REQ-GTB-017 – Graph header with pinned members
- Level: low   Subject: Persistence
- Text: The Graph tables shall store the header of each graph as a record of its ID, kind, context graph ID, testbench ID, description and the ID and version of each of its nodes and edges.
- Rationale: refines FR-40; without a header nothing says which nodes and edges make graph X in version n (MODEL question c2, c3; D-264)
- Parent: FR-40
- Group: HD
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a graph header read back has the same fields and members; after one node is edited and a new header version is stored, header version 1 still names the old node version and reads the old node (exact)
- Verified by: TC-GTB-018
- Status: Verified
- History: G-V2.STORE Plan step 3, 2026-11-07, new (D-264: found by the MODEL session, IF-301 v2 draft)

### REQ-GTB-018 – Skill table
- Level: low   Subject: Persistence
- Text: The Graph tables shall store each skill as a versioned record of its ID, command, workflow graph ID and context graph ID.
- Rationale: refines FR-40 and supports REQ-WFM-040 (the Workflow management checks the content, REQ-WFM-042 stays there); D-264
- Parent: FR-40
- Group: HD
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a skill written and read back has the same four fields; an edit is a new version and the earlier one is unchanged; a record without a command is refused naming the field (exact)
- Verified by: TC-GTB-019
- Status: Verified
- History: G-V2.STORE Plan step 3, 2026-11-07, new (D-264: found by the MODEL session, IF-301 v2 draft)

### REQ-GTB-019 – Header names stored members
- Level: low   Subject: Persistence
- Text: If a graph header names a node or edge version that is not stored, then the Graph tables shall refuse the header and name that node or edge ID.
- Rationale: refines FR-40; a header with a missing member would give a graph that cannot be rebuilt (REQ-GTB-014); D-264
- Parent: FR-40
- Group: HD
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a header that names n1 at version 5 when n1 has only versions 1 and 2 is refused naming n1; the same header with version 2 is accepted (exact)
- Verified by: TC-GTB-020
- Status: Verified
- History: G-V2.STORE Plan step 3, 2026-11-07, new (D-264: found by the MODEL session, IF-301 v2 draft)

### REQ-GTB-020 – Edge names stored nodes
- Level: low   Subject: Persistence
- Text: If an edge names a start or end node that is not stored, then the Graph tables shall refuse the edge and name that node ID.
- Rationale: refines FR-40 and REQ-GTB-006; an edge to a missing node cannot be rebuilt (REQ-GTB-014); found when the IF-301 v2 text was reviewed (D-266)
- Parent: FR-40
- Group: HD
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: an edge from n1 to n9, with only n1 stored, is refused naming n9; the same edge with n9 stored is accepted (exact)
- Verified by: TC-GTB-021
- Status: Verified
- History: G-V2.STORE Plan step 4, 2026-11-07, new (D-266)

### REQ-GTB-021 – Record under its own ID
- Level: low   Subject: Persistence
- Text: If a record of a graph table is written under a record ID that differs from the ID inside the record, then the Graph tables shall refuse the record and name the field `id`.
- Rationale: refines FR-40 and REQ-GTB-005; a graph header pins its members by the ID inside the record while the storage finds them by the record ID, so a record under another ID cannot be found again (REQ-GTB-014); found in G-V2.STORE Implement T-04 (A-92)
- Parent: FR-40
- Group: HD
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a node whose own ID is n1, written under the record ID x, is refused naming `id` and nothing is stored under x; written under n1 it is accepted (exact)
- Verified by: TC-GTB-022
- Status: Verified
- History: G-V2.STORE Implement T-04, 2026-11-07, new (A-92, proposed)

### REQ-GTB-022 – Fixed fields of a node
- Level: low   Subject: Persistence
- Text: If a node is written or read with a field in its JSON field that its type's schema does not list, then the Graph tables shall refuse the node as `schema_break` naming that field.
- Rationale: refines FR-40, REQ-GTB-009, REQ-GTB-011 and REQ-GTB-014; the list of types is fixed, a node that passes the write check but cannot be rebuilt breaks the round trip, and dropping the field would lose data; found in G-V2.STORE Verify (F-01, decided 2026-11-07, A-93)
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a data node with a field `foo` and a data node with a key `id` inside its JSON field are refused as `schema_break` naming `foo` and `id`, when written and when read; the same nodes without the field are accepted (exact)
- Verified by: TC-GTB-023
- Status: Verified
- History: G-V2.STORE Verify F-01, 2026-11-07, new (A-93, proposed)

### REQ-GTB-023 – Context graph tables
- Level: low   Subject: Persistence
- Text: The Graph tables shall list `context_nodes` and `context_edges` as versioned tables whose records are never deleted.
- Rationale: refines FR-40 and FR-41; a context graph is stored in tables of its own because its node types come from the context graph itself, which the Storage layer cannot know (F-02, decided 2026-11-07/08, A-98)
- Parent: FR-40
- Group: CX
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: the definitions of the Graph tables list six record tables; a context node written twice has the versions 1 and 2; a delete of a context node or edge is refused as immutable (exact)
- Verified by: TC-GTB-024
- Status: Verified
- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed)

### REQ-GTB-024 – Context record shape
- Level: low   Subject: Persistence
- Text: If a context node lacks a text ID, a JSON object or a text type, or a context edge lacks a text end, then the Graph tables shall refuse the record naming that field.
- Rationale: refines FR-40; the Storage layer checks the shape only, the caller checks the categories before it writes (decision 14 of IF-301) (A-98)
- Parent: FR-40
- Group: CX
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a context node with data {} is refused naming `type`, one without data naming `data`, an edge without `to` naming `to`; the same records with the field are accepted (exact)
- Verified by: TC-GTB-025
- Status: Verified
- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed)

### REQ-GTB-025 – Context edge ends
- Level: low   Subject: Persistence
- Text: If a context edge names an end that is not a stored context node, then the Graph tables shall refuse the edge as `unknown_endpoint` naming that end.
- Rationale: refines FR-40 and REQ-GTB-020; the ends of a context edge are looked up in `context_nodes` only (A-98)
- Parent: FR-40
- Group: CX
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: an edge from c1 to c9 with only c1 stored is refused naming `c9`, also when a workflow node has the ID c9; an edge between stored context nodes is accepted (exact)
- Verified by: TC-GTB-026
- Status: Verified
- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed)

### REQ-GTB-026 – Context header members
- Level: low   Subject: Persistence
- Text: If a graph header of kind context names a member that is not stored in `context_nodes` or `context_edges` at that version, then the Graph tables shall refuse the header as `unknown_member` naming the member.
- Rationale: refines FR-40 and REQ-GTB-019; a header of kind workflow still looks in `graph_nodes` and `graph_edges` (A-98)
- Parent: FR-40
- Group: CX
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a context header naming c9 with only c1 stored is refused naming `c9`; a workflow header naming the context node c1 is refused naming `c1`; a context header naming c1 is accepted (exact)
- Verified by: TC-GTB-027
- Status: Verified
- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed)

### REQ-GTB-027 – Input that cannot be checked
- Level: low   Subject: Persistence
- Text: If a record is nested deeper than 200 levels or its category schema is not valid, then the Graph tables shall refuse it as `schema_break` naming the field.
- Rationale: refines FR-40 and REQ-GTB-011; before, such input gave `record_identity` with the detail `record`, which names the wrong rule (F-09, A-98); 200 levels is a fixed limit so that mock and real code agree
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a data node whose deepest value is at level 300 is refused naming `data`, one at level 150 or exactly at level 200 is accepted, one at level 201 is refused (a level is the record, an object, a list or a scalar: the record is level 1 and every value below it is one level deeper than its parent, so a scalar in the 200th object is level 201); a category whose schema is {"type": 5} is refused naming `type`; nothing raises (exact)
- Verified by: TC-GTB-028
- Status: Verified
- History: G-V2.STORE Verify F-02/F-09, 2026-11-08, new (A-98, proposed); 2026-11-08 the acceptance criterion says what a level is (F-23, A-104)

### REQ-GTB-028 – Size of a record
- Level: low   Subject: Persistence
- Text: If a record has more than 100,000 values, counting a value once for every path that reaches it, then the Graph tables shall refuse it as `schema_break` naming `data`.
- Rationale: refines FR-40 and REQ-GTB-027; a record that shares sub-objects can have an exponential number of paths and made the check run for minutes (F-22 of the Verify of G-V2.STORE, A-102); 100,000 is about 190 times the largest stored document in the repository (529 values)
- Parent: FR-40
- Group: TY
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-31: a data node whose value is a list of 99,995 numbers (100,000 values with the record, its id, its data object, its type and the list) is accepted, one of 99,996 is refused naming `data`; a record that names the same child twice on 30 levels (2**30 paths) is refused naming `data` within 5 s; nothing raises (exact)
- Verified by: TC-GTB-029
- Status: Verified
- History: G-V2.STORE Verify F-22, 2026-11-08, new (A-102, proposed)
