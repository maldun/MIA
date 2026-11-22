# A-168: CORE task scopes after T-01; the tests A-167 missed (G-V4.GRAPHSTORE.CORE)

Status: **approved by the owner, 2026-11-22 (D-412)**; the staging copies and `tools/apply_amendment_a168.sh` follow; not installed.

## Finding (T-01, implementation log F-1 and F-2)
The rule `unscoped_id` of T-01 (`graph_tables.py`, REQ-GTB-029 to 031) is right, but the plan assumed "all other tests unchanged" after every task. A-167 measured its impact only on the three files it rewrote. The whole suite, measured 2026-11-22:

| State | Unit suite (`discover -s tests`) | Acceptance scripts |
|---|---|---|
| `goal/v4` HEAD (a16465e4) | 2499 tests, OK | CORE scripts red as planned; all others as before |
| HEAD + T-01 code | 44 failures, 33 errors | + 4 protected scripts red (below) |
| HEAD + T-01 + prototype `graph_model.py` (about the end state of T-02 to T-04) | 42 failures, 27 errors | every CORE script green; the same 4 protected scripts red |

So T-02 to T-04 fix almost none of it: the failures are plain IDs in the tests' own data, not product behaviour.

- **Protected** (need this amendment): `tests/acceptance/test_graph_context_tables.py` (TC-GTB-024..028), `test_graph_document_size.py` (TC-GTB-029), `test_graph_node_fields.py` (TC-GTB-023), `test_graph_record_identity.py` (TC-GTB-022). Identical in the prototype.
- **Unprotected**: `tests/test_storage.py` (19), `tests/test_storage_postgres.py` (20), `tests/test_storage_copy_semantics.py` (11), `tests/test_graph_record_objects.py` (7), `tests/test_skill_record_storage.py` (10 per backend; 4 per backend go through `graph_model` and turn green with T-02/T-03, 6 per backend write or compare plain-ID records directly).

## Proposal
1. **T-01 stays as it is** (owner, 2026-11-22). Its "Done when" becomes: the listed tests green; the known red tests listed in the implementation log (the four protected scripts until A-168 is installed, the unprotected modules until T-01b, saves through `graph_model` until T-02).
2. **Protected tests**: scoped copies of the four scripts (same tests, rules and expected results; IDs `g/<local>`, in headers `<header id>/<local>`), installed by the owner with `tools/apply_amendment_a168.sh` like A-167. One case needs care: in TC-GTB-027 the workflow header `h2` names the stored context node `h2/c1`, so it still checks `unknown_member` (wrong table) and not `unscoped_id`; the context header `h1` names `h1/c1`, `h1/c9`.
3. **New task T-01b, before T-02** (owner, 2026-11-22): scoped IDs in the unprotected unit modules above, the six direct-record checks of `test_skill_record_storage.py` per backend included. Test data only, same assertions; touches no product file. Done when the unit suite has no failure outside the four `graph_model` checks of `test_skill_record_storage.py` per backend.
4. **T-02 to T-05**: "all other tests unchanged" is replaced by a named regression set: the unit suite and every acceptance script green except the CORE checks of later tasks; the four `graph_model` checks of `test_skill_record_storage.py` green at the latest after T-03 (each task logs which it turned green).
5. **The list "After every task ... stay green"** in `plan.md` drops `tests/test_skill_record_storage.py` until T-03, and gains the four scripts of point 2 from the installation of A-168 on.
6. **Rule for later amendments that change a check** (lesson): measure the impact on the whole suite (`discover -s tests` and every acceptance script) against a clean checkout, not only on the rewritten files.

## Why not the alternatives
- Merge T-01 into T-02: does not touch the four protected scripts or the unit modules (no `graph_model` in them); only shortens the time where saves are refused.
- Relax the rule (scope only in the Workflow management): rejected in A-167 (FR-60: no record may belong to no graph).
