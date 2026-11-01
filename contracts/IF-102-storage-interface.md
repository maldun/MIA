# IF-102 – Storage interface, v3

Owner (provider): N-3 Database   Consumers: N-2 Backend   Decided by: N-0   Mock complexity: 2 (in-memory fake)   Suite: `tests/acceptance/contract/test_if_102_storage.py`

The only door to the shared state. Python calls on a storage client (the real one is the Storage layer on files or on PostgreSQL).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `put(table, id, doc, author, expected_version=None)` | table name, record id, document, account name | `{"version": n}` | every put is a new immutable version, counted from 1 per record; `expected_version` must equal the current version, else `conflict` |
| `get(table, id, version=None)` | | `{"id","version","author","time","doc"}` | latest version if none given |
| `history(table, id)` | | list of `{"version","author","time"}`, oldest first | |
| `ids(table)` | | sorted list of ids | |
| `delete(table, id, author)` | | nothing | only for the tables whose definition allows it (IF-301, IF-302: `history`, `memory`, `tasks`, `memos`); refused with `immutable` for the others, `workflows` and `context_graphs` among them |
| `categories()` | | list of the vote categories, in their order: `answer_quality`, `reactions`, `character_behaviour`, `service` | read from the record tables (IF-302) inside N-3, so a consumer imports nothing of IF-302 (D-162) |
| `subscribe(table, callback)` | | a function that unsubscribes | `callback({"table","id","version","author"})` after every write; a delete is a write and is told with `"version": None` and the deleting account as `author`; a refused put or delete tells nothing |

Tables: the tables of IF-301 (`workflows`, `context_graphs`) and IF-302 (`history`, `memory`, `votes`, `tasks`, `memos`, `accounts`, `presets`, `gestures`, `runs`, `source_trust`, `cases`, `behaviours`, `workflow_meta`, `reports`); their definitions decide the document rules and whether a record may be deleted.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| unknown table | `StorageError("unknown_table")` | nothing changed |
| unknown id or version | `not_found` | nothing changed |
| `expected_version` differs from the current version | `conflict` with `detail.current` | nothing changed |
| delete on a table that is not deletable | `immutable` | nothing changed |
| a workflow breaks a graph rule | `invalid` with `rule` in `node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle` (detail: the cycle as ids) | nothing stored, no version consumed |
| a text with a NUL character (in the document, its keys or the id), a number that is not finite (NaN, inf) or an id that is not text (A-65) | `invalid` with `rule` `schema` | nothing stored, no version consumed |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| change notification to a subscriber | at most 2 s | REQ-DB-006 |
| a stored version | never changes after it is written | REQ-DB-003 |

## Golden examples
1. Typical: `put("workflows","lookup",doc,"anna")` gives version 1; a second put gives version 2; `get(...,version=1)` returns the first document unchanged.
2. Failure: a workflow with an edge between two data nodes is refused with rule `adjacent_data_nodes`; `ids("workflows")` is unchanged.
3. Edge: `p->d->p` (process, data, process) is a `cycle` of `["p","d","p"]`; a self-loop `a->a` between two process nodes is `adjacent_process_nodes`, not a cycle; `expected_version=0` on a new record is accepted.
4. Delete: a subscriber of `memos` hears `delete("memos","m","ben")` as `{"table":"memos","id":"m","version":None,"author":"ben"}`; a second delete of `m` is `not_found` and tells nothing.
5. Categories: `categories()` gives `["answer_quality","reactions","character_behaviour","service"]`, and a vote of each category is accepted.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | – |
| v1 | 2026-10-26 | tables `runs` (run results with workflow version, model pin and benchmark version) and `source_trust` added, as IF-302 defines them (finding F-5) | 9 |
| v2 | 2026-10-31 | a delete is told to the subscribers with version None (golden 4, TC-IF-102-09; D-158, N-3.1 Verify F7); the tables and the delete rule follow the definitions of IF-301 and IF-302 (D-67 decision 2, D-69; N-3.1 Verify F12). The mock refuses delete for the graph tables only (complexity 2). `categories()`, the vote categories (golden 5, TC-IF-102-10; D-162) | A-59 |
| v3 | 2026-10-31 | values that not every backend keeps alike are refused with `invalid`/`schema`: NUL, numbers that are not finite, ids that are not text (TC-IF-102-11; D-168, N-3.1 re-verification R3a) | A-65 |
