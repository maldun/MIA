# Implementation log: G-V2.STORE (graph records, storage)

Goal: G-V2.STORE   Line of work: goal/v2.store   Supervision: supervised (accepted by Stefan Reiterer)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Record tables, types and record checks | done | 0f1543e | `test_graph_records.py`: TC-GTB-006, 011, 013, 016, 017, 018, 019, 020, 021 (the 6 left are T-02 and T-03); v2 contract suite real side (`IF301_V2_REAL=1`): TC-IF-301-05, 06, 09, 10, 13, 14, 15, 18, 19; new `tests/test_graph_record_checks.py` (4); the v1 IF-301, IF-102 and IF-203 suites and `tests/test_graph_tables.py`, `test_storage.py` unchanged green | 500 + 500 records: about 7 ms (bound 500 ms). Reported, not verified. |
| T-02 Classes from type IDs | done | ef3295e | `test_graph_records.py`: TC-GTB-007, 008, 009, 010, 014 (N = 1000, and once N = 5000: 0 failures); v2 contract suite real side: TC-IF-301-07, 08, 16, 18; new `tests/test_graph_record_objects.py` (5); only TC-GTB-015 and TC-IF-301-11, 12, 17 (T-03) are still red; old suites unchanged green | Reported, not verified. |
| T-03 Document form both ways | done | fd9ee76 | `test_graph_records.py`: all 20 (TC-GTB-015 with the unchanged v1 IF-301 and v0 IF-203 suites and their recorded hashes); v2 contract suite real side: all 15; new `tests/test_graph_document_form.py` (4); old suites unchanged green; MODEL's `test_graph_model.py` (10 failures) and `test_graph_run.py` (4) are red on master as well | Reported, not verified. |
| T-04 The Storage layer takes the four tables | done | 2728b06 | 3 new tests in `tests/test_storage.py` (TC-GTB-013, 016/006/018/019, 017, 020, 021 on `Storage`), on the file backend and on a throwaway postgres:16 (`tests/test_storage_postgres.py`: 29 tests OK, `tools/contract_postgres.sh`: IF-102 suite OK); IF-102 real side, IF-301 v1, IF-203 v0 and the old storage tests unchanged green; full unit suite: the same 3 failures and 61 errors as the baseline, by name | Run with a python from a throwaway venv (`requirements-db.txt` plus `jsonschema==4.23.0`) because the host python has no psycopg. Reported, not verified. |
| T-05 Integration: the real side of the suite without skip | done | 2d21f44 | A-91 installed by the owner: the v2 suite 30 tests OK on both sides, no skip; v1 suite, IF-203 v0 suite and TC-GTB-015 OK (reported with the system python that has jsonschema; the owner's shell needed `pip install -r requirements.txt` first) | Reported, not verified. |
| T-06 Record under its own ID | done | 4d0690d | TC-GTB-022 (`test_graph_record_identity.py`) and the real side of TC-IF-301-20 (green after A-92; the whole v2 suite OK), new unit test in `tests/test_storage.py` for the four tables (red first: 4 failures, then green); file backend and a throwaway postgres:16 (`test_storage_postgres.py` OK, `contract_postgres.sh` OK); `test_graph_records.py`, the IF-301 v1, IF-102 and IF-203 v0 suites and all unit tests of this goal unchanged green; full unit suite: the same 3 failures and 61 errors as the baseline, by name | Reported, not verified. |
| T-07 Fixed fields of a node | done | 27cba26 | TC-GTB-023 (`test_graph_node_fields.py`, 2 tests) and the real side of TC-IF-301-21 (v2 suite 34 tests OK, mock and real); 3 new unit tests in `tests/test_graph_record_checks.py` (red first: 2 failures, 1 error, the record was accepted; then 7 OK); `test_graph_records.py` (20, TC-GTB-014 N = 1000), `test_graph_record_identity.py`, `test_graph_tables.py`, `test_storage.py` (22), `test_graph_record_objects.py`, `test_graph_document_form.py` and the IF-301 v1 suite unchanged green. `test_storage_postgres.py` not run (no psycopg 3 in this environment, 2 skipped; installing it would be a new dependency step). | Reported, not verified. |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| NaN and infinity passed the schema bounds of `stop.max_seconds` (v1 refuses them, A-60) | T-01 | `tests/test_graph_record_checks.py` `test_a_number_that_is_not_finite_breaks_the_schema` (red first, then fixed) |
| An explicit JSON null and an absent optional field (`value`, `task`) are the same node: both give None and `to_record` leaves the field out | T-02 | `tests/test_graph_record_objects.py` `test_an_absent_value_and_a_null_value_are_the_same_node` |
| Adding `jsonschema` to `requirements.txt` invalidated the pip layer of the image cache: `test_delivery_on_stack` (builds with `--network none`, D-148) failed in setUpClass; `test_chat_views_browser` failed because its mock server runs the current source in `localhost/mia:latest`, which had no jsonschema | T-01 | both tests, green again after the image was rebuilt (below) |

## Plan amendments
### A-91: the real side of the IF-301 v2 suite without a skip (IF-301)
- Found in: T-05 (planned)
- Decision: the environment switch and the skip of the real side are removed by the owner's script
- Kind: amendment
- Status: approved in principle 2026-11-07, installed (`2d21f44`)
- Approved by: Stefan Reiterer, 2026-11-07

### A-92: a graph record is stored under its own ID (REQ-GTB-021, TC-GTB-022, TR-GTB-001, IF-301 v2)
- Found in: T-04 (a record under another record ID was accepted)
- Decision: new requirement, check, and the optional `record_id` of `check_record`; task T-06 added to the plan
- Kind: amendment
- Status: approved and installed 2026-11-07 (`d80fdb5`, `d67e7d9`)
- Approved by: Stefan Reiterer, 2026-11-07

### A-93: a node has only the fields of its type (REQ-GTB-022, TC-GTB-023, TC-IF-301-21, IF-301 v2)
- Found in: Verify of G-V2.STORE (F-01: an extra field in a node broke `to_object` with TypeError)
- Decision: the three node schemas are closed (`additionalProperties` false); `_broken_path` orders by path text and names an extra field by its own key; task T-07
- Kind: amendment
- Status: installed by the owner 2026-11-08 after a look-only review, implemented in T-07; the review of REQ-GTB-022, TC-GTB-023 and TR-GTB-001 is still open (Draft)
- Approved by: open (the owner delegated the F-01 choice to the reviewer on 2026-11-07 and may overrule it)

## Stop conditions hit
| Date | Task | Condition | Escalated to | Outcome |
|---|---|---|---|---|
| 2026-11-07 | T-01 | a dependency change breaks two stage 2/3 tests until the image is rebuilt with network | Stefan Reiterer | owner: "change the containers accordingly"; image rebuilt, see Decisions |

## Unspecified behavior (decisions no requirement covers)
| Decision | Where in code | Proposed requirement or amendment |
|---|---|---|
| null and absent are not told apart for `value` and `task` | `graph_tables.to_record` | none needed: JSON null carries no meaning for these fields; say so in the next IF-301 text revision |
| A graph record is written under a record ID that differs from the `id` inside it (`put("graph_nodes", "x", {"id": "y", ...})`): accepted; a header pins by the `id` inside, the storage finds by the record ID | `storage.py` `put` | closed: A-92 (REQ-GTB-021, TC-GTB-022, IF-301 `record_id`), implemented in T-06 |
| NaN and infinity in a record are `schema_break` with the path of the number | `graph_tables._non_finite_path` | none needed: same rule as v1 (A-60) and the Storage layer's `refuse_unstorable`; mention in the next IF-301 text revision |

## Decisions
- Containers (owner, 2026-11-07): `deploy/Containerfile` needs no change (it installs `requirements.txt`). Rebuilt once with network (`podman build --pull=never -f deploy/Containerfile .`), so the pip layer with `jsonschema==4.23.0` is in the cache, and `localhost/mia:latest` now points to that build (image `c58b66d1b7ea`). Before: `latest` and `v0.1.0` were both image `8217ecd0ccf8`; `v0.1.0` still is. Undo: `podman tag localhost/mia:v0.1.0 localhost/mia:latest`. No MIA container was running. A later change of `requirements.txt` (MODEL's `networkx`) needs the same one-time networked build.
- Full unit suite after T-01 (`python -m unittest discover -s tests -q`): 3 failures and 61 errors as in the baseline of 2026-11-07, the two image tests green after the rebuild.
