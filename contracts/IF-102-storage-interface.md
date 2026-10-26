# IF-102 – Storage interface, v0

Owner (provider): N-3 Database   Consumers: N-2 Backend   Decided by: N-0   Mock complexity: 2 (in-memory fake)   Suite: `tests/acceptance/contract/test_if_102_storage.py`

The only door to the shared state. Python calls on a storage client (the real one talks to PostgreSQL). Draft v0 for the owner's review.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `put(table, id, doc, author, expected_version=None)` | table name, record id, document, account name | `{"version": n}` | every put is a new immutable version, counted from 1 per record; `expected_version` must equal the current version, else `conflict` |
| `get(table, id, version=None)` | | `{"id","version","author","time","doc"}` | latest version if none given |
| `history(table, id)` | | list of `{"version","author","time"}`, oldest first | |
| `ids(table)` | | sorted list of ids | |
| `delete(table, id, author)` | | nothing | refused with `immutable` for `workflows` and `context_graphs` |
| `subscribe(table, callback)` | | a function that unsubscribes | `callback({"table","id","version","author"})` after every write |

Tables: workflows, context_graphs, history, memory, votes, tasks, memos, accounts, presets, gestures, runs, source_trust.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| unknown table | `StorageError("unknown_table")` | nothing changed |
| unknown id or version | `not_found` | nothing changed |
| `expected_version` differs from the current version | `conflict` with `detail.current` | nothing changed |
| delete on a versioned table | `immutable` | nothing changed |
| a workflow breaks a graph rule | `invalid` with `rule` in `node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle` (detail: the cycle as ids) | nothing stored, no version consumed |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| change notification to a subscriber | at most 2 s | REQ-DB-006 |
| a stored version | never changes after it is written | REQ-DB-003 |

## Golden examples
1. Typical: `put("workflows","lookup",doc,"anna")` gives version 1; a second put gives version 2; `get(...,version=1)` returns the first document unchanged.
2. Failure: a workflow with an edge between two data nodes is refused with rule `adjacent_data_nodes`; `ids("workflows")` is unchanged.
3. Edge: `p->d->p` (process, data, process) is a `cycle` of `["p","d","p"]`; a self-loop `a->a` between two process nodes is `adjacent_process_nodes`, not a cycle; `expected_version=0` on a new record is accepted.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | – |
| v1 | 2026-10-26 | tables `runs` (run results with workflow version, model pin and benchmark version) and `source_trust` added, as IF-302 defines them (finding F-5) | 9 |
