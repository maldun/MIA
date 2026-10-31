# Verification report: Pipeline runner (N-2.4.1)

**Goal:** G-V1 (iteration), supervised; node N-2.4.1 of `decomposition.yaml` (leaf, verified as a black box against the mocks of its neighbours)
**Branch:** goal/v1 @ 9a9e794 (code as of 99d185a; the two later commits change only `goal.md` and a hand-over)   **Parent line of work:** master @ 53c6766   **Plan baseline:** plan-baseline-it1 (protected material compared against master, as asked)
**Date:** 2026-10-31   **Reviewers:** – (human, open), Claude Opus 5.5 (AI, independent; never saw the implementation chat)

## Verdict (proposal)
**Not verified.** Nine of the eleven requirements in scope have passing component evidence. Two Must requirements block the verdict:
- REQ-RUN-003 fails on the real path. The chat answer is streamed, and with the ollama library of the image a streamed call to a closed port raises `httpx.ConnectError`, which `TurnClient` does not turn into the plain sentence (F1).
- REQ-RUN-013 is incomplete until T-08 is done (AC-9: the review entry).

The acceptance criteria of REQ-RUN-005 and REQ-RUN-009 also contain a measurement that no check covers (F3, F4). The owner decides those.

Commits reviewed (`Task: N-2.4.1`): T-01 `5414163`, `d416356` (both on master already, reviewed for completeness), T-02 `04a7c26`, T-03 `51b524b` + `2c53841`, T-04 `f80c552`, T-05 `fa41936`, T-07 `356f90b`, docs/plan `93733dd`, `c04b041`, `99d185a`. T-06 is deferred (REQ-RUN-007 is out of G-V1, D-125). T-08 is approved (A-35) but not started.

## Automated checks
| Check | Result |
|---|---|
| Stage log (CI) | No CI and no `stages.yaml` stage log. Everything was run locally in `localhost/mia:latest` (Python 3.12) on clean `git worktree` copies of goal/v1 (9a9e794) and master (53c6766) in the scratchpad. These are local runs, not CI evidence. |
| Python tests, all `tests/test_*.py` + 15 contract suites + 23 integration steps | goal/v1: 180 of 183 files green. master: 168 of 171. The three files red on goal/v1 are also red on master: `test_amendment_report` (no git in the image), `test_config` (option example), `test_harness`. `test_harness` has one failure more on goal/v1: `test_the_hard_checks_suite_matches_every_time` fails on case `n-planted-figure` (commit 543983a, N-2.4.2, "red today"). Not this node. `test_shutdown` passed on both, so the list of known master failures is out of date. |
| Node tests | `test_runner_budgets` 6, `test_run_workflow` 11, `test_model_turns` 6, `test_runner_model_server` 7, `test_runner_internet_by_command` 6, `test_runner_context_share` 4, `test_runner_interfaces` 7, `test_tool_calls` 11, `test_content_store` 11: all OK, none skipped |
| Contract suites of the node | IF-202 10 OK, IF-105 8 OK (none skipped, so they ran against the real provider as A-31 intends), IF-203 8 OK, IF-401 10 OK, IF-402 12 OK. IF-103: 6 of 12 skipped (real side only in stage 2; REQ-RUN-011 is out of G-V1). |
| JavaScript tests | 110 of 110 pass. None checks that a `confirm: true` command opens the dialog (see F5). |
| Statistical checks / benchmarks / flakiness | None in scope: REQ-RUN-006 and -007 are out of G-V1, and the node has no eval criterion in G-V1. Not run. No model server was used. |
| Protected material vs master | `git diff --stat master..HEAD -- tests/acceptance tests/helpers tests/smoke tests/integration benchmarks contracts eval/suites eval/baselines` lists 8 files. Each comes from the install commit of A-32 (`825e54a`), A-33 (`f63dc30`) or A-34 (`cca40c8`). The installed files are byte-identical to `specs/mia/contract-drafts/` and to `amendments/A-33`, `A-34`. A-31 (`9cfa556`) is already on master. There is one more change, `eval/suites/hard_checks/cases.jsonl` +1 (`543983a`): a case labelled by the owner (`Labelled-by:` trailer, moved from `eval-drafts/`). That is the agent-app labelling gate, not an amendment, and it belongs to N-2.4.2; the owner should confirm it. No skip or xfail was added to an acceptance test. |
| Traceability (`trace_check.py`) | For this node: ERROR, `test-spec.md` has 15 checks but no `## Scenarios` section (M39). WARN, REQ-RUN-008, -014, -015 have no `@mark.req` marker (their tests name them only in the module docstring). WARN for REQ-RUN-004 and -011, which are out of scope. Project-wide and older than this node: no `test-requirements.md` (M41), so no check of this node has a TR. Other findings concern other nodes. |
| Goals (`goal_check.py`) | 0 errors, 0 warnings. The REQ-RUN-007 row of `goal.md:67` starts with a space and cites D-120, while the scope decision is D-125 (cosmetic). |
| Test documentation (`test_doc_check.py`) | 0 errors in the T-02 to T-07 files. 12 errors in the T-01 files: `test_runner_budgets.py` (3), `test_run_workflow.py` (9). These are missing `Example:` lines and missing Given/When/Then. |
| SysML model (`tools/check_sysml_model.py`) | OK. `.sysml` files are unchanged by the node, so `check_sysml.sh` was not run. |
| Refactoring commits | None |
| Agent configuration (`.claude`, `CLAUDE.md`, `skills/`, `library/`) | Unchanged against master. No prompt or pipeline changed, so no version bump is due. |
| Static / security / dependencies | No lint, type, SAST or dependency tools are configured or installed (CLAUDE.md). Inspection only (below). No new dependency. |
| Usability (bad inputs) | Closed model port: tested live in the image without network (F1). Oversized input: refused with a sentence that names the step, the estimate and the limit. |
| Deployable artifact | Not built (node verify) |

## Verification matrix (requirements in scope of G-V1)
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-RUN-001 internet only on command | Test | `test_runner_internet_by_command.py` (6, one over all shipped skills); inspection: `web_app.run_chat_exchange` passes `started_by="message"`, and no other chat-message entry runs a skill | Pass (F7: the default is fail-open) | yes |
| REQ-RUN-002 switch after confirmation, for all, free memory | Test, Demonstration | `test_runner_model_server.py` (3) checks the `confirm` flags and that `set_profile` unloads with `keep_alive=0`. The page dialog (`templates/static/chat/app.js:227-237`) was inspected and is untested. Demonstration not done. | Pass with finding (F5) | yes |
| REQ-RUN-003 server unreachable in plain words | Test | `test_runner_model_server.py` (4) passes, but its fake raises `ConnectionError` for a stream, and the real ollama 0.6.3 raises `httpx.ConnectError`. Reproduced: `TurnClient(...).chat(stream=True)` on a closed port gives `ConnectError [Errno 111]`, and a Runner code node that streams ends with `converse: ConnectError: [Errno 111] Connection refused`. Non-streamed calls (pipelines) give the sentence. | **Fail** on the chat path (F1) | no: green only because of fake fidelity |
| REQ-RUN-005 inputs within 50 % of the context | Test | `test_runner_context_share.py` (4): an input estimated (4 characters a token) above half of `num_ctx` or 4096 is refused before the call. AC-22 (over the lookup suites, 100 % ≤ 4096 tokens by the server's count) was not measured. | Partly (F3) | yes |
| REQ-RUN-008 four budgets, names what is missing | Test | `test_runner_budgets.py` (6), `test_run_workflow.py` (token budget) | Pass | yes |
| REQ-RUN-009 chat before background | Test | `test_model_turns.py::test_a_waiting_chat_message_gets_the_next_turn` (order b1, chat, b2, b3). AC-19's "first text within 10 s with a review slice running" was not measured: a running call is never interrupted. | Partly (F4) | yes |
| REQ-RUN-010 one model at a time, queue | Test, inspection | `test_model_turns.py` (5): never two calls at once, FIFO, a stream holds its turn. Wiring in `web_app.py:127-128, 559` was inspected. The only other model client is `ollama_remote.py`, reached through `comm.client`. | Pass (note F10) | yes |
| REQ-RUN-012 only through IF-203, IF-402, IF-401 | Inspection, Test | `test_runner_interfaces.py` (1-5). The import allow-list contains `sandbox`. Script nodes run in the sandbox directly (`pipeline.py:465`), and the web checks call web functions directly. | Pass for tool nodes; gap for scripts and web checks (F6) | yes |
| REQ-RUN-013 no particular workflow | Inspection, Test | `test_runner_interfaces.py` (6, 7). Lookup and verify are pipelines. The review is not (`review_chat.run_review`), which is T-08. `core.keep_texts` names `"chat"`, and `core.py` belongs to the part `pipelineRunner` (`architecture.sysml:371`). | **Not verified** (T-08; F2) | – |
| REQ-RUN-014 realise IF-202 | Test | IF-202 contract suite, 10 tests against the real `WorkflowRuns`; `test_run_workflow.py` | Pass (F8: contract text behind the code) | yes |
| REQ-RUN-015 realise IF-105 | Test | IF-105 contract suite, 8 tests; `test_run_workflow.py` (3) | Pass | yes |

Out of scope (goal.md): REQ-RUN-004, -006, -007, -011. Count: 7 verified of 11 in scope, 3 partly (-005, -009, -012), 1 failed (-003); -013 not verified pending T-08.

## Test requirements (M41)
`specs/mia/test-requirements.md` does not exist, so no check of this node has a TR. This is project-wide and older than the node: a plan finding, not a code finding. One aspect still had to be judged by hand.

**Stand-in fidelity (fake versus real):** the fake ollama client of `test_runner_model_server.py:39-49` does not behave like ollama 0.6.3 for streams. This is the cause of F1.

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-RUN-003 for streamed calls | F1 | Phase 3 |
| specified, not done | REQ-RUN-013, the review entry | T-08 (A-35) open | Phase 3 (T-08) |
| specified, not done | AC-22 of REQ-RUN-005, the 10 s of AC-19 in REQ-RUN-009 | F3, F4 | owner decision |
| done, not specified | statuses `stopped`, `error`, `pin_unavailable` on `run`, and `unknown_workflow` for a workflow without a skill (IF-202 v0 lists only done, budget_exhausted, refused) | F8 | Phase 2 amendment of IF-202 |
| done, not specified | the keys `skill` and `pipeline` of a workflow document (D-112) | not in IF-203 | Phase 2 amendment of IF-203 (already named in D-113) |
| done, not specified | the 4-characters-a-token estimate, the default 4096 when a step sets no `num_ctx`, and the profile's `num_ctx` ignored (`pipeline.py:600-604`) | F3 | Phase 2 (state it in REQ-RUN-005) |
| done, not specified | `user="mia"` for runs not started through WorkflowRuns, so chat runs of every user go to IF-401 as `mia` (`pipeline.py:338`) | F9 | owner decision |
| done, not specified | a per-run `tools=` override of a door tool is ignored, because the door wins (`pipeline.py:498`) | F11 | Phase 2 note or Phase 3 |
| done, not specified | web_search through the door returns a list with `content`, while `tool.web_search@1` declares `{results:[{title,url,snippet}]}` | F12 | Phase 2 (library node schema) |

Human review: the specification side goes through `review-log.md`. No item of this node is marked `Code review: needed`.

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | RUN-001..003, 005, 008, 012..015 | tests above | partly | F1, T-08 |
| Performance efficiency | RUN-005, 009, 010 | component tests only | partly | the 10 s and the token count need measurement (F3, F4); RUN-006 and -007 are out |
| Compatibility | RUN-012, 014, 015 | contract suites IF-202, 105, 203, 401, 402 | pass | IF-103 real side out (RUN-011) |
| Interaction capability | RUN-002, 003 | flag test, sentence test | partly | F1, F5 |
| Reliability | RUN-008, 010 | budgets, turns | pass | F10 (an abandoned stream holds the turn until GC) |
| Security | RUN-001, 012 | internet-by-command test, door | partly | F6, F7 |
| Maintainability | RUN-013 | inspection | partly | F2, F13 |
| Flexibility | RUN-013 | two new entries on one runner | pass | – |
| Safety | – | – | not now | no safety requirement on this node |

## Open deferrals (M26)
None for N-2.4.1 in `deferred.md`. The out-of-scope rows of `goal.md` (RUN-004, -006, -007, -011) are scope decisions (D-118, D-119, D-125), not TD records.

## Review findings
| # | Finding | Severity | Needs | Proposal / destination |
|---|---|---|---|---|
| F1 | `pipeline_model.py:88-93`: `TurnClient._stream` maps only `ConnectionError`. With ollama 0.6.3 (the image) a streamed `chat` to a closed port raises `httpx.ConnectError`, so the chat, which streams (`Communicator.exchange` → `chat(stream=True)`), shows "MIA could not answer: converse: ConnectError: [Errno 111] …" instead of the owner's sentence. The fake of `tests/test_runner_model_server.py:47-48` hides this. | High | test | Phase 3: reopen T-03. First a red test whose fake raises `httpx.ConnectError` while a stream is read, as the library does. Then also map `httpx.ConnectError` (or `httpx.TransportError` on connect) in `_call` and `_stream`. Add a TR on stand-in fidelity for the fake ollama client. |
| F2 | REQ-RUN-013: the review is not a workflow of the library (T-08 not started). Also, `core.py:25-28` `keep_texts` names `"chat"`, and `architecture.sysml:371` lists `core.py` among the modules of `pipelineRunner`, so the name only moved inside the same part. | High (blocks the verdict) | decision + task | Do T-08 (A-35). Owner: either make "texts not kept" a property of the skill (for example a front-matter flag in `skills/chat.md`), or take `core.py` out of the runner part in the model. |
| F3 | REQ-RUN-005 / AC-22 asks for "100 % of inputs ≤ 4096 tokens over the lookup suites by the server's count". The code refuses by an estimate of 4 characters a token, which undercounts for numbers, code and German. The limit ignores the `num_ctx` of the model profile (`pipeline.py:601-602`). No measurement was made. | Medium | decision | Owner: either fix an eval or measurement criterion for AC-22 (set out like RUN-006 until `eval-spec.md` exists), or reword AC-22 to the component property that is tested. Also state the estimate and the source of `num_ctx` in the requirement. This is a requirement that only an eval criterion can decide, so it is reported as a gap and not run. |
| F4 | REQ-RUN-009 / AC-19 "first text within 10 s with a review slice running" is a timing measurement. The test checks only the order of the turns. | Medium | decision | Owner: either reduce AC-19 of RUN-009 to the order property and leave the 10 s to REQ-RUN-007 (out of G-V1), or set the timing part out of scope with RUN-007. |
| F5 | REQ-RUN-002: the confirmation exists only in the page (`app.js:228`). No test checks that the dialog opens and that cancel sends nothing. The server switches on any `/full!` that reaches it (another IF-101 client needs no confirmation). | Medium | test + decision | Phase 3: a JS test of `onSend` with a `confirm: true` command (cancel → nothing sent). Owner: is a page-only confirmation enough for "for all users"? |
| F6 | REQ-RUN-012: the runner imports `sandbox` and runs script nodes itself (`pipeline.py:33,465`), and `checks.build_web_checks` reaches the web outside IF-402, although `run_script` is an IF-402 tool. `test_runner_interfaces.py:51-52` allows `sandbox`. | Medium | decision / amendment | Owner: either route script nodes through `ToolCalls.run_script` (Phase 3) or state the exception in REQ-RUN-012 (Phase 2), so the allow-list follows a requirement. |
| F7 | `pipeline.py:338` `started_by="command"` is the default, so a new caller that forgets the argument may start an internet task from a message (fail-open). The implementer already noted this. | Low | test + decision | Phase 3 at the wiring: default `"message"` and pass `"command"` explicitly; add a test that every entry passes it. |
| F8 | IF-202 v0 does not list `stopped`, `error`, `pin_unavailable` on `run`, or `unknown_workflow` for a skill-less workflow. The code returns them (`run_workflow.py:19, 46, 104-106`). | Low | amendment | Phase 2: the IF-202 amendment announced in D-113. |
| F9 | Runs not started through WorkflowRuns go to IF-401 as user `mia` (chat runs of every account). IF-401 asks for the starting account. | Low | decision | Owner: pass the speaker's account from the chat entry, or accept `mia` for chat runs. |
| F10 | `ModelTurns`/`TurnClient`: a streamed answer that is neither read to the end nor closed keeps the turn until its generator is collected, and an interrupted `acquire` leaves its ticket in the queue. Either blocks all model calls. Neither is likely in today's code paths. Separately, two different models can stay resident (chat on `full`, skills on profile `light`); only the calls are serialised, and residency is left to Ollama. | Low | note | Notes for Phase 7 / backlog: watch `ollama ps` while a lookup runs on the full chat model. |
| F11 | `pipeline.py:498`: a run-level `tools=` override of a door tool is silently ignored. The harness passes fixture tools this way (`harness.py:395`). Today `tools/eval.py` builds a Core without the door, so there is no effect now. | Low | test | Phase 3: let the run-level override win, or reject it with an error; one test. |
| F12 | Through the door `web_search` returns `[{url,title,content}]`. The library node `tool.web_search@1` declares `{results:[{title,url,snippet}]}`, and `backend`/`failed` are dropped. No current consumer breaks (`research.top_urls` accepts both). | Low | amendment | Phase 2: align the node's output schema with IF-402, or adapt in the door. |
| F13 | The architecture lists neither `run_workflow.py` nor `tools/sync_workflows.py` under any part. `ModelTurns` is not in the model. `decomposition.yaml:166` says `tasks: 7`, but A-35 makes 8. | Low | amendment | Phase 2: add the modules to `pipelineRunner` `@Implementation`, and update `tasks` with the install of A-35. |
| F14 | `run_workflow.py:112`: the pin check accepts an empty held digest or an empty pinned digest (prefix match on `""`). | Low | test | Phase 3: refuse empty digests; one test. |
| F15 | Without a test, Core's privacy rule could be dropped: no test checks that `Core(...).runner.store_texts("chat")` is False. `test_content_store.py` now injects `keep_texts` itself, so removing `or keep_texts` in `core.py:45` would pass all tests. The behaviour itself is unchanged (a move), but the check is weaker. | Medium | test | Phase 3: one test on `Core`, with no `store_texts`, that chat texts are not stored. |
| F16 | Test documentation: `test_runner_budgets.py` (3) and `test_run_workflow.py` (9) fail `test_doc_check`. REQ-RUN-008, -014, -015 have no `@mark.req`. `test-spec.md` has no Scenarios section. | Low | test docs + plan | Phase 3 for the docstrings and markers. Phase 2 for the scenarios (and the project's `test-requirements.md`). |
| F17 | Test infrastructure: `tools/run_in_image.sh:10` mounts with `:Z` (private SELinux label). While another container relabelled the shared worktree, a run in place lost access to `/work` partway through (`Permission denied`), which made later test files look red. | Low | decision | Owner: use `:z` (shared label) for the checkout mount, or run each session on its own copy. |

## Accepted deviations
None proposed. The team decides F3, F4, F5, F6 and F9.

## Notes for Phase 7 (validation)
- How long a chat message waits behind a review slice (no call is interrupted). This is REQ-RUN-007's subject, now out of G-V1.
- Model residency when the chat is on `full` and a lookup runs on `light` (F10).
- Whether users see the confirmation of `/light!` and `/full!` as enough for a switch that affects everybody.

## Agent verification (agent-app additions)
**Reference host:** not used (no model server, no 26B). **Pins:** none (MIA has no `eval-spec.md`). **Runs:** none.

| Check | Result |
|---|---|
| eval/suites, eval/baselines vs master | One added case, `hard_checks/cases.jsonl` (`543983a`, labelled by the owner, N-2.4.2). Baselines unchanged. |
| Prompts, skills or pipelines changed by this node | none, so no version bump is due |
| Eval criteria decided on holdout | none in G-V1 for this node. No holdout or `split:holdout` case was run or opened. REQ-RUN-005's AC-22 needs a measurement (F3). |
| Red-team cases | not in scope of this node |
| Threat conformance | Tool nodes reach the web only through IF-402 (`door_tools`, trust label, `tool_call` event). Script nodes and web checks bypass the door (F6). Internet skills are refused for chat messages (REQ-RUN-001) and must not declare triggers. |
| Budgets (tokens, time, VRAM) | not measured (out of scope: RUN-006, -007) |
| Replay | not done (no model) |
| Proposed cases from Implement | none for this node |

## Evidence (commands)
```
git diff --stat master..HEAD -- tests/acceptance tests/helpers tests/smoke tests/integration benchmarks contracts eval/suites eval/baselines
for f in $(cd specs/mia/contract-drafts && find . -type f); do diff -q specs/mia/contract-drafts/$f $f; done   # no output
git worktree add --detach <scratch>/wt-goal HEAD; git worktree add --detach <scratch>/wt-master master
podman run --rm --user 0 -v <wt>:/work:Z -w /work localhost/mia:latest bash runall.sh   # every tests/test_*.py, contract suite, integration step
node --test "tests/js/*.test.mjs"                                                    # 110/110
python ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests
python3 -I ~/.claude/skills/dev-workflow/scripts/goal_check.py --spec-dir specs/mia
python3 ~/.claude/skills/dev-workflow/scripts/test_doc_check.py --tests-dir tests/<node test file>
python3 -I tools/check_sysml_model.py .
# F1 reproduction (image, --network none):
#   TurnClient(ollama.Client(host='http://127.0.0.1:9'), ModelTurns(), 'chat').chat(..., stream=True)  -> httpx.ConnectError
#   the same call without stream                                                                       -> ModelServerUnreachable("Can't reach my brain right now beep")
#   Runner code node streaming through it                                                              -> error "converse: ConnectError: [Errno 111] Connection refused"
```

## Re-verification (2026-10-31)

**Branch:** goal/v1 @ 594ba5d (code as of 2ee83db; 097fab5, 3bfbf2c, bff1029, 594ba5d change only specs)   **Compared with:** the first report (5078cfa, code 99d185a), master @ 53c6766   **Reviewer:** Claude Opus 5.5 (AI, independent, a second reviewer; never saw the implementation chat or the first review's chat)

Commits reviewed: `98ae7a2` (F1), `160bef6` (F15), `70a6f35` (N-2.4.2 F2: `tool_calls.build_tool_calls`, `web_app.py`), `2ee83db` (F12: `library/nodes/tool.web_search/2.json`), docs `be32ecf`, `097fab5`, `3bfbf2c` (FB-03, D-126), `bff1029`, `594ba5d` (D-127, N-4.2 only). Code changed since 9a9e794: `pipeline_model.py`, `tool_calls.py`, `web_app.py`, `library/nodes/tool.web_search/2.json`, and four test files; nothing else.

### Proposed verdict
**Not verified** (unchanged), now for one reason only: REQ-RUN-013 (Must, in scope of G-V1) has no evidence for its AC-9 review entry, because T-08 (A-35) is not started and D-126/FB-03 moved the question of "how a workflow is built" to the next iteration without taking REQ-RUN-013 (or its review part) out of G-V1. F1, the other blocker of the first report, is fixed and was confirmed on the real path.

Owner decisions that block "Verified" or "Verified with findings":
1. **REQ-RUN-013 / T-08:** do T-08 in G-V1, or take AC-9's review entry out of the scope of G-V1 (scope row in `goal.md`, with FB-03 as the destination), or accept it as a named deviation. Same decision for the `keep_texts` name of F2 (`core.py` is in the runner part).
2. **F3, F4:** reword AC-22 of REQ-RUN-005 and AC-19 of REQ-RUN-009 to what is tested, or set the measured parts out with REQ-RUN-006/-007.
3. **F5, F6, F9:** page-only confirmation, script nodes and web checks outside IF-402, chat runs logged as user `mia`.
With 1 decided (out of scope or accepted) and 2 decided, the node can be proposed as **Verified with findings** (the rest are Low findings and amendments).

### Per-finding state
| # | State | Evidence |
|---|---|---|
| F1 | **Fixed** | `pipeline_model.py:62-65,88-104`: `_unreachable` maps `ConnectionError` and `httpx.ConnectError` (by name) in `_call` and `_stream`. Test `tests/test_runner_model_server.py:87` `test_a_stream_of_the_real_library_to_a_closed_port_is_the_sentence` uses the real ollama 0.6.3 on port 9, plain and streamed. **Red on 9a9e794** with that test file (`httpx.ConnectError [Errno 111]`, 1 error of 8), green on HEAD (8 OK), both in the image with `--network none`. The test exercises the real library, not a fake, so it covers the actual failure. **Chat path checked end to end** (probe, not a repo test): `Communicator(port=9)` with `comm.client = TurnClient(..., "chat")`, `Core(skills, library).run("chat", started_by="message", functions={"converse": lambda t: comm.exchange(t)[1]})`: on 9a9e794 the run ends `error`, `'converse: ConnectError: [Errno 111] Connection refused'`; on HEAD it ends `error`, `"Can't reach my brain right now beep"` == `pipeline_model.UNREACHABLE`. Remaining limits: N1, N2 below. The TR on fake fidelity proposed in F1 is not written (no `test-requirements.md`, see F16). |
| F2 | **Waiting for owner** (+ T-08 open) | No commit touches T-08; `core.py:25-28` unchanged. D-126/FB-03 name T-08 but leave REQ-RUN-013 in scope (`goal.md` has no out row for it). |
| F3 | Waiting for owner | No decision recorded (D-120..D-127); `pipeline.py` unchanged. |
| F4 | Waiting for owner | as F3 |
| F5 | Open (test) + waiting for owner | No JS test of the `confirm: true` dialog added (`tests/js` 110 tests, unchanged); no decision. |
| F6 | Waiting for owner | `pipeline.py:33,465` and the allow-list in `test_runner_interfaces.py` unchanged. FB-03 lists REQ-RUN-012 as affected but decides nothing for G-V1. |
| F7 | Open | `pipeline.py:338` default still `started_by="command"`. |
| F8 | Open (amendment) | `contracts/IF-202-*.md` unchanged since the report. |
| F9 | Waiting for owner | `pipeline.py:338` `user="mia"` unchanged. |
| F10 | Open (note) | unchanged; see also N2 (a connect that never ends holds the turn). |
| F11 | Open | `pipeline.py:498` unchanged. |
| F12 | **Partly fixed; rest deferred by the owner (D-126, FB-03)** | `library/nodes/tool.web_search/2.json` declares input `{query}` and output `[{url,title,content}]` as IF-402 v2. Test `tests/test_library.py:131` red on 9a9e794 (1 error, `@2` missing), green on HEAD. But every shipped pipeline (7 versions of 4 research pipelines) still `use`s `tool.web_search@1`, so the declaration of the node the app actually runs through the door is still `{results:…}`. The owner moved the pipeline side to the next iteration (D-126). Acceptable as is, because output schemas of tool nodes are not checked at run time (`pipeline.py:586` checks model output only), but F12 is closed only when FB-03 is done. |
| F13 | Open (amendment) | `decomposition.yaml:166` still `tasks: 7`; `architecture.sysml` unchanged (`check_sysml_model.py` OK). |
| F14 | Open | `run_workflow.py:112` unchanged. |
| F15 | **Fixed** | `tests/test_content_store.py:139` `InTheCore`: `Core(...).runner.store_texts("chat")` is False, `("summarize")` True, and `store_texts=lambda n: True` wins. Mutation on HEAD in a scratch copy: removing `or keep_texts` from `core.py:45` makes the test fail (`(True, True) != (False, True)`, 1 failure of 12); restored, 12 OK. A test-only commit is right here (the code was not wrong). |
| F16 | Open | `test_doc_check`: `test_runner_budgets.py` 3, `test_run_workflow.py` 9 errors (unchanged); trace_check still warns REQ-RUN-008, -014, -015 without `@mark.req`; `test-spec.md` still has no `## Scenarios` (ERROR). The new tests of this round pass `test_doc_check` (their files' other errors are older tests). |
| F17 | Open, **reproduced** | My own parallel runs: two containers mounting the same probe folder with `:Z` → the first lost access (`bash: /probe/runall.sh: Permission denied`). Re-run with separate folders. `tools/run_in_image.sh:10` unchanged. |

### New findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| N1 | `chat_service.py:675` shows the run error as `"MIA could not answer: Can't reach my brain right now beep"`. AC-23 of REQ-RUN-003 says "the plain message (exact)". The runner's part is exact; the page adds a prefix. | Low | owner decision | Owner: accept the prefix (the runner's AC is met; the page is N-2.2's) or have the chat service pass `ModelServerUnreachable` through unprefixed, with a test at the chat-service level. |
| N2 | `pipeline_model.py:65` covers a refused connection only. A host that does not answer (remote `ollama_host`, packets dropped) gives `httpx.ConnectTimeout` (other name) or, because `ollama.Client` has `timeout=None` by default and `Communicator` sets none (`communicator.py:138`), no error at all: the chat waits forever and holds the model turn, so every background call waits too (cf. F10). Not covered by AC-23 ("fake server down"). | Low (Medium with a remote model host) | owner decision, then test | Owner: does "unreachable" in REQ-RUN-003 include a host that does not answer? If yes: a connect timeout on the clients and `ConnectTimeout` mapped too, one test each. |
| N3 | `web_app.py:591` (the app uses `build_tool_calls`) is not guarded by any test: `AppDoorTests` (`tests/test_tool_calls.py:260`) tests `build_tool_calls` alone. Reverting `web_app.py` to `ToolCalls(...)` would pass every test. Checked by a probe instead (app imported as `tests/test_review_wiring.py` does, `--network none`): `tool_calls.work_trust/retractions/work_lookup` are `None` on 9a9e794 and set on HEAD. | Low | test | Phase 3 (N-2.4.2): one assertion in `tests/test_review_wiring.py`-style wiring test that `w.tool_calls.work_lookup` etc. are set. |
| N4 | The new wiring is latent: the runner routes only `web_search` and `fetch_page` through the door (`web_app.py:596`, `door_tools`), and no shipped pipeline or app path calls `scholar_search`/`source_record` through `ToolCalls`. When one does, `_scholar_search` (`tool_calls.py:138`) makes one Crossref lookup per found work (rate limit 0.3 s each). | Info | – | Note for the N-2.4.2 owner and for budgets when a caller appears. |
| N5 | An unversioned `tool.web_search` now resolves to `@2` (log, F12 paragraph). Only `library_select` and `tests/test_search_command.py:35` resolve it unversioned; no skill or pipeline does, so no eval path changed and no version bump of a pipeline is due now. | Info | – | Keep in FB-03. |

No new finding on security: the changes add no tool, network path or write access; `_unreachable` matches by class name only to decide which message to show and re-raises everything else.

### Check results (re-run)
| Check | Result |
|---|---|
| Python tests, every `tests/test_*.py` + 17 contract suites + 24 integration steps, image `localhost/mia:latest`, `--network none`, clean scratch worktrees | goal/v1 @ 594ba5d: 183 files, 180 green. Failing tests: `test_amendment_report::FromGit.test_the_files_of_a_commit_are_shown_one_after_the_other`, `test_config::Example.test_every_option_the_code_reads_is_in_the_example`, `test_harness::ShippedSuites.test_every_shipped_suite_is_valid` (`rt_edit` has 2 cases, not 30), `test_harness::ShippedSuites.test_the_hard_checks_suite_matches_every_time` (case `n-planted-figure`, N-2.4.2, red by design until its fix). master @ 53c6766 (same runner): 171 files, 168 green; the same first three failing tests. The only test red on goal/v1 and green on master is `test_the_hard_checks_suite_matches_every_time` (N-2.4.2, owner-labelled case); no test of N-2.4.1 fails. `test_shutdown` passed on both. |
| Node tests | `test_runner_budgets` 6, `test_run_workflow` 11, `test_model_turns` 6, `test_runner_model_server` 8, `test_runner_internet_by_command` 6, `test_runner_context_share` 4, `test_runner_interfaces` 7, `test_tool_calls` 12, `test_content_store` 12, `test_library` 37: all OK |
| Contract suites of the node | IF-202 10, IF-105 8, IF-203 8, IF-401 10, IF-402 12 OK; IF-103 12 run, 6 skipped (real side, REQ-RUN-011 out) |
| JavaScript | `tests/js`: 110/110 (master 103/103). JS contract + integration `.mjs`: 27 tests, 12 pass, 14 skipped, 1 fail (`N-1/step_00`), identical on master: not this node. |
| Red before / green after | F1, F12 and N-2.4.2 F2 tests run against 9a9e794 (red) and HEAD (green); F15 by mutation (above). |
| Protected material vs master | `git diff --stat 53c6766..HEAD -- tests/acceptance tests/helpers tests/smoke tests/integration benchmarks contracts eval/suites eval/baselines`: 8 files, each only from the A-32 (`825e54a`), A-33 (`f63dc30`), A-34 (`cca40c8`) install commits, plus `eval/suites/hard_checks/cases.jsonl` +1 (`543983a`, `n-planted-figure`, `Labelled-by: Stefan Reiterer (owner)`). `specs/mia/contract-drafts/` byte-identical to the installed files. Nothing changed in these folders since the first report (5078cfa..HEAD: empty). |
| Eval material, prompts, pipelines | `eval/baselines` unchanged; no skill or pipeline changed; one new node version (`tool.web_search@2`, a new file, `@1` untouched). No eval, holdout, red-team or model run made. |
| `trace_check.py` (N-2.4.1 only) | ERROR `test-spec.md` without `## Scenarios` (F16); WARN no `@mark.req` for REQ-RUN-008, -014, -015 (F16) and -004, -011 (out of scope); WARN open deferrals TD-01..TD-04 not listed in this report: they belong to REQ-CLV-023, -024, REQ-WFM-032, -039 (other nodes), none to N-2.4.1. Project-wide: no `test-requirements.md`. |
| `test_doc_check.py` on the changed test files | `test_runner_model_server.py` 0, `test_tool_calls.py` 0; `test_content_store.py` 16 and `test_library.py` many errors, all in older tests (the new methods `InTheCore`, `test_the_web_search_node_declares_the_output_of_if_402` pass). |
| `goal_check.py` | 0 errors, 0 warnings (the space and the D-120 citation in `goal.md:67` are still there, cosmetic). |
| `check_sysml_model.py` | OK; no `.sysml` changed, `check_sysml.sh` not needed. |

### Not checked
- No model server, no eval, holdout or red-team run (not allowed for this review; the node has no eval criterion in G-V1).
- No real network: the F1 path was checked only for "connection refused"; N2 (a host that does not answer) was judged from the library source, not run.
- No browser: the page shows the chat error through `chat_service`; read in the code (N1), not seen.
- No CI and no `stages.yaml`: all results are local runs, not CI evidence.

### Evidence (commands)
```
git worktree add --detach <scratch>/n241-reverify-head 594ba5d; ... -master 53c6766; ... -pre 9a9e794
podman run --rm --network none --user 0 -v "$PWD:/work:Z" -w /work localhost/mia:latest python tests/test_runner_model_server.py   # pre (test file of 98ae7a2): errors=1 ConnectError; head: OK
podman run ... -v <probe>:/probe:Z ... python -I /probe/chat_path.py     # Communicator(port=9) + TurnClient + Core.run("chat"): pre 'converse: ConnectError…', head UNREACHABLE
sed -i 's/store_texts=store_texts or keep_texts,/store_texts=store_texts,/' core.py; python tests/test_content_store.py   # failures=1; restored: OK
podman run ... python -I /probe/door_wiring.py                            # app's tool_calls: pre work_trust/retractions/work_lookup None, head set
podman run ... bash /probe/runall.sh                                      # every tests/test_*.py, contract suite, integration step; per-test FAIL/ERROR lines
node --test "tests/js/*.test.mjs"
python ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests
python3 ~/.claude/skills/dev-workflow/scripts/test_doc_check.py --tests-dir tests/<changed file>
```
