# IF-202 – Run a workflow, v0

Owner (provider): N-2.4 Workflow execution   Consumers: N-2.2 Chat agent, N-2.3 Workflow management   Decided by: N-2   Mock complexity: 3 (budgets, event stream, costs)   Suite: `tests/acceptance/contract/test_if_202_run_workflow.py`

Running a workflow version under a budget, and the measured costs the schedule is built from. Python calls; draft v0. The workflow is read from the library (IF-203) by the provider; the consumer names it.

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `run(workflow, version, inputs, budget, user, options=None)` | workflow id, version number, input dict, budget `{steps, seconds, calls, tokens}` (any key may be absent = unlimited), account, optional `options` = `{"model_pin", "seed", "temperature"}` | `{"run_id", "status", "outputs", "missing", "events", "cost"}` | status `done`, `budget_exhausted` or `refused`; `events` are typed run events (`run_start` first, `run_end` last, all with the run id and the user; `run_start` carries the options); `cost` = `{"steps","seconds","calls","tokens"}` actually spent (all 0 when refused) |
| `costs(workflow, node_id)` | | `{"seconds", "calls", "tokens"}` or `None` | measured median of recorded runs, from the run log |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| unknown workflow or version | `ServiceError("unknown_workflow")` | nothing run, no event |
| a budget is exceeded | status `budget_exhausted`, `missing` names the exceeded budgets | the partial `outputs` so far; `run_end` is written |
| the estimate exceeds the budget | status `refused`, no model call | `run_end` is written, `outputs` empty |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| events of one run | each has the run id and the starting user | FR-16 |
| a run that exceeds a budget | ends with what it has | NFR-7, REQ-BE-070 |

## Golden examples
1. Typical: `run("lookup", 1, {"question": "q"}, {"calls": 15}, "anna")` is `done` with outputs and events `run_start` … `run_end`.
2. Failure: workflow `drifting` was estimated at 2 calls but needs 4; with `budget {"calls": 3}` the run ends `budget_exhausted` with `missing == ["calls"]` and partial outputs.
3. Edge: `lookup` with `budget {"calls": 1}` (below its estimate of 3) is `refused`, nothing started; unknown workflow raises `unknown_workflow`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft; options and cost added in the plan of N-4 (F-4, amendment 9) | 8, 9 |
