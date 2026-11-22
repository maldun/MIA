# Requirements: Graph tables (N-3.2, low level)

**Parent:** `specs/mia/nodes/N-3-database/requirements.md` (N-3)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The tables of workflows and context graphs and the graph rules that every write of such a record must pass (the second line of defence for TB-edit). Provides IF-301. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

IDs of steps and connections (A-167, IF-301 v3): the IDs `n1`, `e1`, `c1`, ... named in the acceptance criteria below are local IDs. Since IF-301 v3 (REQ-GTB-029) a step or connection is stored under `<graph id>/<local id>`, so the tests write the scoped form (`wf1/n1`, `g/e1`, `h1/c1`); the rules and the expected results are unchanged.

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
- Frozen: G-V4
- Status: Verified
- History: v0, amendment 5/7 (2026-10-25); v1, A-60 (2026-10-31): session limit and malformed parts; frozen by G-V4 (D-393, 2026-11-20) after G-V2 closed

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

## Iteration 4 (goal G-V4.GRAPHSTORE.CORE, one stored truth for graphs; moved at the merge 2026-11-22, D-408)
Requirements of the subgoal G-V4.GRAPHSTORE.CORE (goal record `specs/mia/goals/G-V4.GRAPHSTORE.CORE/`: plan, test requirements TR-CORE-001 to 009, verification report). Verified 2026-11-22, with the accepted deviations V-1, V-2, V-3 (D-414).

## Groups of G-V4.GRAPHSTORE.CORE
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | SC | Steps belong to one graph: what a record ID says and what a step's history lists (FR-60) | REQ-GTB-029, REQ-GTB-030, REQ-GTB-031 |
| 4 | RD | Reading, history and both places: versions, who and when, a version as it was saved, the same refusals on files and database (FR-57) | REQ-GTB-032 |

### REQ-GTB-029 – Scoped ID of a step or connection
- Level: low   Subject: Persistence
- Group: SC
- Text: If a step or connection record is written under a non-empty ID not of the form `<graph id>/<local id>`, then the Graph tables shall refuse the record and name the rule `unscoped_id`.
- Rationale: refines FR-60 and HR-001; makes a step belong to exactly one graph by construction (D-368); amends the plain IDs of A-92 / REQ-GTB-021
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-01 (accepted case AC-002): a step written under `chat` is refused naming `unscoped_id`, under `lookup/chat` it is accepted (exact)
- Binding: fixed
- Verified by: TC-GTB-033
- Status: Verified
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03); text changed to 'a non-empty ID' (D-409), approved by the owner 2026-11-21; verified (G-V4.GRAPHSTORE.CORE verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.CORE/requirements.md` at the merge (D-408).

### REQ-GTB-030 – Header names only its own members
- Level: low   Subject: Persistence
- Group: SC
- Text: If a graph header names a step or connection whose record ID begins with the ID of another graph, then the Graph tables shall refuse the header and name the rule `unscoped_id`.
- Rationale: refines FR-60 and HR-001; a header of graph g must not pin a member of graph h
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-02: a header `g` naming `h/step` is refused naming `unscoped_id`; naming `g/step` it is accepted (exact)
- Binding: fixed
- Verified by: TC-GTB-034
- Status: Verified
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03); verified (G-V4.GRAPHSTORE.CORE verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.CORE/requirements.md` at the merge (D-408).

### REQ-GTB-031 – The first slash separates
- Level: low   Subject: Persistence
- Group: SC
- Text: The Graph tables shall take the text before the first slash of a record ID as the graph ID, and the rest as the local ID.
- Rationale: refines HR-001 and ASM-1 of round 02; confirmed by the owner (D-402); example: `lookup/a/b` is the local ID `a/b` of the graph `lookup`, so a local ID can hold slashes and a graph ID cannot
- Parent: FR-60
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-03: `lookup/a/b` is accepted as the local ID `a/b` of `lookup` and read back as `a/b` (exact)
- Binding: fixed
- Verified by: TC-GTB-035
- Status: Verified
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03); verified (G-V4.GRAPHSTORE.CORE verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.CORE/requirements.md` at the merge (D-408).

### REQ-GTB-032 – Same refusals in both places
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall refuse the same records with the same rule on the files backend and on the database backend.
- Rationale: refines FR-57 and HR-003; MIA runs on a copy of files and a live database (FR-58)
- Parent: FR-57
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-CORE-20: the cases of AC-CORE-01 to AC-CORE-02, AC-CORE-06, AC-CORE-21, AC-CORE-14 and AC-CORE-15 give the same refusal on both backends (exact)
- Binding: fixed
- Verified by: TC-GTB-036
- Status: Verified
- History: G-V4.GRAPHSTORE.CORE Plan step 1b, 2026-11-21, new (basis: prototype round 03); verified (G-V4.GRAPHSTORE.CORE verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHSTORE.CORE/requirements.md` at the merge (D-408).

## Iteration 4 (goal G-V4.GRAPHAPI.RULES, one rule set for graphs; moved at the merge 2026-11-22)
Requirements of the subgoal G-V4.GRAPHAPI.RULES (goal record `specs/mia/goals/G-V4.GRAPHAPI.RULES/`: plan, test requirements TR-RULES-001 to 009, verification report). Verified 2026-11-22 (verdict ticked by the owner); Verify findings decided in D-461: V-1 fixed (`f478e040`), V-2 corrected in the contract (A-185), V-4 accepted as stated, V-3, V-6, V-7 noted. The rule set is offered through IF-301 v4 (`contracts/IF-301-graph-tables.md`, A-170, A-185).

## Terms of G-V4.GRAPHAPI.RULES
| Term | Meaning |
|---|---|
| kind (of a graph) | the header field `kind`: `workflow` or `context` today (D-404); a graph that names no kind is a workflow graph (REQ-WFM-153) |
| registry of kinds | the one table that names, per kind, its rules in their fixed order and its run flag (D-404, HR-001) |
| run flag | yes when a graph of the kind may be run, no when it may not (FR-64 "a kind that cannot run") |
| rule report | the answer of a check: a list with one item per broken rule, in the registry's order, each `{"rule", "parts", "text"}`; an empty list when every rule is kept (HR-002) |
| parts (of a broken rule) | the local IDs of the steps or connections the rule concerns, in the order the rule finds them |
| refusal (of a run) | the answer of the run check: `{"status": "refused" or "ready", "broken": [...]}`, each item of `broken` a broken rule, an unsupplied input or the kind (HR-003) |
| unsupplied input | an input connection of a processing or loop-controlling step from a data step that has no writer, no start value in the graph and no value given with the run; settings and order connections are not inputs here |
| session setting | the `stop` or `session` field of a step, and the settings connection (`role: "settings"`) into a step (ASM-3, Q-1) |
| stored form | a graph as `{"kind"?, "nodes": [{"id", "data"}], "edges": [{"id", "from", "to", "data"}]}` with local IDs, as the Workflow management saves and reads it (CORE) |

## Groups of G-V4.GRAPHAPI.RULES
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | RS | The rule set by kind: one registry, the rules of each kind in order, the rule report (FR-63, HR-001, HR-002) | REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036, REQ-GTB-037, REQ-GTB-038, REQ-GTB-039, REQ-GTB-040 |
| 2 | RD | The eight rules: what each one finds and which parts it names (FR-63, D-375, Q-1, Q-4, Q-5) | REQ-GTB-041, REQ-GTB-042, REQ-GTB-043, REQ-GTB-044, REQ-GTB-045, REQ-GTB-046, REQ-GTB-047, REQ-GTB-048 |
| 3 | RF | The refusal of a run as a report: kind, broken rules, unsupplied inputs (FR-64, HR-003) | REQ-GTB-049, REQ-GTB-050, REQ-GTB-051 |
| 6 | DF | The document form stays as it is until MIGRATION (Q-6) | REQ-GTB-052 |

### REQ-GTB-033 – One registry of kinds
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall offer through IF-301 one registry of kinds that names, for each kind of graph, its rules in their fixed order and its run flag.
- Rationale: refines HR-001 and FR-63 "written in one place, chosen by the kind" (D-404, D-417); the prototype found three rule implementations today (finding 1)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the registry read through IF-301 lists exactly the kinds `workflow` and `context`, each with a list of rule names and a yes/no for running (exact)
- Binding: fixed
- Verified by: TC-GTB-037
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-034 – The eight workflow rules in order
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall list in the registry of kinds for the kind `workflow` the rules `step_identity`, `step_kind`, `connection_endpoints`, `duplicate_connection`, `adjacency`, `single_writer`, `stop_limit` and `cycle`, in this order.
- Rationale: refines HR-001; D-375: local facts first, the cycle last; no ninth rule (Q-2: the known-tool check goes to G-V4.GRAPHAPI.CODE)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the rules of `workflow` are exactly these eight names in this order (exact)
- Binding: fixed
- Verified by: TC-GTB-037
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-035 – The rules of a context graph
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall list in the registry of kinds for the kind `context` the rules `step_identity`, `connection_endpoints` and `duplicate_connection`, in this order, with the definitions used for `workflow`.
- Rationale: refines HR-001; one definition per rule keeps the context set from drifting (D-404); rule 4 in full, so two identical connections with different IDs are refused (Q-3); CONTEXT may add rules by amendment (FR-75, ASM-4)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the rules of `context` are exactly these three names in this order; a context graph with two identical connections under different IDs is reported with `duplicate_connection` naming the second ID (exact)
- Binding: fixed
- Verified by: TC-GTB-037, TC-GTB-038
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, finding 7); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-036 – Which kinds can run
- Level: low   Subject: Persistence
- Group: RS
- Text: The Graph tables shall set the run flag of the kind `workflow` to yes and the run flag of the kind `context` to no.
- Rationale: refines HR-001 and FR-64 "a kind that cannot run"; context steps are categories, not data and processing steps (D-404)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: `workflow` can run, `context` cannot (exact)
- Binding: fixed
- Verified by: TC-GTB-037
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-037 – The rule report
- Level: low   Subject: Persistence
- Group: RS
- Text: When a graph in stored form is checked, the Graph tables shall return one item per broken rule of the graph's kind, in registry order, each with rule name, parts and sentence.
- Rationale: refines HR-002 and OC-1 "the same broken rules in the same order, each with its steps or connections"; the sentence is what the editor and a refused run show; a graph that keeps every rule gives an empty list
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a workflow graph with a missing connection end and two writers of one data step gives exactly two items, `connection_endpoints` before `single_writer`, each with its parts and a non-empty sentence; a sound graph gives `[]` (exact)
- Binding: fixed
- Verified by: TC-GTB-039
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, CP19); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-038 – No kind means workflow, for the check
- Level: low   Subject: Persistence
- Group: RS
- Text: Where a graph in stored form names no kind, the Graph tables shall check it with the rules of the kind `workflow`.
- Rationale: refines HR-001; the same default as the save path (REQ-WFM-153), so a check and a save of the same graph agree
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: a graph without the field `kind` and the same graph with `"kind": "workflow"` give the same rule report (exact)
- Binding: fixed
- Verified by: TC-GTB-039
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-039 – Unknown kind in a check
- Level: low   Subject: Persistence
- Group: RS
- Text: If the kind of a checked graph is not in the registry of kinds, then the Graph tables shall return a rule report with the single item `unknown_kind`, naming the kind as its part.
- Rationale: refines HR-001 and D-404 (the reason `unknown kind`); the rules of an unknown kind are not known, so nothing else can be said (Q-7); the save keeps CORE's `schema_break` / `kind` (REQ-WFM-154)
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: a graph of kind `swarm` with a cycle gives exactly `[{"rule": "unknown_kind", "parts": ["swarm"], ...}]` (exact)
- Binding: fixed
- Verified by: TC-GTB-040
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, finding 10); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-040 – A check never raises
- Level: low   Subject: Persistence
- Group: RS
- Text: If a checked graph is malformed, then the Graph tables shall return a rule report instead of raising an exception.
- Rationale: refines HR-002; the same contract as the record checks of IF-301 (A-60); the prototype raised on connection data that is not an object and on steps without IDs (finding 4). Malformed: a step or connection that is not an object, data that is not an object, a missing or non-text ID or end
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: each of five malformed graphs (a step that is a number, connection data that is a list, a step without `id`, a connection without `from`, `nodes` that is not a list) returns a list; no exception escapes (exact)
- Binding: fixed
- Verified by: TC-GTB-041
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, finding 4); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge"). Verify V-1 (connections whose `from`, `to`, `id`, `role` or `as` is a list or an object raised) fixed in `f478e040` (D-461).

### REQ-GTB-041 – Rule 1, step identity
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `step_identity` for every step whose ID is not a non-empty text or repeats the ID of an earlier step, naming those IDs.
- Rationale: refines HR-002 and D-375 (whitespace and repeated IDs); a slash inside a step ID is allowed, as in CORE (Q-4, REQ-GTB-029: the graph ID ends at the first slash)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: steps `a`, `a` and `` give `step_identity` naming `a` and `` ; a step `x/y` breaks no rule by its ID (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, finding 5); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-042 – Rule 2, kind of step
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `step_kind` for every step whose type is none of `data`, `transform` and `master`, naming those steps.
- Rationale: refines HR-002; the rule of REQ-WFM-043 under its name in the registry
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a step of type `loop` gives `step_kind` naming it; steps of the three types give no item (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-043 – Rule 3, connection ends
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `connection_endpoints` for every connection whose start or end names no step of the graph, naming those connections.
- Rationale: refines HR-002; today's runner refuses the same before a run (REQ-RUN-016, `graph_run.py`)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a connection `e2` from `a` to the missing step `z` gives `connection_endpoints` naming `e2` (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-044 – Rule 4, duplicate connection
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `duplicate_connection` for every connection that repeats the ID, or the start, end, role and name, of an earlier connection, naming those connections.
- Rationale: refines HR-002 and D-375 (duplicate connections, new against the five older rules); role is the field `role`, name the field `as` of the connection's data; two connections that differ only in `as` hand over two names and are not duplicates
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: `e1` and `e2` both from `a` to `t` without role and name give `duplicate_connection` naming `e2`; two connections with the ID `e1` name `e1`; the same pair with `as` `x` and `y` gives no item (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, finding 6); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-045 – Rule 5, adjacency
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `adjacency` for every connection between two existing steps that are both data steps or both not data steps, naming those connections.
- Rationale: refines HR-002; the rule of REQ-WFM-045 under its name; a connection with a missing end is rule 3, not rule 5; a transform connected to itself breaks this rule and the cycle (seen on the scratch run of 2026-11-22: `T1>T1` is named by both)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a connection from data `d1` to data `d2` and one from transform `t1` to master `m1` give `adjacency` naming both; a connection from `d1` to the missing `z` gives no `adjacency` item (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-046 – Rule 6, one writer
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `single_writer` for every data step that connections from more than one existing step lead into, naming those data steps.
- Rationale: refines HR-002; the rule of REQ-WFM-046 under its name
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: transforms `t1` and `t2` both connected into data `d` give `single_writer` naming `d`; two connections from `t1` into `d` give no `single_writer` item (they are rule 4) (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, finding 6); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-047 – Rule 7, session setting and stop limit
- Level: low   Subject: Persistence
- Group: RD
- Text: The Graph tables shall report the rule `stop_limit` for every loop-controlling step without a valid stop limit, data step holding `stop` or `session`, and step with more than one settings connection, naming those steps.
- Rationale: refines HR-002; Q-1 confirms ASM-3; a valid stop limit is that of REQ-WFM-048 (a positive maximum number of repetitions or a positive maximum time), so `max_seconds: 1.0` stays valid (finding 6); none of the 17 graphs the prototype stores breaks it (finding 11)
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: a master without `stop`, a data step with `session`, and a transform with two settings connections each give `stop_limit` naming that step; a master with `{"max_seconds": 1.0}` gives no item (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, CP18); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-048 – Rule 8, cycle
- Level: low   Subject: Persistence
- Group: RD
- Text: While `step_identity` and `connection_endpoints` are kept, the Graph tables shall report `cycle` for a graph whose steps cannot be ordered, naming the cycle with its first step repeated at the end.
- Rationale: refines HR-002 and REQ-WFM-047 (the cycle is named, its first step repeated at the end; finding 3); an order needs known, unique steps (Q-5), so the owner sees the cycle once identity and ends are fixed
- Parent: HR-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: `d1 → t1 → d1` gives `cycle` with the parts `d1, t1, d1`; the same graph plus a connection to a missing step gives `connection_endpoints` and no `cycle` (exact)
- Binding: fixed
- Verified by: TC-GTB-042
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP17, findings 3 and 8); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-049 – Refusal of a run: the kind first and alone
- Level: low   Subject: Persistence
- Group: RF
- Text: If a graph's kind is not in the registry or has the run flag no, then the run check of the Graph tables shall answer refused with one item naming the kind: `unknown_kind` or `kind_cannot_run`.
- Rationale: refines HR-003 and FR-64 "of a kind that cannot run"; the rules of such a kind say nothing about a run (ASM-7); refusal order kind, rules, inputs (D-416 (3))
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: a context graph gives refused with exactly one item `kind_cannot_run` naming `context`; a graph of kind `swarm` with a cycle gives exactly one item `unknown_kind` naming `swarm` (exact)
- Binding: fixed
- Verified by: TC-GTB-043
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-050 – Refusal of a run: rules, then inputs
- Level: low   Subject: Persistence
- Group: RF
- Text: When a graph whose kind has the run flag yes is checked for a run, the Graph tables shall answer refused, listing every broken rule in registry order, then every unsupplied input, else ready.
- Rationale: refines HR-003 and D-416 (3); the trust check follows in the runner (REQ-RUN-038); the given values of the run are part of the question, so the same graph can be refused without values and ready with them (AC-018)
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: a workflow graph with two writers and an unsupplied input gives refused with `single_writer` first and the input second; the converted `chat` skill gives ready with `{"input.text": "hello"}` (exact)
- Binding: fixed
- Verified by: TC-GTB-043
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-051 – Unsupplied input
- Level: low   Subject: Persistence
- Group: RF
- Text: The run check of the Graph tables shall report every unsupplied input as one item naming the processing or loop-controlling step and the data step it reads.
- Rationale: refines HR-003 and D-375 (a step input nobody supplies); the term is defined above: no writer, no start value in the graph, no value given with the run; settings and order connections are not inputs here (a step gets `{}` without settings, REQ-RUN-030, an order connection hands over nothing, REQ-RUN-035); the inputs of a Stage with a prepare function count as given (REQ-RUN-039, D-418 (1))
- Parent: HR-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: the converted `chat` skill without values names the step `step.converse` and the data step `input.text`; a data step with a graph value, or one written by another step, is not named (exact)
- Binding: fixed
- Verified by: TC-GTB-044
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: prototype round 04, CP19); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").

### REQ-GTB-052 – The document form keeps its five rules
- Level: low   Subject: Persistence
- Group: DF
- Text: The Graph tables shall keep the check of the document form (IF-301 `validate`) and its five rules unchanged in IF-301 v4.
- Rationale: Q-6: the document form (IF-301 `validate`, IF-102, IF-104 v1, IF-203) keeps REQ-GTB-002 until G-V4.MIGRATION retires it; RULES covers every check of the stored form; the v1 to v3 contract suites stay unchanged
- Parent: HR-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: the contract suites of IF-301 v1, v2 and v3 and the suites of IF-102, IF-104 v1 and IF-203 pass unchanged against the v4 code (exact)
- Binding: fixed
- Verified by: TC-GTB-045
- Status: Verified
- History: G-V4.GRAPHAPI.RULES Plan step 1b, 2026-11-22, new (basis: Q-6, prototype round 04, finding 1); verified (G-V4.GRAPHAPI.RULES verification report, verdict ticked by the owner 2026-11-22) and moved here from `specs/mia/goals/G-V4.GRAPHAPI.RULES/requirements.md` at the merge (plan.md, "At the merge").
