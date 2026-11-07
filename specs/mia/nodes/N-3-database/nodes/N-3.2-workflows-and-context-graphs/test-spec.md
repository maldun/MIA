# Test specification: Graph tables (N-3.2)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md   **Status:** Draft (Plan for node N-3.2, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: unit tests with plain data, no database. The interface IF-301 is tested by its contract suite against the mock and the real part. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-GTB-001 | REQ-GTB-001 | Unit | 1 | definitions() of the Graph tables | exactly the tables workflows and context_graphs, both versioned, neither deletable | exact |
| TC-GTB-002 | REQ-GTB-002 | Unit | 1 | validate(workflows, doc) for one valid graph (the lookup graph) and one minimal document per rule: duplicate id, an edge to an unknown id, two adjacent data nodes, two adjacent process nodes, a session node with no stopping criterion, a cycle p->d->p | None for the valid graph; the rule name node_identity, node_identity, adjacent_data_nodes, adjacent_process_nodes, session_stopping_criterion, cycle in turn; the cycle is named by its ids with the first id repeated at the end | exact |
| TC-GTB-003 | REQ-GTB-002 | Property | 1 | 1000 generated graphs (seeds 1 to 1000) with random nodes, edges, shared inputs and session nodes; the reference is `graphlib.TopologicalSorter` on the same graph | a graph is accepted exactly when the reference finds no cycle and no other rule is broken; every accepted graph has a topological order; a data node read by two processes appears once | 0 failures over 1000 seeds |
| TC-GTB-004 | REQ-GTB-003 | Unit | 1 | validate(context_graphs, doc) for a valid context graph and for one with a broken rule; definitions() | the valid graph gives None, the broken one its rule; the table is versioned and not deletable | exact |
| TC-GTB-005 | REQ-GTB-004 | Component | 1 | the five seed entries (lookup, verify, review, search, method_transfer) read from `library/` and `skills/` of the repository | all five pass validate(workflows, ...); each names a specification, a context graph and a benchmark reference; method_transfer is marked off by default | exact |
| TC-GTB-016 | REQ-GTB-005, FR-40 | Unit | 1 | one node of each registered type written through the storage stand-in | read back with the same ID and the same JSON field; the field holds the type | exact |
| TC-GTB-006 | REQ-GTB-006 | Unit | 1 | one edge with an ID, a start node, an end node and a JSON field | read back with the same four fields | exact |
| TC-GTB-007 | REQ-GTB-007 | Unit | 1 | a transform node whose JSON field holds a toolbox ID | read back naming the same toolbox ID | exact |
| TC-GTB-008 | REQ-GTB-008 | Unit | 1 | a master node whose JSON field holds a task definition and a stopping criterion | read back with the same definition and stopping criterion | exact |
| TC-GTB-009 | REQ-GTB-009 | Unit | 1 | one stored node of each registered type | each is rebuilt as the class registered for its type ID, with equal values | exact |
| TC-GTB-010 | REQ-GTB-010 | Unit | 1 | a node with the type ID `x.unknown`, written, and the same record present in storage, read | both are refused; the message names `x.unknown` | exact |
| TC-GTB-011 | REQ-GTB-011 | Unit | 1 | for a node and for an edge: one field that breaks its type's schema (a missing required key, a wrong value type) | each write is refused; the message names the path of the field | exact |
| TC-GTB-012 | REQ-GTB-012 | Inspection | 1 | all modules of the Graph tables, read as source (syntax tree) | none imports `pickle`, `marshal` or `shelve` | exact |
| TC-GTB-013 | REQ-GTB-013, FR-40 | Unit | 1 | a graph stored, then one node edited, then one edge edited, then the graph edited | after each edit versions n and n+1 both exist and version n is unchanged | exact |
| TC-GTB-014 | REQ-GTB-014, FR-40 | Property | 1 | N generated graphs (seeds 1 to N; N is a parameter, default 1000) of the three node types, with edges, written, read and rebuilt | every rebuilt graph equals the stored one | 0 failures over N seeds |
| TC-GTB-017 | REQ-GTB-016 | Unit | 1 | a stored graph at version 1; one edit of a node, one of an edge and one of the whole graph, each breaking a check (unknown type, schema break, a duplicate ID) | each edit is refused; the latest version is still 1 and its content is unchanged; no version 2 exists | exact |
| TC-GTB-015 | REQ-GTB-015 | Component | 2 | the contract suites of IF-301 v1 and IF-203 v0, run unchanged, with the graphs stored as records | both suites pass | exact |

Contract test cases of IF-301: TC-IF-301-01 to the last of the suite (listed in the root `test-spec.md`).

## Scenarios (iteration 2, G-V2.STORE)

Examples use only what the requirements fix. The registered types are those the registry of the test lists (at least one data, one transform and one master type); concrete type IDs come with the registry in Implement.

### TC-GTB-016 – A node is stored as a record
- Verifies: REQ-GTB-005, FR-40
- Given: one node of each registered type, each with an ID and a JSON field that holds its type
- When: each node is written and read back
- Then: the ID and the JSON field are the same as written
- And: the type is present in the JSON field

### TC-GTB-006 – An edge is stored as a record
- Verifies: REQ-GTB-006
- Given: an edge with the ID `e1`, the start node `n1`, the end node `n2` and a JSON field `{"label": "x"}`
- When: it is written and read back
- Then: it has the same ID, start node, end node and JSON field

### TC-GTB-007 – A transform node keeps its toolbox ID
- Verifies: REQ-GTB-007
- Given: a transform node whose JSON field names the toolbox ID `t-demo`
- When: it is written and read back
- Then: the node names `t-demo`

### TC-GTB-008 – A master node keeps its definition
- Verifies: REQ-GTB-008
- Given: a master node whose JSON field holds a task definition and a stopping criterion
- When: it is written and read back
- Then: both are equal to what was written
- And: nothing is run (the definition is a record only until goal D)

### TC-GTB-009 – The class is rebuilt from the type ID
- Verifies: REQ-GTB-009
- Given: one stored node of each registered type
- When: each is read
- Then: the object is of the class registered for its type ID
- And: its values equal the stored ones

### TC-GTB-010 – An unknown type is refused
- Verifies: REQ-GTB-010
- Given: a node with the type ID `x.unknown`, once as a write and once as a record already present in storage
- When: it is written, and when it is read
- Then: both are refused
- And: the message names `x.unknown`; no other record changes

### TC-GTB-011 – A field that breaks its schema is refused
- Verifies: REQ-GTB-011
- Given: a node and an edge, each with one field that breaks the JSON schema of its type (a required key missing; a value of the wrong kind)
- When: each is written
- Then: each write is refused
- And: the message names the path of the broken field

### TC-GTB-012 – No language-specific serialisation
- Verifies: REQ-GTB-012
- Given: the source of every module of the Graph tables, and a test module that imports `pickle`
- When: the inspection reads the syntax trees
- Then: it finds no import of `pickle`, `marshal` or `shelve` in the Graph tables
- And: it does report the test module (the inspection can fail)

### TC-GTB-013 – An edit is a new version
- Verifies: REQ-GTB-013, FR-40
- Given: a stored graph at version 1
- When: one node is edited, then one edge, then the whole graph
- Then: after each edit the new version exists and the one before is unchanged
- And: all earlier versions can still be read

### TC-GTB-014 – A stored graph is rebuilt equal
- Verifies: REQ-GTB-014, FR-40
- Given: N generated graphs (seeds 1 to N) with nodes of all three types and edges; N is a parameter of the check, its default is 1000
- When: each is written, read and rebuilt
- Then: the rebuilt graph equals the stored one
- And: a failing seed is reported with the graph, so it can be replayed

### TC-GTB-017 – A refused edit changes nothing
- Verifies: REQ-GTB-016
- Given: a stored graph at version 1, and three edits that each break a check: a node of the type `x.unknown`, a field that breaks its schema, an ID that already exists
- When: each edit is made
- Then: each is refused
- And: the latest version is still 1, its content is unchanged and no version 2 exists

### TC-GTB-015 – The document form still works
- Verifies: REQ-GTB-015
- Given: graphs stored as node and edge records, the contract suites of IF-301 v1 and IF-203 v0 unchanged
- When: both suites run with those graphs as the real part
- Then: both pass
- And: the suite files are the ones from before A-90 (no edit)

## Evidence of the acceptance criteria outside this node (Verify F6)

TC-GTB-001 and TC-GTB-004 check the definitions and the validation; the storing itself is done by the Storage layer and the workflow library, so their tests are the evidence of the two acceptance criteria:

| Requirement | Acceptance criterion | Verified by (test outside N-3.2) |
| --- | --- | --- |
| REQ-GTB-001 | AC-15: a record of each kind is written and read back identically | `tests/test_storage.py` `test_a_record_of_each_table_reads_back_equal` (TC-SLY-002, N-3.1; a workflow and a context graph among the tables) |
| REQ-GTB-003 | AC-10: a context graph edit creates a new version | `tests/test_workflow_library.py` `test_the_template_may_be_optimised_as_a_new_version` (N-2.3: an edit of a context graph is version 2, version 1 stays readable) |

## Assumptions (checked in validation)

- ASM-N3-004: the graph rules are the ones of FR-7 and `contracts/IF-301-graph-tables.md`; `graphlib` of the standard library is the reference in the property test.
