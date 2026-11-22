# Test specification: Graph tables (N-3.2)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md   **Status:** Draft (Plan for node N-3.2, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: unit tests with plain data, no database. The interface IF-301 is tested by its contract suite against the mock and the real part. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

IDs of steps and connections (A-167, IF-301 v3): the IDs `n1`, `e1`, `c1`, ... named in the scenarios below are local IDs. Since IF-301 v3 (REQ-GTB-029) a step or connection is stored under `<graph id>/<local id>`, so the tests write the scoped form (`wf1/n1`, `g/e1`, `h1/c1`); the rules and the expected results are unchanged.

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
| TC-GTB-018 | REQ-GTB-017 | Unit | 1 | a header `wf1` naming nodes n1 and n2 and edge e1 at version 1, stored; then n1 edited (version 2) and a second header version naming n1 at version 2 | header version 1 reads n1 at version 1 with its old content; header version 2 reads n1 at version 2; all other fields equal what was stored | exact |
| TC-GTB-019 | REQ-GTB-018 | Unit | 1 | a skill with ID `lookup`, command `/lookup`, a workflow graph ID and a context graph ID; then an edit of the context graph ID; a record without a command | read back equal; the edit is version 2 and version 1 is unchanged; the record without a command is refused naming `command` | exact |
| TC-GTB-020 | REQ-GTB-019 | Unit | 1 | a header naming n1 at version 5 when n1 has versions 1 and 2; the same header with version 2 | the first is refused naming `n1`; the second is accepted | exact |
| TC-GTB-021 | REQ-GTB-020 | Unit | 1 | an edge e1 from n1 to n9 with only n1 stored; the same edge with n9 stored | the first is refused naming `n9`; the second is accepted | exact |
| TC-GTB-022 | REQ-GTB-021 | Unit | 1 | a node with its own ID n1, written under the record ID n1 and under the record ID x | the first is accepted; the second is refused naming `id`; nothing is stored under x | exact |
| TC-GTB-023 | REQ-GTB-022 | Unit | 1 | a node of each type with an extra field `foo`, and a data node with a key `id` in its JSON field, each written and, put past the check, read; the same nodes without the field | the first group is refused on write and on read naming the field; the twins are accepted | exact |
| TC-GTB-024 | REQ-GTB-023 | Unit | 1 | the definitions of the Graph tables; a context node written twice; a delete of a context node and of a context edge | six record tables are listed; the versions are 1 and 2; both deletes are refused as immutable | exact |
| TC-GTB-025 | REQ-GTB-024 | Unit | 1 | a context node without type, without a JSON object, without ID; a context edge without an end; the same records complete | each broken record is refused naming the field; the complete ones are accepted | exact |
| TC-GTB-026 | REQ-GTB-025 | Unit | 1 | a context edge to a stored context node, to one that is not stored, and to the ID of a stored workflow node | the first is accepted; the others are refused naming the end | exact |
| TC-GTB-027 | REQ-GTB-026 | Unit | 1 | a header of kind context naming a stored and a missing context node; a workflow header naming a context node | the first is accepted; the others are refused as unknown_member naming the member | exact |
| TC-GTB-028 | REQ-GTB-027 | Unit | 1 | a data node nested 300 and 150 levels deep; a category whose schema is not valid | the deep one is refused naming `data`, the other accepted; the category is refused naming `type`; no exception | exact |
| TC-GTB-029 | REQ-GTB-028 | Unit | 1 | a data node whose value is a list of 99,995 and one of 99,996 numbers; a record that names the same child twice on 30 levels | the first is stored; the others are refused naming `data`, the last within 5 s | exact |
| TC-GTB-015 | REQ-GTB-015 | Component | 2 | the contract suites of IF-301 v1 and IF-203 v0, run unchanged, with the graphs stored as records | both suites pass | exact |

Contract test cases of IF-301: TC-IF-301-01 to the last of the suite (listed in the root `test-spec.md`). The cases of IF-301 v4, TC-IF-301-27 to 34 (G-V4.GRAPHAPI.RULES), are listed with their scenarios in the section "Test cases of G-V4.GRAPHAPI.RULES" below.

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

### TC-GTB-018 – A graph version pins its members
- Verifies: REQ-GTB-017
- Given: a header `wf1` with ID, kind `workflow`, a context graph ID, an empty testbench ID, a description, the nodes n1 and n2 and the edge e1, each at version 1
- When: the header is stored and read back; then node n1 is edited (version 2) and a second header version naming n1 at version 2 is stored; header versions 1 and 2 are read with their members
- Then: the first read equals what was stored
- And: header version 1 still reads n1 at version 1 with its old content; header version 2 reads n1 at version 2

### TC-GTB-019 – A skill is stored as a versioned record
- Verifies: REQ-GTB-018
- Given: a skill with ID `lookup`, command `/lookup`, a workflow graph ID and a context graph ID
- When: it is stored and read back; then its context graph ID is edited and stored; then a record without a command is stored
- Then: the first read has the same four fields
- And: the edit is version 2 and version 1 is unchanged; the record without a command is refused and names `command`

### TC-GTB-020 – A header with a missing member is refused
- Verifies: REQ-GTB-019
- Given: node n1 stored with versions 1 and 2; a header that names n1 at version 5, and the same header naming n1 at version 2
- When: each is stored
- Then: the first is refused and names `n1`
- And: the second is accepted (the twin differs only in the broken rule, as TR-GTB-001 and the older checks)

### TC-GTB-021 – An edge to a missing node is refused
- Verifies: REQ-GTB-020
- Given: node n1 stored; an edge e1 from n1 to n9, and the same edge after n9 is stored
- When: each is stored
- Then: the first is refused and names `n9`
- And: the second is accepted (the twin differs only in the broken rule)

### TC-GTB-022 – A record under another ID is refused
- Verifies: REQ-GTB-021
- Given: a node whose own ID is `n1`
- When: it is written under the record ID `x`, and then under the record ID `n1`
- Then: the write under `x` is refused and names `id`
- And: nothing is stored under `x`; the write under `n1` is accepted (the twin differs only in the broken rule)

### TC-GTB-023 – A node with an extra field is refused
- Verifies: REQ-GTB-022
- Given: one node of each type with an extra field `foo`, and a data node with a key `id` inside its JSON field
- When: each is written, and each is read as a record already in storage
- Then: each write is refused and each read is refused, both as `schema_break` naming the extra field (`foo`, `id`)
- And: the refused writes store nothing; the same nodes without the extra field are accepted, and a context-graph node keeps the fields its category allows (the twins differ only in the broken rule)

### TC-GTB-024 – The context tables are versioned and never deleted
- Verifies: REQ-GTB-023
- Given: the definitions of the Graph tables and an empty store
- When: a context node is written twice, a context edge once, and a delete of each is tried
- Then: six record tables are listed, the context node has the versions 1 and 2, the edge version 1
- And: both deletes are refused as immutable and the records stay

### TC-GTB-025 – A context record of a bad shape is refused
- Verifies: REQ-GTB-024
- Given: a context node with data `{}`, one with a number as type, one without data, one with an empty ID, and a context edge without `to` and one without data
- When: each is written without categories
- Then: each write is refused naming the broken field (`type`, `type`, `data`, `id`, `to`, `data`) and stores nothing
- And: the same records complete are accepted (the twins differ only in the broken rule)

### TC-GTB-026 – A context edge names stored context nodes
- Verifies: REQ-GTB-025
- Given: a stored context node `c1` and a stored workflow node `n9`
- When: a context edge from `c1` to `c9`, one from `c1` to `n9`, and one from `c1` to `c1` are written
- Then: the first two are refused as `unknown_endpoint` naming `c9` and `n9`
- And: the third is accepted

### TC-GTB-027 – A context header names stored context members
- Verifies: REQ-GTB-026
- Given: a stored context node `c1`
- When: a header of kind context naming `c9`, a header of kind workflow naming `c1`, and a header of kind context naming `c1` are written
- Then: the first two are refused as `unknown_member` naming `c9` and `c1`
- And: the third is accepted

### TC-GTB-028 – Input that cannot be checked is a schema break
- Verifies: REQ-GTB-027
- Given: a data node whose value is nested 300 levels, one nested 150 levels, and a category whose schema is `{"type": 5}`
- When: each is checked, and the deep node is also rebuilt with `to_object`
- Then: the 300-level node is refused as `schema_break` naming `data`, in the check and in the rebuild, without an exception; the category is refused as `schema_break` naming `type`
- And: the 150-level node is accepted

### TC-GTB-029 – A record with too many values is refused
- Verifies: REQ-GTB-028
- Given: a data node whose value is a list of 99,995 numbers (100,000 values with the record, its id, its data object, its type and the list), one with 99,996 numbers, and a record that names the same child twice on 30 levels (2**30 paths, 31 levels deep)
- When: each is written, with a time limit of 5 s
- Then: the first is stored as version 1; the second is refused as `schema_break` naming `data`
- And: the third is refused the same way within the limit; the refusals store nothing

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

## Test cases of G-V4.GRAPHSTORE.CORE (moved at the merge 2026-11-22, D-408; test requirements TR-CORE-001 to 009)
| Test ID | Verifies | Level | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|
| TC-GTB-033 | REQ-GTB-029 | component | a step record and a connection record, each written under `chat`, `lookup/chat`, `/chat`, `lookup/` and an empty ID | `chat`, `/chat` and `lookup/` refused naming `unscoped_id`; the empty ID refused naming `record_identity` (`id`); `lookup/chat` accepted (a step `lookup/end` stored first) | exact rule name and field |
| TC-GTB-034 | REQ-GTB-030 | component | headers `g` that pin `g/step`, `h/step`, `g/conn` and `h/conn`; all members exist | headers with `h/step` or `h/conn` refused naming `unscoped_id`; with `g/step` or `g/conn` accepted | exact |
| TC-GTB-035 | REQ-GTB-031 | unit | the record IDs `lookup/a/b`, `lookup/a`, `g//`, `lookup/` | graph `lookup` and local ID `a/b`; `lookup`, `a`; `g`, `/`; no local ID (not scoped) | exact |
| TC-GTB-036 | REQ-GTB-032 | contract | the refusal cases of TC-GTB-033, TC-GTB-034, TC-WFM-164, TC-WFM-172, TC-WFM-173, TC-WFM-178 on the files backend and on PostgreSQL 16 | the same refusal rule and detail on both | exact; the PostgreSQL half skips (never weakened) where podman, the image or psycopg 3 is missing |

## Scenarios (G-V4.GRAPHSTORE.CORE, approved by the owner 2026-11-21)

### TC-GTB-033 – A step or connection without a graph in its ID is refused
- Verifies: REQ-GTB-029
- Given: a step record and a connection record, each offered under four IDs: `chat`, `/chat`, `lookup/` and the empty ID, and once under `lookup/chat`; a step `lookup/end` is stored first, so that every connection has stored ends (D-410)
- When: each of the ten records is written
- Then: the three unscoped IDs `chat`, `/chat` and `lookup/` of each table are refused, each naming the rule `unscoped_id`; the empty ID is refused naming `record_identity` with the field `id`, as before (D-409)
- And: the records under `lookup/chat` are accepted and stored
- And: witnesses AC-002

### TC-GTB-034 – A header names only its own members
- Verifies: REQ-GTB-030
- Given: four headers for the graph `g`: one pins the step `h/step`, one the step `g/step`, one the connection `h/conn`, one the connection `g/conn`; all four members exist
- When: each header is written
- Then: the headers with `h/step` and with `h/conn` are refused, each naming `unscoped_id`; the headers with `g/step` and with `g/conn` are accepted
- And: witnesses AC-002

### TC-GTB-035 – The first slash separates graph and local ID
- Verifies: REQ-GTB-031
- Given: the record IDs `lookup/a/b`, `lookup/a`, `g//` and `lookup/`
- When: each is split into graph ID and local ID
- Then: `lookup/a/b` gives graph `lookup` and local ID `a/b`; `lookup/a` gives `lookup` and `a`; `g//` gives `g` and `/`; `lookup/` gives no local ID, so it is not scoped

### TC-GTB-036 – Both stores refuse the same way
- Verifies: REQ-GTB-032
- Given: one files store and one PostgreSQL 16 store (throw-away container), both empty
- When: the refusal cases of TC-GTB-033, TC-GTB-034, TC-WFM-164, TC-WFM-172, TC-WFM-173 and TC-WFM-178 are run on both
- Then: each case gives the same refusal rule and the same named detail on both stores
- And: where podman, the image or psycopg 3 is missing the PostgreSQL half is skipped and reported as skipped, never as passed

## Test cases of G-V4.GRAPHAPI.RULES (moved at the merge 2026-11-22; test requirements TR-RULES-001 to 009)
All checks of RULES are exact (rule names, IDs, orders, counts, equalities): no statistical check, no benchmark (no hard bound, D-416 (4)). Accepted cases (`specs/mia/goals/G-V4/accepted-cases.md`): AC-017 is witnessed by TC-GTB-046 and TC-WFM-180, AC-018 by TC-RUN-036, TC-RUN-037 and TC-GTB-044. The validation criterion VAL-RULES-01 stays in the goal record `specs/mia/goals/G-V4.GRAPHAPI.RULES/test-spec.md`.

| Test ID | Verifies | Level | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|
| TC-GTB-037 | REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036 | unit | `kinds()` | exactly the kinds `workflow` and `context`; `workflow`: the eight rule names in order, runs yes; `context`: `step_identity`, `connection_endpoints`, `duplicate_connection`, runs no; changing the returned value does not change the next answer | exact |
| TC-GTB-038 | REQ-GTB-035 | unit | a context graph with two connections `e1`, `e2` from `c1` to `c2` (no role, no name); a context graph with a cycle between steps of one category and two connected steps of one category | the first gives exactly `duplicate_connection` naming `e2`; the second gives `[]` (none of rules 2, 5 to 8 applies) | exact |
| TC-GTB-039 | REQ-GTB-037, REQ-GTB-038 | unit | a workflow graph with a connection to a missing step and two writers of one data step; a sound workflow graph; both again without the field `kind` | exactly two items, `connection_endpoints` before `single_writer`, each with its parts and the fixed sentence; the sound graph gives `[]`; without `kind` the reports are equal | exact |
| TC-GTB-040 | REQ-GTB-039 | unit | the graph of TC-GTB-039 plus a cycle, under the kinds `swarm`, `""` and `5` | exactly one item `unknown_kind` naming `swarm`, `` and `5` | exact |
| TC-GTB-041 | REQ-GTB-040 | unit | five malformed graphs: a step that is `5`, connection data that is `[]`, a step without `id`, a connection without `from`, `nodes` that is `"x"`; a graph that is a list | each returns a list, no exception, with the items of the paragraph "Malformed input" of IF-301 v4 | exact |
| TC-GTB-042 | REQ-GTB-041, REQ-GTB-042, REQ-GTB-043, REQ-GTB-044, REQ-GTB-045, REQ-GTB-046, REQ-GTB-047, REQ-GTB-048 | unit | one small graph per rule that breaks only that rule, and its sound twin (the cases in the scenario) | each broken graph gives exactly one item with that rule and the named parts; each twin gives `[]` | exact |
| TC-GTB-043 | REQ-GTB-049, REQ-GTB-050 | unit | a context graph; a graph of kind `swarm` with a cycle; a workflow graph with two writers and an unsupplied input; the converted `chat` skill with `{"input.text": "hello"}` | refused with only `kind_cannot_run` (`context`); refused with only `unknown_kind` (`swarm`); refused with `single_writer` first and the input second; ready with `[]` | exact |
| TC-GTB-044 | REQ-GTB-051 | unit | the converted `chat` skill without values; the same with a graph value on `input.text`; a data step written by another step; a settings and an order connection from data steps without values | one item `unsupplied_input`, step `step.converse`, input `input.text`; no item for the graph value, the written step, the settings and the order connection | exact |
| TC-GTB-045 | REQ-GTB-052 | contract | the contract suites of IF-301 v1, v2, v3, IF-102, IF-104 v1 (Python and JS) and IF-203, unchanged, against the v4 code | every suite passes; the suite files are byte-identical to `goal/v4` | exact |
| TC-GTB-046 | REQ-GTB-037, REQ-WFM-163, REQ-RUN-037, HR-004 | component | the AC-017 graph plus an identical connection (three rules) and a graph with a connection to a missing step, two identical connections and a data step holding `session` (three rules); each sent through `rule_report`, the save, the check route (IF-104 v2 mock) and the run, five times each | the same items, rule by rule, with the same parts in the same order and the same sentences, at every entry point and in every repeat | 0 differences |
| TC-GTB-047 | REQ-GTB-034, HR-005 | component | the cases of TC-GTB-002 and the generator of TC-GTB-003, seeds 1 to 1000, each document turned into the stored form by the mapping of the scenario | 0 graphs refused by the five older rules and accepted by the eight, except a stop limit that REQ-WFM-048 accepts; the newly refused graphs counted by rule and printed | 0 lost |

### Contract suite IF-301 v4 (`tests/acceptance/contract/test_if_301_v4_rule_set.py`, real side and mock side)
| Test ID | Verifies | Golden | Expected result |
|---|---|---|---|
| TC-IF-301-27 | REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036 | 24 | `kinds()` as in the contract; a changed copy changes nothing |
| TC-IF-301-28 | REQ-GTB-037, REQ-GTB-038 | 25 | the converted `chat` skill gives `[]`, with and without `kind` |
| TC-IF-301-29 | REQ-GTB-037, REQ-GTB-046, REQ-GTB-048 | 26 | `single_writer ["d1"]`, then `cycle ["d1", "t1", "d1"]` |
| TC-IF-301-30 | REQ-GTB-043, REQ-GTB-048 | 27 | `connection_endpoints ["e9"]`, `single_writer ["d1"]`, no `cycle` |
| TC-IF-301-31 | REQ-GTB-035 | 28 | `duplicate_connection ["e2"]`; the context cycle gives `[]` |
| TC-IF-301-32 | REQ-GTB-039, REQ-GTB-049 | 29 | `unknown_kind` alone in both operations; `kind_cannot_run` alone for a context graph |
| TC-IF-301-33 | REQ-GTB-050, REQ-GTB-051 | 30 | `unsupplied_input` of `step.converse` at `input.text`; ready with `"hello"` and with `None` |
| TC-IF-301-34 | REQ-GTB-040 | 31 | five malformed graphs, each a list, no exception |

### Edge inputs of G-V4.GRAPHAPI.RULES (per rule: zero, empty, missing, at and past the limit; per pair of rules acting on the same data)
| Rule (REQ) | Edge or pair | Test ID | Expected result |
|---|---|---|---|
| REQ-GTB-041 | a slash inside a step ID (`x/y`) | TC-GTB-042 | no item (Q-4) |
| REQ-GTB-041 | the empty ID and a repeated ID in one graph | TC-GTB-042 | one item naming both |
| REQ-GTB-044 and REQ-GTB-046 | two connections from `t1` into `d` | TC-GTB-042 | `duplicate_connection` only, no `single_writer` |
| REQ-GTB-044 | two connections that differ only in `as` | TC-GTB-042 | no item |
| REQ-GTB-045 and REQ-GTB-048 | a transform connected to itself | TC-GTB-042 | `adjacency` and `cycle` (`["T1", "T1"]`) |
| REQ-GTB-043 and REQ-GTB-045 | a connection from a data step to a missing step | TC-GTB-042 | `connection_endpoints` only |
| REQ-GTB-047 | `{"max_seconds": 1.0}`, `{"max_repetitions": 0}`, `{"max_repetitions": true}`, no `stop` | TC-GTB-042 | the first valid, the other three named |
| REQ-GTB-047 and REQ-RUN-033 | a transform with two settings connections | TC-GTB-042, TC-RUN-036 | `stop_limit` naming the transform; the run is refused before REQ-RUN-033's check |
| REQ-GTB-048 | a cycle while rule 1 or rule 3 is broken | TC-GTB-042, TC-IF-301-30 | no `cycle` item |
| REQ-GTB-051 | a graph value of `null` | TC-GTB-044 | counts as no start value: named |
| REQ-GTB-051 | a given value of `None` | TC-IF-301-33 | counts as given: not named |
| REQ-GTB-049 and REQ-GTB-050 | a context graph that also breaks rule 4 | TC-GTB-043 | only `kind_cannot_run` |

## Scenarios (G-V4.GRAPHAPI.RULES, approved by the owner 2026-11-22, D-422)

### TC-GTB-037 – The registry names two kinds
- Verifies: REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036
- Given: the rule set of IF-301 v4, nothing else
- When: the registry of kinds is read twice, the first answer changed in between
- Then: it names exactly the kinds `workflow` and `context`
- And: `workflow` lists `step_identity`, `step_kind`, `connection_endpoints`, `duplicate_connection`, `adjacency`, `single_writer`, `stop_limit`, `cycle` in this order and can run; `context` lists `step_identity`, `connection_endpoints`, `duplicate_connection` and cannot run
- And: the second answer is unchanged by the change of the first

### TC-GTB-038 – A context graph has three rules
- Verifies: REQ-GTB-035
- Given: a context graph with steps `c1`, `c2` of one category and two connections `e1`, `e2` from `c1` to `c2` without role or name; a second context graph with `c1 → c2 → c1`
- When: each is checked
- Then: the first gives exactly one item, `duplicate_connection` naming `e2` (Q-3: rule 4 in full)
- And: the second gives an empty list: a cycle and two connected steps of one category break no rule of the context kind

### TC-GTB-039 – The rule report lists every broken rule in order
- Verifies: REQ-GTB-037, REQ-GTB-038
- Given: a workflow graph with a connection `e9` to the missing step `z` and two transforms writing the data step `d`; a sound workflow graph; both once more without the field `kind`
- When: each is checked
- Then: the broken graph gives exactly two items, `connection_endpoints` naming `e9` and then `single_writer` naming `d`, each with its fixed sentence
- And: the sound graph gives an empty list
- And: the graphs without `kind` give the same reports as with `"kind": "workflow"`

### TC-GTB-040 – An unknown kind is the only item
- Verifies: REQ-GTB-039
- Given: the broken graph of TC-GTB-039 plus a cycle, under the kinds `swarm`, the empty text and the number 5
- When: each is checked
- Then: each report is exactly one item `unknown_kind`, naming `swarm`, the empty text and `5`; none of the broken rules is listed

### TC-GTB-041 – A malformed graph never makes the check fail
- Verifies: REQ-GTB-040
- Given: six inputs: a step that is the number 5, connection data that is a list, a step without `id`, a connection without `from`, `nodes` that is the text `"x"`, and a graph that is a list
- When: each is checked
- Then: each check returns a list and no exception escapes
- And: the items are those of IF-301 v4 "Malformed input": rule 1 for the bad steps (`5`, `None`) and for `nodes` (`nodes`), rule 3 for the connection without `from`, the list data counted as empty data, rule 1 naming `graph` for the list (D-418 (2))

### TC-GTB-042 – Each rule finds what it is for, and nothing else
- Verifies: REQ-GTB-041, REQ-GTB-042, REQ-GTB-043, REQ-GTB-044, REQ-GTB-045, REQ-GTB-046, REQ-GTB-047, REQ-GTB-048
- Given: for each rule a small workflow graph that breaks only that rule, and a sound twin that differs in one place:
  - rule 1: steps `a`, `a` and `` (twin: `a`, `b`, `x/y`)
  - rule 2: a step of type `loop` (twin: type `transform`)
  - rule 3: connection `e2` from `a` to the missing `z` (twin: to `b`)
  - rule 4: `e1`, `e2` both from `d` to `t` without role and name (twin: `as` `x` and `y`)
  - rule 5: `d1 → d2` and `t1 → m1` (twin: `d1 → t1 → d2`)
  - rule 6: `t1` and `t2` both into `d` (twin: `t2` into `d2`)
  - rule 7: a master without `stop`, one with `{"max_repetitions": 0}`, a data step with `session`, a transform with two settings connections (twin: `{"max_seconds": 1.0}`, one settings connection)
  - rule 8: `d1 → t1 → d1` (twin: `d1 → t1 → d2`)
- When: each graph is checked
- Then: each broken graph gives exactly one item with its rule and the named parts (rule 8: `d1, t1, d1`); each twin gives an empty list
- And: the edge pairs of the table "Edge inputs" give the results listed there (two connections `t1 → d`: rule 4 only; a self-loop: rules 5 and 8; a cycle with a missing end: no rule 8)

### TC-GTB-043 – The run check: kind first and alone, then rules, then inputs
- Verifies: REQ-GTB-049, REQ-GTB-050
- Given: a context graph that also has two identical connections; a graph of kind `swarm` with a cycle; a workflow graph with two writers of `d` and a step reading the unsupplied `q`; the converted `chat` skill
- When: each is checked for a run, `chat` with `{"input.text": "hello"}`
- Then: the context graph is refused with only `kind_cannot_run` naming `context`; `swarm` with only `unknown_kind` naming `swarm`
- And: the workflow graph is refused with `single_writer` (`d`) first and the unsupplied input (`q`) second
- And: `chat` with its value is ready with an empty list (AC-018)

### TC-GTB-044 – An input nobody supplies is named with its step
- Verifies: REQ-GTB-051
- Given: the converted `chat` skill without values; the same with a graph value on `input.text`; a transform reading a data step another transform writes; a transform with a settings connection and an order connection from data steps that have no values; a data step whose graph value is `null`
- When: each is checked for a run, with no values given
- Then: `chat` gives one item `unsupplied_input`, step `step.converse`, input `input.text` (AC-018)
- And: the graph value, the written data step, the settings and the order connection give no item; the `null` graph value is named

### TC-GTB-045 – The document form is unchanged
- Verifies: REQ-GTB-052
- Given: the contract suites of IF-301 v1, v2 and v3, IF-102, IF-104 v1 (Python and JS) and IF-203 as they are on `goal/v4`
- When: they run against the code with IF-301 v4
- Then: every suite passes and every suite file is byte-identical to `goal/v4`

### TC-GTB-046 – The same list at every entry point
- Verifies: REQ-GTB-037, REQ-WFM-163, REQ-RUN-037, HR-004
- Given: two graphs that each break three rules: the AC-017 graph (a cycle and a second writer into one data step) plus a second, identical connection `d1 → t1` (`duplicate_connection`, `single_writer`, `cycle`; an empty step name would hide the cycle, Q-5) and a graph with a connection to a missing step, two identical connections and a data step holding `session`; a files store; the check route of IF-104 v2 as a mock that answers with the rule report (D-416 (2))
- When: each graph is checked through the rule report, saved, sent to the check route and run, five times in a row each; the second graph is run with a value for `d1`, which has no value and no writer (A-170b, D-428)
- Then: the rule report, the save and the check route give the same items, rule by rule, with the same parts in the same order and the same sentences, and the run names the parts of those items in the same order (a run result carries the parts only, REQ-RUN-037), in all five repeats (0 differences)
- And: witnesses AC-017

### TC-GTB-047 – No old refusal is lost
- Verifies: REQ-GTB-034, HR-005
- Given: the cases of TC-GTB-002 and the generator of TC-GTB-003 with seeds 1 to 1000, each document turned into the stored form as the prototype did (`cp17_check.to_graph`): a session processing step becomes a loop-controlling step with `max_cycles` read as `max_repetitions`, another processing step a transform, connections numbered `e1`, `e2`, ... (not `from_document`, which keeps a session as a transform and refuses unknown kinds, D-424)
- When: each graph is checked by the five older rules (document form) and by the eight rules
- Then: no graph is refused by the five and accepted by the eight, except a stop limit that REQ-WFM-048 accepts (`max_seconds: 1.0`)
- And: the graphs that only the eight refuse are counted by rule and printed (the prototype: 57, of them 42 `duplicate_connection` and 15 `single_writer`; the count is reported, not asserted)

### TC-IF-301-27 – The registry as the contract states it
- Verifies: REQ-GTB-033, REQ-GTB-034, REQ-GTB-035, REQ-GTB-036
- Given: golden example 24 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the registry of kinds is read, changed and read again, against both
- Then: it equals the value in the table of operations, and the change does not reach the second answer
- And: the real module and the mock give the same answer

### TC-IF-301-28 – A sound skill breaks no rule
- Verifies: REQ-GTB-037, REQ-GTB-038
- Given: golden example 25 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the converted `chat` skill is checked with and without its `kind`, against both
- Then: both reports are empty
- And: the real module and the mock give the same answer

### TC-IF-301-29 – Several rules, in order
- Verifies: REQ-GTB-037, REQ-GTB-046, REQ-GTB-048
- Given: golden example 26 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the graph `d1 → t1 → d1` with a second writer `t2 → d1` is checked, against both
- Then: exactly `single_writer` naming `d1`, then `cycle` naming `d1, t1, d1`
- And: the real module and the mock give the same answer

### TC-IF-301-30 – The cycle waits for known steps
- Verifies: REQ-GTB-043, REQ-GTB-048
- Given: golden example 27 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the graph of golden 26 plus `e9` to the missing `z` is checked, against both
- Then: `connection_endpoints` naming `e9`, `single_writer` naming `d1`, and no `cycle`
- And: the real module and the mock give the same answer

### TC-IF-301-31 – Context graphs keep rule 4
- Verifies: REQ-GTB-035
- Given: golden example 28 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: a context graph with `e1`, `e2` both from `c1` to `c2`, and one with a cycle, are checked, against both
- Then: the first gives only `duplicate_connection` naming `e2`; the second gives an empty list
- And: the real module and the mock give the same answer

### TC-IF-301-32 – An unknown kind and a kind that cannot run
- Verifies: REQ-GTB-039, REQ-GTB-049
- Given: golden example 29 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: a graph of kind `swarm` with a cycle is checked and run checked, and a context graph is run checked, against both
- Then: `swarm` gives only `unknown_kind` in both; the context graph is refused with only `kind_cannot_run`
- And: the real module and the mock give the same answer

### TC-IF-301-33 – Inputs given or not
- Verifies: REQ-GTB-050, REQ-GTB-051
- Given: golden example 30 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the converted `chat` skill is run checked without values, with `"hello"` and with `None` for `input.text`, against both
- Then: refused with one `unsupplied_input` of `step.converse` at `input.text`; ready twice
- And: the real module and the mock give the same answer

### TC-IF-301-34 – Malformed graphs
- Verifies: REQ-GTB-040
- Given: golden example 31 of IF-301 v4, word for word; the real module `graph_rule_set` and the mock `tests/helpers/mocks/if_301_graph_tables_v4.py`
- When: the five malformed graphs of golden 31 are checked, against both
- Then: each gives a list with the items of "Malformed input", and no exception escapes
- And: the real module and the mock give the same answer
