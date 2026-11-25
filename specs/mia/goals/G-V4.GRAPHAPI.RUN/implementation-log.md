# Implementation log: G-V4.GRAPHAPI.RUN

Goal: G-V4.GRAPHAPI.RUN   Line of work: goal/v4.graphapi.run   Supervision: supervised

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 The loader and IF-301 v5 | done | (this commit) | TC-GTB-048, 049, 050 (`tests/acceptance/test_graph_loader.py`; its TC-GTB-051 stays red for T-02); regression set: unit suite 2535 tests, 59 of 71 acceptance scripts OK, reds only the known two (decide_guard, judge_calibration), the RUN checks of T-02 and T-03 and the image tests of F-2; TC-IF-301-35 to 38 mock and real side (`tests/acceptance/contract/test_if_301_v5_load.py`); `tests/test_graph_loader.py` (5 unit tests) | `networkx==3.7` added to `requirements.txt` and installed into mia312 (approved in the plan); `load` in `graph_rule_set.py`; `graphRecords` doc in `architecture.sysml` names graph_rule_set.py instead of the planned graph_load.py (as the plan's Touches says) |

## TR-RUN-007 for T-01 (each check shown able to fail)
| Defect (planted in `graph_rule_set.load`, then removed) | Caught by |
|---|---|
| the loader keeps a second `d1` (a later step overwrites the first's data and position) | TC-GTB-050 since A-188 (before: only the TC-IF-301 v5 suite and the new unit test, Findings F-1) |
| the loader drops a parallel connection (`has_edge` guard) | TC-GTB-048 |
| step data shared, not copied | TC-GTB-050 |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| F-1: TC-GTB-050's case "a second step d1" asserts only the node IDs `["d1"]`; a loader that lets the second `d1` overwrite the first's `data` and `position` passes it (networkx's `add_node` on an existing key updates its attributes), so TC-GTB-050 alone cannot show the defect "keeps a second d1" of TR-RUN-007. The v5 contract suite catches it. | T-01 | `tests/test_graph_loader.py::test_a_second_step_with_a_used_id_leaves_the_first_as_it_was`; TC-GTB-050 after A-188 (D-482) |
| F-2: the four browser tests `test_chat_views_browser.py`, `test_run_line_browser.py`, `test_speak_again_browser.py`, `test_task_files_browser.py`, and the acceptance scripts `test_skill_run_view_browser.py` and `test_skill_run_view_restart.py` (protected, unchanged) run the worktree's code in the image `localhost/mia:latest`, which was built before `networkx` was a dependency: `import networkx` in `graph_rule_set.py` fails there and the mock server does not start ("did not answer in 30 s"). An environment gap, not a code defect; on the host the unit suite is green apart from these (2535 tests, 2026-11-25). Owner's decision (2026-11-25, questionnaire): keep the top-level import; the owner rebuilds the image from `requirements.txt`; the six were red until then. Rebuilt 2026-11-25 by the agent on the owner's word (`podman build --pull=never --network=host --env PIP_DEFAULT_TIMEOUT=120 --env PIP_RETRIES=10 -f deploy/Containerfile -t localhost/mia:latest -t localhost/mia:pip-cache .`, image 9206eeb93719; two builds before failed on pip read timeouts); `localhost/mia:v0.2.1` keeps the release image, while `deploy/compose.yaml` defaults to `latest` | T-01 | the six tests themselves: all six green after the rebuild (2026-11-25) |

## Plan amendments
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

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|

## Decisions
- `networkx` is imported at the top of `graph_rule_set.py` (it is a dependency now); the mock imports it inside `load` only so the protected suite could import before T-01.

## Open questions for Phase 4
- F-2: `localhost/mia:latest` is now a branch build (9206eeb93719); the deployed stack should start with `MIA_IMAGE=localhost/mia:v0.2.1` until v0.3 is deployed.
