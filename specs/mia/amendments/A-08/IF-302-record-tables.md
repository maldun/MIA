# IF-302 – Record table definitions and validation, v1

Owner (provider): N-3.3 Record tables   Consumers: N-3.1 Storage layer   Decided by: N-3   Mock complexity: 1 (static definitions, a pure function)   Suite: `tests/acceptance/contract/test_if_302_record_tables.py`

What the storage layer needs to know about all tables except workflows and context graphs. Python calls; draft v0.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `definitions()` | | `{table: {"versioned": bool, "deletable": bool}}` for `history`, `memory`, `votes`, `tasks`, `memos`, `accounts`, `presets`, `gestures`, `runs`, `source_trust`, and **[v1]** `cases` (proposed benchmark cases, REQ-CHA-016) and `behaviours` (the adaptation counters, REQ-CHA-017, -018); the two new tables are versioned and not deletable | `memory`, `tasks`, `memos` are deletable (a user deletes any record, FR-14); `votes` and `runs` are not |
| `validate(table, doc)` | table name, document | `None` or `{"rule", "detail"}` | rule `schema` with the missing field, or `category` for a vote outside the four categories |

Required fields: `memory` {text, source}; `votes` {user, subject, category, value}; `tasks` {text}; `memos` {text}; `runs` {workflow, workflow_version, model_pin, benchmark_version}; **[v1]** `cases` {question, answer, status}; `behaviours` {name, net, votes}. Vote `category` is one of `answer_quality`, `reactions`, `character_behaviour`, `service`; `value` is 1 or -1.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a table that is not defined here | `ValueError` | the caller asks IF-301 instead |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| text of a task or memo | returned unchanged, any characters | REQ-DB-014, FR-28 |

## Golden examples
1. Typical: a vote `{user, subject, category: "reactions", value: -1}` gives `None`.
2. Failure: a vote with category `mood` gives rule `category`; a memory record without `source` gives rule `schema`, detail `source`.
3. Edge: `memory` is deletable, `votes` is not; text with newlines, quotes and non-ASCII characters is valid.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | – |
| v1 | 2026-10-27 | the tables `cases` and `behaviours` (owner 2026-10-27: a database table for the adaptation counters; a minus on a fact proposes a case) | A-08 |
