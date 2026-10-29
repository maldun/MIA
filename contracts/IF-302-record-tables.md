# IF-302 – Record table definitions and validation, v5

Owner (provider): N-3.3 Record tables   Consumers: N-3.1 Storage layer   Decided by: N-3   Mock complexity: 1 (static definitions, a pure function)   Suite: `tests/acceptance/contract/test_if_302_record_tables.py`

What the storage layer needs to know about all tables except workflows and context graphs. Python calls; draft v0.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `definitions()` | | `{table: {"versioned": bool, "deletable": bool}}` for `history`, `memory`, `votes`, `tasks`, `memos`, `accounts`, `presets`, `gestures`, `runs`, `source_trust`, and **[v1]** `cases` (proposed benchmark cases, REQ-CHA-016) and `behaviours` (the adaptation counters, REQ-CHA-017, -018), **[v3]** `workflow_meta` (the lifecycle of a workflow, REQ-WFM-002, -006), **[v4]** `reports` (a finished report of a task, REQ-WFM-038); the new tables are versioned and not deletable by the application (v5: also `reports`; a finished report has one version, the application never changes or deletes it, it is deleted in the database) | `memory`, `tasks`, `memos` are deletable (a user deletes any record, FR-14); `votes` and `runs` are not |
| `validate(table, doc)` | table name, document | `None` or `{"rule", "detail"}` | rule `schema` with the missing field, or `category` for a vote outside the four categories |

Required fields: `memory` {text, source} **[v2]** and optionally `kind` (`fact`, `preference` or `commitment`), `status` (`active` or `replaced`), `subject` (the account the record is about) and `updated` (a UTC time): a given `kind` or `status` outside its list is rule `schema` with that field as detail, a record of v1 without them stays valid (REQ-CHA-011); `votes` {user, subject, category, value}; **[v4]** `reports` {task, skill, skill_version, question, account, model_pin, report} (`report` is the structured report as an object); `tasks` {text}; `memos` {text}; `runs` {workflow, workflow_version, model_pin, benchmark_version}; **[v1]** `cases` {question, answer, status}; `behaviours` {name, net, votes}; **[v3]** `workflow_meta` {status} with `status` one of `draft`, `tested`, `trusted`, `retired` (else rule `schema`, detail `status`), and the free parts `specification` and `benchmark`; the record id is the workflow id. Vote `category` is one of `answer_quality`, `reactions`, `character_behaviour`, `service`; `value` is 1 or -1.

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
| v2 | 2026-10-27 | the optional fields `kind`, `status`, `subject`, `updated` of a `memory` record; `kind` and `status` are checked when present (owner 2026-10-27: structured memory, D-78) | A-10 |
| v3 | 2026-10-27 | the table `workflow_meta`: status, specification and benchmark of a workflow, a new version per change (owner 2026-10-27: lifecycle in a new IF-302 table, D-89) | A-15 |
| v4 | 2026-10-29 | the table `reports`: the finished report of a review as a record for reference and benchmarks (owner 2026-10-29: results also in the database) | A-23 |
| v5 | 2026-10-29 | correction of v4: `reports` is versioned like every table (one version) and not deletable by the application; v4 said "not versioned", which the storage layer and the suite do not allow | A-24 |
