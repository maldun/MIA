# IF-301 – Graph table definitions and validation, v1

Owner (provider): N-3.2 Graph tables   Consumers: N-3.1 Storage layer   Decided by: N-3   Mock complexity: 1 (static definitions, a pure function)   Suite: `tests/acceptance/contract/test_if_301_graph_tables.py`

What the storage layer needs to know about the tables of workflows and context graphs. Python calls; draft v0, v1 since A-60. The rules are those of FR-7 and IF-102.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `definitions()` | | `{table: {"versioned": bool, "deletable": bool}}` for `workflows` and `context_graphs` | both versioned, neither deletable |
| `validate(table, doc)` | table name, document | `None` or `{"rule", "detail"}` | the first broken rule: `node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle` (detail: the cycle as ids, first id repeated at the end). Any document gives a rule or `None`, never an exception (A-60) |

Rules in detail (A-60, D-160, D-162):
- `node_identity`: every node has a non-empty text `id`, unique, and a `kind` of `process` or `data`; every edge is `{"from", "to"}` with two text ids of known nodes. A document whose `nodes` or `edges` is not a list, a node or edge that is not an object, and an edge endpoint that is not text (a list, an object, a number) are `node_identity`.
- `session_stopping_criterion`: a process node with `session: true` has a `stop` object with `max_cycles` or `max_seconds`; each limit that is given is a positive integer (an integer >= 1, not a boolean; `-1`, `0`, `"3"`, `true`, `2.5`, NaN are refused), and a limit that is `null` counts as not given (D-162). A `stop` that is not an object is this rule too.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a table that is not defined here | `ValueError` | the caller asks IF-302 instead |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| validate a graph of 500 nodes | at most 200 ms | proposal, set in Plan |

## Golden examples
1. Typical: a valid lookup graph gives `None`.
2. Failure: an edge between two data nodes gives `adjacent_data_nodes`.
3. Edge: `p->d->p` gives `cycle` with detail `["p","d","p"]`; a session node with `max_cycles: 0` and no `max_seconds` gives `session_stopping_criterion`.
4. Malformed (A-60): a session node with `stop: "x"` or `max_cycles: -1`, `"3"`, `true` or `2.5` gives `session_stopping_criterion`, with `max_cycles: 1` it is valid; an edge `{"from": ["q"], "to": "p"}` gives `node_identity`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | – |
| v1 | 2026-10-31 | a session limit is a positive integer (not a boolean, null = not given); a malformed part (a `stop` that is not an object, an edge endpoint that is not text) is named by its rule instead of raising; golden 4 | A-60 (D-160, D-162) |
