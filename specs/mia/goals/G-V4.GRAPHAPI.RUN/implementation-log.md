# Implementation log: G-V4.GRAPHAPI.RUN

Goal: G-V4.GRAPHAPI.RUN   Line of work: goal/v4.graphapi.run   Supervision: supervised

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 The loader and IF-301 v5 | done | `2379dc0a` | TC-GTB-048, 049, 050 (`tests/acceptance/test_graph_loader.py`; its TC-GTB-051 stays red for T-02); regression set: unit suite 2535 tests, 59 of 71 acceptance scripts OK, reds only the known two (decide_guard, judge_calibration), the RUN checks of T-02 and T-03 and the image tests of F-2; TC-IF-301-35 to 38 mock and real side (`tests/acceptance/contract/test_if_301_v5_load.py`); `tests/test_graph_loader.py` (5 unit tests) | `networkx==3.7` added to `requirements.txt` and installed into mia312 (approved in the plan); `load` in `graph_rule_set.py`; `graphRecords` doc in `architecture.sysml` names graph_rule_set.py instead of the planned graph_load.py (as the plan's Touches says) |
| T-02 The order and the rule set on the loaded graph | done | (this commit) | TC-GTB-051, 052 (0 differences against the oracle), 053 (`tests/acceptance/test_graph_loader.py`); TC-IF-301-39 both sides (`contract/test_if_301_v5_load.py`); kept green: TC-WFM-185, 186 (`test_run_graph_order.py`; its "the run reads the loaded graph" stays red for T-03), the IF-301 v1 to v4 suites; unit tests: 5 new in `tests/test_graph_loader.py`, `tests/test_graph_run_findings.py` (the find_cycle checks now ask the cycle rule), `tests/test_graph_rule_set.py` (a list as connection `id` is rule 3, A-189); regression set (2026-11-25): unit suite 2563 tests OK; 67 of 71 acceptance scripts OK, red only the known two (decide_guard, judge_calibration) and T-03's checks ("the run reads the loaded graph", `test_stored_graph_run.py` 15) | rules 1 to 4 on the stored form, rule 3 also for a connection without a non-empty text ID (A-189); adjacency, one writer, `stop_limit`, cycle (`networkx.find_cycle`) and unsupplied inputs on `load(graph)`, connections in their stored order; `order_of` a queue over the loaded graph (D-480); `graph_model.find_cycle` and the rule set's copied cycle finder removed |

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

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| F-1: TC-GTB-050's case "a second step d1" asserts only the node IDs `["d1"]`; a loader that lets the second `d1` overwrite the first's `data` and `position` passes it (networkx's `add_node` on an existing key updates its attributes), so TC-GTB-050 alone cannot show the defect "keeps a second d1" of TR-RUN-007. The v5 contract suite catches it. | T-01 | `tests/test_graph_loader.py::test_a_second_step_with_a_used_id_leaves_the_first_as_it_was`; TC-GTB-050 after A-188 (D-482) |
| F-2: the four browser tests `test_chat_views_browser.py`, `test_run_line_browser.py`, `test_speak_again_browser.py`, `test_task_files_browser.py`, and the acceptance scripts `test_skill_run_view_browser.py` and `test_skill_run_view_restart.py` (protected, unchanged) run the worktree's code in the image `localhost/mia:latest`, which was built before `networkx` was a dependency: `import networkx` in `graph_rule_set.py` fails there and the mock server does not start ("did not answer in 30 s"). An environment gap, not a code defect; on the host the unit suite is green apart from these (2535 tests, 2026-11-25). Owner's decision (2026-11-25, questionnaire): keep the top-level import; the owner rebuilds the image from `requirements.txt`; the six were red until then. Rebuilt 2026-11-25 by the agent on the owner's word (`podman build --pull=never --network=host --env PIP_DEFAULT_TIMEOUT=120 --env PIP_RETRIES=10 -f deploy/Containerfile -t localhost/mia:latest -t localhost/mia:pip-cache .`, image 9206eeb93719; two builds before failed on pip read timeouts); `localhost/mia:v0.2.1` keeps the release image, while `deploy/compose.yaml` defaults to `latest` | T-01 | the six tests themselves: all six green after the rebuild (2026-11-25) |
| F-3: moving the rules onto the loaded graph loses connections that `load` leaves out: a connection without a non-empty text ID was no longer reported (v4: e.g. `adjacency ["None"]`), and `GraphModel.save_graph` then raised `KeyError: 'id'` in `_scoped`; REQ-GTB-060 asked for the v4 answers "for every stored form" | T-02 | TC-GTB-053 and TC-IF-301-39 (A-189, D-483) |
| F-4: the third pass of `stop_limit` counted settings connections into steps that do not exist; on the loaded graph two `settings` connections into a missing `z` are rule 3 only (v4 also `stop_limit ["z"]`), inside REQ-GTB-060 as narrowed by A-189. Shown to the owner in the graph viewer of G-V4.VIEW (two throw-away servers, v4 and RUN rule set) | T-02 | `tests/test_graph_loader.py::test_settings_connections_into_a_missing_step_are_rule_three_only`; REQ-GTB-060 narrowed again (D-484) |
| F-5: networkx lists the edges of a loaded graph grouped by their start step, not in stored order; parts of adjacency, single_writer, stop_limit, unsupplied inputs and the readiness in `order_of` depend on the stored order | T-02 | three unit tests in `tests/test_graph_loader.py` (adjacency order, single_writer order, readiness by the last connection); the code sorts by `position` |

## Plan amendments
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

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|

## Decisions
- `networkx` is imported at the top of `graph_rule_set.py` (it is a dependency now); the mock imports it inside `load` only so the protected suite could import before T-01.

## Open questions for Phase 4
- A-189: the re-approval of REQ-GTB-060 and REQ-GTB-043 (changed) and the agreement of IF-301's consumers.
- The sentence of rule 3 ("a connection leads to or from a step that does not exist") also covers a connection without an ID now; a better sentence would change the oracle's answers for golden 27 and 31.
- F-2: `localhost/mia:latest` is now a branch build (9206eeb93719); the deployed stack should start with `MIA_IMAGE=localhost/mia:v0.2.1` until v0.3 is deployed.
