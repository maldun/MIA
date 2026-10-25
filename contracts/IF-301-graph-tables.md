# IF-301 – Graph table definitions and validation, v0

Owner (provider): N-3.2 Graph tables   Consumers: N-3.1 Storage layer   Decided by: N-3   Mock complexity: 1 (static definitions, a pure function)   Suite: `tests/acceptance/contract/test_if_301_graph_tables.py`

What the storage layer needs to know about the tables of workflows and context graphs. Python calls; draft v0. The rules are those of FR-7 and IF-102.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `definitions()` | | `{table: {"versioned": bool, "deletable": bool}}` for `workflows` and `context_graphs` | both versioned, neither deletable |
| `validate(table, doc)` | table name, document | `None` or `{"rule", "detail"}` | the first broken rule: `node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle` (detail: the cycle as ids, first id repeated at the end) |

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

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | – |
