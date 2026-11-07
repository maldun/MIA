# Verification report: G-V2.STORE (graph records, storage)

**Goal:** G-V2.STORE (subgoal of G-V2), supervised, accepted by Stefan Reiterer
**Branch:** goal/v2.store @ 5f42018   **Parent line of work:** goal/v2 (the branch does not exist in this repository; compared with `master`)   **Plan baseline:** `plan-baseline-it2-store` (827957c)
**Date:** 2026-11-07   **Reviewers:** (human) pending, Stefan Reiterer; (AI) Claude Sonnet 5.5, a fresh session that never saw the implementation chat

Everything below was run by the reviewer on a clean checkout of HEAD (`git archive`, no `.git`, no untracked files), with a new Python 3.12 venv from `requirements.txt` plus `requirements-db.txt` (jsonschema 4.23.0, psycopg 3.3.8). Scratch material (mutants, probes, logs) is in `/home/maldun/.claude-work/jobs/d597730b/tmp/`; nothing in the worktree was changed except this report.

## Verdict
**Not verified** (proposal; updated after the owner's answers of 2026-11-07, see "Owner decisions"). Nothing found is a high-severity defect, and every requirement of the scope has a green check. The verdict is "not verified" for one reason of the rules: **a protected file, `specs/mia/plausibility.yaml`, differs from the tag far beyond what A-92 states (F-05)**, and the owner has to say whether that was intended. In addition there is one real defect (F-01: a stored node can fail to be read back) and two specification gaps (F-01, F-02) that are one small decision each. With F-05 confirmed by the owner and F-01 decided, the verdict would be "Verified with accepted deviations" for the rest (F-02 to F-10, all low or latent).

Findings: **0 high, 3 medium (F-01, F-02, F-05), 7 low (F-03, F-04, F-06 to F-10)**. 0 blockers of the merge by themselves, apart from the F-05 stop condition.

## Automated checks (clean environment; no CI run exists for this branch, so these are reviewer runs, not CI evidence)
| Check | Result |
|---|---|
| Stage 0/1 mechanical: `check_sysml_model.py .`, `tools/check_sysml.sh specs/mia/architecture.sysml` (49 s), `decomp_check.py`, `quality_check.py`, `node --test tests/js/*.test.mjs` | all OK (SysML: 1 file, 0 errors, 0 warnings; decomposition: only INFO lines; quality: all nine characteristics covered; JS 161/161) |
| Unit suite `python -m unittest discover -s tests -v` on HEAD and, the same way, on the tag checkout | HEAD: 2064 tests, 0 failures, 1 error (`test_tailscale.ScriptTest.test_without_tailscale_it_says_how_to_install`), 4 skipped, 1 expected failure. Tag: 2039 tests, the same 1 error, 5 skipped. **No difference by test name**; 25 tests are new. (The host's known baseline of 3 failures and 61 errors comes from missing libraries in the host python; in the clean venv they are gone, the one tailscale error is the same on both sides and not caused by the branch.) |
| Contract suites, mock side (stage 1) | 126 tests OK |
| Contract suites, real side (stage 2) `-k _real` | 126 tests OK, 18 skipped, all of them IF-101, 103, 201, 404, 405 (real model server, web, other nodes); **none is IF-301 or IF-102**. The IF-301 v2 suite alone: 32 tests (16 cases, both sides), no skip |
| Acceptance, one process per file (18 files) | 16 green. `test_graph_model.py` (10 failures) and `test_graph_run.py` (4) are red: **identical red at the tag**, MODEL's pending Implement (known open point) |
| PostgreSQL: `tests/test_storage_postgres.py` with the venv python; `MIA_DB_PYTHON=<venv python> bash tools/contract_postgres.sh` (postgres:16, local image) | 30 tests OK (the T-06 test runs there); IF-102 real suite 11 tests OK, none skipped |
| Protected material vs. baseline | see "Protected material" below: only A-91 and A-92 (+ one out-of-scope change, F-05) |
| Traceability: `trace_check.py --spec-dir specs/mia --tests-dir tests` | 518 errors (517 known + 1 new). **The one new error names GTB: "TC-GTB-022 scenario defined 2 times"** (F-04). No other error for GTB-005..021 or IF-301 v2 |
| Goals: `goal_check.py --spec-dir specs/mia` and with `--parent-ref master` | 0 errors, 0 warnings (`--parent-ref goal/v2` fails with GL5: no such branch; G-V2.STORE has no frozen requirement) |
| `req_graph.py --tree --goal G-V2.STORE` | every REQ-GTB-005..021 has its check (TC-GTB-016, 006..014, 015, 017..022) |
| `req_lint.py` (N-3.2 requirements) | GTB-005..021: only the L1-SUBJECT warning that the text does not name "Persistence", the same for all older requirements (style, not for this goal). The 5 errors (L0-GROUP) are IF-301 and REQ-GTB-001..004 of v1, outside this goal |
| `req_plausibility.py` | 0 errors; GTB-005..021 rated plausible (REQ-GTB-021 by Stefan Reiterer, 2026-11-07) |
| `test_doc_check.py` on the five new or protected test files of this goal (copied to a scratch folder) | 0 errors, 0 warnings |
| Refactoring commits (`refactor_check.py`) | 0 refactor commits, no finding |
| Agent configuration (`agent_config_diff.py`) | no configuration change |
| Statistical checks | TC-GTB-014 (exact criterion, no rate): seeds 1..1000 green in the unit run, **N = 5000 once: OK, 12.3 s**, 0 failures; the "round trip check can fail" case (writer that drops `task`) is green |
| Benchmarks | 500 node + 500 edge records through `check_record`: 13.5 to 15.8 ms in three runs (bound 500 ms; mock 6 ms, implementer 7 ms; plausible: a dictionary walk and a pre-built validator) |
| Static / security | no linter, type checker or SAST is configured (project rule); inspection instead: no `pickle`, `marshal`, `shelve`, `exec`, `eval`, `importlib`, `__import__` in `graph_tables.py` or `storage.py`; a task definition is kept as data (probe with `__import__('os').system('touch …')` as task: kept equal, marker not created). Dependency diff: one new line, `jsonschema==4.23.0` (approved D-187). No secret in the diff |
| Deployable artifact | `podman build --pull=never --network none -f deploy/Containerfile .` from the cache: 7.9 s, 4 cache hits, exit 0; the image has jsonschema 4.23.0; `localhost/mia:latest` is c58b66d1b7ea, `v0.1.0` is 8217ecd0ccf8 (as logged); my scratch tag was removed again. `tests/test_delivery_on_stack.py` 5 tests OK (41 s), `tests/test_chat_views_browser.py` 12 tests OK (47 s) |
| Usability | the tables are an internal interface, nothing people operate; the refusal messages name rule and field/ID (probes below). Not applicable beyond that |
| Documentation | no user-visible change; `CHANGELOG.md` is not changed (T-05 listed it under "Touches" but the plan does not require an entry; the commit step will) |

### Protected material (check A)
`git diff --stat plan-baseline-it2-store..HEAD -- tests/acceptance tests/helpers tests/smoke tests/integration contracts benchmarks eval stages.yaml specs/*/test-requirements.md` shows exactly:
| File | Change | Amendment |
|---|---|---|
| `contracts/IF-301-graph-tables.md` | `record_id` argument, golden 15, decision 12, history row | A-92 |
| `tests/helpers/mocks/if_301_graph_tables_v2.py` | `record_id` in `check_record` | A-92 (the new `if` is written twice, F-04) |
| `tests/helpers/graph_store_standin.py` | `put` passes `record_id` | A-92 |
| `tests/acceptance/contract/test_if_301_v2_graph_tables.py` | skip and environment switch removed (A-91); case TC-IF-301-20 added (A-92; defined twice, F-04) | A-91, A-92 |
| `tests/acceptance/test_graph_record_identity.py` | new, TC-GTB-022 | A-92 |
| N-3.2 `test-requirements.md` | TR-GTB-001 also applies to TC-GTB-022 | A-92 (review-log rows 07589037882d, b9eed201d1c0, d3d0c86173d3, c44f8cf3f707) |
Not in the list and checked separately: `tests/helpers/contract.py`, `tests/acceptance/test_graph_records.py`, smoke, benchmarks, eval, `stages.yaml`: unchanged. **The two old suites are byte-identical to the recorded hashes** (and to the tag): `test_if_301_graph_tables.py` 1d9022ca…606b, `test_if_203_workflow_library.py` 0eb58da6…14c3 (TR-GTB-006). The skips and expected failures in the three GTB acceptance files and the v2 suite: none.
**Outside the list, protected by the workflow's rule (`plausibility.yaml`): changed by commit d80fdb5 far beyond A-92: finding F-05.**

## Verification matrix (REQ-GTB-005 to REQ-GTB-021)
All commands on the clean checkout; "suite" = `tests/acceptance/contract/test_if_301_v2_graph_tables.py` (32 tests green). "TA" = `tests/acceptance/test_graph_records.py` (20 tests green, 2.9 s). Code read against the requirement text, not only the test.

| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-GTB-005 Node records | Test | TC-GTB-016 (TA `test_a_node_of_each_type_is_stored_as_a_record`); on the real `Storage`: `tests/test_storage.py::test_the_graph_records_are_stored_as_versions_and_never_deleted`, file backend and postgres:16. Code: `check_record` + `Storage.put` | met | yes |
| REQ-GTB-006 Edge records | Test | TC-GTB-006 (TA); same Storage test | met | yes |
| REQ-GTB-007 transform toolbox ID | Test | TC-GTB-007 (TA); `to_record`/`to_object` read | met | yes |
| REQ-GTB-008 master definition and stop | Test | TC-GTB-008 (TA, marker file); my probe: a task with `__import__('os').system(…)` stays data, no marker | met | yes |
| REQ-GTB-009 class from type ID | Test | TC-GTB-009 (TA), suite `to_object` cases. **But see F-01**: a stored node with an additional field in its JSON field raises in `to_object` | met for the tested shapes; F-01 for others | yes |
| REQ-GTB-010 unknown type refused | Test | TC-GTB-010 (TA), written and read; Storage test `test_a_refused_graph_edit_changes_nothing` | met | yes |
| REQ-GTB-011 types as schemas | Test | TC-GTB-011 + path of the pinned validator (TA); M10, M30 to M32 killed | met | yes |
| REQ-GTB-012 no language serialisation | Inspection | TC-GTB-012 (TA); my inspection: no such import or dynamic import in `graph_tables.py`/`storage.py`; TR-GTB-005 shown below | met | yes |
| REQ-GTB-013 versions kept | Test | TC-GTB-013 (TA); Storage test (version 1 unchanged, delete is `immutable` for all four tables); M13, M18 killed | met | yes |
| REQ-GTB-014 rebuilt equals stored | Test | TC-GTB-014: N = 1000 (default) and **N = 5000, 0 failures**; M03, M19 (redo) see table. Fields outside the schema are not generated: F-01 | met for generated graphs | yes (2.9 s for 1000 seeds) |
| REQ-GTB-015 document form | Test | TC-GTB-015 (TA) with the two old suites at their hashes; suite cases 11, 12, 17; `tests/test_graph_document_form.py`; M04, M17, M27, M28 killed | met | yes |
| REQ-GTB-016 refused edit changes nothing | Test | TC-GTB-017 (TA); Storage test `refusal_of` compares all versions before and after; code: `_check_graph_record` runs before the version number is taken; M36 (notice before the check) killed. My probe: a refused write left `ids` and notices unchanged | met | yes |
| REQ-GTB-017 header with pinned members | Test | TC-GTB-018 (TA) | met | yes |
| REQ-GTB-018 skill table | Test | TC-GTB-019 (TA); M20, M29 killed | met | yes |
| REQ-GTB-019 header names stored members | Test | TC-GTB-020 (TA); Storage test. **Mutant M25 (only the first member checked) survives**: F-06 | met; test gap F-06 | yes |
| REQ-GTB-020 edge names stored nodes | Test | TC-GTB-021 (TA); Storage test; M15, M26 killed | met | yes |
| REQ-GTB-021 record under its own ID | Test | TC-GTB-022 (`test_graph_record_identity.py`, through the stand-in); suite TC-IF-301-20 both sides; Storage unit test for all four tables, file backend and postgres. M06, M08, M33 killed | met | yes |
| IF-301 v2 (contract) | Test | suite 32/32; code vs. contract text in "Code against the contract" below | met, with F-01/F-08/F-09 for undefined inputs | yes |

17 of 17 requirements and the interface have evidence, 17 green.

## Test requirements (M41)
Source of all six: product-specific (no catalog adopted, `–`).
| Test requirement | Kind | Applies to | Credibility aspect | Verified by | Met? (evidence) |
|---|---|---|---|---|---|
| TR-GTB-001 exact values by hand | unit | TC-GTB-016, 006..011, 013, 017..022 | reference accuracy | known answer | **met.** Read the expected values of TA, the suite, the three implementer test files and the new `test_storage.py` tests: all literals written into the test (`{"version": 1}`, `("unknown_type", "x.unknown")`, …), none computed by the code under test |
| TR-GTB-002 the storage under the checks passes IF-102 | setup | TC-GTB-016, 006, 013, 014, 018, 019 | stand-in fidelity | contract suite | **met**, with a remark: `test_the_storage_standin_passes_the_if_102_suite` (TA) runs the 11 IF-102 `_mock` cases with `GraphStoreStandIn` and is green; the stand-in calls the real `graph_tables.check_record`. It is a test in the same file, not a gate that runs *before* the others; accepted. IF-102 itself also green on the real file backend and on postgres:16 (11 tests, none skipped). The stand-in is `StorageMock` and **not** the real `Storage`, so TA says nothing about `storage.py`; that is covered by the implementer's unit tests (they kill seven Storage mutants, M07, M08, M23, M35, M36, M33, M26), which are unprotected: note F-06 |
| TR-GTB-003 errors from the pinned validator | setup | TC-GTB-011, 010 | reference accuracy | known answer | **met.** jsonschema 4.23.0 in the clean venv (as in `requirements.txt`); `test_the_paths_are_those_of_the_pinned_validator` green; the real code names a missing key by the key (`graph_tables._broken_path`) |
| TR-GTB-004 seeds 1 to N, broken writer is caught | setup | TC-GTB-014 | repetitions and seeds | property test with a broken writer | **met.** `TC_GTB_014_N` parameter, default 1000; seeds `range(1, n + 1)`; ran N = 5000 once: OK, 0 failures; `test_the_round_trip_check_can_fail` (writer without `task`) green and my own mutant M03 (`to_record` drops `task`) is killed; sizes 1..20 nodes and up to 40 edges checked by the test over seeds 1..200 |
| TR-GTB-005 the import check can fail | setup | TC-GTB-012 | validity domain | mutation | **met.** Scratch copy 1: `import pickle` inside `record_definitions()` → TC-GTB-012 and its sibling fail, naming file, line and module. Scratch copy 2: a new sibling module `graph_types.py` with `import shelve`, imported by `graph_tables.py` → fails (the check follows local imports). A dynamic `__import__("pickle")` is not seen: accepted in the text of TR-GTB-005 |
| TR-GTB-006 the old suites are the old ones | setup | TC-GTB-015 | reference accuracy | contract suite | **met.** sha256 of both files equal to the recorded value and to the tag (0 commits touch them since the tag); TC-GTB-015 green |

## Mutation check (D, my own, in a scratch copy only)
Runner: `/home/maldun/.claude-work/jobs/d597730b/tmp/mut/run.py` and `run2.py`; each mutant runs nine files one process each: TA, the identity test, the v2 suite with `IF301_V2_REAL=1`, the v1 suite, the three implementer test files of this goal, `test_storage.py`, `test_graph_tables.py`.
| # | Mutant | Result | Caught by |
|---|---|---|---|
| M01 | `check_record` returns None | killed | TA, identity, suite, record_checks, storage |
| M02 | `types()` loses `master` | killed | TA, suite |
| M03 | `to_record` drops `task` | killed | TA, suite |
| M04 | `to_document` maps master to process | killed | TA, suite |
| M05 | `check_record` ignores `stored` | killed | TA, suite, storage |
| M06 | `check_record` ignores `record_id` | killed | identity, suite, storage |
| M07 | `Storage.put` skips the graph check | killed | `test_storage.py` only |
| M08 | `Storage.put` passes no `record_id` | killed | `test_storage.py` only (the protected TC-GTB-022 goes through the stand-in and cannot see it) |
| M09 | `Storage.validate` skips the record tables | **survived** | – (the call in `put` covers the same ground; only the path of `storage_copy` uses `validate` alone, F-06/F-07) |
| M10 | schema_break path always `data` | killed | TA, suite, record_checks |
| M11 | `unknown_type` detail wrong | killed | TA, suite, record_checks, storage |
| M12 | NaN/inf no longer refused | killed | record_checks |
| M13 | record tables not versioned | killed | TA, identity, suite |
| M14 | header members unchecked | killed | TA, suite, storage |
| M15 | `unknown_endpoint` removed | killed | TA, suite, storage |
| M16 | `from_document` edge IDs start at e0 | killed | document_form |
| M17 | `to_document` maps transform to data | killed | TA, suite, document_form |
| M18 | record tables deletable | killed | TA, identity, suite, storage |
| M19 | `to_record` without `setdefault("parameters")` (first version left an empty `if` body, an invalid mutant; redone with `pass`) | survived | – equivalent mutant: `DataNode.parameters` already defaults to `{}`, so the line is redundant |
| M20 | skill needs no command | killed | TA, suite |
| M21 | `max_repetitions` minimum 0 | killed | suite |
| M22 | duplicate header member allowed | killed | TA, storage |
| M23 | Storage builds `stored` without nodes | killed | storage |
| M24 | `to_object`/check accepts unknown type | killed | TA, suite, record_checks, storage |
| M25 | header: only the first member's version checked | **survived** | – test gap F-06 |
| M26 | edge: only the start node checked | killed | TA, suite, storage |
| M27 | `to_document` drops edge data | killed | suite, document_form |
| M28 | `from_document` keeps kind process as type | killed | TA, suite, document_form |
| M29 | `skills` missing in `record_definitions` | killed | TA, identity, suite, storage |
| M30 | header `kind` enum widened | killed | record_checks |
| M31 | transform `toolbox_id` optional | killed | TA, suite |
| M32 | master `stop` optional | killed | suite |
| M33 | `record_id` compared for nodes only | killed | suite, storage |
| M34 | context-node `to_object` ignores categories | killed | suite, record_objects |
| M35 | Storage guard only for nodes | killed | storage |
| M36 | Storage tells subscribers before the check | killed | storage |
36 mutants (one invalid and redone), 33 killed, 3 survived: 1 equivalent (M19), 2 real gaps (M09, M25). No mutant of the requested list survived (`check_record` None, `types()`, `to_record` task, `to_document` master, Storage skip, no `record_id`, `stored` ignored are M01 to M08).

## Code against the contract (F) and behaviour that only lives in the code (G)
Probes: `/home/maldun/.claude-work/jobs/d597730b/tmp/probe/p1.py` to `p5.py`, run against the clean checkout.
| Input | Result |
|---|---|
| foreign table to `check_record` | `ValueError`, as the contract says |
| `None`, a number, `{}` as record; type `["data"]`, `None`; edge end `True`; non-object `data` | a rule, never an exception |
| `max_repetitions: True`, version `True` in a header | `schema_break` (path `stop.max_repetitions`, `nodes.0.version`) |
| NaN / inf in `max_seconds` or in `value` | `schema_break` with the path (as v1, A-60); `Storage.put` also refuses NaN as `invalid/schema` |
| `max_repetitions: 2.0`, header version `1.0` | accepted (jsonschema counts 2.0 as an integer): G-1 |
| NUL character in an ID or `toolbox_id` | `check_record` accepts (pure function); `Storage.put` refuses it as `invalid/schema` ("a NUL character") on both backends |
| JSON nested 100 000 deep, or an array 5000 deep | no exception, but the answer is `record_identity` / `record` (the catch-all of `check_record`): F-09 |
| a `categories` schema that is not a valid schema | same catch-all answer `record_identity`/`record`: F-09 |
| header naming a node and an edge with the same ID | accepted (separate namespaces), G-2 |
| edge from a node to itself | accepted by `check_record`, `Storage.put` and `to_document` (the rules of the Workflow management do not apply here, D-262): G-3 |
| header with the same member twice | `record_identity` with detail `nodes`/`edges` (logged by the implementer) |
| node `data` with an extra field (`{"type": "data", "foo": 1}`), or a key `id` in `data` | `check_record` accepts, `Storage.put` stores it, **`to_object` raises `TypeError`**; the mock accepts and silently drops the field in `to_object`: F-01 |
| a record with an extra top-level key (`{"id", "data", "extra": 1}`) | stored as is: G-4 |
| `to_document` of a node without `data`, of an edge without `from`; `from_document` of a node without `id`, or with `kind` a list | `KeyError` / `TypeError`: F-08 |
| `from_document`: generated `e1` next to an explicit `e1`; an edge `data` that is not an object | two edges `e1`; the record is returned unchecked (documented as "not checked"): F-08 |
| context-graph node (`categories`) through the real `Storage.put` | `invalid/unknown_type` for every category: F-02 |
| `check_record` with a fresh `categories` dict per call, 20 000 calls | no wrong answer (the cache holds the schemas, so ids are not reused), but `len(graph_tables._validators)` is 20 000: F-03 |
| `copy_records(source, target, ("graph_nodes", "graph_edges"))` with a node stored under `x` carrying id `y` and an edge to a node that is not stored | **both copied**: F-07 |
| refused write | no version number taken, no notice to subscribers (Storage test; probe: 1 notice for 1 accepted write, `ids` unchanged) |
| `delete` on a record table | `StorageError("immutable")` |
| input of `check_record`, `types()` result | not changed / independent copy |
| timing, 500 + 500 records | 13.5 to 15.8 ms |

Bypass routes for the four tables: the only callers of `backend.append` are `Storage.put` (guarded) and `storage_copy.copy_records` (F-07). No other module writes `graph_nodes`, `graph_edges`, `graphs` or `skills`.

## Goal acceptance (M34, M36)
| Item | Result |
|---|---|
| Requirements in scope verified | 17 of 17 (REQ-GTB-005..021) plus IF-301 v2 |
| Frozen requirements unchanged vs. parent | none frozen; `goal_check.py --parent-ref master` clean |
| Protected checks identical to the baseline | yes except A-91 and A-92 and the out-of-scope `plausibility.yaml` (F-05) |
| Nothing outside the goal's parts touched | `git diff --name-only` outside `specs/`, `tests/`, `tools/`, `contracts/`: `graph_tables.py`, `storage.py`, `requirements.txt` (one line). Inside the "Touches" list of every task, see "Task commits" |
| Every stop condition logged | yes: one (the image cache after the dependency change, owner decided); the A-92 finding was routed to an amendment, not worked around |
| Exit criterion met | OC-1, OC-2, OC-3 have their checks green (OC-1 TC-GTB-016/018/014, OC-2 TC-GTB-010/011/017, OC-3 TC-GTB-015); the real-use side is Phase 7 |
| Accepted by | Stefan Reiterer (at the merge) |

## Task commits (K)
| Commit | Task | Inside "Touches"? | Review |
|---|---|---|---|
| 0f1543e | T-01 | yes (`graph_tables.py`, `requirements.txt`, new test file) | correct against the contract; the catch-all `except Exception` in `check_record` is what makes F-09 |
| ef3295e | T-02 | yes | `to_object` does `Class(id, **data)`: F-01 |
| fd9ee76 | T-03 | yes | F-08 |
| 2728b06 | T-04 | yes (`storage.py`, `tests/test_storage.py`) | guard before the version number, `stored` only for named IDs: correct; no context categories: F-02 |
| 2d21f44 | T-05 = A-91 | the suite only, as the note says | correct; skip and switch removed, the cases and expected values untouched |
| c2876b2 / d80fdb5 / d67e7d9 / 4d0690d | A-92 and T-06 | T-06 yes (`graph_tables.py`, `storage.py`, `tests/test_storage.py`) | correct; the comparison sits right after the record's own `id` as planned. The install commit d80fdb5 carries the duplicates (F-04) and the `plausibility.yaml` rewrite (F-05) |
The implementation log's three findings are covered by tests that exist and fail under mutation (M12 killed by `test_a_number_that_is_not_finite_breaks_the_schema`; the null/absent case and the image case are tested).

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | – | nothing found: every operation and rule of IF-301 v2 and of REQ-GTB-005..021 is implemented | – |
| done, not specified | extra fields in a node's JSON field are accepted on write, then `to_object` raises (real) or drops them (mock) | F-01 | Phase 2 (decide), Phase 3 |
| done, not specified | the Storage layer cannot take a context-graph node (no `categories` on `put`) | F-02 | Phase 2 |
| done, not specified | float with an integral value counts as an integer; extra top-level keys of a record are stored; a header with the same member twice is `record_identity` (logged); self edges and a node and an edge with the same ID are accepted; deep JSON gives `record_identity`/`record` | G-1..G-5 | Phase 2 (a line in the next IF-301 text revision, as the implementer proposed for null/absent and NaN) |
Human review: the specification side is in `review-log.md` (REQ-GTB-021, TC-GTB-022, TR-GTB-001 and the goal approved by Stefan Reiterer, 2026-11-07); no item is marked `Code review: needed`.

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | REQ-GTB-005..021 | matrix above | met | F-01, F-02 |
| Performance efficiency | IF-301 bound (500 records in 500 ms) | TC-IF-301-19, my run 13.5 to 15.8 ms | met | – |
| Compatibility | REQ-GTB-015 | old suites at their hashes, TC-GTB-015, image builds | met | the hash of the IF-203 v0 suite, see "Known open points" |
| Interaction capability | – | internal interface | not now (nothing people operate) | – |
| Reliability | REQ-GTB-013, 016 | versions kept, refused write changes nothing, postgres run | met | F-03 (cache growth), F-08, F-09 |
| Security | REQ-GTB-008, 012 | task is data, no unsafe serialiser, no dynamic code, NUL and NaN refused at the Storage layer | met | F-07 (copy route) |
| Maintainability | – | `test_doc_check` clean | met | F-04 (duplicates in protected files) |
| Flexibility | REQ-GTB-009, 010 | a new type is a new class and schema | met | – |
| Safety | – | not applicable to this goal | not now | – |
`quality_check.py`: all nine characteristics covered (for the whole system).

## Open deferrals (M26)
None for GTB-005..021 (`trace_check.py` lists only older TD records, none for this goal).

## Review findings
Severity: high = wrong result or breach of the contract in normal use; medium = real defect or rule breach with a narrow trigger, or a gap that needs a decision; low = latent, cosmetic, or test gap. Each has the test that would catch it.

| # | Finding | Severity | Test that would catch it | Resolution / destination |
|---|---|---|---|---|
| F-01 | **A node that passes the write check can fail to read back.** The schemas of `data`, `transform` and `master` do not forbid additional fields (as the contract's table and the mock), so `Storage.put` stores `{"type": "data", "foo": 1}`; then `graph_tables.to_object` does `DataNode(id, **data)` and raises `TypeError` (also for a key `id` inside `data`, "multiple values for argument 'id'"). The mock accepts the same record and silently drops `foo` in `to_object`, so the mock, the real code and REQ-GTB-014 ("rebuilt equals stored") disagree and no check shows it. | medium | `to_object({"id": "n", "data": {"type": "data", "foo": 1}})` returns either `{"refused": …}` (schemas forbid extras) or an object that `to_record` turns back into the same record, and never raises; the same case on the mock, in the contract suite | **Decided 2026-11-07: refuse extras (A-93 + T-07, see Owner decisions).** Was: Phase 2 first: the owner decides (extras refused by `additionalProperties: false`, or kept); mock and suite change with it (amendment at the owner, as any interface); then Phase 3 fix with the test first |
| F-02 | **A context-graph node cannot be stored through the real Storage layer.** `check_record` knows a context graph only through `categories`; `Storage.put(table, id, doc, author, expected_version)` (IF-102) has no such argument, so every context node is `invalid/unknown_type` (probe: category `entity`). The stand-in of the tests takes `categories`, so TA cannot see it. REQ-GTB-005 and REQ-GTB-011 name "a workflow or context graph". Not needed for OC-1..3 (skills' workflow graphs), but a hidden hole for MODEL/TRUST | medium | `Storage.put("graph_nodes", "c1", {"id": "c1", "data": {"type": "entity"}}, …)` with the categories of its context graph is accepted and a wrong field is refused | Phase 2: the parent decides who carries `categories` (an IF-102 change, so an amendment at the owner of IF-102, or the Workflow management calls `check_record` itself with `categories`, D-264, and the Storage layer must then not refuse); record in G-V2 |
| F-03 | `graph_tables._validators` is keyed by `id(schema)` and never emptied; a caller that builds `categories` per call (the usual way for a context graph) adds one validator per call and keeps every schema alive (20 000 calls give 20 000 entries). No wrong answer found (the cache holds the schema, so an `id` cannot be reused) | low now, medium once a context-graph caller exists | after 10 000 `check_record` calls with fresh equal `categories` dicts, the cache stays below a fixed size | Phase 3, a regression test first; cache only the fixed list, or key by the schema's JSON |
| F-04 | **The A-92 install is not idempotent, and its second run is in the repository.** `tools/apply_amendment_a92.sh --do` run once on the commit before gives a clean result (I ran it in a scratch copy); run twice it duplicates four places: the scenario TC-GTB-022 in `test-spec.md` (**new `trace_check` error "scenario defined 2 times"**), the scope row REQ-GTB-021 in `goal.md`, the case `test_a_record_under_another_id_is_refused` in `test_if_301_v2_graph_tables.py` (Python keeps the second, so 16 cases run, not 17; harmless but a protected file), and the `if record_id …` block of the mock. The note says "running it twice changes nothing" | low | `trace_check.py` shows no GTB error; a check that no test method is defined twice in a file; a second `--do` in a scratch copy changes nothing | Phase 2, owner: remove the four duplicates by amendment (protected files) and fix `once()` in the script's "done" test |
| F-05 | **`specs/mia/plausibility.yaml` (protected) was rewritten as a whole by commit d80fdb5 ("A-92 installed, REQ-GTB-021 reviewed"), far beyond the one entry that A-92 and its note name.** Compared as data with the tag: 464 `rated_by` values changed from `maldun` to `Stefan Reiterer`, 433 `rated` dates reset to 2026-11-07 (also for ratings made on 2026-10-26, which hides their age for `--max-age-days`), 31 basis texts changed (among them REQ-GTB-008's), 42 `accepted_risk` entries changed (owner and date renamed), 37 items added, **4 items removed: REQ-API-004, REQ-CLV-011, REQ-VPB-002, REQ-API-007**. No `rating` value changed. `plausibility-proposal.yaml` changed by 398 lines the same way. The change is the owner's own commit with the owner's tool, so I do not suspect an agent, but nothing in the plan or the amendment approves it | medium (stop condition) — **accepted by the owner, 2026-11-07** | `git diff plan-baseline-it2-store..HEAD -- specs/mia/plausibility.yaml` shows only the REQ-GTB-021 entry for this goal | Owner: confirm that the rewrite was intended (probably a tool run on a newer state of the parent checkout) and that the 4 removed items are meant to go; if intended, record it as an amendment of its own so this branch carries one explanation; the rest of this goal does not depend on it |
| F-06 | Two test gaps: (a) mutant M25, a header whose **second** member names a version that is not stored, is not covered (both Storage and the protected tests use one-member headers or put the stale member first); (b) mutant M09, the record-table branch of `storage.validate`, has no test of its own | low | (a) `check_record("graphs", header([n1 v1, n2 v5]), stored={"nodes": {"n1": [1], "n2": [1, 2]}})` gives `unknown_member` `n2`, also on `Storage`; (b) `validate("graph_nodes", {"id": "n", "data": {"type": "zz"}})` raises `invalid/unknown_type` | Phase 3, unit tests in `tests/test_storage.py` and `tests/test_graph_record_checks.py` (unprotected; no amendment needed) |
| F-07 | Latent bypass of REQ-GTB-019, 020 and 021 by `storage_copy.copy_records`. It is not used for the four tables today (plan decision 4: CONVERT decides), but its `tables` argument accepts them, and `validate()` calls `check_record` without `record_id` or `stored`. Probe: a node stored under `x` with id `y` and an edge to a node that is not stored were both copied | low (latent until CONVERT) | `copy_records(src, dst, ("graph_edges",))` with an edge to a node not in `dst` raises `invalid/unknown_endpoint` | CONVERT's plan, or a small Phase 3 guard that refuses the four tables in `copy_records` until CONVERT decides; mention in G-V2.CONVERT |
| F-08 | `to_document` raises `KeyError`/`TypeError` for a record that has no `data` or an edge without `from`; `from_document` raises for a node without `id` or with an unhashable `kind`; a generated edge ID `e1` can collide with an explicit `e1`; an edge `data` that is not an object passes. The contract promises "never an exception" only for `check_record` and `validate`, so this is a gap, not a breach | low | `from_document({"nodes": [{"kind": "data"}], "edges": []})` gives `{"refused": …}` | Phase 2 line in IF-301 (inputs of the conversion are checked records or v1 documents), then Phase 3 |
| F-09 | The catch-all of `check_record` answers `record_identity` with detail `record` for input it cannot handle: JSON nested deeper than the recursion limit (a legal but deep `value`), and a `categories` entry that is not a valid schema. No exception, as promised, but the rule name misleads | low | a deep `value` gives a documented rule (or is accepted), not `record_identity` | Phase 2: name the rule (`schema_break` with path `value`?), Phase 3 |
| F-10 | `goal.md` header says `Status: Proposed` while its Phases table records Plan and Implement as done; the scope table lists REQ-GTB-021 twice (F-04) | low | `goal_check.py` (does not catch it today) | owner or the Commit phase |

Checked without a finding: `IF301_V2_REAL` is gone from the suite as A-91 says; no linter is configured, so style is not judged.

## Owner decisions (2026-11-07, after this report)
- **F-05 accepted** by Stefan Reiterer: the rewrite of `plausibility.yaml` was intended. The stop condition is cleared; no amendment needed for it.
- **F-01 decided** (the owner delegated the choice to the reviewer; the owner may overrule): **refuse additional fields.** The JSON schemas of `data`, `transform` and `master` get `additionalProperties: false`, so a node with an extra field (or a key `id` inside `data`) is `schema_break` naming that field, at write and at read; `to_object` then never sees a field its class lacks. Why: the contract calls the list of types fixed, the round trip of REQ-GTB-014 stays exact, and the mock's silent drop would lose data. Context-graph schemas come from `categories` and are not affected.
- Steps that apply it (none done by the reviewer; a fix is a new task): (1) amendment A-93 at the owner: IF-301 v2 fixed-types table and a golden example (an extra field gives `schema_break`, detail the field), mock `TYPE_SCHEMAS` with `additionalProperties: false`, a suite case TC-IF-301-21, TC-GTB-010/011 or a new TC-GTB-023 for the Storage side; the owner installs it with a script as for A-91/A-92 (the script must be idempotent, F-04); (2) task T-07 in `plan.md`: schemas in `graph_tables.py`, a failing test first (`to_object` and `Storage.put` of `{"type": "data", "foo": 1}`); touches `graph_tables.py` only; (3) Verify re-runs the automated checks and reads the fix commits only. F-01 stays open until then.

## Accepted deviations
F-05 (above). F-02 to F-10 can be accepted by the owner as "known, routed" (each names its destination). F-01 is decided and waits for A-93 and T-07.

## Known open points (not findings; they do not block this merge)
- Root `specs/mia/test-spec.md` still has no rows for TC-IF-301-05..20, and the A-90 draft's operations table says six tables for `definitions()` (the contract text itself is correct: two tables, `record_definitions()` four). Parent session.
- The review-log rows for D-189 and D-190: still missing (`grep` finds neither). Parent session.
- `test_graph_model.py` (10 failures) and `test_graph_run.py` (4) are red at the tag as well: MODEL's pending Implement. They do not touch this goal's code.
- **TC-GTB-015 and the IF-203 v0 hash.** The check compares the file `tests/acceptance/contract/test_if_203_workflow_library.py` with sha256 `0eb58da6f0a808c589e6c25c6f40b56472f7d0ba28fd807f0493811b8a9214c3`. When MODEL or TOOLBOX amends IF-203 to v1 and **edits that file**, TC-GTB-015 fails on the hash. What the owner does then: (1) preferred, the v1 amendment adds its cases in a new file (`test_if_203_v1_workflow_library.py`, as A-90 did for IF-301) and leaves the v0 file untouched, so the hash and TC-GTB-015 stay; (2) if the v0 file must change, the owner reviews that the change is wanted and re-records the hash in `V1_SUITES` of `tests/acceptance/test_graph_records.py` by an amendment (a protected file; the check's text in `test-spec.md` and TR-GTB-006 name the file as "before A-90", so say in the amendment which version is now the old one). The same holds for the IF-301 v1 hash. Agents must not edit either hash.

## Notes for Phase 7 (validation)
- The graph tables are not yet read by anything but tests (Workflow management and runner come with MODEL, TRUST, CONVERT); whether the pinned-member header and record split feel right in use is for those goals.
- Whether extras in a node's JSON field (F-01) are wanted by authors is a question for the people who write workflows.
- When a context graph writer exists, F-02 and F-03 become real and the validator cache (F-03) should be measured with it.

## What was not verified
- No CI run, no reference hardware statement for stage 4: reviewer runs only (all checks of this goal are stage 1 to 3).
- Static analysis (lint, types, SAST) does not exist in the repository; replaced by inspection and probes.
- The human code read of unmarked code is not done (no item marked); the diff of `graph_tables.py` and `storage.py` was read in full.
- PostgreSQL behaviour was run on the local postgres:16 image only (throwaway, tmpfs).
- `tests/test_tailscale.py::test_without_tailscale_it_says_how_to_install` errors on this host both at the tag and at HEAD; not investigated (outside this goal).
