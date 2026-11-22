# Implementation log: G-V4.GRAPHSTORE.CORE

## T-01: Scoped IDs in the Graph tables
- Status: done, committed with known reds (owner, 2026-11-22, D-412); F-1 and F-2 handled by A-168 and the new task T-01b
- Requirements: REQ-GTB-029, REQ-GTB-030, REQ-GTB-031
- Done: `graph_tables.py`: `SCOPED`, `scoped`, `split_scoped`; in `_check` the `unscoped_id` refusal for the four step and connection tables, after the identity checks (D-409: the empty ID and a differing `record_id` stay `record_identity`); `_check_members` takes the header's own ID and refuses a member of another graph as `unscoped_id` before `unknown_member`, with and without `stored`. Reused from the prototype (R1, lines 159 to 224) with shorter docstrings.
- Unit tests (new, `tests/test_graph_tables.py`, class `ScopedIds`): split at the first slash, empty parts; plain IDs in the four tables, graphs and skills unscoped; empty ID and differing `record_id` stay `record_identity`; header members of another graph, plain, and a prefix look-alike (`wf10/` for `wf1`), checked before `unknown_member`.
- Tests reported green (feedback, not verification): `tests/test_graph_tables.py` 8 of 8; TC-GTB-033, TC-GTB-034, TC-GTB-035 in `tests/acceptance/test_core_scoped_ids.py`; `tests/acceptance/contract/test_if_301_v2_graph_tables.py` 44 of 44 (on HEAD 2 failures: the real side of TC-IF-301-25 and -26, now green); `test_if_301_graph_tables.py` 8 of 8.
- Still red, as planned: TC-WFM-178, 162, 163 (T-02, T-03); the other CORE scripts. TC-WFM-178 has one more failure than at the red commit: the twin save under `lookup` is now refused (`unscoped_id` naming `query`), because `graph_model.save_graph` still writes plain step IDs until T-02 scopes them. Between T-01 and T-02 no workflow graph can be saved through the Workflow management on `goal/v4`.
- Findings:
  - F-1 (needs a protected change, stop): A-167 rewrote the v2 tests that wrote plain IDs, but missed four protected acceptance scripts. They are green on HEAD and red with the T-01 code, each refused as `unscoped_id` before the rule it checks:
    - `tests/acceptance/test_graph_context_tables.py` (TC-GTB-024..028): 6 failures, 4 errors
    - `tests/acceptance/test_graph_document_size.py` (TC-GTB-029): 1 failure
    - `tests/acceptance/test_graph_node_fields.py` (TC-GTB-023): 5 errors
    - `tests/acceptance/test_graph_record_identity.py` (TC-GTB-022): 1 error
    The four files are the same in the prototype, so the prototype had the same gap. Proposed A-168: the same tests with scoped IDs (`g/d1`, `h1/c1`, ...), same rules and expected results, installed by `tools/apply_amendment_a168.sh` like A-167. One case needs care: in TC-GTB-027 the workflow header `h2` must name a context node `h2/c1` (stored), so that it still checks `unknown_member` (wrong table) and not `unscoped_id`. Staging the copies was not allowed in this session; waiting for the owner.
  - F-2 (outside the task's bounds, stop): `unittest discover -s tests` on a clean HEAD checkout: 2499 tests, OK. With the T-01 code: 2507 tests, 44 failures and 33 errors, all `unscoped_id` on plain IDs in unprotected unit modules not listed under Touches: `tests/test_storage.py` and `tests/test_storage_postgres.py` (graph records with IDs `n`, `n1`, `d0`, ...), `tests/test_storage_copy_semantics.py`, `tests/test_graph_record_objects.py` (test data only), and `tests/test_skill_record_storage.py` (saves through `graph_model`, so mostly T-02). The plan's "all other tests unchanged" cannot hold for T-01 alone.
- Other acceptance scripts on the graph tables, HEAD against T-01: unchanged (`test_graph_model`, `test_graph_records`, `test_graph_order`, `test_graph_run`, `test_graph_run_stages`, `test_pipeline_graph`, `test_skill_binding`); CORE scripts fewer failures or the same.

## A-168: task cut after T-01 (plan amendment)
- Status: approved by the owner, 2026-11-22 (D-412); staging copies of the four protected scripts and `tools/apply_amendment_a168.sh` to follow; not installed
- Measured basis (feedback, not verification): a clean checkout of HEAD, HEAD + T-01, and HEAD + T-01 + the prototype's `graph_model.py` (about the end state of T-02 to T-04): with the prototype code every CORE script is green and the same four protected scripts and the same unit modules stay red, so the reds are test data, not product behaviour. Numbers in `specs/mia/amendments/A-168-note.md`.
- Changes to `plan.md`: new task T-01b before T-02; "all other tests unchanged" replaced by a named regression set with known reds; `tests/test_skill_record_storage.py` in the always-green list from T-03 on.
