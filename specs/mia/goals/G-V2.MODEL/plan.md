# Plan: G-V2.MODEL (skill record and graph model)

**Goal:** specs/mia/goals/G-V2.MODEL/goal.md   **Requirements:** REQ-WFM-040..049 in `nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md`, REQ-RUN-016..019 in `nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/requirements.md`   **Test specs:** the `test-spec.md` next to each, scenarios at the end; test requirements TR-MODEL-001..005 in `specs/mia/test-requirements.md`   **Status:** Approved by the owner, 2026-11-07 (Plan Step 5)

Line of work `goal/v2.model`; supervised. Eight small tasks, pure logic: no model step, no prompt, no eval suite, no eval budget. The red tests are written first in a session of their own (Step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `eval/suites/` or `eval/baselines/`.

## Interface fixed by the red tests
The stubs `graph_model.py`, `skill_record.py` and `graph_run.py` in the repository root carry the interface the installed tests expect; T-01 to T-04 replace the stubs with the real code and keep these signatures: `GraphModel(tables).save_graph(graph)`, `read_graph(graph_id, version=None)`, `topological_order(graph_id)`; `SkillRecords(tables).store(record)`, `read(skill_id, version=None)`; `SkillCatalog(records, legacy).list()`, `start(skill_id)`; `GraphRunner(trust).run(graph, nodes, inputs)`. The result shapes are in the stub docstrings. A change of a signature is a plan amendment, not a code change.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Graph rules for the new workflow graph | REQ-WFM-043, 044, 045, 046, 047, 048, 049 | TC-WFM-043..049 | red tests installed |
| T-02 Skill record | REQ-WFM-040, 041, 042 | TC-WFM-040..042 | red tests installed |
| T-03 Run in topological order, master node like a transform, failed node stops | REQ-RUN-016, 018, 019 | TC-RUN-016, 018, 019 | T-01 |
| T-04 Untrusted node refuses the run | REQ-RUN-017 | TC-RUN-017 | T-03 |
| T-05 Skill records on the real Storage layer (adapter test) | REQ-WFM-040 (TR-MODEL-001) | the five scenarios of TC-WFM-040, 041, 042, 044, 049 give the same answers on the fake and on the real Storage layer, in `tests/test_skill_record_storage.py` | T-02; G-V2.STORE merged |
| T-06 Skill listing and start take the record (extension loader) | REQ-WFM-041 | new tests (marked TC-WFM-041) for `extension_loader.py` and the wiring, written first | T-05 |
| T-07 Graph model on the record tables | REQ-WFM-043..049 (stored form), REQ-WFM-044 | the adapter test of T-05 runs the graph scenarios (TC-WFM-044, 049) on the real Storage through `graph_model.py` itself, without the test-side mapping | T-05 |
| T-08 Findings of the first Verify run (F-01, F-02, F-03, F-05) | REQ-WFM-042, REQ-WFM-048, REQ-RUN-016, REQ-RUN-017 | the failing tests proposed in `verification-report.md` for F-01, F-02, F-03, F-05 | T-01 to T-07 |

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

### T-05: Skill records on the real Storage layer (adapter test)
- Implements: REQ-WFM-040 (TR-MODEL-001 as reworded by A-105)
- Tests to turn green: a new file `tests/test_skill_record_storage.py` (outside the protected folders) that runs the scenarios of TC-WFM-040, TC-WFM-041, TC-WFM-042, TC-WFM-044 and TC-WFM-049 on the real `Storage` of STORE (file backend; PostgreSQL where the test environment offers it) and on the fake, and compares the answers; the five protected tests in `tests/acceptance/test_graph_model.py` stay green on the fake
- Touches: `skill_record.py` (wiring to `Storage`: the list of skill IDs comes from `Storage.ids("skills")` instead of the `skill_index` record, the `author` of `put` is given by the caller), the new test file
- Must not touch: protected material (`tests/acceptance/`, `tests/helpers/`, `contracts/`), STORE's files (`storage.py`, `graph_tables.py`, `storage_copy.py`)
- Depends on: T-02; G-V2.STORE merged
- Done when: the adapter test is green on the file backend (and on PostgreSQL where available, no skip there), the fake and the real Storage layer give the same answers for the five scenarios, or each difference is reported as a finding for these checks
- Notes: T-05 stopped on 2026-11-08 because the fake cannot pass the contract suite of IF-301 v2 (key-value store against record checks); A-105 is the answer. A skill record that the real record checks refuse is a finding for the skill record (REQ-WFM-040), not a reason to change STORE.

### T-06: Skill listing and start take the record (extension loader)
- Implements: REQ-WFM-041
- Tests to turn green: new tests marked TC-WFM-041, written first: (1) `load_extensions` with a `catalog` registers a skill that has a record under the record's command and its task carries the record's `workflow_graph_id`; (2) a skill without a record is registered exactly as before; (3) a record-only skill (no manifest folder) is not invented as a runnable task; the listing of commands (`TaskRegistry.commands`) shows the record's command; (4) the wiring in `web_app.py` creates the catalog from the Storage layer and passes it (as far as a test without a running server can show it)
- Touches: `extension_loader.py` (new optional parameter `catalog`, default None = behaviour as today), `task_registry.py` (one new attribute `workflow_graph_id` on `Task`, default None), `web_app.py` (create the `SkillCatalog` over `SkillRecords` and pass it to `load_extensions`), their tests
- Must not touch: protected material, STORE's files (`storage.py`, `graph_tables.py`, `storage_copy.py`), `library.py` (it has no skill listing: the plan's first wording was wrong)
- Depends on: T-05
- Done when: the listing and the start of a skill with a record use the record, and a skill without a record behaves as before (the existing tests of the three modules stay green)
- Notes: A-107 (2026-11-08): the first wording named `library.py`, which has no skill listing or start; the T-06 agent stopped and reported. Owner decision: option A (the extension loader) and the two extra files in the bounds. What runs when a record exists but no entry module does is not decided here: such a skill is listed by its command but is not made runnable by T-06 (report as a note, G-V2.CONVERT moves the skills one by one).

### T-07: Graph model on the record tables
- Implements: REQ-WFM-043, REQ-WFM-044, REQ-WFM-045, REQ-WFM-046, REQ-WFM-047, REQ-WFM-048, REQ-WFM-049 (the stored form of a graph; the rules themselves are T-01)
- Tests to turn green: the graph scenarios of the adapter test `tests/test_skill_record_storage.py` (TC-WFM-044, TC-WFM-049) with the test-side class `RealGraphTables` removed, so that `GraphModel(Storage)` itself saves a graph as `graph_nodes` and `graph_edges` records plus a `graphs` header that pins the member versions, and reads it back; a graph refused by the record checks of the Storage layer is a refused result naming the rule and detail, not an exception; the 10 protected tests in `tests/acceptance/test_graph_model.py` stay green on the fake
- Touches: `graph_model.py` (detects the real Storage as `SkillRecords` does; the `workflow_graphs` table name stays only for the fake path), `tests/test_skill_record_storage.py` (the mapping moves out of the test)
- Must not touch: protected material (`tests/acceptance/`, `tests/helpers/`, `contracts/`), STORE's files (`storage.py`, `graph_tables.py`, `storage_copy.py`)
- Depends on: T-05 (independent of T-06)
- Done when: the graph scenarios give the same answers on the fake, the file backend and PostgreSQL with the production wiring; the rules of T-01 are checked before the write (the record checks of STORE check each record again); a graph header that names an unknown member version is refused with the rule of the Storage layer
- Notes: finding 3 of T-05 (2026-11-08): `GraphModel` saved into `workflow_graphs`, which the real Storage does not have (`unknown_table`), and the real Storage returns `put` as `{"version": n}` and `get` as an entry with `doc`. A difference that is not an adapter detail is a finding for TR-MODEL-001, reported, not changed in the fake (`tests/helpers` is protected).

### T-08: Findings of the first Verify run (F-01, F-02, F-03, F-05)
- Implements: REQ-WFM-048 (F-01: the stop criterion of a master node uses `max_seconds`, as IF-301 v2 and the owner's field names say, not `max_time`), REQ-WFM-042 (F-02: the command clash check also catches a command that differs only in case or leading slash, and a record command that is a manifest-only skill's command), REQ-WFM-041 (F-03: the form of a record command; the loader refuses or skips a command that cannot be registered, with a problem report, instead of raising or registering an empty ID), REQ-RUN-016 and REQ-RUN-017 (F-05: a graph with a cycle or an edge to an unknown node is refused by the runner, not run, not raised)
- Tests to turn green: new tests, written first, from the proposals in `verification-report.md` (F-01, F-02, F-03, F-05), in `tests/test_skill_record_storage.py`, `tests/test_skill_catalog_loader.py` and a new `tests/test_graph_run_findings.py` (the protected acceptance files are not edited); the tests also pin the owner's decisions of 2026-11-08: an unknown trust status is refused (fail safe), `named_status` stays one value (the first refused node's)
- Touches: `graph_model.py`, `skill_record.py`, `graph_run.py`, `extension_loader.py` and their new tests
- Must not touch: protected material, STORE's files
- Depends on: T-01 to T-07
- Done when: the proposed failing tests are green, the protected tests (`test_graph_model.py` 10, `test_graph_run.py` 4) and the earlier tests of the goal stay green, and the report's findings F-01, F-02, F-03, F-05 can be closed by the next Verify run
- Notes: F-04, F-06 to F-11 are not part of T-08 (owner's decision 2026-11-08: fix the high and the medium findings; the re-save and orphan versions of F-07 are a known property, versions are append-only; F-09 test gaps, F-10 re-approval of TC-WFM-047, TR-MODEL-003 and TR-MODEL-001 and F-11 text/doc items go to the next steps).

## Order and checks
T-01 and T-02 are independent; T-03 needs T-01; T-04 needs T-03; T-05 waits for STORE; T-06 and T-07 need T-05 and are independent of each other. After each task: `python tests/test_<name>.py` for its tests, then the stage 1 and 2 steps of `stages.yaml`.

## Size check (splitting)
14 requirements, eight tasks of one session each, no task across two nodes except T-02 (N-2.3 only), T-05, T-06 and T-07 (N-2.3 only) and T-03/T-04 (N-2.4.1 only). No split is suggested; the goal record's "keep together" stands.

## Decided by the owner (2026-11-07)
1. Module names `graph_model.py`, `skill_record.py`, `graph_run.py` are fine; the only existing code that changes is the skill listing in T-02 (`library.py`, `extension_loader.py`).
2. STORE's write validation does not share the rules of T-01 (D-262, point 1).
3. `requirements.txt` gets `networkx` in T-01 (D-187); `jsonschema` is already installed.
