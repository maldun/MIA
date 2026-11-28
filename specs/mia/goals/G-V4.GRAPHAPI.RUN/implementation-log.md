# Implementation log: G-V4.GRAPHAPI.RUN

Goal: G-V4.GRAPHAPI.RUN   Line of work: goal/v4.graphapi.run   Supervision: supervised

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 The loader and IF-301 v5 | done | `2379dc0a` | TC-GTB-048, 049, 050 (`tests/acceptance/test_graph_loader.py`; its TC-GTB-051 stays red for T-02); regression set: unit suite 2535 tests, 59 of 71 acceptance scripts OK, reds only the known two (decide_guard, judge_calibration), the RUN checks of T-02 and T-03 and the image tests of F-2; TC-IF-301-35 to 38 mock and real side (`tests/acceptance/contract/test_if_301_v5_load.py`); `tests/test_graph_loader.py` (5 unit tests) | `networkx==3.7` added to `requirements.txt` and installed into mia312 (approved in the plan); `load` in `graph_rule_set.py`; `graphRecords` doc in `architecture.sysml` names graph_rule_set.py instead of the planned graph_load.py (as the plan's Touches says) |
| T-02 The order and the rule set on the loaded graph | done | `4f8a9c56` | TC-GTB-051, 052 (0 differences against the oracle), 053 (`tests/acceptance/test_graph_loader.py`); TC-IF-301-39 both sides (`contract/test_if_301_v5_load.py`); kept green: TC-WFM-185, 186 (`test_run_graph_order.py`; its "the run reads the loaded graph" stays red for T-03), the IF-301 v1 to v4 suites; unit tests: 5 new in `tests/test_graph_loader.py`, `tests/test_graph_run_findings.py` (the find_cycle checks now ask the cycle rule), `tests/test_graph_rule_set.py` (a list as connection `id` is rule 3, A-189); regression set (2026-11-25): unit suite 2563 tests OK; 67 of 71 acceptance scripts OK, red only the known two (decide_guard, judge_calibration) and T-03's checks ("the run reads the loaded graph", `test_stored_graph_run.py` 15) | rules 1 to 4 on the stored form, rule 3 also for a connection without a non-empty text ID (A-189); adjacency, one writer, `stop_limit`, cycle (`networkx.find_cycle`) and unsupplied inputs on `load(graph)`, connections in their stored order; `order_of` a queue over the loaded graph (D-480); `graph_model.find_cycle` and the rule set's copied cycle finder removed |
| T-03 The runner and the stored-graph path | done | `551c414b` | TC-RUN-043, 049 (`test_run_graph_order.py`), TC-RUN-044 to 048, TC-WFM-187, TC-WFM-115 (`test_stored_graph_run.py`); kept green: TC-RUN-041, 042, 045, TC-WFM-185, 186, `test_graph_run.py`, `test_graph_run_stages.py`, `test_graph_order.py`, `test_graph_loader.py`, the IF-301 v4 and v5 suites; unit tests: `tests/test_core_stored_graph.py` (5 new: F-6, a storage error other than not_found, `run_explain show`, the refusal text); regression set (2026-11-27): unit suite 2610 tests, red only F-6's unit test in the suite (F-7, fixed in the test), then OK on re-run (2610 tests, skipped 5, expected failures 2); 73 of 75 acceptance scripts OK, red only the known two (decide_guard, judge_calibration); against 39dd1e1f newly green: test_graph_loader, test_rules_rule_set, test_run_graph_order, test_stored_graph_run, and the VIEW scripts of the merge | `graph_run.py` reads types, roles and names from `graph_rule_set.load` (`_kinds`, the `reads` map, the edge scans gone; `_given` over the loaded graph); `order_of` moved into `graph_rule_set.py`, `graph_model.order_of` the same function (A-190, REQ-RUN-047); `Core(graph_store=)`: `<pipeline>@<version>` looked up with `graph_versions` (not_found = no stored graph), the newest read once, run check before any step (`refused`, naming rule, parts, graph and version), `graph` and `graph_version` in the record; `run_converted(graph=)` runs the stored graph, the conversion names only the answer step (REQ-RUN-046); `run_explain show` names graph and version (owner, 2026-11-27); demonstrator: `show` printed `graph verify.single@1, version 2` |
| T-04 The equivalence runs on the stored-graph path | done | `66a49249` (store option), `fcf37362` (runs and log) | TC-WFM-110 to 114: `eval_decide.py` PASS for all five on the first run (feedback on the dev split; the decision for the record is Verify's), see "Eval runs"; SMOKE-RUN-001 green on the branch (`tests/smoke/smoke_run.py`, 2026-11-28: saved `verify.single@1` v1, read once from the store, run `done` in 1.6 s, record names graph and version, store removed); unit tests: `tests/test_eval_cli_stored.py` (5 new: the flag, refused with `--pipeline`/`--converted`, the graph stored under its pipeline, a case on the stored path and the pin with the header, a fallback to the old runner is an error of the case; the last shown able to fail by removing the check); regression set after the merge of `goal/v4` (`56c4894f`, 2026-11-27): unit suite 2662 tests OK (skipped 5, expected failures 2); acceptance scripts all OK except the known two (decide_guard, judge_calibration), the five TRANSFER scripts OK; unit suite after T-04's code (2026-11-28): 2667 tests, one error, F-8 (environment) | `tools/eval.py run ... --stored`: the skill's graph converted and bound as `run_converted` does, saved by `GraphModel.save_graph` into a throw-away files store, every case through `Core.run` with `graph_store=` on the pin's model (`_PinnedChat`), header `stored_graph` (path, graph ID, version); `ui/README.md` names the option. Merge of `goal/v4` (TRANSFER, `f6ccde75`) before any model run, no conflict |
| T-05 One common module for the thin code (F-7, D-486) | done | `259a64b8` | new `tests/test_toolbox_one_module.py` (2: plain modules with the package importable, red before the fix with `ToolMissing`; the package as the app runs it); `test_api_events` then `test_core_stored_graph` in one process without the pin: OK (with the old `toolbox.py`: 2 failures); regression set (2026-11-28): unit suite 2669 tests OK (skipped 5, expected failures 2); acceptance scripts all OK except the known two (decide_guard, judge_calibration) | `Toolbox._code_namespace` hands its own `common_operations` into the namespace, the thin code is `ops = common_operations` (no import). A first version kept the import as a fallback and made every thin entry 4 lines longer: TC-WFM-118 (`tests/acceptance/test_common_operations.py`, at most 12 lines) went red in the regression set, so the fallback went (only `_code_namespace` runs thin code). Entries already seeded into a stored library keep their old text (`seed_shipped` adds nothing for a known ID); they run as before, as in production there is one module. The pin in `tests/test_core_stored_graph.py` is gone (with its two imports) |

## TR-RUN-007 for T-01 (each check shown able to fail)
| Defect (planted in `graph_rule_set.load`, then removed) | Caught by |
|---|---|
| the loader keeps a second `d1` (a later step overwrites the first's data and position) | TC-GTB-050 since A-188 (before: only the TC-IF-301 v5 suite and the new unit test, Findings F-1) |
| the loader drops a parallel connection (`has_edge` guard) | TC-GTB-048 |
| step data shared, not copied | TC-GTB-050 |

## TR-RUN-007 for T-02
| Defect (planted, then removed) | Caught by |
|---|---|
| one rule answering from its old view: `single_writer` with its own `writers` dict over the stored connections | TC-GTB-051 (the search) |
| one changed branch: adjacency counts only connections between two data steps | TC-GTB-052 (the oracle) |
| ties by ID instead of first-ready: the first ready steps sorted | TC-WFM-186 |

## TR-RUN-007 for T-03 (`python tools/plant_defects.py`, 2026-11-27, after A-190)
| Defect (planted, then removed) | Caught by |
|---|---|
| two steps run in a thread pool (a plain step submitted to a pool, not awaited) | TC-RUN-042 |
| the stored graph ignored (the in-memory converted graph runs) | TC-WFM-187 (planted option), `test_core_stored_graph` F-6 |
| version 1 run instead of the newest | TC-RUN-044, TC-RUN-047 |
| the run record without `graph_version` | TC-RUN-046, `test_core_stored_graph` (`show`) |
| one prompt changed in the stored graph (the first `literal.` step) | TC-WFM-187 |
| the answer taken from the last data step of the stored form (A-190) | TC-RUN-048 |
| `graph_run.py` imports `graph_model` (A-190) | TC-RUN-049 |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| F-1: TC-GTB-050's case "a second step d1" asserts only the node IDs `["d1"]`; a loader that lets the second `d1` overwrite the first's `data` and `position` passes it (networkx's `add_node` on an existing key updates its attributes), so TC-GTB-050 alone cannot show the defect "keeps a second d1" of TR-RUN-007. The v5 contract suite catches it. | T-01 | `tests/test_graph_loader.py::test_a_second_step_with_a_used_id_leaves_the_first_as_it_was`; TC-GTB-050 after A-188 (D-482) |
| F-2: the four browser tests `test_chat_views_browser.py`, `test_run_line_browser.py`, `test_speak_again_browser.py`, `test_task_files_browser.py`, and the acceptance scripts `test_skill_run_view_browser.py` and `test_skill_run_view_restart.py` (protected, unchanged) run the worktree's code in the image `localhost/mia:latest`, which was built before `networkx` was a dependency: `import networkx` in `graph_rule_set.py` fails there and the mock server does not start ("did not answer in 30 s"). An environment gap, not a code defect; on the host the unit suite is green apart from these (2535 tests, 2026-11-25). Owner's decision (2026-11-25, questionnaire): keep the top-level import; the owner rebuilds the image from `requirements.txt`; the six were red until then. Rebuilt 2026-11-25 by the agent on the owner's word (`podman build --pull=never --network=host --env PIP_DEFAULT_TIMEOUT=120 --env PIP_RETRIES=10 -f deploy/Containerfile -t localhost/mia:latest -t localhost/mia:pip-cache .`, image 9206eeb93719; two builds before failed on pip read timeouts); `localhost/mia:v0.2.1` keeps the release image, while `deploy/compose.yaml` defaults to `latest` | T-01 | the six tests themselves: all six green after the rebuild (2026-11-25) |
| F-3: moving the rules onto the loaded graph loses connections that `load` leaves out: a connection without a non-empty text ID was no longer reported (v4: e.g. `adjacency ["None"]`), and `GraphModel.save_graph` then raised `KeyError: 'id'` in `_scoped`; REQ-GTB-060 asked for the v4 answers "for every stored form" | T-02 | TC-GTB-053 and TC-IF-301-39 (A-189, D-483) |
| F-4: the third pass of `stop_limit` counted settings connections into steps that do not exist; on the loaded graph two `settings` connections into a missing `z` are rule 3 only (v4 also `stop_limit ["z"]`), inside REQ-GTB-060 as narrowed by A-189. Shown to the owner in the graph viewer of G-V4.VIEW (two throw-away servers, v4 and RUN rule set) | T-02 | `tests/test_graph_loader.py::test_settings_connections_into_a_missing_step_are_rule_three_only`; REQ-GTB-060 narrowed again (D-484) |
| F-5: networkx lists the edges of a loaded graph grouped by their start step, not in stored order; parts of adjacency, single_writer, stop_limit, unsupplied inputs and the readiness in `order_of` depend on the stored order | T-02 | three unit tests in `tests/test_graph_loader.py` (adjacency order, single_writer order, readiness by the last connection); the code sorts by `position` |
| F-6: from a stored graph, model calls inside a map or loop step took the model options of the skill file, not of the stored `descriptor.model` (research: the stored option in 1 of 5 calls, verify_computable 1 of 3); TC-WFM-187 sees only call 1 | T-03 | `tests/test_core_stored_graph.py::test_every_model_call_takes_the_options_of_the_stored_graph` (red, then fixed in `run_converted`) |
| F-7 (pre-existing, tests only): after a test that makes the package `MIA` importable (`checkout_copy.use()`, e.g. `test_api_events`), the thin code of the toolbox (`IMPORT_OPS`: `from MIA import common_operations` first) loads `MIA.common_operations`, a second module beside the plain `common_operations` in which `run_converted` registers model and tools; every tool step then fails with `ToolMissing`. Seen as F-6's test red only inside the unit suite. Not in production (`python -m MIA` has one module). The cause is in `toolbox.py` (outside T-03): the thin code could take the toolbox's own module instead of importing one | T-03 | `tests/test_core_stored_graph.py` pins one module while it runs (bisected to `test_api_events`); a fix of `IMPORT_OPS` is its own task T-05 (owner, D-486); fixed in T-05 (`259a64b8`), `tests/test_toolbox_one_module.py` |
| F-8 (environment, not T-04's code): `tests/test_delivery_on_stack.py` skips while Ollama is down; with Ollama started for T-04 it ran and its setUpClass failed: the image is built with `--network none`, and the pip layer for `requirements.txt` as merged from `goal/v4` (TRANSFER) is not in the podman cache ("Could not find a version that satisfies the requirement Flask==3.1.0"). The test is meant to fail rather than download (its own comment, M2, D-148). Green again after one build with network (`deploy/build.sh` or the build of F-2) | T-04 | the test itself (red 2026-11-28, unit suite 2667 tests, errors=1) |

## Plan amendments
### A-190: the answer step of a stored graph, and the graph run on its own (REQ-RUN-046, 047 new; TC-RUN-048, 049)
- Found in: T-03 (the stored form names no answer step; the owner's re-use of the runner, memory of 2026-11-27)
- Decision: the answer is the value of the data step the pipeline names as its result; `graph_run.py` and `graph_rule_set.py` import only the standard library, networkx and each other (re-use = module boundary only)
- Kind: amendment inside RUN's line (no frozen requirement, no interface)
- Status: installed by the owner (`e12d5d94`); REQ-RUN-046, 047 Draft, to approve
- Approved by: maldun, 2026-11-27 (D-485, questionnaire)
### A-189: rule 3 names a connection without a non-empty text ID (REQ-GTB-043 changed, REQ-GTB-060 narrowed; IF-301; TC-GTB-053, TC-IF-301-39)
- Found in: T-02 (F-3, F-4)
- Problem: see F-3 and F-4
- Decision: rule 3 also names such a connection; REQ-GTB-060 holds for stored forms whose connections have unique non-empty text IDs and existing ends
- Kind: joint amendment (IF-301 is frozen at G-V4; consumers VIEW, EDIT, CONTEXT and the run to agree)
- Status: approved by the owner's questionnaire answers, installed (`tools/apply_amendment_a189.sh --do`); open: REQ-GTB-060 back to Draft and approved again, REQ-GTB-043 (changed) approved, the consumers' agreement
- Approved by: maldun, 2026-11-25 (D-483, D-484)

### A-188: TC-GTB-050 checks the first of two steps `d1` (TC-GTB-050, TR-RUN-007)
- Found in: T-01 (F-1)
- Problem: the case "a second step d1" listed only the node IDs; a loader whose second `d1` overwrites the first passed it
- Decision: TC-GTB-050 also asserts `d1` with the first step's data and position 0; the goal's test spec follows; no code or requirement change
- Kind: amendment
- Status: approved, installed by the owner (`tools/apply_amendment_a188.sh --do`)
- Approved by: maldun, 2026-11-25 (D-482)

## Stop conditions hit
| Date | Task | Condition | Escalated to | Outcome |
|---|---|---|---|---|
| 2026-11-25 | T-01 | a finding needs a changed protected test (F-1) | owner | A-188 approved and installed (D-482) |
| 2026-11-25 | T-02 | REQ-GTB-057 and 059 contradict REQ-GTB-060 (F-3) | owner | A-189 approved and installed (D-483), joint amendment of IF-301 |
| 2026-11-25 | T-02 | REQ-GTB-060 as narrowed still contradicted by `stop_limit` (F-4) | owner | REQ-GTB-060 narrowed again, A-189 drafts corrected and installed again (D-484) |
| 2026-11-27 | T-03 | the demonstrator needs `run_explain.py`, outside the Touches | owner | one line in T-03 (questionnaire) |
| 2026-11-27 | T-03 | unspecified behaviour: which step holds the answer of a stored graph | owner | A-190, REQ-RUN-046 (D-485) |

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|
| A variant run (`Core.run(..., pipeline=...)`) stays on the old runner even when the variant's graph is stored (as on the converted path) | `core.py` `run` | none yet; REQ-RUN-042 speaks of "a skill"; ask in Verify |
| A stored graph with an `ask_user` step while `ask` is given, or whose pipeline cannot be converted, falls back to the old runner without saying so (as on the converted path) | `core.py` `_run_converted` | open; the stored graph is then ignored silently |
| A stored graph without the result step runs to `done` with no answer | `skill_converter.run_converted` | open point of A-190 (an error naming the step, if wanted) |

## Eval runs (dev split only)

Feedback for the implementer, not verification. All on `66a49249` (header `commit`), MP-light `gemma4:12b-it-qat` sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 (digest on the server compared with `eval-spec.md` before the first run, Ollama 0.40.5), seed 7, temperature 0, num_ctx 8192, 3 repeats, `python tools/eval.py run <suite> --pin MP-light --repeats 3 --variant stored --stored --results eval/runs` (extraction with `--skill extract_claims`). No prompt, schema, skill or pipeline changed, so no version bump. Every header names `stored_graph` = Core graph_store, the graph and version 1; 0 cases ended `error:` (no fallback to the old runner). Decided with `eval_decide.py --run <run> --baseline eval/baselines/<suite>__<variant>__baseline.jsonl --criterion "<Eval criterion line of requirements.md>"`.

| Run | Date | Task | Suite / split | Skill and pipeline versions | Pin (digest) | Repeats | Result (rate, interval) | vs baseline of `1fb0c35` | Cases changed | Seconds, calls |
|---|---|---|---|---|---|---|---|---|---|---|
| R-01 `eval/runs/research__stored__20261127-225417.jsonl` | 2026-11-27 | T-04 | EV-research / dev, 20 | research v3, `research.escalate@1` stored v1 | MP-light (sha256:38044be4…) | 3 | REQ-WFM-110 **PASS**: 19 of 20, 0.950 (0.764 to 0.991) >= 0.85, stability 1.00 | same 20 cases, majority right identical: 0 better, 0 worse | none | 356 s, 177 |
| R-02 `eval/runs/plans__stored__20261127-230013.jsonl` | 2026-11-27 | T-04 | EV-plans / dev, 36 | plan_question v1, `plan.free@1` stored v1 | as above | 3 | REQ-WFM-111 **PASS**: 23 of 36, 0.639 (0.476 to 0.775) >= 0.54, stability 1.00 | identical, 0 / 0 | none | 182 s, 108 |
| R-03 `eval/runs/verdicts__stored__20261127-230316.jsonl` | 2026-11-27 | T-04 | EV-verdicts / dev, 50 | verify_claim v1, `verify.single@1` stored v1 | as above | 3 | REQ-WFM-112 **PASS**: 47 of 50, 0.940 (0.838 to 0.979) >= 0.83, stability 1.00 | identical, 0 / 0 | none | 227 s, 150 |
| R-04 `eval/runs/computable__stored__20261127-230703.jsonl` | 2026-11-27 | T-04 | EV-computable / dev, 39 | verify_computable v1, `verify.computable@2` stored v1 | as above | 3 | REQ-WFM-113 **PASS**: 38 of 39, 0.974 (0.868 to 0.995) >= 0.87, stability 1.00 | identical, 0 / 0 | none | 950 s, 135 |
| R-05 `eval/runs/extraction__stored__20261127-232254.jsonl` | 2026-11-27 | T-04 | EV-extraction / dev, 51 | extract_claims v1, `extract.llm@1` stored v1 | as above | 3 | REQ-WFM-114 **PASS**: 34 of 51, 0.667 (0.530 to 0.780) >= 0.59, stability 1.00 | identical, 0 / 0 | none | 360 s, 153 |
| R-06 `eval/runs/research_compound__stored__20261127-232856.jsonl` | 2026-11-28 | T-04 | EV-research_compound / all 16 (reported, not decided) | research v3, `research.escalate@1` stored v1 | as above | 3 | harness report: answer right 36 of 45 runs, "unknown" where nothing is to be found 3 of 3, quotes not in their page 0 of 48, refused although answerable 9 of 45 | not compared | – | 370 s, 186 |

### Notes on R-01 to R-06
- Time of the first full run (measured, plan T-04): the five decided suites 36 min (2075 s of case time), research_compound 6 min; the old-runner baselines of `1fb0c35` summed to about 138 min.
- vs baseline: `tools/eval.py compare` refuses the pairs (the suites' `cases.jsonl` changed after `1fb0c35`: the `split:dev` tags), and `eval_decide.py` finds no `split:dev` case in the old baseline files, so the threshold rule decided alone (as the criterion lines say). The side by side was counted per case (majority of `right` over the three repeats, harness metrics): the same case IDs in both, no case differs, for all 196.
- Deviation from the plan's command: the plan names `--select req:<ID>`; no case of these suites carries a `req:` tag, so it selected nothing (`no case selected`, a FAIL that is no result). The criterion lines say `select=` (all cases), and G-V2 decided the same criteria without `--select`; decided that way. Repeats, seeds, thresholds and rules unchanged; no re-run was needed.
- Transcripts: no case changed against the baseline, so none read for changes; the wrong cases are the same as the old runner's.
- Other sessions were told before the first run (EDIT, the G-V4 line session) and after; Ollama started on the owner's word (questionnaire 2026-11-27) and stopped again afterwards.

## Proposed eval cases (for labelling)
None: no new bad output (every wrong case is wrong in the baseline too).

## Decisions
- T-04: `--stored` converts with the skill's own budget seconds, as `run_converted` does (`pipeline_graph.convert` writes them as `max_seconds` of loops and sessions: research 600, plan_question 120, verify_claim 300, verify_computable 240, extract_claims 120), so the stored graph is the graph the in-memory path ran in G-V2; the test helper `converted_skills` (TR-RULES-004) uses 300 s for every skill, which is its own matter.
- T-04: the store option lives in `tools/eval.py` only (a `Harness` subclass), as the plan's Touches say; `harness.py` is unchanged.
- `networkx` is imported at the top of `graph_rule_set.py` (it is a dependency now); the mock imports it inside `load` only so the protected suite could import before T-01.

## Open questions for Phase 4
- T-05: `tests/plain_modules.py` (F-3 of G-V3.REPORT) still hides the package for four converted-skill test modules; with F-7 fixed it may no longer be needed (not in T-05's Touches, left as it is).
- T-04: the plan's command `--select req:<ID>` fits no case of the five suites; the criteria were decided by their lines (`select=`, all dev cases), see "Eval runs". Correct the command in `plan.md` / CLAUDE.md template if Verify agrees.
- T-04: the old baselines of `1fb0c35` have no `split:dev` tags, so no paired check against them is possible with the tools; the per-case count (0 differences in 196 cases) was done by a short script, not by `eval_decide.py`.
- T-04: which graph MIGRATION will store for a skill is not decided here; `--stored` stores the one the in-memory graph path runs today (see Decisions).
- F-8: rebuild the image with network once, then `test_delivery_on_stack.py` again.
- T-03: REQ-RUN-046 and 047 (A-190) to approve; the three rows under "Unspecified behavior".
- T-03: the refusal of REQ-RUN-045 runs `run_check` in `Core` with the run's inputs as given (the converted stages have no `prepare`), so it answers as GraphRunner's own check; GraphRunner keeps its check for every other caller.
- A-189: the re-approval of REQ-GTB-060 and REQ-GTB-043 (changed) and the agreement of IF-301's consumers.
- The sentence of rule 3 ("a connection leads to or from a step that does not exist") also covers a connection without an ID now; a better sentence would change the oracle's answers for golden 27 and 31.
- F-2: `localhost/mia:latest` is now a branch build (9206eeb93719); the deployed stack should start with `MIA_IMAGE=localhost/mia:v0.2.1` until v0.3 is deployed.
