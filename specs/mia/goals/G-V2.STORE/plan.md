# Plan: G-V2.STORE (graph records, storage)

**Goal:** specs/mia/goals/G-V2.STORE/goal.md   **Requirements:** REQ-GTB-005..020 in `nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md`, interface IF-301 v2 (`contracts/IF-301-graph-tables.md`)   **Test specs:** `test-spec.md` next to the requirements (scenarios "iteration 2, G-V2.STORE"), test requirements TR-GTB-001..006 in `test-requirements.md` next to it   **Status:** Approved by the owner, 2026-11-07 (Plan Step 5)

Line of work `goal/v2.store`; supervised. Twelve small tasks (T-06 added with A-92, T-07 with A-93, T-08 and T-09 with A-98, T-10 after the fourth Verify run, T-11 with A-100, T-12 with A-102), pure logic and one wiring: no model step, no prompt, no eval suite, no eval budget. The red tests were written in a session of their own (Step 4) and are installed (tag `plan-baseline-it2-store`); the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `eval/suites/` or `eval/baselines/`.

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
| T-08 Context graph tables | REQ-GTB-023, 024, 025, 026 | TC-GTB-024, 025, 026, 027; real side of TC-IF-301-05 (six tables) and TC-IF-301-22; new unit tests of the Storage layer; the six-table assertions of `test_graph_records.py` and `test_graph_record_identity.py` | T-07; amendment A-98 (installed) |
| T-09 Small fixes of the record checks | REQ-GTB-027 (F-09); robustness of REQ-GTB-011 and REQ-GTB-022 (F-03, F-11); tests F-06, F-13b | TC-GTB-028; real side of TC-IF-301-23; new unit tests | T-08; amendment A-98 (installed) |
| T-10 Findings of the fourth Verify run (F-15, F-16, F-17) | REQ-GTB-027 at the Storage entry (F-15); remote references of a category schema (F-17); boundary tests (F-16) | new unit tests that fail first | T-09 |
| T-11 Findings of the fifth Verify run (F-19, F-20, F-21) | REQ-SLY-013, REQ-SLY-014; F-21 | TC-SLY-012, TC-SLY-013 (in `tests/test_storage.py`); `test_doc_check` clean | T-10; amendment A-100 (installed) |
| T-12 Size of a document (F-22) | REQ-GTB-028, REQ-SLY-015 | TC-GTB-029; real side of TC-IF-301-24; TC-SLY-014 (in `tests/test_storage.py`) | T-11; amendment A-102 (installed) |

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

### T-08: Context graph tables
- Implements: REQ-GTB-023, REQ-GTB-024, REQ-GTB-025, REQ-GTB-026 (A-98, F-02)
- Tests to turn green: TC-GTB-024 to TC-GTB-027 (`tests/acceptance/test_graph_context_tables.py`); the real side of TC-IF-301-05 (six record tables) and of TC-IF-301-22; new unit tests in `tests/test_storage.py` that repeat TC-GTB-024 to 027 on `Storage`, on the file backend and, where `tests/test_storage_postgres.py` runs, on PostgreSQL (red first)
- Touches: `graph_tables.py` (`RECORD_TABLES` gets `context_nodes` and `context_edges`; `_check` has a branch for them: shape, with `categories` the type and schema of a node, the ends of an edge against `stored["context_nodes"]`; a header of kind context looks its members up in `stored["context_nodes"]` and `stored["context_edges"]`); `storage.py` (the list of record tables follows `graph_tables.RECORD_TABLES`; the `stored` it builds for a write holds the versions of the context records that an edge or header names); `tests/test_storage.py`, `tests/test_storage_postgres.py`
- Must not touch: protected material, `contracts/`, `storage_postgres.py`, `storage_files.py`, `storage_copy.py` (F-07 is routed to CONVERT), IF-102 (put has no `categories`: decision 14 of IF-301)
- Depends on: T-07; A-98 installed
- Done when: the listed tests are green, all other tests unchanged except the two that stay red on purpose: TC-GTB-028 and the real side of TC-IF-301-23 (T-09); until this task the six-table assertions of `test_graph_records.py`, `test_graph_record_identity.py` and TC-IF-301-05 are red because the real code lists four tables (the three contract suites, `test_graph_records.py`, `test_graph_record_identity.py`, `test_graph_node_fields.py`, `test_storage.py`, `test_storage_postgres.py`, TC-GTB-014 with N = 1000, 500 node and 500 edge records within 500 ms)
- Notes: the Storage layer calls `check_record` without `categories` for the context tables, so it checks the shape only; the context-graph owner or the Workflow management calls `check_record` with the categories before it writes. `check_record("graph_nodes", ..., categories=...)` keeps working as before (golden 13). No new part or dependency; the interface change is the one of IF-301 v2 decided in A-98.

### T-09: Small fixes of the record checks (F-03, F-06, F-09, F-11, F-13b)
- Implements: REQ-GTB-027 (F-09, A-98); robustness of REQ-GTB-011 and REQ-GTB-022 (F-03, F-11); the test additions F-06 and F-13(b) have no requirement of their own
- Tests to turn green: TC-GTB-028 (`tests/acceptance/test_graph_context_tables.py`, the test of REQ-GTB-027); the real side of TC-IF-301-23 (`test_input_that_cannot_be_checked_is_a_schema_break_real`); new unit tests that fail first, in `tests/test_graph_record_checks.py`: F-03 (after 10 000 `check_record` calls with fresh equal `categories` dicts the validator cache stays below 256 entries), F-11 (`{"type": "entity", "xa": 1, "zz": 2}` with `patternProperties {"^x": {}}` and `additionalProperties: false` names `zz`), F-06(a) (a header whose second member names a version that is not stored gives `unknown_member` naming that member, also on `Storage`), F-06(b) (`validate("graph_nodes", {"id": "n", "data": {"type": "zz"}})` raises `invalid`/`unknown_type`); in `tests/test_storage_postgres.py`: F-13(b) (a node with an extra field is refused as `invalid`, `schema_break`, nothing stored)
- Touches: `graph_tables.py` (the validator cache keeps only the schemas of the fixed list, or is keyed by the schema's JSON; `_error_path` names an extra field as a key that neither `properties` nor `patternProperties` matches; a record nested deeper than 200 levels is `schema_break` naming `data`, a category whose schema fails `Draft202012Validator.check_schema` is `schema_break` naming `type`; the catch-all stays for anything else); `tests/test_graph_record_checks.py`, `tests/test_storage.py`, `tests/test_storage_postgres.py`
- Must not touch: protected material, `contracts/` (A-98 changed IF-301 already), `storage.py`
- Depends on: T-08; A-98 installed
- Done when: the listed tests are green and `test_graph_context_tables.py` is green; all other tests green (the three contract suites with no skip, `test_graph_records.py`, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, TC-GTB-014 with N = 1000)
- Notes: the 200 levels count the record itself as level 1; checked iteratively, so the check itself does not hit the recursion limit. F-13(a) (two extra fields in a protected case) is accepted by the owner and waits for the next amendment of IF-301; F-07 and F-08 are routed to CONVERT. No new part, interface or dependency.

### T-10: Findings of the fourth Verify run (F-15, F-16, F-17)
- Implements: REQ-GTB-027 at the Storage entry (F-15); the rule that untrusted text gets no network access (F-17, CLAUDE.md); no requirement of its own for the boundary tests (F-16)
- Tests to turn green: new unit tests that fail first. F-15 (`tests/test_storage.py`): `Storage.put` of a document nested 600 and 900 levels, for a graph table and for a table that is not a graph table, is refused as `StorageError` (`invalid`, rule `schema_break`, detail `data` for the graph tables), never a `RecursionError`; 300 levels still `schema_break`/`data`. F-16 (`tests/test_graph_record_checks.py`): exactly 200 levels are accepted and 201 refused (the record is level 1; kills the mutants cap 201, `>=` and level 0), 20 000 distinct `categories` keep the validator cache at or below its bound and 1000 equal ones keep one entry (kills the cache mutants). F-17 (`tests/test_graph_record_checks.py`): a category schema with a `$ref` to a URL on a local test server is refused or ignored without a single request reaching the server, in `check_record` for `graph_nodes` and `context_nodes`
- Touches: `storage.py` (`refuse_unstorable` or the order of the checks: the depth check comes first, or the recursion becomes iterative, so no `RecursionError` leaves `put`); `graph_tables.py` (category schemas are checked with a validator that fetches no remote reference, for example a `referencing` registry whose retrieve function refuses; a remote `$ref` is `schema_break` naming `type`); the two test files
- Must not touch: protected material, `contracts/`, `storage_postgres.py`, `storage_files.py`, `storage_copy.py`
- Depends on: T-09
- Done when: the listed tests are green and all other tests unchanged (the contract suites with no skip, the acceptance tests of the goal, TC-GTB-014 with N = 1000, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, 500 node and 500 edge records within 500 ms)
- Notes: F-18 (non-string keys, Python callers only) is accepted by the owner on 2026-11-08 and routed to the context-graph writer goal; F-13(a), F-07 and F-08 stay accepted. A document nested more than about 990 levels is not valid JSON for `json.loads`, so an API caller can reach about 990 levels. No new part, interface or dependency (`referencing` comes with jsonschema 4.23.0).

### T-11: Findings of the fifth Verify run (F-19, F-20, F-21)
- Implements: REQ-SLY-013 (one depth limit of 200 levels for every table, F-20) and REQ-SLY-014 (a document that contains itself is refused within one second, F-19); F-21 is a missing comment line
- Tests to turn green: new tests in `tests/test_storage.py` that fail first (unprotected; TC-SLY-012 and TC-SLY-013): a document nested 200 levels is stored as version 1, nested 201, 600 and 990 levels is refused as `StorageError` `invalid` and nothing is stored, for `graph_nodes` (rule `schema_break`, detail `data`) and for a table that is not a graph table (rule `schema`, detail `nested too deep`); a list that contains itself, a dict that contains itself twice (`d["a"] = d; d["b"] = d`) and the same as the value of a graph node are refused as `StorageError` within one second (the test runs `put` in a thread and fails when it does not finish in time, so a hang cannot stall the suite); on the file backend, and on PostgreSQL in `tests/test_storage_postgres.py` through the shared `StorageBehaviour`. F-21: the Given/When/Then comments of `test_a_local_reference_still_works` in `tests/test_graph_record_checks.py`, so `test_doc_check` is clean
- Touches: `storage.py` (`_unstorable` counts the depth with the document as level 1 and refuses more than 200 levels for every table; it keeps the containers on the current path and refuses a container that contains itself, walking each shared container once so that a document that names the same object many times cannot make the check exponential; the existing `RecursionError` catches in `validate` and `put` can stay as a last guard); `tests/test_storage.py`, `tests/test_storage_postgres.py`, `tests/test_graph_record_checks.py`
- Must not touch: protected material, `graph_tables.py` (its 200-level rule is REQ-GTB-027 and stays), `contracts/`, `storage_postgres.py`, `storage_files.py`, `storage_copy.py`
- Depends on: T-10; A-100 installed
- Done when: the listed tests are green and all other tests unchanged (the contract suites with no skip, the acceptance tests of the goal, TC-GTB-014 with N = 1000, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, 500 node and 500 edge records within 500 ms), `test_doc_check` clean on the goal's test files
- Notes: the read side (`Storage.get` of a stored document nested about 480 levels on a deep call stack) is older behaviour and not part of this task; F-13(a), F-18, F-07 and F-08 stay accepted. No new part, interface or dependency.

### T-12: Size of a document (F-22)
- Implements: REQ-GTB-028 (Graph tables) and REQ-SLY-015 (Storage layer): more than 100,000 values, counting a value once for every path that reaches it, is refused
- Tests to turn green: TC-GTB-029 (`tests/acceptance/test_graph_document_size.py`); the real side of TC-IF-301-24 (`test_a_record_with_too_many_values_is_a_schema_break_real`); new tests in `tests/test_storage.py` that fail first (unprotected; TC-SLY-014): a task document `{"text": "t", "numbers": [...]}` with 99,997 numbers and one with 99,998 numbers (100,000 and 100,001 values: the document, the text and the list count 3; documents of the tables other than graph tables are mappings) (the first is stored, the second refused as `StorageError` `invalid`, rule `schema`, detail `too large`), a data node whose value is a list of 99,995 and of 99,996 numbers for `graph_nodes` (stored / refused `schema_break`, `data`), and a document that names the same child twice on 30 levels is refused within one second for both kinds of table (the test runs `put` in a thread, so a hang cannot stall the suite); on the file backend, and on PostgreSQL through the shared `StorageBehaviour`. The T-11 test that calls `refuse_unstorable` on the 2**30-path document must now expect the refusal `too large` and still finish within a second
- Touches: `storage.py` (`_unstorable` counts the values with every path counted, memoising the count of each shared container and stopping at 100,001, so a shared structure is refused at once; the size check runs for every table, also for the graph tables whose depth check stays with `check_record`, so `check_record` never sees an expanded structure through `Storage.put`); `graph_tables.py` (`_too_deep` also counts the values and stops at 100,001, so `check_record` called directly, as the Workflow management does, refuses such a record as `schema_break` naming `data` at once; the order of the depth and size checks does not change the answer); `tests/test_storage.py`
- Must not touch: protected material, `contracts/` (A-102 changed IF-301 already), `storage_postgres.py`, `storage_files.py`, `storage_copy.py`
- Depends on: T-11; A-102 installed
- Done when: the listed tests are green and all other tests unchanged (the contract suites with no skip, the acceptance tests of the goal, TC-GTB-014 with N = 1000, `test_storage.py`, `test_storage_postgres.py` on a throwaway postgres:16, 500 node and 500 edge records within 500 ms, `test_doc_check` clean on the goal's test files)
- Notes: 100,000 values is about 190 times the largest stored document in the repository (529 values); the count includes the record or document itself, every object and list, and every scalar. A document nested deeper than 200 levels or containing itself is refused as before. F-18, F-13(a), F-07 and F-08 stay accepted. No new part, interface or dependency.

## Order and checks
T-01 first (everything else needs the record checks); T-02, then T-03; T-04 may run beside T-02 and T-03 (it needs only T-01); T-06 after T-04; T-07 after T-06 and the install of A-93; T-08 (context tables) after T-07 and T-09 (small fixes) after T-08, both after the install of A-98; T-10 after T-09; T-11 after T-10 and the install of A-100; T-12 after T-11 and the install of A-102. Between the install of A-98 and T-08 the six-table assertions of three protected checks are red on purpose. After each task: `python tests/acceptance/test_graph_records.py` and `IF301_V2_REAL=1 python tests/acceptance/contract/test_if_301_v2_graph_tables.py -k _real` for the progress of the red tests, `python tests/test_graph_tables.py` and `python tests/test_storage.py` for the old behaviour, then the stage 1 and 2 steps of `stages.yaml`. Before the hand-over: `trace_check`, `goal_check`, `req_graph`.

## Size check (splitting)
23 requirements and one interface, twelve tasks of one session each, two nodes (N-3.2 in T-01 to T-03 and T-05 to T-10 and T-12, N-3.1 in T-04, T-06, T-08, T-10, T-11 and T-12); this is over the guideline of about 8 tasks; a split into a follow-on goal for the context tables was offered and the owner decided on 2026-11-08 to keep all in G-V2.STORE. The leaf limit (about 8 tasks, 3 interfaces) is kept; no split is suggested, the goal record's "keep together" stands. T-04 is the only change outside N-3.2 and touches one file.

## Decided by the owner (2026-11-07)
1. A-90 (contract text of IF-301 v2 with its Clarifications, installed) is approved, and A-91 in principle: T-05 removes the skip of the v2 suite by an amendment the owner installs; the agent drafts its script for a look-only review when T-05 comes.
2. The cut of five tasks stands.
3. `requirements.txt` gets `jsonschema==4.23.0` in T-01 (D-187; MODEL's `networkx` line merges as a union).
4. `storage_copy.py` is not changed in T-04; CONVERT decides about copying the record tables.
5. A-92 (record under its own ID, REQ-GTB-021, TC-GTB-022, the optional `record_id` of `check_record` in IF-301 v2) is approved and installed; T-06 is added to this plan on the owner's word (2026-11-07).
6. A-93 (fixed fields of a node, REQ-GTB-022, TC-GTB-023, TC-IF-301-21, IF-301 v2) follows the decision of F-01 on 2026-11-07, which the owner delegated to the reviewer and may overrule; T-07 is added to this plan on that decision, the owner installs the amendment after a look-only review.
7. A-98 (context graph tables `context_nodes` and `context_edges`, the rule for input that cannot be checked, REQ-GTB-023 to 027, TC-GTB-024 to 028, TC-IF-301-22 and -23, IF-301 v2) follows the owner's decisions of 2026-11-08 on F-02 and F-09: separate tables, symmetric (`context_edges` too), the caller checks the categories, `schema_break` for input that cannot be checked; F-03, F-11, F-06 and F-13(b) are fixed now (T-09), F-13(a) is accepted, F-07 and F-08 are routed to CONVERT.
8. After the fourth Verify run (2026-11-08): T-10 fixes F-15 (RecursionError at the Storage entry), adds the boundary tests of F-16 and closes the remote references of F-17; F-18 is accepted and routed to the context-graph writer goal.
9. After the fifth Verify run (2026-11-08): the owner decided to add one Storage requirement for all tables (REQ-SLY-013, depth 200) and one for a document that contains itself (REQ-SLY-014, F-19), A-100 and T-11; the plausibility ratings of the two requirements follow in A-101.
10. After T-11 (2026-11-08): the owner decided to add a size limit of 100,000 values for every table (REQ-SLY-015) and for the record checks (REQ-GTB-028), A-102 and T-12 (F-22); the plausibility ratings of the two requirements follow in A-103.
