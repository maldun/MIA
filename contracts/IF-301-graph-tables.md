# IF-301 – Graph table definitions, record checks and conversion, v2

Owner (provider): N-3.2 Graph tables   Consumers: N-3.1 Storage layer, N-2.3 Workflow management (converts), N-2.4.1 Pipeline runner (reads)   Decided by: N-3   Mock complexity: 1 (a fixed list of types and pure functions, nothing stored)   Suites: `tests/acceptance/contract/test_if_301_graph_tables.py` (v1, unchanged) and `tests/acceptance/contract/test_if_301_v2_graph_tables.py` (v2)

What the storage layer needs to know about the tables of workflows and context graphs, and, since v2, about the graphs kept as separate node and edge records. Python calls; draft v0, v1 since A-60, v2 since A-90 (text approved 2026-11-07, D-262 to D-266). The rules are those of FR-7 and IF-102.

## What changes against v1
1. Four new tables, all versioned and not deletable: `graph_nodes`, `graph_edges` (REQ-GTB-005, 006, 013), `graphs` (the graph header and its members, D-264) and `skills` (the skill record of REQ-WFM-040, D-264). `workflows` and `context_graphs` stay as they are (document form, REQ-GTB-015). `definitions()` stays the v1 result; the four tables are listed by the new `record_definitions()` (owner, 2026-11-07: the v1 suite and REQ-GTB-001 say exactly two tables for `definitions()`).
2. A fixed list of node types built into the Graph tables: a node's JSON field names a type ID; each type has a data class and a JSON schema (REQ-GTB-009, 011). A new type is an amendment of this interface (owner, 2026-11-07).
3. New refusals `unknown_type`, `schema_break`, `unknown_member` and `unknown_endpoint` (REQ-GTB-010, 011, 019, 020) and the rule that a refused edit leaves the stored version alone (REQ-GTB-016).
4. Conversion between the record form and the document form of v1 (REQ-GTB-015).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `definitions()` | | `{table: {"versioned": bool, "deletable": bool}}` for `workflows` and `context_graphs` | both versioned, neither deletable; unchanged since v1 |
| `record_definitions()` | | the same form for `graph_nodes`, `graph_edges`, `graphs` and `skills`: `{"versioned": true, "deletable": false}` | the versions are kept by the Storage layer from this flag (REQ-GTB-013) |
| `validate(table, doc)` | table name, document | `None` or `{"rule", "detail"}` | for `workflows` and `context_graphs` exactly as v1: the first broken rule: `node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle` (detail: the cycle as ids, first id repeated at the end). Any document gives a rule or `None`, never an exception (A-60) |
| `types()` | | the type IDs of the fixed list for workflow graphs, sorted, each with its JSON schema | the list is part of this contract (below); context graphs have no fixed list (decision 5) |
| `check_record(table, record, categories=None, stored=None, record_id=None)` | `graph_nodes`, `graph_edges`, `graphs` or `skills`; `{"id", "data"}` for a node, a skill and a graph header, `{"id", "from", "to", "data"}` for an edge; for a record of a context graph `categories` = `{type ID: JSON schema}` of that context graph; `stored` = `{"nodes": {id: [versions]}, "edges": {id: [versions]}}`, what the caller has stored; `record_id` = the record ID the caller writes the record under (optional) | `None` or `{"rule", "detail"}` | rules: `record_identity` (detail: the field; `id` also when `record_id` is given and differs from the `id` inside the record, REQ-GTB-021), `unknown_member` (a graph header names a node or edge version that is not in `stored`; detail: its ID, REQ-GTB-019), `unknown_endpoint` (an edge names a start or end node that is not in `stored["nodes"]`; detail: that node ID, REQ-GTB-020), `unknown_type` (detail: the type ID, REQ-GTB-010; for a workflow graph the type is not in the fixed list, for a context graph not in `categories`), `schema_break` (detail: the path of the broken field, REQ-GTB-011). Without `stored` the two rules that need it are not checked (a pure function stores nothing); the Storage layer and the Workflow management always pass it. A record of a context graph without `categories` is `unknown_type`. Any input gives a rule or `None`, never an exception (as A-60); a table that is not one of the four is a `ValueError` |
| `to_object(record, categories=None)` | a node record, `categories` as above for a context graph | `{"object": obj}` or `{"refused": {"rule", "detail"}}` | for a workflow node `obj` is an instance of the class listed for the type ID in `record["data"]["type"]` (REQ-GTB-009); for a context-graph node it is a plain `ContextNode` (ID, type, JSON field) |
| `to_record(obj)` | an object of a listed class | a node record | `to_object(to_record(x))` equals `x` (REQ-GTB-014) |
| `to_document(nodes, edges)` | node records, edge records of one workflow | `{"document": doc}` or `{"refused": {"rule", "detail"}}` | the v1 document form (`{"nodes", "edges"}`): type `transform` becomes kind `process`, `data` stays `data`; a graph with a master node is `not_representable` (decision 3) |
| `from_document(doc)` | a v1 document | `{"nodes": [...], "edges": [...]}` (records) or `{"refused": {"rule", "detail"}}` | kinds `process` become `transform`, `data` stays `data` |

Record shapes of the two new tables (D-264): a graph header is `{"id", "data": {"kind": "workflow" or "context", "context_graph_id", "testbench_id" (may be empty), "description", "nodes": [{"id", "version"}], "edges": [{"id", "version"}]}}`; a graph version pins the version of each member, so "graph X, version n" is found from its header and an edit of one node makes a new graph version. A skill is `{"id", "data": {"command", "workflow_graph_id", "context_graph_id"}}`; that no command is used twice is a rule of the Workflow management (REQ-WFM-042), not of this interface.

The Workflow management calls `check_record` itself before it writes and so receives the rule and the detail it names in its refusal; the Storage layer calls it again as a guard. IF-102 does not change (D-264).

The Storage layer calls `check_record` before every write and writes nothing when it returns a rule; the version counter is changed only by a write that passed (REQ-GTB-016).

Rules in detail of the document form (A-60, D-160, D-162) are as in v1:
- `node_identity`: every node has a non-empty text `id`, unique, and a `kind` of `process` or `data`; every edge is `{"from", "to"}` with two text ids of known nodes. A document whose `nodes` or `edges` is not a list, a node or edge that is not an object, and an edge endpoint that is not text (a list, an object, a number) are `node_identity`.
- `session_stopping_criterion`: a process node with `session: true` has a `stop` object with `max_cycles` or `max_seconds`; each limit that is given is a positive integer (an integer >= 1, not a boolean; `-1`, `0`, `"3"`, `true`, `2.5`, NaN are refused), and a limit that is `null` counts as not given (D-162). A `stop` that is not an object is this rule too.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a table not defined here | `ValueError` | the caller asks IF-302 instead |
| a record or document that breaks a rule | the rule in the result, no exception | nothing was stored |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| validate a graph of 500 nodes | at most 200 ms (v1) | v1 |
| check 500 node records and 500 edge records | at most 500 ms (best of 3 runs, TC-IF-301-19) | proposal, measured in Plan step 4 (D-187: starting guess) |

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

The list is closed for the fields of a type too (A-93, REQ-GTB-022): the schema of each type sets `additionalProperties: false`, so the JSON field of a node holds `type`, the fields of the table above and nothing else. A node with another field, or with a key `id` inside `data`, is `{"rule": "schema_break", "detail": "<that field>"}` in `check_record` and in `to_object` (a stored node is refused on read; `to_object` never raises). This holds for workflow nodes only: the schema of a context-graph node comes from its categories (decision 5). The schemas that `types()` returns carry the setting.

## Golden examples
1. Typical: a valid lookup graph gives `None`.
2. Failure: an edge between two data nodes gives `adjacent_data_nodes`.
3. Edge: `p->d->p` gives `cycle` with detail `["p","d","p"]`; a session node with `max_cycles: 0` and no `max_seconds` gives `session_stopping_criterion`.
4. Malformed (A-60): a session node with `stop: "x"` or `max_cycles: -1`, `"3"`, `true` or `2.5` gives `session_stopping_criterion`, with `max_cycles: 1` it is valid; an edge `{"from": ["q"], "to": "p"}` gives `node_identity`.
5. Typical (v2): a `transform` node record with a known type and a field that fits its schema gives `None`; `to_object` returns an instance of the listed class with equal values.
6. Failure (v2): a node whose `data.type` is `x.unknown` gives `{"rule": "unknown_type", "detail": "x.unknown"}`.
7. Failure (v2): a node whose required key is missing gives `{"rule": "schema_break", "detail": "<path of the key>"}` (the path as the pinned validator names it, TR-GTB-003).
8. Edge (v2): a refused edit leaves version 1 as the latest version (REQ-GTB-016); `check_record` itself stores nothing and changes neither its input nor `stored`.
9. Compatibility (v2): `from_document(to_document(g))` equals `g` for a graph without a master node; the v1 suite passes unchanged.
10. Header (v2): a `graphs` record naming n1 at version 5 with `stored = {"nodes": {"n1": [1, 2]}, "edges": {}}` gives `{"rule": "unknown_member", "detail": "n1"}`; naming version 2 gives `None`.
11. Edge (v2): an edge `e1` from `n1` to `n9` with `stored["nodes"] == {"n1": [1]}` gives `{"rule": "unknown_endpoint", "detail": "n9"}`.
12. Skill (v2): `{"id": "lookup", "data": {"command": "/lookup", "workflow_graph_id": "wf-lookup"}}` (no context graph ID) gives `{"rule": "schema_break", "detail": "context_graph_id"}`.
13. Context graph (v2): a node of category `entity` with `categories = {"entity": <schema>}` and a field that fits gives `None`; the same node without `categories` gives `{"rule": "unknown_type", "detail": "entity"}`.
14. Document form (v2): `to_document` of a graph with a master node gives `{"refused": {"rule": "not_representable", "detail": "<master node ID>"}}`.
15. Record identity (v2): a node record whose `id` is `n1`, checked with `record_id="x"`, gives `{"rule": "record_identity", "detail": "id"}`; with `record_id="n1"` or without `record_id` it gives `None`.
16. Extra field (v2): a node record `{"id": "d1", "data": {"type": "data", "foo": 1}}` gives `{"rule": "schema_break", "detail": "foo"}` in `check_record`, and `to_object` of it gives `{"refused": {"rule": "schema_break", "detail": "foo"}}`; a key `id` inside `data` is named `id`; the same node without the extra field gives `None`.

## Decisions of the owner, 2026-11-07 (D-262, D-263, D-264, D-266)
1. **Graph rules for the new node types** stay in the Workflow management only. IF-301 keeps the v1 rules for the document form and adds only the record rules; A-90's "validate also reports ..." is read as `check_record`.
2. **Refusal** is a result with the rule, as in v1 (A-60), not an exception.
3. **Master node in the document form:** `to_document` refuses with `not_representable`.
4. **Types** of workflow graphs are a fixed list inside the Graph tables, not registered by other parts. Adding a type is an amendment of this interface.
5. **Context graphs (D-263):** no fixed list. A context-graph node names a category whose JSON schema comes from the context graph's own definition (FR-41, goal C); the caller passes it as `categories`. Where that definition is stored is decided in goal C; in G-V2 no context graph is converted, so only the rule and its checks exist.
6. **Master node (D-264):** `toolbox_id` required, `stop` required, `task` optional.
7. **Membership (D-264):** a versioned table `graphs` holds the header and lists its members with their versions.
8. **Skill record (D-264):** a versioned table `skills` in IF-301; STORE defines it, the Workflow management checks the content.
9. **Refusals (D-264):** the Workflow management calls `check_record` itself; IF-102 is unchanged.
10. **Review of 2026-11-07 (D-266):** `check_record` gets the argument `stored` for the rules that need to know what is stored; `to_document` maps `transform` to `process`; an edge must name stored nodes (`unknown_endpoint`, REQ-GTB-020); golden examples (here 10 to 14) added; stale wording corrected.
11. **Plan step 4 (owner, 2026-11-07):** `definitions()` stays the two tables of v1 and the four record tables come from `record_definitions()`, because the v1 suite (TC-IF-301-01) and REQ-GTB-001 say exactly two tables.
12. **A-92 (found in Implement T-04, 2026-11-07):** a record written under a record ID that differs from the `id` inside it is refused; the rule stays in the Graph tables (REQ-GTB-021), so `check_record` takes the optional `record_id` and the Storage layer passes the ID it writes under. v2 is not merged yet, so the argument is part of v2.
13. **A-93 (Verify finding F-01, 2026-11-07; the owner delegated the choice to the reviewer and may overrule):** the fixed list is closed for the fields of a type too: a node with a field its type does not list is refused as `schema_break` naming the field, on write and on read. Before, such a node was stored and then `to_object` raised (the mock silently dropped the field). Why: the list of types is fixed (decision 4), REQ-GTB-014 needs the round trip exact, and a silent drop would lose data. Context-graph nodes are not affected (decision 5). Several breaks in one record: the detail is the first path in text order, a missing key counting at the path of its object and an extra field at its own path, so a missing `toolbox_id` is named before an extra `foo`. v2 is not merged yet, so this is part of v2.

## Clarifications fixed by the v2 mock and suite (for approval with this text; the approved text of D-262 to D-266 was silent on them)
- `types()` returns a dict `{type ID: JSON schema}` whose keys are the three type IDs in sorted order: `data`, `master`, `transform`.
- A node object has the attribute `id` and, for each field of its type in the table above, an attribute of that name (absent optional fields: `value` and `task` are `None`, `parameters` is `{}`); `to_record` leaves `value` and `task` out when they are `None` and always writes `parameters`. A context-graph node object has `id`, `type` and its other fields.
- An edge has no type; the JSON field `data` of an edge must be an object, else `schema_break` with the detail `data`. A record whose `data` is missing or is not an object is `schema_break` with the detail `data`.
- The category of a context-graph node is in `data["type"]`, as the type of a workflow node. Given `categories` (even empty) a record is a context-graph record: its type must be one of the categories.
- The detail of `schema_break` is the path of the field with dots (`stop.max_repetitions`); a missing required key is named by that key. The contract suite fixes only top-level paths.
- An additional field of a node's JSON field is named by its own key (`foo`; `id` for a key `id` inside `data`); when several are extra, the first in sorted order is named (decision 13).
- A graph header that names the same member ID twice is `record_identity` with the detail `nodes` or `edges` (the mock does so; the suite only requires a refusal in TC-GTB-017).
- The document form carries the other fields of a node flat beside `id` and `kind`, and the JSON field of an edge under `data` with its `id`; an edge of a v1 document without an ID gets `e1`, `e2`, ... in order. A node record converted from a v1 document is not checked (a `process` node has no `toolbox_id`, so the record breaks the schema of `transform` until a toolbox ID is added).

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | – |
| v1 | 2026-10-31 | a session limit is a positive integer (not a boolean, null = not given); a malformed part (a `stop` that is not an object, an edge endpoint that is not text) is named by its rule instead of raising; golden 4 | A-60 (D-160, D-162) |
| v2 | 2026-11-07 | tables `graph_nodes`, `graph_edges`, `graphs`, `skills` (listed by `record_definitions()`); fixed list of types; `types`, `check_record`, `to_object`, `to_record`, `to_document`, `from_document`; rules `record_identity`, `unknown_type`, `schema_break`, `unknown_member`, `unknown_endpoint`; golden 5 to 16, `record_id` of `check_record`, the fixed types forbid additional fields | A-90 (D-188, D-262 to D-266), A-92, A-93 |
