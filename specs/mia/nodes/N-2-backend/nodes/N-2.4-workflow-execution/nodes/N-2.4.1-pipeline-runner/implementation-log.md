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

## T-02 One model at a time, chat before background (2026-10-31, done) – REQ-RUN-009, REQ-RUN-010

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-RUN-010 one model at a time, users served by the queue | `pipeline_model.ModelTurns`: one call at a time on the one model server, the waiting calls in the order they came; `TurnClient` puts an ollama client behind the turns (`chat`, `generate`; a streamed answer holds its turn until it is read to the end or closed; the holder may call again without waiting for itself; other methods pass through) | `tests/test_model_turns.py` (5 of 6) |
| REQ-RUN-009 chat before background | a waiting chat call gets the next turn before any waiting background call, so a background run yields the server between its calls | `tests/test_model_turns.py` (1 of 6: b1, chat, b2, b3) |

Wiring (owner's approval 2026-10-31: "arbiter + wiring now", a deviation from the file list of T-02): `web_app.py` makes one `ModelTurns`; the communicator's client becomes `TurnClient(…, "chat")` (the chat answer, the expression model of the editor, the model switch), the runner's `OllamaModel` gets `TurnClient(…, "background")` (every pipeline). `communicator.py` is not changed. The chat skill's pipeline has the single node `converse`, which talks through the communicator: chat answers take chat turns.

Decisions made while building:
- Every pipeline call is background, also a `/lookup` or `/search` typed in the chat: they are tasks and yield between their calls to a waiting chat message. The communicator's own background work (dreaming, summaries) takes chat turns, as it runs through the chat's client.
- A running call is never interrupted: a chat message waits at most for the background call that runs. Whether that keeps the first text within 10 s (AC-19) depends on the length of one background call (a review slice); measured in T-06 (stage 4).
- A stream takes its turn when it is first read (Ollama starts the request then), not when `chat(stream=True)` returns.

Local coder: `tests/test_model_turns.py` (task `run0910-tests`, 2 attempts, both failed on a syntax slip: an extra `)` on three lines); the last draft compared with the instruction by script: every statement there; fixed by hand, verdict `fixed`. Red before the change (no `ModelTurns`), green after.

Tests reported green (feedback, not verification): `tests/test_model_turns.py` (6); all `tests/test_*.py` in the image fail only as on master (`test_config`, `test_shutdown`, `test_harness`, `test_amendment_report`); all 15 contract suites and all integration steps.

Open for Phase 4: no live run with the real model server was made (the tests use a fake client); AC-19's 10 s with a review slice running is T-06.

## T-03 Switch the model, server unreachable (2026-10-31, done; REQ-RUN-011 out of the scope of G-V1, D-118) – REQ-RUN-002, REQ-RUN-003

Owner's answers (D-118): `/light!` and `/full!` ask for confirmation; the switch to the light model is the "free GPU memory on request"; REQ-RUN-011 (IF-103 only) is set out of G-V1 (the IF-103 suite cannot hand scripted replies to a real provider).

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-RUN-002 switch after confirmation, for all, memory freed | **changed:** `chat_service.COMMANDS` marks `/light!` and `/full!` `confirm: True` (the page asks before it sends them, `templates/static/chat/app.js`); `Communicator.set_profile` switches the one shared model (all users) and unloads the previous one (`generate(keep_alive=0)`), nothing when the model stays | `tests/test_runner_model_server.py` (3 of 6) |
| REQ-RUN-003 server unreachable in plain words | **new:** `TurnClient` turns the `ConnectionError` of the ollama library (also while a stream is read) into `ModelServerUnreachable` with the sentence `pipeline_model.UNREACHABLE`; the runner ends the run with exactly that sentence as its error (no node id, no type); the chat shows it as its error note (the status line says "Can't reach my brain right now." as before) | `tests/test_runner_model_server.py` (3 of 6) |

Files outside T-03's list: `chat_service.py` (two flags, owner's answer); `web_app.py` not touched.

Wording: the owner chose "Can't reach my brain right now beep" (D-120, 2026-10-31); pinned by `test_the_sentence_is_the_owners_wording` in `tests/test_runner_model_server.py` (red before the change, green after).

Live check (feedback): with the image on the host network, a client on a closed port gave the sentence; the running Ollama answered `list` through `TurnClient` (5 models). No model was loaded.

Local coder: `tests/test_runner_model_server.py` (task `run0203-tests`, 2 attempts, the second passed its check); compared with the instruction by script: identical, verdict `ok`. Red before the change (no `UNREACHABLE`), green after.

Tests reported green (feedback, not verification): `tests/test_runner_model_server.py` (6), `tests/test_model_turns.py`, `tests/test_runner_budgets.py`, `tests/test_run_workflow.py`, `tests/test_pipeline.py`, `tests/test_chat_backend.py`; all `tests/test_*.py` in the image fail only as on master; all contract suites and integration steps.

## T-04 Internet tasks only on command (2026-10-31, done) – REQ-RUN-001

Before the task the property held by construction only: a chat message runs the skill `chat` (one node, `converse`, no tools), internet skills start through commands (`/lookup`, `/search`, `/review`), and the `triggers` of the skills are parsed but used nowhere. Now it is enforced:

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-RUN-001 internet tasks only by a command | `pipeline.reaches_internet(skill)`: a web tool of `INTERNET_TOOLS` or `max_safety.reads_web`; `Runner.run(..., started_by=)`: a run that reaches the internet and was started by a `"message"` raises `PipelineError` before any step; `validate_pipeline` reports an internet skill that declares `triggers` (so `Core.check` at start and every run refuse it); `web_app.run_chat_exchange` passes `started_by="message"` | `tests/test_runner_internet_by_command.py` (6, one of them over all shipped skills: `research` reaches the internet, no internet skill has triggers) |

Decisions made while building:
- `started_by` defaults to `"command"`, so the command paths, the harness, `reproduce.py` and `run_workflow.py` stay as they are; only the one entry of chat messages says `"message"`. A safer default (`"message"`) would need every command path changed (outside the task); proposed for the wiring of T-07.
- `INTERNET_TOOLS` names the web and scholarly tools of N-2.4.2 (IF-402) besides the two the runner has today.

File outside T-04's list: `web_app.py` (one argument at the chat entry, the wiring the owner approved in T-02).

Local coder: `tests/test_runner_internet_by_command.py` (task `run01-tests`, 1 attempt, 53 s); compared with the instruction by script: identical, verdict `ok`. Red before the change (no `reaches_internet`), green after.

Tests reported green (feedback, not verification): `tests/test_runner_internet_by_command.py` (6), `tests/test_pipeline.py`; all `tests/test_*.py` in the image fail only as on master; all contract suites and integration steps.

## T-05 Context window share (2026-10-31, done; REQ-RUN-004 and REQ-RUN-006 out of the scope of G-V1, D-119) – REQ-RUN-005

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-RUN-005 every model input inside 50 % of the context window | `Runner._ask_model`: the input is estimated at 4 characters a token (as the budget does); over the limit the step fails before the call, not counted, with "the input is about N tokens, more than half of the context window (L tokens)" (the run error starts with the step id); the limit is half of `num_ctx` when the step's options set it, else `Runner(max_input_tokens=4096)` | `tests/test_runner_context_share.py` (4) |

Owner's answers (D-119): refuse, do not cut; REQ-RUN-004 (optional learning) and REQ-RUN-006 (fewer than 15 calls, a measurement) out of the scope of G-V1.

Checked against the shipped pipelines: the largest inputs by construction are review sections (`extensions/review/fulltext.py`, 6000 characters, about 1500 tokens) and the passages of a lookup (budget 6000 characters): inside the limit. The measurement over the lookup suites (AC-22: 100 % at most 4096 tokens by the server's count, `tokens_in` of the `model_call` events) is not made here.

Local coder: `tests/test_runner_context_share.py` (task `run05-tests`, 1 attempt, 38 s); compared with the instruction by script: identical, verdict `ok`. Red before the change (2 failures, 1 error), green after.

Tests reported green (feedback, not verification): `tests/test_runner_context_share.py` (4); all `tests/test_*.py` in the image fail only as on master; all contract suites and integration steps.

## T-06 First text in 10 seconds (2026-10-31, deferred) – REQ-RUN-007

Deferred by the owner (D-120): a measurement (median of 20 runs, AC-19) without an eval criterion and model pins, like REQ-RUN-006. It comes back with `eval-spec.md`. Whether REQ-RUN-007 leaves the scope of G-V1 is the owner's decision (scope table of `goal.md`).

## T-07 Interfaces only, no particular workflow (2026-10-31, done; the review entry split out as T-08, A-35) – REQ-RUN-012, REQ-RUN-013

Owner's answers (D-120, D-122): tools through IF-402 `ToolCalls`; events to IF-401 and the run log side by side; IF-402 gets `fetch_page` (A-34); the review as a pipeline is its own task (T-08, A-35); the networkx redesign waits for the next iteration (FB-02).

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-RUN-012 tools only through IF-402 | `Runner(tool_calls=, door_tools={tool: budget key})`: a tool node of the door goes to `ToolCalls.call({"id", "limits"}, tool, args)`, the limits are the budgets of the run; the runner's own count still ends the run first (`budget_spent`, `missing`), a `budget` error of the door becomes the same budget end; the app wires `web_search` and `fetch_page` through `ToolCalls` (`web_app.py`) | `tests/test_runner_interfaces.py` (1, 2, 3) |
| REQ-RUN-012 events only through IF-401 | `_RunEventsSink`: every event goes to the run log, the 14 types of IF-401 also through `RunEvents.emit` (user of the run, actor, plain); a door call adds a `tool_call` event with tool and trust; a run without a run log gets an id `r-<hex>` | `tests/test_runner_interfaces.py` (1, 3, 4) |
| REQ-RUN-012 the workflow only through IF-203 | `WorkflowRuns.run` reads `estimate` (IF-203) instead of `check_budget`, which IF-203 does not offer (found by the mock); `user` is passed to the run | `tests/test_runner_interfaces.py` (4) |
| REQ-RUN-012 no other import | `pipeline.py`, `run_workflow.py` import the standard library and `events`, `schema_check`, `sandbox`, `pipeline_model`, `pipeline` only | `tests/test_runner_interfaces.py` (5) |
| REQ-RUN-013 no workflow named | the privacy rule "the chat's texts are not kept" (LG3) moved from the runner to `core.keep_texts`; no text constant of the two modules is the name of a shipped skill | `tests/test_runner_interfaces.py` (6, 7); `tests/test_content_store.py` takes the rule from Core |

Decisions made while building:
- `run(..., user="mia")`: IF-401 needs a user; WorkflowRuns passes its user, the other paths are MIA's own.
- `fetch_page` in the real `ToolCalls` (`tool_calls.py`, N-2.4.2's file, provider side of A-34; test `test_a_fetched_page_is_web_text`); contract, mock, contract suite and test-spec row are drafts (A-34), installed by the owner.
- Scratch check (feedback): `research.escalate` and `research.decompose@1` on the fixture world give the same answers through the door as through the old tool map; IF-401 got 3 `tool_call` events, no order problems.

Files outside T-07's list: `core.py` (pass-through, `keep_texts`), `run_workflow.py` (T-01's module of this part), `tool_calls.py` (A-34 provider side), `web_app.py` (the wiring), `tests/test_content_store.py` (see below).

Open for Phase 4:
- `tests/test_content_store.py` changed: it pinned the privacy rule as a default of `Runner`; it now takes `core.keep_texts`, the rule Core gives its runner. The behaviour of the app is unchanged; check that this is a move, not a weakening.
- Still outside IF-402: script nodes run in the sandbox directly (`Runner._do_script`, `sandbox.Operation`), the web checks of `checks.build_web_checks` call the web functions directly, the library tools `library_select`/`library_describe` are Core's. AC-1 holds for tool nodes; whether these must move too is a question for Verify or the redesign (FB-02).
- `ToolCalls` keeps the calls per run id in memory for the life of the app (`_used`); a long-running app grows by one small dict a run.
- The stricter default `started_by="message"` (proposed in T-04) is not done: it changes every command path outside the runner.
- AC-9 "lookup, verify and review on the same runner": lookup (`research`) and verify (`verify_claim`) are pipelines; review is T-08.

Local coder: `tests/test_runner_interfaces.py` (task `run1213-tests`, 2 attempts, both failed only on my wrong check `--forbid 'class Runner'`, which matched `class RunnerInterfaceTests`); the draft compared with the instruction by script: two hex digests lengthened, fixed by hand, verdict `fixed`. The added test methods in `tests/test_tool_calls.py` and `tests/test_runner_model_server.py` are one method each, written by hand. Red before the change (5 errors, 1 failure), green after.

Tests reported green (feedback, not verification): `tests/test_runner_interfaces.py` (7), `tests/test_tool_calls.py` (11), `tests/test_content_store.py`, `tests/test_run_workflow.py`; all `tests/test_*.py` in the image fail only as on master (`test_amendment_report`, `test_config`, `test_harness`, `test_shutdown`); all contract suites and integration steps; A-34 on a scratch copy: `test_if_402_tool_calls.py` 12 tests, all suites as before.
