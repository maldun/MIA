# IF-401 – Run event log, v0

Owner (provider): N-2.4.3 Run log   Consumers: N-2.4.1 Pipeline runner, N-2.4.2 Tools and sandbox   Decided by: N-2.4   Mock complexity: 2 (in-memory log)   Suite: `tests/acceptance/contract/test_if_401_run_events.py`

The log is the source of truth (FR-16): the runner and the tools write typed events of a run here, and the step-by-step account of an answer is a view of them. Draft v0 from `events.py` (`emit(type, payload, actor, parent, node, item, plain, round)`).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `emit(run_id, type, payload, user, actor=None, plain="")` | run id, event type, payload dict, starting account | `{"seq": n}` | `seq` counts from 1 per run; the event carries the run id and the user; payload keys named like `password`, `token`, `api_key`, `secret` are stored as `[removed]` |
| `events(run_id)` | | events in order of `seq` | |
| `account(run_id)` | | list of `{"seq","plain"}` | built only from events that have a `plain` text, never by a model |
| `check_order(run_id)` | | list of problems | empty if `seq` runs 1..n without gap or repeat and `run_start` is first |
| `compare(run_a, run_b)` | | `{"same": bool, "differences": [..]}` | compares the sequence of event types and the payloads, not time and run id |

Event types: `run_start`, `run_end`, `model_call`, `tool_call`, `check_run`, `query_issued`, `source_found`, `passage_extracted`, `claim_made`, `claim_verified`, `stop_decision`, `budget_spent`, `router_decision`, `error`.

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| type not in the list | `ServiceError("unknown_type")` | nothing written |
| unknown run | `ServiceError("unknown_run")` | nothing changed |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| an event | has run id, user, seq and type | FR-16, REQ-BE-058 |
| the accurate part of the account | comes from code events | FR-4 |

## Golden examples
1. Typical: `run_start`, `model_call`, `run_end` give seq 1, 2, 3 with the same run id and user; `account` lists the events that have a `plain` text.
2. Failure: `emit(..., "nonsense")` is `unknown_type`; a payload with `api_key` is stored with `[removed]`.
3. Edge: two runs with the same steps differ only in time and run id: `compare` says same; one extra `check_run` is a difference.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from events.py | – |
