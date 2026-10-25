# IF-105 – Evaluation access to the platform, v0

Owner (provider): N-2 Backend (realised by N-2.4.1 Pipeline runner, through IF-202)   Consumers: N-4 Evaluation and operation (the harness, N-4.1)   Decided by: N-0   Mock complexity: 2 (a fake runner that echoes its options)   Suite: `tests/acceptance/contract/test_if_105_evaluation_access.py`

Added in the plan of N-4 (finding F-4: the harness runs workflows with a pinned model, a seed and a temperature, and records versions; no top-level interface carried that). Python calls on the Backend; the harness never reaches into the runner. Draft v0 from `harness.py` and the reproducibility rules of `specs/number-gate` (REQ-EVAL-001..003).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `workflows()` | | list of `{"id", "versions": [..], "status"}` | what the library holds |
| `run_case(workflow, version, inputs, options)` | `options` = `{"model_pin", "seed", "temperature", "budget"}`; `model_pin`, `seed` and `temperature` are required | `{"run_id", "status", "outputs", "missing", "events", "cost", "options"}` | `status` as in IF-202; `cost` = `{"steps","seconds","calls","tokens"}`; the run is attributed to the user `harness` |
| `events(run_id)` | | the typed events of the run in order | read side of IF-401 |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| unknown workflow or version | `ServiceError("unknown_workflow")` | nothing run |
| `model_pin`, `seed` or `temperature` missing | `ServiceError("bad_options")` | nothing run |
| the pinned model is not the one the server holds (name or digest differs) | `ServiceError("pin_unavailable")` | nothing run, no silent fallback to another model |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| reproducibility | with a fake model, the same inputs and options give the same outputs and the same sequence of event types and payloads (not the run id or the time) | FR-9, REQ-BE-050 |
| options | recorded in the `run_start` event of the run | FR-16, REQ-OPS-004 |

## Golden examples
1. Typical: `run_case("lookup", 1, {"question": "q"}, {"model_pin": "MP-light", "seed": 7, "temperature": 0, "budget": {"calls": 15}})` is `done`; the `run_start` event carries the options; the user is `harness`.
2. Failure: options without `seed` are `bad_options`; the pin `MP-huge` is `pin_unavailable`.
3. Edge: two runs with the same inputs and options have equal outputs and equal event sequences; a budget below the estimate is `refused`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 9 |
