# Plan: G-V4.GRAPHAPI.RULES (one rule set for graphs, the same list everywhere, refusal before a run)

**Goal:** `specs/mia/goals/G-V4.GRAPHAPI.RULES/goal.md`   **Requirements:** `requirements.md` of this folder (28 new, 3 changed (count corrected from 27, Verify V-5); approved 2026-11-22; they move into N-3.2, N-2.3 and N-2.4.1 at the merge)   **Test spec:** `test-spec.md`, `test-requirements.md` of this folder (approved, D-422, D-424)   **Interface:** IF-301 v4 (`specs/mia/amendments/A-170/IF-301-graph-tables.md`, D-419)   **Status:** Approved by the owner (plan gate ticked 2026-11-22; written by the agent by delegation, D-423)

Line of work `goal/v4.graphapi.rules` (worktree `../MIA-goal-v4-rules`), merges into `goal/v4`; supervised. Four tasks as in the high-level spec, pure logic: no model step, no prompt, no eval suite, no new dependency, no new part (one new module `graph_rule_set.py` in N-3.2, D-417).

## Deployment and feedback (M51)
- Environment for the current-state deployment: none of its own: RULES has no user surface beyond the refusals the save and the run give; SMOKE-RULES-001 runs on the owner's host in Deploy (`python tests/smoke/smoke_rules.py`, writes nothing).
- Feedback slices: none: four tasks; the owner validated the behaviour on the prototype (round 04: FR-63, FR-64, AC-017, AC-018 met).
- Living prototype (M46): `specs/mia/goals/G-V4/prototype/status.md`; reuse map row R3 (adapt: `graph_rules_proto.py` becomes `graph_rule_set.py`; the save path and the runner ask it).
- Source of each fact (P26): `requirements.md` of this folder → the generated block of `specs/mia/architecture.sysml` (D-420); FR-63, FR-64 by hand in the model.

## Before the first task (the owner)
1. `bash tools/apply_amendment_a170.sh --do` (IF-301 v4 text, suite, mock, helper), commit "plan: A-170 installed".
2. `bash tools/apply_rules_red_tests.sh --do` (the four acceptance files, the smoke script), commit "test: RULES acceptance tests (red)", tag `plan-baseline-g-v4-rules`.
3. Tick the plan gate below. Then Implement starts in a fresh session on this branch.

## Interface fixed by the red tests
- `graph_rule_set.kinds()`, `rule_report(graph)`, `run_check(graph, given=None)` as IF-301 v4 says; the stub in the branch has the names only.
- `GraphModel.save_graph(graph) -> SaveResult(saved, version, named, rule, detail, rules)`: a new last field `rules` (default `None`), the rule report of a refusal for broken rules (ASM-8, REQ-WFM-163); `named` lists the parts of every item in order, repeats kept (REQ-WFM-150).
- `graph_model.check_graph(graph)`: the flat list of the parts of the workflow rule report (REQ-WFM-164).
- `GraphRunner.run(graph, nodes, inputs) -> RunResult(status, named, named_status, values)`: unchanged shape; a refusal of the run check gives `("refused", <parts of every item, repeats kept>, None, ...)` before any step (REQ-RUN-036, 037); the inputs of a Stage with a prepare function are passed as given (REQ-RUN-039); trust after (REQ-RUN-038).

## State at the red commit
Every RULES check fails by assertion against the stub (scratch install, 2026-11-22), except these, green from the start and to be kept green: TC-WFM-182 and TC-WFM-183 (CORE's V-3 and V-2, now stated), TC-RUN-038 (today's runner already refuses the cycle before trust), TC-GTB-045 (the document-form suites unchanged), the cycle and missing-start cases of TC-RUN-036 and TC-RUN-037, and the mock side of TC-IF-301-27 to 34. Each is shown able to fail by its defect of TR-RULES-008 in its task.

Regression set: after every task the unit suite (`discover -s tests`, about 8 minutes) and every acceptance script one by one (not in parallel in this worktree: `mia.log`) are green except the RULES checks of later tasks and the known reds `test_decide_guard.py`, `test_judge_calibration.py` (G-V3.REPORT F-3). In particular: the IF-301 v1 to v3 suites, `test_graph_run.py`, `test_graph_run_stages.py`, `test_graph_order.py`, `test_pipeline_graph.py`, `test_skill_binding.py`, the CORE checks (TC-WFM-164, 168 unchanged, prototype CP17), `tests/test_graph_rules.py`, `tests/test_graph_run_findings.py` (changed in T-03, below).

## Tasks
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 The rule set module | REQ-GTB-033 to 052 | TC-GTB-037 to 045, TC-GTB-047, TC-RUN-040; the real side of TC-IF-301-27 to 34 | red tests and A-170 installed |
| T-02 The save path on the rule set | REQ-WFM-162 to 165; REQ-WFM-150, 154, 155 (changed) | TC-WFM-179 to 184 | T-01 |
| T-03 The runner asks the run check | REQ-RUN-036 to 039 | TC-RUN-036 to 039 | T-01 |
| T-04 Every entry point, and the smoke check | HR-004, HR-006 (whole) | TC-GTB-046; SMOKE-RULES-001 on the branch | T-02, T-03 |

### T-01: The rule set module
- Implements: REQ-GTB-033 to REQ-GTB-052
- Tests to turn green: TC-GTB-037 to 045 (`tests/acceptance/test_rules_rule_set.py`), TC-GTB-047 and TC-RUN-040 (`test_rules_measures.py`), the real side of TC-IF-301-27 to 34 (`tests/acceptance/contract/test_if_301_v4_rule_set.py`)
- Touches: `graph_rule_set.py` (replaces the stub); new unit tests `tests/test_graph_rule_set.py`; `specs/mia/architecture.sysml` (`graph_rule_set.py` as a module of `persistence.graphRecords`, doc "planned" removed)
- Reuses: prototype `graph_rules_proto.py` (R3, adapt): `KINDS`, the eight rule functions, `check`, `missing_inputs`, `refusal`; adapted to the contract: the names `kinds`, `rule_report`, `run_check`, the field `rule` on every run-check item, malformed input as IF-301 v4 says (D-418 (2)), `given` counted by its keys
- Must not touch: protected material; `graph_rules.py` (document form, Q-6), `graph_tables.py`, `graph_model.py` (T-02), `graph_run.py` (T-03)
- Demonstrator after this task: `python -c "import graph_rule_set as r; print(r.rule_report(...))"` names every broken rule in order
- Done when: the listed tests green, the regression set holds; each of the defects of TR-RULES-008 makes its check fail (logged): two rules swapped (TC-GTB-037), the first broken rule only (TC-GTB-039), the cycle asked while rule 3 is broken (TC-GTB-042), inputs listed before rules or a kind that cannot run also listing its rules (TC-GTB-043; the first three do not reach the run check, T-01 finding, settled by delegation D-423)
- Notes: the module must not import `graph_model` (it would tie N-3.2 to N-2.3); `find_cycle` and the stop limit move with it or are copied (as the mock does).


### T-02: The save path on the rule set
- Implements: REQ-WFM-162, REQ-WFM-163, REQ-WFM-164, REQ-WFM-165; the changes of REQ-WFM-150, REQ-WFM-154, REQ-WFM-155
- Tests to turn green: TC-WFM-179 to 184 (`tests/acceptance/test_rules_save.py`)
- Touches: `graph_model.py` (`save_graph` asks `rule_report` instead of `check_graph`/`context_problems`; `SaveResult` gets `rules`; `check_graph` becomes the flat view; `context_problems` removed or a view); unit tests of the save path
- Must not touch: protected material; `graph_rule_set.py` (T-01, done), `graph_tables.py`, `storage.py`
- Depends on: T-01
- Demonstrator after this task: saving the AC-017 graph names both broken rules, in order, with their sentences
- Done when: the listed tests green, TC-WFM-164 and 168 unchanged and green, the three `check_graph(...) == []` tests green; the defect "save path left on check_graph" makes TC-WFM-179 and 180 fail (logged)

### T-03: The runner asks the run check
- Implements: REQ-RUN-036, REQ-RUN-037, REQ-RUN-038, REQ-RUN-039
- Tests to turn green: TC-RUN-036 to 039 (`tests/acceptance/test_rules_run.py`)
- Touches: `graph_run.py` (`GraphRunner.run`: the run check first, with the given values and the inputs of Stages with a prepare function; the old unknown-end and cycle check replaced); `tests/test_graph_run_findings.py`: the self-loop case now also names `adjacency` (REQ-GTB-045), the only expected value that changes (scratch run 2026-11-22)
- Must not touch: protected material; `graph_rule_set.py`, `graph_model.py`
- Depends on: T-01
- Demonstrator after this task: running `chat` without a value refuses before any step, naming `input.text`
- Done when: the listed tests green; TC-RUN-016, 017, 033, 034 unchanged and green; the defects "repeats removed", "trust before the run check", "prepare inputs not counted" each make their check fail (logged)

### T-04: Every entry point, and the smoke check
- Implements: HR-004 and HR-006 as a whole (the measures over T-01 to T-03)
- Tests to turn green: TC-GTB-046 (`test_rules_measures.py`), so every RULES acceptance file is green; `python tests/smoke/smoke_rules.py` passes on the branch
- Touches: only what TC-GTB-046 finds different between the entry points, else nothing
- Must not touch: protected material; MIA's own store
- Depends on: T-02, T-03
- Demonstrator after this task: the same list of broken rules from the rule report, the save, the check route stand-in and the run, five times
- Done when: every RULES check green, the regression set holds with no known red of RULES left

## At the merge (Commit phase, not a task)
- Move the 28 new requirements into the node files: REQ-GTB-033 to 052 into N-3.2, REQ-WFM-162 to 165 into N-2.3, REQ-RUN-036 to 039 into N-2.4.1; replace the texts of REQ-WFM-150, 154, 155 in N-2.3 with the approved changes; checks, scenarios and smoke rows into the node test specs; TR-RULES-001 to 009 into `specs/mia/test-requirements.md` through an owner-run script (groups as rows of its one `## Groups` table); regenerate the model.
- Fill the Witness column of AC-017 (TC-GTB-046, TC-WFM-180) and AC-018 (TC-RUN-036, TC-RUN-037, TC-GTB-044) in `specs/mia/goals/G-V4/accepted-cases.md`.
- Notes for other subgoals stay as written in `requirements.md`: CODE (known-tool check, Q-2), TRANSFER or MIGRATION (read-only listing of an unknown kind, Q-7), MIGRATION (document form, Q-6), EDIT (every entry point checks with the stored kind, finding 9).

## Plan gate
- [X] Plan package approved by maldun (owner): goal, high-level spec, requirements, checks and test code (red tests staged in `red-tests/`, A-170 staged). Date:
