# Plan: G-V2.MODEL (skill record and graph model)

**Goal:** specs/mia/goals/G-V2.MODEL/goal.md   **Requirements:** REQ-WFM-040..049 in `nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`, REQ-RUN-016..019 in `nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/requirements.md`   **Test specs:** the `test-spec.md` next to each, scenarios at the end; test requirements TR-MODEL-001..005 in `specs/mia/test-requirements.md`   **Status:** Approved by the owner, 2026-11-07 (Plan Step 5)

Line of work `goal/v2.model`; supervised. Five small tasks, pure logic: no model step, no prompt, no eval suite, no eval budget. The red tests are written first in a session of their own (Step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `eval/suites/` or `eval/baselines/`.

## Interface fixed by the red tests
The stubs `graph_model.py`, `skill_record.py` and `graph_run.py` in the repository root carry the interface the installed tests expect; T-01 to T-04 replace the stubs with the real code and keep these signatures: `GraphModel(tables).save_graph(graph)`, `read_graph(graph_id, version=None)`, `topological_order(graph_id)`; `SkillRecords(tables).store(record)`, `read(skill_id, version=None)`; `SkillCatalog(records, legacy).list()`, `start(skill_id)`; `GraphRunner(trust).run(graph, nodes, inputs)`. The result shapes are in the stub docstrings. A change of a signature is a plan amendment, not a code change.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Graph rules for the new workflow graph | REQ-WFM-043, 044, 045, 046, 047, 048, 049 | TC-WFM-043..049 | red tests installed |
| T-02 Skill record | REQ-WFM-040, 041, 042 | TC-WFM-040..042 | red tests installed |
| T-03 Run in topological order, master node like a transform, failed node stops | REQ-RUN-016, 018, 019 | TC-RUN-016, 018, 019 | T-01 |
| T-04 Untrusted node refuses the run | REQ-RUN-017 | TC-RUN-017 | T-03 |
| T-05 Replace the fake storage by the contract-checked one | REQ-WFM-040 (TR-MODEL-001) | TC-WFM-040, 041, 042, 044, 049 against the IF-301 v2 contract suite, no skip | T-02; G-V2.STORE merged |

## Tasks

### T-01: Graph rules for the new workflow graph
- Implements: REQ-WFM-043, REQ-WFM-044, REQ-WFM-045, REQ-WFM-046, REQ-WFM-047, REQ-WFM-048, REQ-WFM-049
- Tests to turn green: TC-WFM-043, TC-WFM-044, TC-WFM-045, TC-WFM-046, TC-WFM-047, TC-WFM-048, TC-WFM-049
- Touches: a new module `graph_model.py` in N-2.3 (name proposed); `requirements.txt` (adds `networkx`, approved D-187, installed on the host: no, jsonschema yes)
- Must not touch: protected material (above), `graph_rules.py` and `graph_tables.py` (N-3.2, G-V2.STORE), `pipeline.py`
- Depends on: red tests installed
- Done when: the listed tests are green, all other tests unchanged
- Notes: the cycle is reported as IDs with the first repeated at the end (WFM-047); the cycles of TC-WFM-047 have 2 or 4 nodes (odd cycles break the alternation of REQ-WFM-045), and a fixed 5-node cycle is only refused, without naming the cycle; the order check must not reuse the function under test (TR-MODEL-003). STORE's write validation does not call these rules: the graph rules of the new node types stay in the Workflow management only (D-262).

### T-02: Skill record
- Implements: REQ-WFM-040, REQ-WFM-041, REQ-WFM-042
- Tests to turn green: TC-WFM-040, TC-WFM-041, TC-WFM-042
- Touches: a new module `skill_record.py` in N-2.3 (name proposed); the listing and start of skills in `library.py` and `extension_loader.py`, only so that a skill with a record takes its command, workflow graph and context graph from the record (WFM-041)
- Must not touch: protected material, `graph_rules.py`, `graph_tables.py`, `pipeline.py`
- Depends on: red tests installed
- Done when: the listed tests are green, all other tests (the old skills without a record) unchanged
- Notes: the storage in these tests is the minimal fake of the red tests (TR-MODEL-001); the record uses IF-301 v2 through that fake only. Versions never change (REQ-WFM-069 belongs to CONVERT).

### T-03: Run in topological order, master node like a transform, failed node stops
- Implements: REQ-RUN-016, REQ-RUN-018, REQ-RUN-019
- Tests to turn green: TC-RUN-016, TC-RUN-018, TC-RUN-019
- Touches: a new module `graph_run.py` in N-2.4.1 (name proposed); it uses T-01 for the order
- Must not touch: protected material, `pipeline.py` (the old pipeline runner keeps running the old pipelines), `library.py`
- Depends on: T-01
- Done when: the listed tests are green, all other tests unchanged
- Notes: a master node runs once, as a transform; its stop criterion is stored and unused until debates (FR-39, later goal).

### T-04: Untrusted node refuses the run
- Implements: REQ-RUN-017
- Tests to turn green: TC-RUN-017
- Touches: `graph_run.py` (T-03)
- Must not touch: protected material, the toolbox and its trust records (G-V2.TOOLBOX)
- Depends on: T-03
- Done when: TC-RUN-017 is green, all other tests unchanged
- Notes: the status of a node comes in through a small lookup the test supplies (stand-in for IF-203 v1 of TOOLBOX); the refusal happens before any node runs, so the marker file never appears. No new tool, no permission change.

### T-05: Replace the fake storage by the contract-checked one
- Implements: REQ-WFM-040 (TR-MODEL-001)
- Tests to turn green: TC-WFM-040, TC-WFM-041, TC-WFM-042, TC-WFM-044, TC-WFM-049 run against the IF-301 v2 contract suite of STORE, with no skip
- Touches: the wiring in `skill_record.py` to the real graph tables
- Must not touch: protected material, STORE's files
- Depends on: T-02; G-V2.STORE merged
- Done when: the minimal fake passes the IF-301 v2 contract suite, or the difference is reported as a finding; the listed tests are green against the real tables
- Notes: if the fake fails the suite, stop and report (TR-MODEL-001: a finding for these checks).

## Order and checks
T-01 and T-02 are independent; T-03 needs T-01; T-04 needs T-03; T-05 waits for STORE. After each task: `python tests/test_<name>.py` for its tests, then the stage 1 and 2 steps of `stages.yaml`.

## Size check (splitting)
14 requirements, five tasks of one session each, no task across two nodes except T-02 (N-2.3 only) and T-03/T-04 (N-2.4.1 only). No split is suggested; the goal record's "keep together" stands.

## Decided by the owner (2026-11-07)
1. Module names `graph_model.py`, `skill_record.py`, `graph_run.py` are fine; the only existing code that changes is the skill listing in T-02 (`library.py`, `extension_loader.py`).
2. STORE's write validation does not share the rules of T-01 (D-262, point 1).
3. `requirements.txt` gets `networkx` in T-01 (D-187); `jsonschema` is already installed.
