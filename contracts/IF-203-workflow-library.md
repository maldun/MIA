# IF-203 – Workflow library, v0

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

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| a graph rule is broken | `ServiceError("invalid", rule=…)` | nothing stored |
| unknown id, version or kind | `not_found` | nothing changed |
| stale `expected_version` | `conflict` with `detail.current` | nothing changed |
| promotion without specification or benchmark | `not_promotable` with `detail` = the missing parts | status unchanged |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| estimate of a graph of 200 nodes | at most 1 s | proposal, set in Plan |

## Golden examples
1. Typical: save, edit, `diff` names the changed node, `restore` makes version 3 equal to version 1; status stays `draft`.
2. Failure: `set_status(id, "tested", …)` before a specification and a benchmark is `not_promotable`, `detail == ["specification", "benchmark"]`.
3. Edge: `estimate` of a graph with a session node counts its maximum cycles times the cost of one cycle.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 8 |
