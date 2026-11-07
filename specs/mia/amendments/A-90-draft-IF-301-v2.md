# A-90, draft of the contract text IF-301 v2 (Graph table definitions and validation)

Status: **draft; all open points answered by the owner (D-262, D-263, D-264); the text still to be approved as a whole** (G-V2.STORE Plan step 4, 2026-11-07). It is not `contracts/IF-301-graph-tables.md`: that file, the mock and the contract suite change only after this text is approved, and then in a session of their own (tests are written outside the implementing session). Basis: A-90 (approved, D-188), REQ-GTB-005 to 016, v1 text of 2026-10-31.

Owner (provider): N-3.2 Graph tables   Consumers: N-3.1 Storage layer, N-2.3 Workflow management (converts), N-2.4.1 Pipeline runner (reads)   Decided by: N-3   Mock complexity: **1** (a fixed list of types and pure functions, nothing stored)   Suite: `tests/acceptance/contract/test_if_301_graph_tables.py` (v1 cases stay; v2 cases are added)

## What changes against v1
1. Four new tables, all versioned and not deletable: `graph_nodes`, `graph_edges` (REQ-GTB-005, 006, 013), `graphs` (the graph header and its members, D-264) and `skills` (the skill record of REQ-WFM-040, D-264). `workflows` and `context_graphs` stay as they are (document form, REQ-GTB-015).
2. A fixed list of node types built into the Graph tables: a node's JSON field names a type ID; each type has a data class and a JSON schema (REQ-GTB-009, 011). A new type is an amendment of this interface (owner, 2026-11-07).
3. New refusals `unknown_type` and `schema_break` (REQ-GTB-010, 011) and the rule that a refused edit leaves the stored version alone (REQ-GTB-016).
4. Conversion between the record form and the document form of v1 (REQ-GTB-015).

## Operations (new and changed)
| Name | Input | Output | Notes |
|---|---|---|---|
| `definitions()` | | v1 result plus `graph_nodes`, `graph_edges`, `graphs` and `skills`: `{"versioned": true, "deletable": false}` | the versions are kept by the Storage layer from this flag (REQ-GTB-013) |
| `validate(table, doc)` | table name, document | `None` or `{"rule", "detail"}` | for `workflows` and `context_graphs` exactly as v1 |
| `types()` | | the type IDs of the fixed list for workflow graphs, sorted, each with its JSON schema | the list is part of this contract (below); context graphs have no fixed list (open point 5, decided) |
| `check_record(table, record, categories=None)` | `graph_nodes`, `graph_edges`, `graphs` or `skills`; `{"id", "data"}` for a node, a skill and a graph header, `{"id", "from", "to", "data"}` for an edge; for a record of a context graph `categories` = `{type ID: JSON schema}` of that context graph | `None` or `{"rule", "detail"}` | rules: `record_identity` (detail: the field), `unknown_member` (a graph header names a node or edge version that is not stored; detail: its ID), `unknown_type` (detail: the type ID, REQ-GTB-010; for a workflow graph the type is not in the fixed list, for a context graph not in `categories`), `schema_break` (detail: the path of the broken field, REQ-GTB-011). A record of a context graph without `categories` is `unknown_type`. Any input gives a rule or `None`, never an exception (as A-60) |
| `to_object(record, categories=None)` | a node record, `categories` as above for a context graph | `{"object": obj}` or `{"refused": {"rule", "detail"}}` | for a workflow node `obj` is an instance of the class listed for the type ID in `record["data"]["type"]` (REQ-GTB-009); for a context-graph node it is a plain `ContextNode` (ID, type, JSON field) |
| `to_record(obj)` | an object of a listed class | a node record | `to_object(to_record(x))` equals `x` (REQ-GTB-014) |
| `to_document(nodes, edges)` | node records, edge records of one workflow | `{"document": doc}` or `{"refused": {"rule", "detail"}}` | the v1 document form (`{"nodes", "edges"}`); a graph with a master node is `not_representable` (see open point 3) |
| `from_document(doc)` | a v1 document | `{"nodes": [...], "edges": [...]}` (records) or `{"refused": {"rule", "detail"}}` | kinds `process` become `transform`, `data` stays `data` |

Record shapes of the two new tables (D-264): a graph header is `{"id", "data": {"kind": "workflow" or "context", "context_graph_id", "testbench_id" (may be empty), "description", "nodes": [{"id", "version"}], "edges": [{"id", "version"}]}}`; a graph version pins the version of each member, so "graph X, version n" is found from its header and an edit of one node makes a new graph version. A skill is `{"id", "data": {"command", "workflow_graph_id", "context_graph_id"}}`; that no command is used twice is a rule of the Workflow management (REQ-WFM-042), not of this interface.

The Workflow management calls `check_record` itself before it writes and so receives the rule and the detail it names in its refusal; the Storage layer calls it again as a guard. IF-102 does not change (D-264).

The Storage layer calls `check_record` before every write and writes nothing when it returns a rule; the version counter is changed only by a write that passed (REQ-GTB-016).

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a table not defined here | `ValueError` | the caller asks IF-302 instead |
| a record or document that breaks a rule | the rule in the result, no exception | nothing was stored |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| validate a graph of 500 nodes | at most 200 ms (v1) | v1 |
| check 500 node records and 500 edge records | at most 500 ms | proposal, measured in Step 4 (D-187: starting guess) |

## Golden examples (new, besides the four of v1)
1. Typical: a `transform` node record with a known type and a field that fits its schema gives `None`; `to_object` returns an instance of the listed class with equal values.
2. Failure: a node whose `data.type` is `x.unknown` gives `{"rule": "unknown_type", "detail": "x.unknown"}`.
3. Failure: a node whose required key is missing gives `{"rule": "schema_break", "detail": "<path of the key>"}` (the path as the pinned validator names it, TR-GTB-003).
4. Edge: a refused edit leaves version 1 as the latest version (REQ-GTB-016).
5. Compatibility: `from_document(to_document(g))` equals `g` for a graph without a master node; the v1 suite passes unchanged.

## The fixed list of types (field names confirmed by the owner in D-264)
Workflow nodes only (D-263); the rules of the whole graph are checked by the Workflow management (D-262). Besides `type`, the JSON field of a node holds:
| Type ID | Field | JSON kind | Required | From |
|---|---|---|---|---|
| `data` | `value` | any JSON | optional | REQ-WFM-049 |
| `data` | `parameters` | object | optional (empty object if absent) | REQ-WFM-049 |
| `transform` | `toolbox_id` | string | required | REQ-GTB-007 |
| `master` | `toolbox_id` | string | required (a master node runs like a transform, REQ-RUN-018) | REQ-RUN-018 |
| `master` | `stop` | object with `max_repetitions` (integer, at least 1) and/or `max_seconds` (number, above 0), at least one of them | required | REQ-WFM-048, REQ-GTB-008 |
| `master` | `task` | object, shape open until the debates goal | optional | REQ-GTB-008 |
The graph description (ID, context graph ID, testbench ID, description) is not a node field: it is in the graph header.

## Decisions of the owner, 2026-11-07 (D-262, D-263, D-264)
1. **Graph rules for the new node types** stay in the Workflow management only. IF-301 keeps the v1 rules for the document form and adds only the record rules; A-90's "validate also reports ..." is read as `check_record`.
2. **Refusal** is a result with the rule, as in v1 (A-60), not an exception.
3. **Master node in the document form:** `to_document` refuses with `not_representable`.
4. **Types** of workflow graphs are a fixed list inside the Graph tables, not registered by other parts. Adding a type is an amendment of this interface.
5. **Context graphs (D-263):** no fixed list. A context-graph node names a category whose JSON schema comes from the context graph's own definition (FR-41, goal C); the caller passes it as `categories`. Where that definition is stored is decided in goal C; in G-V2 no context graph is converted, so only the rule and its checks exist.

6. **Master node (D-264):** `toolbox_id` required, `stop` required, `task` optional.
7. **Membership (D-264):** a versioned table `graphs` holds the header and lists its members with their versions.
8. **Skill record (D-264):** a versioned table `skills` in IF-301; STORE defines it, the Workflow management checks the content.
9. **Refusals (D-264):** the Workflow management calls `check_record` itself; IF-102 is unchanged.

## Version history (to be added when approved)
| Version | Date | Change | Amendment |
|---|---|---|---|
| v2 | – | tables `graph_nodes`, `graph_edges`, `graphs`, `skills`; fixed list of types; `check_record`, `to_object`, `to_record`, `to_document`, `from_document`; rules `unknown_type`, `schema_break`, `record_identity` | A-90 (D-188) |
