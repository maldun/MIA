# Implementation log: Pipeline runner (N-2.4.1)

## T-01 Realise IF-202 and IF-105 under budgets (2026-10-30, done; contract adapters wait for A-31) – REQ-RUN-008, REQ-RUN-014, REQ-RUN-015
Method (owner's rule: test the existing code first, change only what fails): `pipeline.Runner` already runs a skill's pipeline with budgets of steps, seconds and
tool calls, events and a run log; it did not count model calls or tokens, did not say which budget ended a run, did not return a cost, and nothing ran a
workflow of the library (IF-203) by id and version for a user.

Design gap found and decided (D-112, owner 2026-10-30, "reference + sync"): IF-203 holds graph documents without executable content, the runnable pipelines
are in `library.py`. A workflow document names its skill (`"skill"`) and may pin another pipeline (`"pipeline": "id@version"`); its process nodes carry the ids
of the pipeline's nodes. The storage accepts the extra keys unchanged (checked). `run_workflow.sync_skills` and `tools/sync_workflows.py` (dry run by default, `--do` saves) write one IF-203 workflow per skill: the input, then each top step of the pipeline as a process node with its output as a data node; a new version only when the document changed; a workflow not made from a skill (the review draft) is kept. All 15 shipped skills sync without a problem (dry run on an empty storage).

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-RUN-008 four budgets, ends with what it has, names what is missing | `Runner._ask_model` (calls before the call, tokens after it; a model without a count is estimated at 4 characters a token), `_guard` (steps counted only when a step runs, tokens), the final token check in `_run_state`; `RunResult.missing`, `RunResult.cost`; `OllamaModel.chat_with_usage` (`prompt_eval_count`, `eval_count`); `model_call` events carry `tokens_in`, `tokens_out` | `tests/test_runner_budgets.py` (6) |
| REQ-RUN-014 IF-202 | `run_workflow.WorkflowRuns.run`, `costs`, `node_costs` (the costs the IF-203 estimate is built from; the calls between the start and the end of a top node count for it, also those inside a map), `sync_skills` | `tests/test_run_workflow.py` (8 of 11) |
| REQ-RUN-015 IF-105 | `WorkflowRuns.workflows`, `run_case`, `events`; pins `{id: {name, digest}}` checked against what the server holds | `tests/test_run_workflow.py` (3 of 11) |

Decisions made while building (small, inside the contracts):
- A run can end `stopped` or `error` (with `error`) besides the three statuses of IF-202 v0: a failure is a visible result (as REQ-WFM-036). The contract text should list them (next amendment of IF-202).
- A workflow that names no skill is `unknown_workflow` (it cannot run); a pin given to `run` (IF-202) is checked like in `run_case` (`pin_unavailable`), which IF-202 v0 does not list.
- `node_costs` keys the costs by node id over all workflows (the estimate of IF-203 takes `costs()` without a workflow); two workflows with a node of the same id share its measured cost.
- The estimate has no `steps`; a budget of steps is checked during the run only.
- `run_workflow.py` is a new module of this part (the plan names `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`): IF-202 and IF-105 are a thin facade over `Core` and the runner, not a part of the runner loop.

Contract adapters drafted as A-31 (D-113, `specs/mia/contract-drafts/tests/helpers/contract.py`): on a scratch copy the suites of IF-202 and IF-105 pass as `_real` (18 tests, none skipped), all other contract suites and the N-2.4 integration steps as before.

Tests reported green (feedback, not verification): the two new modules (17 tests); all `tests/test_*.py` in the image, failing as on master only: `test_config`, `test_harness` (suite `rt_edit` has 2 cases, wants 30), `test_shutdown`, `test_amendment_report` (no `git` in the image).

Not done yet:
- The wiring of `WorkflowRuns` into the app and the harness (pins from `eval-spec.md`, `held` from `ollama list`, the sync at start or by hand), and nothing calls it yet: the chat and the extensions still call `Core.run` directly.
- The review is not a pipeline (`implemented_by: review_chat.run_review`): it cannot run through IF-202 yet (REQ-RUN-013, T-07).
- The events are written to the run log of `RunLog` only, not through IF-401 (`RunEvents`); REQ-RUN-012 (T-07) decides the wiring.
