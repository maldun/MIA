# IF-203 – Workflow library, v1

Owner (provider): N-2.3 Workflow management   Consumers: N-2.1 API and accounts, N-2.2 Chat agent, N-2.4 Workflow execution   Decided by: N-2   Mock complexity: 2 (in-memory library)   Suite: `tests/acceptance/contract/test_if_203_workflow_library.py`

The library of workflows (and context graphs) as versioned data, with lifecycle and estimate. N-2.1 uses it for IF-104, N-2.2 to select skills, N-2.4 to fetch the workflow it runs. Python calls; draft v0. The graph rules are those of IF-102.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `list_ids(kind)` | `workflows` or `context_graphs` | sorted ids | |
| `read(kind, id, version=None)` | | `{"id","version","author","time","status","doc"}` | |
| `save(kind, id, doc, author, expected_version=None)` | | `{"version"}` | a new immutable version; status `draft` |
| `history(kind, id)`, `diff(kind, id, a, b)`, `restore(kind, id, version, author)` | | as IF-104 | |
| `set_status(id, status, author)` | `draft`, `tested`, `trusted`, `retired` | `{"status"}` | promotion to `tested` or `trusted` needs a specification and a benchmark record (`attach(id, "specification" or "benchmark", doc)`) |
| `estimate(id, version=None)` | | `{"order", "critical_path", "seconds", "calls", "tokens"}` | from the graph and the costs of IF-202; `order` is a topological order of process nodes |
| **[v1]** `list_ids("transforms")`, `read("transforms", id, version=None)`, `save("transforms", id, doc, author, expected_version=None)`, `history("transforms", id)` | the kind `transforms` | as for the other kinds | `doc` is {id, version, inputs, outputs, code}: the versioned code of a transform (table `transforms`, IF-302 v9), `version` is the version of the code as the file states it; a missing, empty or null `code` is valid (a stub transform); every save is a new immutable version; `read` also gives `trust` and `lifecycle`; the first `save` of an id creates the meta record (table `transform_meta`, IF-302 v8) with trust `untrusted` and lifecycle `draft`, a later save leaves it as it is (REQ-WFM-092) |
| **[v1]** `get_meta(id)` | a transform id | `{"trust","lifecycle"}` and the optional `reason`, `evidence`, `baseline_allowed`, `shipped`, `changed_by` | |
| **[v1]** `get_trust(id)`, `get_lifecycle(id)` | a transform id | the value | the read side of the two setters |
| **[v1]** `set_trust(id, trust, author)` | `untrusted`, `trusted` | `{"trust"}` | who may set it (only the owner trusts, REQ-WFM-054) is a rule of the Workflow management, not of the library |
| **[v1]** `set_lifecycle(id, lifecycle, author, evidence=None)` | `draft`, `tested`, `retired` | `{"lifecycle"}` | `evidence` is stored when given; that `tested` needs it is a rule of the Workflow management (REQ-WFM-067) |
| **[v1]** `set_meta(id, author, **fields)` | trust, lifecycle, reason, evidence, baseline_allowed (boolean), shipped (boolean), changed_by | the meta record | one new version of the meta record; `changed_by` is set to the author |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a graph rule is broken | `ServiceError("invalid", rule=…)` | nothing stored |
| unknown id, version or kind | `not_found` | nothing changed |
| stale `expected_version` | `conflict` with `detail.current` | nothing changed |
| promotion without specification or benchmark | `not_promotable` with `detail` = the missing parts | status unchanged |
| **[v1]** a value outside the lists of trust or lifecycle, an optional meta field of the wrong type or an unknown field | `ServiceError("invalid", rule="schema", detail=<field>)` | the meta record is unchanged |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| estimate of a graph of 200 nodes | at most 1 s | proposal, set in Plan |

## Golden examples
1. Typical: save, edit, `diff` names the changed node, `restore` makes version 3 equal to version 1; status stays `draft`.
2. Failure: `set_status(id, "tested", …)` before a specification and a benchmark is `not_promotable`, `detail == ["specification", "benchmark"]`.
3. Edge: `estimate` of a graph with a session node counts its maximum cycles times the cost of one cycle.
4. **[v1]** Typical: a new transform is untrusted and draft; a second save is version 2 (TC-IF-203-05).
5. **[v1]** Typical: trusted and tested (evidence `run-1`) survive version 2; version 1 still reads its own document (TC-IF-203-06).
6. **[v1]** Failure: `fine` is refused for trust and for lifecycle with the field as detail, the statuses stay (TC-IF-203-07).
7. **[v1]** Edge: the optional meta fields are kept, a boolean field with a text is refused (TC-IF-203-08); unknown ids and stale versions are `not_found` and `conflict` (TC-IF-203-09).

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 8 |
| v1 | 2026-11-11 | the kind `transforms` and its meta record: operations `get_meta`, `get_trust`, `get_lifecycle`, `set_trust`, `set_lifecycle`, `set_meta`, golden examples 4 to 7 (suite TC-IF-203-05 to 09) | A-90, A-111 |
