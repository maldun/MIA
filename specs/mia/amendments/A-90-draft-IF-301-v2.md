# A-90, draft of the contract text IF-301 v2 (Graph table definitions and validation)

Status: **draft; open decisions answered by the owner (D-262), the type list and the text still to be approved** (G-V2.STORE Plan step 4, 2026-11-07). It is not `contracts/IF-301-graph-tables.md`: that file, the mock and the contract suite change only after this text is approved, and then in a session of their own (tests are written outside the implementing session). Basis: A-90 (approved, D-188), REQ-GTB-005 to 016, v1 text of 2026-10-31.

Owner (provider): N-3.2 Graph tables   Consumers: N-3.1 Storage layer, N-2.3 Workflow management (converts), N-2.4.1 Pipeline runner (reads)   Decided by: N-3   Mock complexity: **1** (a fixed list of types and pure functions, nothing stored)   Suite: `tests/acceptance/contract/test_if_301_graph_tables.py` (v1 cases stay; v2 cases are added)

## What changes against v1
1. Two new tables for the record form: `graph_nodes` and `graph_edges`, versioned, not deletable (REQ-GTB-005, 006, 013). `workflows` and `context_graphs` stay as they are (document form, REQ-GTB-015).
2. A fixed list of node types built into the Graph tables: a node's JSON field names a type ID; each type has a data class and a JSON schema (REQ-GTB-009, 011). A new type is an amendment of this interface (owner, 2026-11-07).
3. New refusals `unknown_type` and `schema_break` (REQ-GTB-010, 011) and the rule that a refused edit leaves the stored version alone (REQ-GTB-016).
4. Conversion between the record form and the document form of v1 (REQ-GTB-015).

## Operations (new and changed)
| Name | Input | Output | Notes |
|---|---|---|---|
| `definitions()` | | v1 result plus `graph_nodes` and `graph_edges`: `{"versioned": true, "deletable": false}` | the versions are kept by the Storage layer from this flag (REQ-GTB-013) |
| `validate(table, doc)` | table name, document | `None` or `{"rule", "detail"}` | for `workflows` and `context_graphs` exactly as v1 |
| `types()` | | the type IDs of the fixed list for workflow graphs, sorted, each with its JSON schema | the list is part of this contract (below); context graphs have no fixed list (open point 5, decided) |
| `check_record(table, record, categories=None)` | `graph_nodes` or `graph_edges`; `{"id", "data"}` for a node, `{"id", "from", "to", "data"}` for an edge; for a record of a context graph `categories` = `{type ID: JSON schema}` of that context graph | `None` or `{"rule", "detail"}` | rules: `record_identity` (detail: the field), `unknown_type` (detail: the type ID, REQ-GTB-010; for a workflow graph the type is not in the fixed list, for a context graph not in `categories`), `schema_break` (detail: the path of the broken field, REQ-GTB-011). A record of a context graph without `categories` is `unknown_type`. Any input gives a rule or `None`, never an exception (as A-60) |
| `to_object(record, categories=None)` | a node record, `categories` as above for a context graph | `{"object": obj}` or `{"refused": {"rule", "detail"}}` | for a workflow node `obj` is an instance of the class listed for the type ID in `record["data"]["type"]` (REQ-GTB-009); for a context-graph node it is a plain `ContextNode` (ID, type, JSON field) |
| `to_record(obj)` | an object of a listed class | a node record | `to_object(to_record(x))` equals `x` (REQ-GTB-014) |
| `to_document(nodes, edges)` | node records, edge records of one workflow | `{"document": doc}` or `{"refused": {"rule", "detail"}}` | the v1 document form (`{"nodes", "edges"}`); a graph with a master node is `not_representable` (see open point 3) |
| `from_document(doc)` | a v1 document | `{"nodes": [...], "edges": [...]}` (records) or `{"refused": {"rule", "detail"}}` | kinds `process` become `transform`, `data` stays `data` |

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

## The fixed list of types (to be filled before approval)
One type per node kind of the graph model; the schemas come from the requirements named, they are placeholders until MODEL and TOOLBOX confirm them:
| Type ID | Kind | Fields of the JSON field (besides `type`) | From |
|---|---|---|---|
| `data` | data node | the four fields of the graph description and the parameters of REQ-WFM-049 | REQ-WFM-044, 049 |
| `transform` | transform node | `toolbox_id` (text) | REQ-GTB-007 |
| `master` | master node | `task` (the definition), `stop` (the stopping criterion) | REQ-GTB-008, REQ-WFM-048 |
The names and the exact fields are open until the MODEL session confirms REQ-WFM-043 to 049 (it states them).

## Decisions of the owner, 2026-11-07 (D-262, D-263)
1. **Graph rules for the new node types** stay in the Workflow management only. IF-301 keeps the v1 rules for the document form and adds only the record rules; A-90's "validate also reports ..." is read as `check_record`.
2. **Refusal** is a result with the rule, as in v1 (A-60), not an exception.
3. **Master node in the document form:** `to_document` refuses with `not_representable`.
4. **Types** of workflow graphs are a fixed list inside the Graph tables, not registered by other parts. Adding a type is an amendment of this interface.
5. **Context graphs (D-263):** no fixed list. A context-graph node names a category whose JSON schema comes from the context graph's own definition (FR-41, goal C); the caller passes it as `categories`. Where that definition is stored is decided in goal C; in G-V2 no context graph is converted, so only the rule and its checks exist.

## Version history (to be added when approved)
| Version | Date | Change | Amendment |
|---|---|---|---|
| v2 | – | tables `graph_nodes`, `graph_edges`; fixed list of types; `check_record`, `to_object`, `to_record`, `to_document`, `from_document`; rules `unknown_type`, `schema_break`, `record_identity` | A-90 (D-188) |
