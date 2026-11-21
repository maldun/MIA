# Plan: G-V4.GRAPHSTORE.CORE (one stored truth, graph-scoped steps, atomic saves, both graph kinds)

**Goal:** `specs/mia/goals/G-V4.GRAPHSTORE.CORE/goal.md`   **Requirements:** `requirements.md` of this folder (22 requirements, 2 assumptions; they move into N-3.2 and N-2.3 at the merge, D-408)   **Test spec:** `test-spec.md`, `test-requirements.md` of this folder   **Interface:** IF-301 v3 (`contracts/IF-301-graph-tables.md`, A-167 installed)   **Status:** Approved (owner, 2026-11-21: task cut and frame accepted in the chat questionnaire)

Line of work `goal/v4`; supervised. Five small tasks, pure logic on the Storage layer: no model step, no prompt, no eval suite, no new dependency, no new part (the nodes N-3.1, N-3.2 and N-2.3 stay, high-level spec section 5).

## Deployment and feedback (M51)
- Environment for the current-state deployment: none of its own for CORE: the store has no user surface; what a person can see of it is the viewer of the living prototype (`prototype/g-v4`), which already runs on the same rules. The smoke check SMOKE-CORE-001 runs on the owner's host in Deploy.
- Deploy command: none for CORE alone (the G-V4 release); SMOKE-CORE-001: `python tests/smoke/smoke_core_graphs.py` (see its docstring for the server URL).
- Feedback slices: none: a short goal of five tasks; the owner validated the behaviour on the prototype (round 03: FR-57, FR-60, NFR-16 met).
- Living prototype (M46): `specs/mia/goals/G-V4/prototype/status.md`; reuse map `specs/mia/goals/G-V4/prototype/reuse-map.md`, unsigned until the last subgoal (D-401). CORE takes from row R1 (keep+tests) the parts of `graph_tables.py` and `graph_model.py` named below; the tables `arrangements` and `graph_changes` and the append-only rule of R1 belong to EDIT and REPLAY and stay out. R11 (fixtures) is done: `tests/fixtures/graphs/` (commit c783f0a2, `tools/make_core_fixtures.py`).
- Source of each fact (P26): `requirements.md` of this folder → the generated block of `specs/mia/architecture.sysml` (D-408); FR-57, FR-60, NFR-16 by hand in the model with their top-level sentences.

## Interface fixed by the red tests
The checks call the API of the prototype's `graph_model.py` (reuse map R1): `GraphModel(Storage(backend), author)` with `save_graph(graph) -> SaveResult(saved, version, named, rule, detail)`, `read_graph(graph_id, version=None)`, `graph_versions(graph_id)` and `step_history(graph_id, local_id)`, and `graph_tables.check_record` with the rule `unscoped_id` (IF-301 v3). On `goal/v4` `graph_versions` and `step_history` are added as stubs (they return an empty list) with the red tests, so every check fails by assertion.

How the checks reach the code: the acceptance tests write through the real Storage layer on a fresh files store and a fresh PostgreSQL 16 database per check (`tests/helpers/core_stores.py`, TR-CORE-003, -007); the interruption checks wrap the backend in `FailingBackend` (TR-CORE-001, -002); the IF-301 suite runs on the mock and on the real Graph tables.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Scoped IDs in the Graph tables | REQ-GTB-029, REQ-GTB-030, REQ-GTB-031 | TC-GTB-033, TC-GTB-034, TC-GTB-035; real side of TC-IF-301-25, -26 | red tests installed |
| T-02 The save path: checked first, header last, changed members only | REQ-WFM-146, 147, 148, 149, 150, 151, 160 | TC-WFM-164 to TC-WFM-169, TC-WFM-178 | T-01 |
| T-03 Reading with local IDs, versions and step history | REQ-WFM-144, 145, 158, 159 | TC-WFM-162, TC-WFM-163, TC-WFM-176, TC-WFM-177 (workflow half) | T-02 |
| T-04 Context graphs on the same path | REQ-WFM-152, 153, 154, 155, 156, 157, 161 | TC-WFM-170 to TC-WFM-175, TC-WFM-177 (context half) | T-03 |
| T-05 Both stores, and the smoke check | REQ-GTB-032; REQ-WFM-152, 158, 159 on the owner's stores | TC-GTB-036 on files and PostgreSQL; SMOKE-CORE-001 green against a throw-away server | T-04 |

After every task: the IF-301 v1 and v2 suites, `tests/acceptance/test_graph_records.py`, `test_graph_model.py`, `test_graph_run.py`, `test_graph_run_stages.py`, `test_graph_order.py`, `test_pipeline_graph.py`, `test_skill_binding.py`, `tests/test_graph_record_checks.py`, `tests/test_graph_tables.py`, `tests/test_graph_run_findings.py`, `tests/test_skill_record_storage.py` and the IF-102 suite stay green.

State at the red commit (`goal/v4` with the stubs): every CORE check fails by assertion, except TC-WFM-164, which is green from the start (today's code already checks before it writes; the owner accepted it, D-410; it is shown able to fail by the defect "no check before the first write", TR-CORE-006) and must stay green; in TC-WFM-169 two positions of the changed save end with the injected `Interrupted`, because today's code writes every member again (the defect of REQ-WFM-148).

## Tasks

### T-01: Scoped IDs in the Graph tables
- Implements: REQ-GTB-029, REQ-GTB-030, REQ-GTB-031
- Tests to turn green: TC-GTB-033, TC-GTB-034, TC-GTB-035 (`tests/acceptance/test_core_scoped_ids.py`); the real side of TC-IF-301-25 and -26
- Touches: `graph_tables.py` (`scoped`, `split_scoped`, the check in `_check` and in `_check_members`); unit tests in `tests/test_graph_tables.py`
- Reuses: prototype `graph_tables.py` lines 159 to 224 (R1, keep+tests)
- Must not touch: protected material; `graph_model.py` (T-02), `storage.py`
- Depends on: red tests installed
- Demonstrator after this task: the storage refuses a step without its graph in the ID, on files and PostgreSQL
- Done when: the listed tests green, all other tests unchanged
- Notes: the empty ID stays `record_identity` (D-409); the scoped check comes after the identity checks, a header member is checked before `unknown_member`. A graph ID with a slash is caught through its steps, not checked by itself (D-410).

### T-02: The save path: checked first, header last, changed members only
- Implements: REQ-WFM-146, REQ-WFM-147, REQ-WFM-148, REQ-WFM-149, REQ-WFM-150, REQ-WFM-151, REQ-WFM-160
- Tests to turn green: TC-WFM-164 to TC-WFM-169 (`tests/acceptance/test_core_save.py`), TC-WFM-178 (`test_core_scoped_ids.py`)
- Touches: `graph_model.py` (`save_graph`, `_scoped`, `_latest`); new unit tests in a new `tests/test_graph_model_save.py`
- Reuses: prototype `graph_model.py` `save_graph` (line 175 on) (R1, keep+tests)
- Must not touch: protected material; `graph_tables.py` (T-01, done), `storage.py`
- Depends on: T-01
- Demonstrator after this task: a save interrupted at any write leaves the graph as before or new; repeating it finishes it
- Done when: the listed tests green on both backends, all other tests unchanged; `tests/acceptance/test_graph_model.py` keeps working with its fake tables (the `real` switch of the prototype)
- Notes: unused step versions after an interruption stay (ASM-002, D-402); the fault-injection checks run every write position (about 30 runs per backend).

### T-03: Reading with local IDs, versions and step history
- Implements: REQ-WFM-144, REQ-WFM-145, REQ-WFM-158, REQ-WFM-159
- Tests to turn green: TC-WFM-162, TC-WFM-163 (`test_core_scoped_ids.py`), TC-WFM-176, TC-WFM-177 workflow half (`test_core_context_and_history.py`)
- Touches: `graph_model.py` (`read_graph`, `graph_versions`, `step_history`, replacing the stubs)
- Reuses: prototype `graph_model.py` lines 219 to 250 (R1, keep+tests)
- Must not touch: protected material; `graph_tables.py`, `storage.py`
- Depends on: T-02
- Demonstrator after this task: the history of a step lists only its own graph's versions with account and time
- Done when: the listed tests green, all other tests unchanged

### T-04: Context graphs on the same path
- Implements: REQ-WFM-152, REQ-WFM-153, REQ-WFM-154, REQ-WFM-155, REQ-WFM-156, REQ-WFM-157, REQ-WFM-161
- Tests to turn green: TC-WFM-170 to TC-WFM-175, TC-WFM-177 context half (`test_core_context_and_history.py`)
- Touches: `graph_model.py` (`MEMBER_TABLES`, `context_problems`, the kind in `save_graph` and `read_graph`)
- Reuses: prototype `graph_model.py` (`context_problems` line 118, the kind switch) (R1, keep+tests)
- Must not touch: protected material; `graph_rules.py`, the workflow rules of `check_graph` (REQ-WFM-156: not applied to a context graph)
- Depends on: T-03
- Demonstrator after this task: a context graph is saved, changed and read like a workflow graph
- Done when: the listed tests green, all other tests unchanged
- Notes: the rule set of the context kind is CONTEXT's decision (ASM-4 of round 03): identity and ends only.

### T-05: Both stores, and the smoke check
- Implements: REQ-GTB-032; REQ-WFM-152, 158, 159 on the owner's two stores (SMOKE-CORE-001)
- Tests to turn green: TC-GTB-036 (`tests/acceptance/test_core_both_stores.py`) on files and PostgreSQL; `tests/smoke/smoke_core_graphs.py` against a throw-away PostgreSQL server
- Touches: only what TC-GTB-036 finds different between the backends (`storage_postgres.py`, `storage_files.py`), else nothing
- Must not touch: protected material; MIA's own database and files store (TR-CORE-009)
- Depends on: T-04
- Demonstrator after this task: the same refusals in both places
- Done when: the listed checks green, PostgreSQL not skipped on the owner's host, all other tests unchanged; the smoke run on the owner's server is part of Deploy, not of this task

## At the merge (Commit phase, not a task)
- Move the 22 requirements and 2 assumptions of `requirements.md` into `nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md` (REQ-GTB) and `nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md` (REQ-WFM), with their checks and test requirements, and regenerate the model (D-408).
- Fill the Witnesses column of the accepted cases AC-001 to AC-003 (`specs/mia/goals/G-V4/accepted-cases.md`) from the checks named in `test-spec.md`.
