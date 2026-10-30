# Implementation log: Pipeline runner (N-2.4.1)

## T-01 Realise IF-202 and IF-105 under budgets (2026-10-30, in progress) – REQ-RUN-008, REQ-RUN-014, REQ-RUN-015
Method (owner's rule: test the existing code first, change only what fails): `pipeline.Runner` already runs a skill's pipeline with budgets of steps, seconds and
tool calls, events and a run log; it did not count model calls or tokens, did not say which budget ended a run, did not return a cost, and nothing ran a
workflow of the library (IF-203) by id and version for a user.

Design gap found and decided (D-112, owner 2026-10-30, "reference + sync"): IF-203 holds graph documents without executable content, the runnable pipelines
are in `library.py`. A workflow document names its skill (`"skill"`) and may pin another pipeline (`"pipeline": "id@version"`); its process nodes carry the ids
of the pipeline's nodes. The storage accepts the extra keys unchanged (checked). A sync tool that writes one IF-203 workflow per skill is still to be built.

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-RUN-008 four budgets, ends with what it has, names what is missing | `Runner._ask_model` (calls before the call, tokens after it; a model without a count is estimated at 4 characters a token), `_guard` (steps counted only when a step runs, tokens), the final token check in `_run_state`; `RunResult.missing`, `RunResult.cost`; `OllamaModel.chat_with_usage` (`prompt_eval_count`, `eval_count`); `model_call` events carry `tokens_in`, `tokens_out` | `tests/test_runner_budgets.py` (6) |
| REQ-RUN-014 IF-202 | `run_workflow.WorkflowRuns.run`, `costs`, `node_costs` (the costs the IF-203 estimate is built from) | `tests/test_run_workflow.py` (6 of 9) |
| REQ-RUN-015 IF-105 | `WorkflowRuns.workflows`, `run_case`, `events`; pins `{id: {name, digest}}` checked against what the server holds | `tests/test_run_workflow.py` (3 of 9) |

Decisions made while building (small, inside the contracts):
- A run can end `stopped` or `error` (with `error`) besides the three statuses of IF-202 v0: a failure is a visible result (as REQ-WFM-036). The contract text should list them (next amendment of IF-202).
- A workflow that names no skill is `unknown_workflow` (it cannot run); a pin given to `run` (IF-202) is checked like in `run_case` (`pin_unavailable`), which IF-202 v0 does not list.
- `node_costs` keys the costs by node id over all workflows (the estimate of IF-203 takes `costs()` without a workflow); two workflows with a node of the same id share its measured cost.
- The estimate has no `steps`; a budget of steps is checked during the run only.
- `run_workflow.py` is a new module of this part (the plan names `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`): IF-202 and IF-105 are a thin facade over `Core` and the runner, not a part of the runner loop.

Tests reported green (feedback, not verification): the two new modules (15 tests); all `tests/test_*.py` in the image, failing as on master only: `test_config`, `test_harness` (suite `rt_edit` has 2 cases, wants 30), `test_shutdown`, `test_amendment_report` (no `git` in the image).

Not done yet:
- The real adapters of IF-202 and IF-105 in `tests/helpers/contract.py` (protected): amendment A-31 with the fixtures of the suites (`lookup` answers "42" with a node `judge`, `drifting` estimated at 2 calls and needing 4).
- The sync tool (one IF-203 workflow per skill, D-112), and the wiring of `WorkflowRuns` into the app (pins from `eval-spec.md`, `held` from `ollama list`).
- The events are written to the run log of `RunLog` only, not through IF-401 (`RunEvents`); REQ-RUN-012 (T-07) decides the wiring.
