# Plan: G-V4.GRAPHAPI.RUN (the stored graph as one graph for the order, the rules and the run)

**Goal:** `specs/mia/goals/G-V4.GRAPHAPI.RUN/goal.md`   **Requirements:** `requirements.md` of this folder (REQ-GTB-053 to 060, REQ-WFM-166 to 168, REQ-RUN-040 to 045; changes of REQ-RUN-016 and REQ-WFM-110 to 115; REQ-RUN-030 to 035 taken in unchanged; reviewed by group 2026-11-24, D-478; REQ-WFM-167 and REQ-GTB-057 changed after the red tests, D-480, D-481)   **Test spec:** `test-spec.md`, `test-requirements.md` of this folder   **Interface:** IF-301 v5 (`specs/mia/amendments/A-187/IF-301-graph-tables.md`)   **Status:** Draft (written by the agent, 2026-11-25)

Line of work `goal/v4.graphapi.run` (worktree `.claude/worktrees/goal-v4-run`), merges into `goal/v4`; supervised. Four tasks (the five of the high-level spec, with the oracle already recorded in Plan step 4). One new dependency, approved: `networkx==3.7` (D-473 (2)), added to `requirements.txt` in T-01. No new part: the loader is a function in the existing module `graph_rule_set.py` of N-3.2 (D-475 (1)). The model-dependent part is T-04 only: the six skills run on the pinned model from their stored graph; their prompts, schemas and tools do not change.

## Deployment and feedback (M51)
- Environment for the current-state deployment: none of its own. RUN has no user surface; a skill without a stored graph runs as before (REQ-RUN-043). SMOKE-RUN-001 runs on the owner's host in Deploy (verify_claim saved into a throw-away store, run once on MP-light).
- Feedback slices: none; the stored-graph path is used by the real skills only after MIGRATION (D-473 (1)) and SWITCH (D-474).
- Living prototype (M46): `specs/mia/goals/G-V4/prototype/status.md`; the networkx spike (15 of 15 graphs keep every attribute; cycle check agrees with today's code on 500 random graphs) is the reference for the loader; its order rule is not (D-480).
- Source of each fact (P26): `requirements.md` of this folder; the generated block of `specs/mia/architecture.sysml` after the approved requirements are generated (`python tools/gen_node_requirements_model.py`).

## Before the first task (the owner)
1. Sign: REQ-WFM-167 and REQ-GTB-057 (changed text, back to Draft), the contract text of A-187 (changed by D-481), `high-level-spec.md`, `test-spec.md`, the open boxes of `goal.md` (date cell); then `python tools/gen_node_requirements_model.py`, `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh`.
2. `bash tools/apply_amendment_a187.sh --do` (IF-301 v5 text, suite, mock, generator, oracle, the three acceptance files and their helper), commit "plan: A-187 installed (red tests of RUN)".
3. Tag `plan-baseline-run`; tick the plan gate below. Then Implement starts in a fresh session on this branch.
4. Before T-04: tell the running sessions (`ListAgents`, "real run for about N hours, please hold model tests"): the Ollama server is shared and has no queue.

## Interface fixed by the red tests
- `graph_rule_set.load(graph) -> networkx.MultiDiGraph` as IF-301 v5 says (node key: step ID, attributes `data` and `position`; edge key: connection ID, attributes `data` and `position`; graph attributes: the header fields, `kind` = `workflow` when none; malformed items left out, a connection with `data` that is no object kept with empty `data`; copies; never an exception).
- `graph_model.order_of(graph)`: the stored form in, the list of step IDs out, as today; the walk is first-ready-first over the loaded graph (REQ-WFM-167, D-480).
- `Core(..., graph_store=<GraphModel>)`: a skill whose graph `<pipeline name>@<pipeline version>` is in the store runs from its newest version (read once, `read_graph(graph_id)`, the version from `graph_versions(graph_id)`); an empty store changes nothing (REQ-RUN-043). The run record has `graph` and `graph_version` only for such a run (REQ-RUN-044). A stored graph that the run check refuses ends the run `refused` with `error` containing the rule name, the graph ID and `version <n>`, before any model or tool call (REQ-RUN-045).
- `GraphRunner.run(graph, nodes, inputs)`: unchanged shape and answers; inside, types, roles and names come from the loaded graph (REQ-RUN-041).

## State at the red commit
Red by assertion or by `NotImplementedError` against the stub (scratch install, 2026-11-25): TC-GTB-048 to 051, TC-IF-301-35 to 38 (real side; the mock side needs networkx), TC-RUN-043, TC-RUN-044, TC-RUN-046, TC-RUN-047, TC-WFM-187, TC-WFM-115. Green from the start and to be kept green: TC-GTB-052, TC-WFM-185, TC-WFM-186, TC-RUN-041, TC-RUN-042, TC-RUN-045 (they guard today's behaviour against the oracle `f3e6243c`); each is shown able to fail by its defect of TR-RUN-007 in its task. TC-WFM-110 to 114 are eval runs (T-04), no test file.

Regression set: after every task the unit suite (`discover -s tests`) and every acceptance script one by one (not in parallel in this worktree: `mia.log`) are green except the RUN checks of later tasks and the known reds `test_decide_guard.py`, `test_judge_calibration.py` (G-V3.REPORT F-3). In particular: the IF-301 v1 to v4 suites, `test_graph_run.py`, `test_graph_run_stages.py`, `test_graph_order.py`, `test_pipeline_graph.py`, `test_skill_binding.py`, `test_skill_conversion.py`, `tests/test_graph_rules.py`, `tests/test_graph_run_findings.py`. `trace_check.py` shows 549 ERROR lines on `goal/v4`, none of them RUN's.

## Tasks
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 The loader and IF-301 v5 | REQ-GTB-053 to 058 | TC-GTB-048 to 050; TC-IF-301-35 to 38 (both sides) | red tests and A-187 installed |
| T-02 The order and the rule set on the loaded graph | REQ-GTB-059, 060; REQ-WFM-166, 167 | TC-GTB-051, 052; TC-WFM-185, 186 | T-01 |
| T-03 The runner and the stored-graph path | REQ-RUN-016, 040 to 045; REQ-WFM-168; REQ-WFM-115 (the check) | TC-RUN-041 to 047; TC-WFM-187; TC-WFM-115 | T-02 |
| T-04 The equivalence runs on the stored-graph path | REQ-WFM-110 to 114 | `eval_decide.py` PASS for TC-WFM-110 to 114; SMOKE-RUN-001 on the branch | T-03 |
| T-05 One common module for the thin code (F-7, D-486) | none (finding F-7) | the new F-7 test green inside the full unit suite; the pin in `tests/test_core_stored_graph.py` removed | T-03 |

### T-01: The loader and IF-301 v5
- Implements: REQ-GTB-053 to REQ-GTB-058
- Tests to turn green: TC-GTB-048 to 050 (`tests/acceptance/test_graph_loader.py`), the real side and the mock side of TC-IF-301-35 to 38 (`tests/acceptance/contract/test_if_301_v5_load.py`)
- Touches: `graph_rule_set.py` (`load` replaces the stub); `requirements.txt` (`networkx==3.7`, then `/home/maldun/prog/Python/venvs/mia312/bin/pip install -r requirements.txt -r requirements-db.txt`); new unit tests `tests/test_graph_loader.py`; `specs/mia/architecture.sysml` (the operation `load` of `graph_rule_set.py`)
- Reuses: the mock `tests/helpers/mocks/if_301_graph_tables_v5.py` is the reference for the shape (a few lines after the spike)
- Must not touch: protected material; `graph_tables.py`, `graph_model.py`, `graph_run.py`; the other rule functions (T-02)
- Demonstrator after this task: `python -c "import graph_rule_set as r; print(list(r.load(<the golden 33 graph>).edges(keys=True)))"` shows two edges `d1 → t1` keyed `e1`, `e2`
- Done when: the listed tests green, the regression set holds; each defect of TR-RUN-007 makes its check fail (logged): the loader keeps a second `d1`, drops a parallel connection, shares data instead of copying

### T-02: The order and the rule set on the loaded graph
- Implements: REQ-GTB-059, REQ-GTB-060, REQ-WFM-166, REQ-WFM-167, REQ-GTB-043 (changed, A-189)
- Tests to turn green: TC-GTB-051 (`test_graph_loader.py`, the search; the checklist of TR-RUN-008 is read by a person); TC-GTB-053 (`test_graph_loader.py`) and the real side of TC-IF-301-39 (`contract/test_if_301_v5_load.py`), both A-189; to keep green: TC-GTB-052, TC-WFM-185, TC-WFM-186 (`test_run_graph_order.py`), the IF-301 v4 suite
- Touches: `graph_rule_set.py` (the rules about adjacency, one writer, session setting and stop limit, cycle and unsupplied inputs read `load`; the copied `_find_cycle` and the adjacency maps go; the rules about step identity, kind of step, connection ends and duplicate connections stay on the stored form, REQ-GTB-059); `graph_model.py` (`order_of` and `topological_order` walk the loaded graph, first-ready-first; `find_cycle` goes once no production code uses it, checked with a search)
- Must not touch: protected material; `graph_run.py` (T-03); the answers of `rule_report` and `run_check` (the oracle)
- Depends on: T-01
- Demonstrator after this task: the order of `research` from the loaded graph equals the recorded order, step by step
- Done when: the listed tests green with 0 differences against the oracle; the defects "one rule answering from its old view with one changed branch" and "ties by ID instead of first-ready" each make their check fail (logged)
- Notes: the walk is a queue over the loaded graph, not networkx `lexicographical_topological_sort` (D-480); the risk row of the high-level spec that names that function is outdated by D-480

### T-03: The runner and the stored-graph path
- Implements: REQ-RUN-016 (changed), REQ-RUN-040 to 047 (046 and 047 by A-190), REQ-WFM-168, and the check of REQ-WFM-115
- Tests to turn green: TC-RUN-043 (`test_run_graph_order.py`), TC-RUN-044, 046, 047, 048, TC-WFM-187, TC-WFM-115 (`test_stored_graph_run.py`), TC-RUN-049 (`test_run_graph_order.py`, A-190); to keep green: TC-RUN-041, 042, 045, TC-RUN-016 to 019 and 030 to 039 unchanged
- Touches: `graph_run.py` (types, roles and names from the loaded graph; `_kinds`, the `reads` map and `_given` go; no list `graph["nodes"]` or `graph["edges"]` is scanned); `core.py` (`graph_store=`: look up `<pipeline>@<version>`, run it, write `graph` and `graph_version`, refuse a stored graph the run check refuses); `skill_converter.py` (`run_converted` takes the loaded graph instead of converting in memory when one is given); `run_log.py` only if the record needs the two fields in its shape; `graph_rule_set.py` (`order_of` moves in, A-190) and `graph_model.py` (keeps `order_of` as the same function); `run_explain.py` (`show` names graph and version, owner 2026-11-27); unit tests
- Must not touch: protected material; the old runner `pipeline.py` and the skills, pipelines and library nodes (a skill without a stored graph runs as before)
- Depends on: T-02
- Demonstrator after this task: `Core(..., graph_store=store).run("verify_claim", ...)` on scripted replies, then `python tools/run_explain.py show <run>` names `verify.single@1` and its version
- Done when: the listed tests green, the regression set holds; the defects "two steps run in a thread pool", "the stored graph ignored (the in-memory converted graph runs)", "version 1 run instead of the newest", "the run record without `graph_version`", "one prompt changed in the stored graph", "the answer taken from the last data step", "`graph_run.py` imports `graph_model`" each make their check fail (logged)

### T-04: The equivalence runs on the stored-graph path
- Implements: REQ-WFM-110 to REQ-WFM-114 (each keeps its threshold, `Eval criterion` line, relaxation and repeats of G-V2); HR-007
- Tests to turn green: TC-WFM-110 to 114 (eval runs, stage 4, no test file); SMOKE-RUN-001 on the branch (`python tests/smoke/smoke_run.py`, to be staged with the other red material before the gate: see Open points)
- Touches: `tools/eval.py` (a store option: the five model skills run from their graph saved into a throw-away store; the run header names the stored-graph path, the graph ID and its version); `ui/README.md` (the option); the run files under `eval/runs/` (never `eval/suites/`, `eval/baselines/`, red-team cases or holdout)
- Must not touch: protected material; suites, baselines, truth labels, repeats, seeds, thresholds, decision rules; `*.holdout` suites are never run or opened by an agent
- Depends on: T-03
- Budget (agent-app-plan): the five dev suites EV-research (20 cases), EV-plans (36), EV-verdicts (50), EV-computable (39), EV-extraction (51, the model skill extract_claims; extract_claims_rules runs the same 51 cases without a model in TC-WFM-115) with 3 repeats on MP-light, 196 cases and 588 case runs in all; at most one re-run with fresh seeds per criterion that FAILs, never more; the time of the first full run is measured and reported, not guessed here; one model loaded, no other session's model work in the meantime (`ListAgents` first)
- Commands: `python tools/eval.py run <suite> --pin MP-light --repeats 3 <store option>`, then `python ~/.claude/skills/agent-app/scripts/eval_decide.py --run <run> --baseline eval/baselines/<suite>__<variant>__baseline.jsonl --criterion "<Eval criterion line>" --select req:<ID>` for the five criteria of REQ-WFM-110 to 114; the secondary suite EV-research_compound is run and reported, not decided
- Demonstrator after this task: the five `eval_decide.py` verdicts side by side with the old-runner baselines of commit `1fb0c35`
- Done when: all five criteria PASS (a FAIL re-run once, only the re-run counts); the runs are logged with versions and the model pin; the dev runs are feedback, the decision for the record is Verify's
- Stop and report: a criterion looks unreachable on the pinned model within the budget; results flip between repeats more than `eval-spec.md` allows; an eval case or truth label seems wrong

### T-05: One common module for the thin code (F-7, D-486)
- Implements: no requirement; fixes finding F-7 of T-03 (owner's decision D-486: its own task in RUN's line)
- Test to turn green first: a new unit test that reproduces F-7 (once the package `MIA` is importable beside the plain modules, a tool step of a converted skill run fails with `ToolMissing`); it is red before the fix
- Touches: `toolbox.py` (the thin code reaches the same `common_operations` module the run registers its model and tools in, instead of importing whichever of `MIA.common_operations` and `common_operations` comes first); the new unit test; `tests/test_core_stored_graph.py` (the pin of one module that worked around F-7 goes)
- Must not touch: protected material; `graph_run.py`, `core.py`, `skill_converter.py` beyond what the fix needs; suites, baselines
- Depends on: T-03. Runs in this worktree before or after T-04, never during its model runs or its regression set
- Done when: the new test green, the full unit suite green without the pin, the regression set holds; taking the fix out makes the new test fail (logged)
- Stop and report: the fix changes the stored thin code text of shipped entries in a way that gives them new versions or touches their trust (`seed_shipped`, `changed_since_trusted`); that needs a decision first

## Open points before the gate
- ~~SMOKE-RUN-001 has no script yet~~: done, `tests/smoke/smoke_run.py` installed with A-187 (`a3d1d800`).
- The risk row of the high-level spec about `lexicographical_topological_sort` is outdated (D-480); correct it with the next change of that document.
- Amendment numbers and decisions: next free A-188, D-482 (VIEW uses D-500 and up, BUILDER D-520 to D-539).

## At the merge (Commit phase, not a task)
- Move the requirements into the node files: REQ-GTB-053 to 060 into N-3.2, REQ-WFM-166 to 168 into N-2.3, REQ-RUN-040 to 045 into N-2.4.1; replace the texts of REQ-RUN-016, REQ-GTB-043 (A-189) and REQ-WFM-110 to 115 with the approved changes; checks, scenarios and smoke rows into the node test specs; TR-RUN-001 to 012 into `specs/mia/test-requirements.md` through an owner-run script; regenerate the model.
- Merge request: eval changes per suite and the model pin (MP-light, digest from `eval-spec.md`); the baselines are not recorded new (HR-007: none needed).
- Notes for other subgoals stay as in `requirements.md`: MIGRATION stores the converted skills and switches each skill to its stored graph; SWITCH moves the nine user-interface skills and removes the old runner; CODE uses the run record's graph and version; VIEW, EDIT and CONTEXT consume IF-301 v5 (joint amendment A-187, `G-V4/goal.md`).

## Plan gate
- [x] Plan package approved by maldun (owner): goal, high-level spec, requirements, checks and test code (red tests staged in `specs/mia/amendments/A-187/tests/`, A-187 staged). Date: (Mal'Dun Finsterschreck, 2026-11-25)
