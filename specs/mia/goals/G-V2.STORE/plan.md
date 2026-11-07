# Plan: G-V2.STORE (graph records, storage)

**Goal:** specs/mia/goals/G-V2.STORE/goal.md   **Requirements:** REQ-GTB-005..020 in `nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md`, interface IF-301 v2 (`contracts/IF-301-graph-tables.md`)   **Test specs:** `test-spec.md` next to the requirements (scenarios "iteration 2, G-V2.STORE"), test requirements TR-GTB-001..006 in `test-requirements.md` next to it   **Status:** Approved by the owner, 2026-11-07 (Plan Step 5)

Line of work `goal/v2.store`; supervised. Seven small tasks (T-06 added with A-92, T-07 with A-93), pure logic and one wiring: no model step, no prompt, no eval suite, no eval budget. The red tests were written in a session of their own (Step 4) and are installed (tag `plan-baseline-it2-store`); the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `eval/suites/` or `eval/baselines/`.

## Interface fixed by the red tests and the contract
The stubs in `graph_tables.py` (`record_definitions`, `types`, `check_record`, `to_object`, `to_record`, `to_document`, `from_document`) carry the signatures of IF-301 v2; T-01 to T-03 replace them and keep the signatures and result shapes of the contract (`definitions()` stays the two tables of v1; the four record tables are in `record_definitions()`). Where the contract text left a point open, the section "Clarifications" of the contract and the v2 mock (`tests/helpers/mocks/if_301_graph_tables_v2.py`) are the reference. A change of a signature is a plan amendment, not a code change.

How the checks reach the code: the acceptance tests `tests/acceptance/test_graph_records.py` write through a storage stand-in that calls the real `graph_tables.check_record` (so T-01 to T-03 turn them green without the real Storage layer); the contract suite `test_if_301_v2_graph_tables.py` runs on the real side with `IF301_V2_REAL=1` while the work is going on, and without the skip after T-05.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Record tables, types and record checks | REQ-GTB-005, 006, 011, 013 (flag), 016 (the check), 017, 018, 019, 020; REQ-GTB-007, 008, 010 (write side) | TC-GTB-006, 011, 013, 016, 017, 018, 019, 020, 021; real side of TC-IF-301-05, 06, 09, 10, 13, 14, 15, 19 | red tests installed |
| T-02 Classes from type IDs | REQ-GTB-007, 008, 009, 010 (read side), 014 | TC-GTB-007, 008, 009, 010, 014; real side of TC-IF-301-07, 08, 16, 18 | T-01 |
| T-03 Document form both ways | REQ-GTB-015 | TC-GTB-015; real side of TC-IF-301-11, 12, 17 | T-02 |
| T-04 The Storage layer takes the four tables | REQ-GTB-013, 016, 005, 006 (on the real storage) | new unit tests of the Storage layer (TC-GTB-013, 016, 017 on `Storage` with the file backend), IF-102 suite on the real side unchanged | T-01 |
| T-05 Integration: the real side of the suite without skip | REQ-GTB-015, IF-301 | the v2 suite passes on the real Graph tables with no skip; TC-GTB-015 with the real storage | T-03, T-04; amendment A-91 (owner installs) |
| T-06 Record under its own ID | REQ-GTB-021 | TC-GTB-022; real side of TC-IF-301-20; a new unit test of the Storage layer | T-04; amendment A-92 (installed) |
| T-07 Fixed fields of a node | REQ-GTB-022 | TC-GTB-023; real side of TC-IF-301-21; new unit tests of `check_record` and `to_object` | T-06; amendment A-93 (installed) |

TC-GTB-012 (no pickle, marshal, shelve) is green today and must stay green after every task; TC-GTB-014's N (default 1000) is raised by the owner or the verifier with `TC_GTB_014_N`.

## Tasks

### T-01: Record tables, types and record checks
- Implements: REQ-GTB-005, REQ-GTB-006, REQ-GTB-011, REQ-GTB-013, REQ-GTB-016, REQ-GTB-017, REQ-GTB-018, REQ-GTB-019, REQ-GTB-020; the write side of REQ-GTB-007, REQ-GTB-008, REQ-GTB-010
- Tests to turn green: TC-GTB-006, TC-GTB-011, TC-GTB-013, TC-GTB-016, TC-GTB-017, TC-GTB-018, TC-GTB-019, TC-GTB-020, TC-GTB-021; with `IF301_V2_REAL=1` the real side of TC-IF-301-05, 06, 09, 10, 13, 14, 15, 19
- Touches: `graph_tables.py` (the stubs `record_definitions`, `types`, `check_record`; a new module for the type list and its schemas only if `graph_tables.py` grows past what is readable, and then imported by `graph_tables.py` so TC-GTB-012 sees it); `requirements.txt` (adds `jsonschema==4.23.0`: approved D-187, the version TR-GTB-003 names, installed on the host)
- Must not touch: protected material (above), `graph_rules.py` (the document rules of v1), `storage.py` (T-04), `pipeline.py`
- Depends on: red tests installed
- Done when: the listed tests are green, all other tests unchanged, `python tests/acceptance/test_graph_records.py` shows only the failures of T-02 and T-03
- Notes: the schemas are the table "fixed list of types" of the contract; the detail of a `schema_break` is the path of the first broken field as the pinned jsonschema names it (a missing required key is named by the key; the mock `_broken_path` shows the convention, the real code writes its own); validators are built once (the bound is 500 ms for 500 node and 500 edge records, the mock needs about 6 ms); `check_record` never raises (any input gives a rule or `None`), except `ValueError` for a table that is not one of the four; the order of the checks is the one of the mock (identity, type, schema, endpoints or members). The Workflow management's graph rules (cycle, adjacency, master) are not here (D-262).

### T-02: Classes from type IDs
- Implements: REQ-GTB-007, REQ-GTB-008, REQ-GTB-009, REQ-GTB-010 (read side), REQ-GTB-014
- Tests to turn green: TC-GTB-007, TC-GTB-008, TC-GTB-009, TC-GTB-010, TC-GTB-014; real side of TC-IF-301-07, 08, 16 and 18 (they also call `to_object`)
- Touches: `graph_tables.py` (the stubs `to_object`, `to_record`; the three data classes and `ContextNode`, in `graph_tables.py` or in the new module of T-01)
- Must not touch: protected material, `storage.py`, `graph_rules.py`
- Depends on: T-01
- Done when: the listed tests are green (TC-GTB-014 with the default N = 1000), all other tests unchanged
- Notes: one class per type ID and the attributes named in the contract's clarifications (`id` and the field names; `value` and `task` are `None` when absent, `parameters` is `{}`); `to_record` leaves out `value` and `task` when they are `None`; a task definition is data only, nothing is executed (TC-GTB-008 checks with a marker file); `to_object` refuses with the rule of `check_record`, with no storage involved.

### T-03: Document form both ways
- Implements: REQ-GTB-015
- Tests to turn green: TC-GTB-015; real side of TC-IF-301-11, 12 and 17
- Touches: `graph_tables.py` (the stubs `to_document`, `from_document`)
- Must not touch: protected material (above all the v1 IF-301 suite and the IF-203 v0 suite: TC-GTB-015 fails on a changed hash), `graph_rules.py`, `workflow_library.py`
- Depends on: T-02
- Done when: the listed tests are green, the v1 IF-301 and v0 IF-203 suites pass unchanged
- Notes: `transform` becomes kind `process`, `data` stays `data`; a master node is `not_representable`; the other fields of a node go flat beside `id` and `kind`, the JSON field of an edge goes under `data` (contract clarification); an edge of a v1 document without an ID gets `e1`, `e2`, ... in order; a record converted from a v1 document is not checked.

### T-04: The Storage layer takes the four tables
- Implements: REQ-GTB-013 and REQ-GTB-016 on the real storage; REQ-GTB-005 and REQ-GTB-006 as stored by it
- Tests to turn green: new unit tests in `tests/test_storage.py` (free in Phase 3) that repeat TC-GTB-013, TC-GTB-016 and TC-GTB-017 on `Storage` with the file backend (and on PostgreSQL where `tests/test_storage_postgres.py` already runs); the IF-102 contract suite on the real side stays green
- Touches: `storage.py` (`table_definitions` adds `graph_tables.record_definitions()`; `validate` or `put` calls `check_record` with `stored` for the four tables and refuses with `invalid`, the rule and the detail); tests in `tests/test_storage.py`
- Must not touch: protected material, `storage_postgres.py` and `storage_files.py` (both backends keep every table in one generic store, no schema change), `storage_copy.py` (its table list is the library only; copying record tables is a decision for CONVERT)
- Depends on: T-01
- Done when: the new unit tests and the old `tests/test_storage.py`, `tests/test_storage_postgres.py` are green, the IF-102 suite (real side) passes, a refused write leaves the number of versions as it was
- Notes: `stored` is built for what the record names only (an edge's two ends, a header's members), from `backend.versions(table, id)`, so a write does not read the whole table; the refusal is `StorageError("invalid", rule, detail)` as for the document tables; delete of the four tables is `immutable`; this task needs no schema file in `deploy/db/`.

### T-05: Integration: the real side of the suite without skip
- Implements: REQ-GTB-015 and IF-301 v2 (integration gate of N-3.2)
- Tests to turn green: the v2 contract suite on the real Graph tables with no skip (stage 2, `contract-real`); TC-GTB-015 with the real storage
- Touches: a new amendment script `tools/apply_amendment_a91.sh` with its draft of the suite and of `tests/helpers/contract.py` (drafted by the agent, installed by the owner), `CHANGELOG.md`
- Must not touch: protected material directly (the amendment replaces the environment switch `IF301_V2_REAL` of `subject()` in `test_if_301_v2_graph_tables.py` by the real provider; that is a change of a protected suite and needs the owner)
- Depends on: T-03, T-04; A-91 reserved for STORE
- Done when: after the owner installs A-91 the suite passes on both sides with no skip, the v1 suite and the IF-203 v0 suite pass unchanged, the stage 1 to 3 steps of `stages.yaml` show nothing new
- Notes: removing the skip belongs to the integration gate of N-3.2 (decomposition rule 3); at this point the implementation log lists what was measured: the time for 500 node and 500 edge records (bound 500 ms) and the seeds of TC-GTB-014.

### T-06: Record under its own ID
- Implements: REQ-GTB-021 (A-92)
- Tests to turn green: TC-GTB-022 (`tests/acceptance/test_graph_record_identity.py`); the real side of TC-IF-301-20 (`test_a_record_under_another_id_is_refused_real`); a new unit test in `tests/test_storage.py` that repeats TC-GTB-022 on `Storage` for each of the four tables, on every backend (the file backend and, where `tests/test_storage_postgres.py` runs, PostgreSQL)
- Touches: `graph_tables.py` (`check_record` uses its argument `record_id`: when given and different from the `id` inside the record, `record_identity` with the detail `id`, checked right after the record's own `id`); `storage.py` (`put` passes the record ID it writes under to `check_record`, also in the check that needs `stored`); `tests/test_storage.py`
- Must not touch: protected material, `contracts/` (A-92 changed IF-301 already), `storage_postgres.py`, `storage_files.py`, `storage_copy.py`
- Depends on: T-04; A-92 installed
- Done when: the listed tests are green, all other tests unchanged (the three contract suites, `test_graph_records.py`, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16)
- Notes: the stub of `check_record` accepts `record_id` and ignores it since the draft of A-92; `validate()` (used by the copy tools) has no record ID and stays as it is; the document form is not affected. No new part, interface or dependency.

### T-07: Fixed fields of a node
- Implements: REQ-GTB-022 (A-93, F-01 of the verification report)
- Tests to turn green: TC-GTB-023 (`tests/acceptance/test_graph_node_fields.py`); the real side of TC-IF-301-21 (`test_a_node_with_an_extra_field_is_refused_naming_it_real`); new unit tests in `tests/test_graph_record_checks.py` that fail first: `check_record` and `to_object` of `{"type": "data", "foo": 1}` and of `{"type": "data", "id": "x"}`, and `Storage.put` of the first (refused as `invalid`, `schema_break`, `foo`, nothing stored)
- Touches: `graph_tables.py` (the three schemas of `TYPE_SCHEMAS` get `"additionalProperties": False`; `_broken_path` names an additional field by its own key, the first in sorted order when several, and orders the errors by these paths as text, so a missing key at the same level is named first); `tests/test_graph_record_checks.py`
- Must not touch: protected material, `contracts/` (A-93 changed IF-301 already), `storage.py` (it calls `check_record` already), `graph_rules.py`, the schemas of `graphs`, `skills` and `graph_edges`, the schemas of context-graph nodes (they come from the caller's categories)
- Depends on: T-06; A-93 installed
- Done when: the listed tests are green, all other tests unchanged (the three contract suites, `test_graph_records.py`, `test_graph_record_identity.py`, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, TC-GTB-014 with N = 1000)
- Notes: `to_object` needs no change of its own: it calls `check_record` first, so a node with an extra field is refused before `CLASSES[type_id](id, **data)` is reached. The schemas that `types()` returns carry the setting (TC-IF-301-21 checks it). `_STOP`, the member lists and the edge schema are not changed. No new part, interface or dependency.

## Order and checks
T-01 first (everything else needs the record checks); T-02, then T-03; T-04 may run beside T-02 and T-03 (it needs only T-01); T-06 after T-04; T-07 after T-06 and the install of A-93. After each task: `python tests/acceptance/test_graph_records.py` and `IF301_V2_REAL=1 python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _real` for the progress of the red tests, `python tests/test_graph_tables.py` and `python tests/test_storage.py` for the old behaviour, then the stage 1 and 2 steps of `stages.yaml`. Before the hand-over: `trace_check`, `goal_check`, `req_graph`.

## Size check (splitting)
18 requirements and one interface, seven tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-07, N-3.1 in T-04 and T-06). The leaf limit (about 8 tasks, 3 interfaces) is kept; no split is suggested, the goal record's "keep together" stands. T-04 is the only change outside N-3.2 and touches one file.

## Decided by the owner (2026-11-07)
1. A-90 (contract text of IF-301 v2 with its Clarifications, installed) is approved, and A-91 in principle: T-05 removes the skip of the v2 suite by an amendment the owner installs; the agent drafts its script for a look-only review when T-05 comes.
2. The cut of five tasks stands.
3. `requirements.txt` gets `jsonschema==4.23.0` in T-01 (D-187; MODEL's `networkx` line merges as a union).
4. `storage_copy.py` is not changed in T-04; CONVERT decides about copying the record tables.
5. A-92 (record under its own ID, REQ-GTB-021, TC-GTB-022, the optional `record_id` of `check_record` in IF-301 v2) is approved and installed; T-06 is added to this plan on the owner's word (2026-11-07).
6. A-93 (fixed fields of a node, REQ-GTB-022, TC-GTB-023, TC-IF-301-21, IF-301 v2) follows the decision of F-01 on 2026-11-07, which the owner delegated to the reviewer and may overrule; T-07 is added to this plan on that decision, the owner installs the amendment after a look-only review.
