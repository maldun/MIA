# Verification report: Graph tables (N-3.2)

**Goal:** G-V1 (iteration), supervised; node N-3.2 (leaf) verified as a black box with the mocks of its neighbours, and in the N-3 integration steps with its real siblings
**Branch:** goal/v1 @ 30ad986 (node files identical to 53c6766: no commit on goal/v1 touches `graph_rules.py`, `graph_tables.py` or their tests)   **Parent line of work:** master   **Plan baseline:** plan-baseline-it1, decomp-baseline
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed:** f02030a (T-01 `graph_rules.py`), 641e8b9 (T-02 `graph_tables.py`), b1be0e3 (T-03 seed test, skipped), all on master before 53c6766. Protected material of the node: fe819ca (suite, mocks, N-3 steps), df132a8 (IF-301 v0), 7d6f3d6 (A-02: real provider, READY). Scope: REQ-GTB-001..004, IF-301 (provided). Not judged against the networkx redesign (D-121/D-122, FB-02: next iteration). `context_graph.py` (the run provenance graph, D-108 "run graph") is not part of this node (implementation log, reuse check) and was not reviewed.

## Verdict (proposal)
**Verified with findings; REQ-GTB-004 not verified.** REQ-GTB-001, -002, -003 and IF-301 have tests that pass on the host and in the image, the IF-301 suite passes on the mock and the real module (3/3 each, none skipped), and N-3 steps 0 to 3 pass. Mutation testing killed 13 of 17 mutants. Findings: a malformed graph from an edit (TB-edit) crashes the rules instead of naming one, which the IF-104 route turns into HTTP 500 (F1); the session rule accepts negative or non-numeric limits (F2); "first broken rule in a fixed order" holds only per edge, not per rule (F3); REQ-GTB-004 (Must) is skipped with no deferral record or scope row (F5). F1 and F2 are implementation defects (test first); F3 and F5 need the owner.

## Automated checks (local runs, not CI)
| Check | Result |
|---|---|
| Stage log (CI) | no CI run; all evidence below is local |
| Node tests, host python 3 | `test_graph_rules.py` 8 OK; `test_graph_tables.py` 4 OK; `test_seed_workflows.py` 3 skipped (no `library/workflows`) |
| Node tests in the image (`podman run --rm --init --network none --user 0 … localhost/mia:latest`, Python 3.12.15, one container) | the same 3 files plus the IF-301 suite, N-3 steps 0–3, `test_storage.py`: all OK (seed test skipped=3) |
| IF-301 contract suite | 6/6: `_mock` 3 and `_real` 3 (the real side is `graph_tables`, `contract.py:792-794`, A-02); no skip |
| Consumers (image) | `test_workflow_library.py`, `test_storage_copy.py`, IF-102 suite, IF-104 suite, N-0 step 1: OK |
| N-3 integration steps (A-02) | step_00 (mocks), step_01 (N-3.2 real), step_02, step_03: OK on host and in the image |
| Statistical / property checks | TC-GTB-003: seeds 1–1000 fixed by the test spec, deterministic, 0 failures in one run (no re-run needed) |
| Bound of IF-301 (500 nodes ≤ 200 ms) | test OK; probe: 500 nodes with 62 500 edges 30 ms; a cycle of 100 000 nodes found in 141 ms without recursion error |
| PostgreSQL | not applicable: the node is pure Python without storage; the PostgreSQL path of validation belongs to N-3.1 (its report) |
| Protected material | suite, `mocks/graph_rules.py`, `mocks/if_301_graph_tables.py`, `contracts/IF-301-graph-tables.md`, `tests/integration/N-3/*`: unchanged since decomp-baseline; `tests/helpers/integration.py` equal to the A-02 install (7d6f3d6); `contract.py` IF-301 lines equal to A-02. No skip/xfail in the suite |
| Traceability (`trace_check.py`) | 93 errors / 255 warnings tree-wide; for this node one: `test-spec.md` has 5 checks and no `## Scenarios` section (M39) |
| `test_doc_check.py` (node's 4 test files) | 26 errors (T2 no `Example:` line, T3 no Given/When/Then); same class as N-3.1 F11 |
| Mutation testing (scratch export of HEAD, 17 hand mutants, 4 test files) | 13 killed; survived: M2 unknown `kind` accepted, M6 `session` honoured on data nodes, M11 empty id accepted, M12 session rule checked before the edge rules (F3, F4) |
| Architecture rules | `graph_tables` imports only `graph_rules`; `storage.py` is the only production consumer (`storage.py:19-22,36,55`), as IF-301 says. No SysML part for the Graph tables (requirements satisfied by `mia.persistence`); same gap as N-3.1 F13 |
| Static / security / dependencies | no linter configured; no new dependency (stdlib only); no subprocess, file or network access |
| Usability with bad inputs | through IF-104 (`graph_api.py`): see F1 |

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-GTB-001 shared state held | Test | TC-GTB-001 `test_graph_tables.py:20` (exact definitions), copy test `:25`; TC-IF-301-01 mock and real; AC-15 (written and read back) only outside the node: `test_storage.py:45` (one record of each table) and N-3 scenario | Pass (F6) | yes |
| REQ-GTB-002 validation on write | Test | TC-GTB-002 `test_graph_rules.py:25-64` (each rule named, cycle `[p,d,p]`), TC-GTB-003 property `:111-141` (1000 seeds vs graphlib), TC-IF-301-02/03 both sides; mutants M1, M3–M5, M7–M10, M17 killed | Pass with findings F1–F4 | yes; the property oracle copies the adjacency and session rules from the code (F7) |
| REQ-GTB-003 context graphs stored | Test | TC-GTB-004 `test_graph_tables.py:31` (validated, not deletable); AC-10 (an edit is a new version) only in `test_workflow_library.py:187-191` (N-2.3) | Pass (F6) | yes |
| REQ-GTB-004 example workflows as seed data | Test | TC-GTB-005 `test_seed_workflows.py:22` skipped: `library/workflows` does not exist (root task T-10 not done) | **Not verified** (F5) | – |
| IF-301 | Test | suite 6/6 (mock and real), N-3 step_01; error `ValueError` for a foreign table (`test_graph_tables.py:38`, TC-IF-301-03); bound 500 nodes | Pass; golden 1–3 met | yes |

## Test requirements (M41)
`specs/mia/test-requirements.md` has no TR items (trace_check warning, tree-wide). Applied as fixed in `test-spec.md`: TC-GTB-003 seeds 1–1000, 0 failures (met); IF-301 contract suite against mock and real (met, stage 1 and 2 locally).

## Goal acceptance (M34, M36)
| Item | Result |
|---|---|
| Requirements in scope verified | 4 of 5 (REQ-GTB-004 open, F5) |
| Frozen requirements unchanged | G-V1 has no frozen requirements |
| Protected checks identical to the baseline | yes (see Automated checks) |
| Nothing outside the node's parts touched | the three commits touch only `graph_rules.py`, `graph_tables.py`, their tests and the implementation log |
| Every stop condition logged | yes: the real provider of the suite was left to the owner (A-02), the seed entries to root T-10 |
| Exit criterion | node level only; G-V1 exit is checked in Validate |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | IF-104/IF-102 "a broken rule gives `invalid` with `rule`" | a malformed `stop` or edge endpoint raises instead (F1) | Phase 3 |
| specified, not done | R4 "positive max_cycles or max_seconds" (`graph_rules.py:10`) | any truthy value passes (F2) | Phase 3 (+ IF-301 text) |
| specified, not done | "the first broken rule" in the order identity, data, process, session, cycle (REQ-GTB-002, `graph_rules.py:13`, log "Decisions") | order holds per edge only (F3) | owner decision |
| specified, not done | REQ-GTB-004 seed entries | not built, no record (F5) | owner decision |
| done, not specified | `session: true` on a data node is ignored without a rule; a duplicate edge is accepted; ids are not trimmed (`" "` is a valid id) | not stated by FR-7/IF-301 | F4: owner decides, then test |

Human review: specification side via `review-log.md`; code read in full by the reviewer (95 lines).

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | REQ-GTB-001..004, IF-301 | matrix | pass with findings | F1–F5 |
| Performance efficiency | IF-301 bound | test + probes (30 ms dense, 141 ms for 100 000 nodes) | pass | – |
| Compatibility | IF-301 | suite on mock and real; N-3 steps | pass | – |
| Interaction capability | – | – | – | not now: no user interface in this node; the error text reaches the graph app through IF-104 (F1) |
| Reliability | REQ-GTB-002 | iterative cycle search; property test | partly | F1 (exceptions on bad input) |
| Security | TB-edit (REQ-GTB-002 rationale) | nothing invalid is stored on the probes; a malformed edit gives HTTP 500 | partly | F1, F2 |
| Maintainability | – | 95 lines, one dependency; mutation 13/17 | ok | F4, F8 |
| Flexibility | – | – | – | not now: the graph model is redesigned in FB-02 |
| Safety | – | – | – | not applicable |

## Open deferrals (M26)
| TD | Requirement | Interim criterion verified? | Target check state | Trigger |
|---|---|---|---|---|
| none recorded | REQ-GTB-004 | – | skip (`test_seed_workflows.py:15`) | root task T-10 (F5: a TD record or scope row is missing) |

## Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | `graph_rules.py:38-39`: a `stop` that is not a dict (`"x"`, `[1]`) raises `AttributeError`; `graph_rules.py:33`: an unhashable edge endpoint (`{"from": ["a"]}`) raises `TypeError`. `storage.put` passes the exception through (`storage.py:54-58`), so `PUT /api/workflows/<id>` answers **HTTP 500** instead of 422 `invalid` with a rule (probe in the image with `graph_api.create_graph_blueprint`; IF-104 error table line 40). Nothing is stored. The protected mock has the same gap (`tests/helpers/mocks/graph_rules.py:23,31`); the node's own finding "not a graph must give a rule name, not an exception" (implementation log) covers only the top level | Medium (TB-edit boundary) | Phase 3: failing tests in `test_graph_rules.py` first; fix: an edge endpoint that is not a string is `node_identity`, a `stop` that is not a dict is `session_stopping_criterion` (or `node_identity`). Mock alignment optional (amendment) |
| F2 | `graph_rules.py:39`: R4 accepts any truthy limit: `max_cycles: -1`, `"0"`, `True`, `NaN` pass (probe; `-5` stored through IF-104 with 200). The module's own text says "positive" (`:10`). `workflow_library.py:199` multiplies a session's costs by `max_cycles`, so a negative value lowers the estimate that `check_budget` compares with the budget; a string makes it fail at run time. N-2.3 checks `budget_tokens` strictly (`workflow_library.py:78`), the graph rule does not | Medium | Phase 3: test first; fix: a limit counts only as a number > 0 (not bool, finite). Owner: confirm the types and write them into IF-301 (text amendment, the suite case `max_cycles: 0` stays) |
| F3 | `graph_rules.py:31-36` checks node identity of edges, adjacent data and adjacent process **per edge**: edges `[a->b (data,data), a->ghost]` give `adjacent_data_nodes` though R1 is broken; `[p->q, a->b]` give `adjacent_process_nodes` before R2. The docstring (`:13`) and the log ("the order of the rules is fixed … always sees the same first violation") claim a rule order; the mock behaves the same; no test fixes the order (mutant M12 survives) | Low | Owner decision: (a) "first" means the first finding of one pass: amend the docstring and REQ-GTB-002 text; or (b) rule order: one pass per rule, a test with two broken rules per pair, and the mock in an amendment |
| F4 | Untested rule parts (surviving mutants): unknown `kind` (M2), empty id (M11), and unspecified behaviour: `session: true` on a data node silently ignored (M6), duplicate edges and whitespace ids accepted | Low | Phase 3: add cases for M2, M11; owner decides M6/duplicates/whitespace (FR-7 makes a session a process; proposal: `node_identity` for a session data node) |
| F5 | REQ-GTB-004 (Must) is not verified: TC-GTB-005 is skipped because root T-10 never wrote `library/workflows`; there is no TD record in `deferred.md` and no scope row in `goals/G-V1/goal.md`. The entry format of the test is provisional and predates D-108 and D-112 (a workflow document names `skill` and `pipeline`); the review entry is already out of G-V1 (REQ-RUN-013 partly, D-128/D-130). Seeding without validation is N-3.1 F1 | Medium (Must requirement without evidence or record) | Owner decision: either a scope row "partly/out" for REQ-GTB-004 (reason T-10, FB-02) or a TD with trigger T-10; T-10 then confirms the format and amends the test |
| F6 | TC-GTB-001 and TC-GTB-004 check the definitions and validation only; the acceptance criteria AC-15 (written and read back) and AC-10 (an edit is a new version) are evidenced only by `test_storage.py:45` (N-3.1) and `test_workflow_library.py:187-191` (N-2.3) | Low | Phase 2: name those tests in `Verified by`, or accept them as integration evidence |
| F7 | `test_graph_rules.py:124`: the check "a data node read by two processes appears once" is `len(order) == len(nodes)`, which graphlib always satisfies (the graph is built from all ids), so it cannot fail; the oracle copies the adjacency and session rules (`:98-99`) from the code, only the cycle part is independent | Low | Phase 3 backlog: assert the shared-input property on the generated graph itself |
| F8 | `test_doc_check`: 26 errors in the node's test files; `test-spec.md` has no `## Scenarios` (trace_check ERROR) | Low | backlog (refactoring commit, M31), as N-3.1 F11 |
| F9 | `tests/helpers/contract.py:19` still lists IF-301 in `REAL_NOT_READY` ("not integrated yet") although the real side runs since A-02; IF-301 stays "v0, draft" and the node `status: Draft` in `decomposition.yaml:236` | Low | Phase 2: text-only amendment with the next change of `contract.py`; status update at the gate |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| – (candidate: F5, if the owner moves REQ-GTB-004 out of G-V1) | | |

## Notes for Phase 7 (validation)
- A person editing a graph in the graph app after F1 is fixed should see which node or edge is wrong; today the detail is `a->b` or an id, which is enough for small graphs only.
- With FB-02 (networkx, executable nodes) the rules move; F2 and F3 should be decided before, so the new code inherits a clear rule order and limit type.

## Reproduction
Probe and mutation scripts (not committed): `/tmp/claude-1000/-home-maldun-prog-Python-MIA/1251f948-2f8f-400a-acca-407c0b962dbf/scratchpad/n32verify/` (`probe.py <repo>` rule probes, `probe2.py <repo>` storage, `probe3.py` IF-104 in the image, `mutate.py` 17 mutants on an export of HEAD).

# Re-verification (after v1-n32b and the A-60 install)

**Goal:** G-V1 (iteration), supervised; node N-3.2 (leaf), black box with its neighbours' mocks, and in the N-3 integration steps with its real siblings
**Branch:** goal/v1 @ 6243c4d (node code as of 2ba48ac; later commits are docs only)   **Plan baseline:** plan-baseline-it1, decomp-baseline   **Date:** 2026-10-31
**Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed:** v1-n32b (merged in 2ba48ac): fda514a (F1), 0442a40 (F2), 97c425d (F4 part), 33db7b7 (F7), ec9c452 (F6), 75638e8 and 508ed36 (A-60 draft, D-162); 849ac36 (A-59, A-60, A-61 installed by the owner). Inputs: D-160, D-162, IF-301 v1, IF-104 JS mock and suite, sibling report N-3.1 (re-verification).

## Verdict (proposal)
**Verified with accepted deviations.** F1, F2, F4 (tested part) and F7 are closed with tests that fail on a mutant (table below); F9 and the IF-301 text of F1/F2 are closed by A-60 (installed files equal their drafts); F6 is closed by naming the outside evidence in `test-spec.md`; F3 and the rest of F4 are deferred to FB-02 (D-160, recorded in `feedback/FB-02.md:19`); F5 is decided (REQ-GTB-004 partly, `goals/G-V1/goal.md:73`, TD-06). The D-162 module collision is closed for IF-301: a mutant of the real `graph_rules.py` turns only the `_real` cases red in a full contract run in one process. New findings are low: the TD-06 record does not meet the deferral format (R1, trace_check ERROR), TC-IF-104-06 is listed for the real side but runs only on the JS mock (R2), and plan text residue (R3). None blocks the merge.

## Automated checks (local runs, not CI)
| Check | Result |
|---|---|
| Node tests, host | `test_graph_rules.py` 12 OK; `test_graph_tables.py` 4 OK; `test_seed_workflows.py` 3 skipped (TD-06) |
| IF-301 suite, host | 8/8 (`_mock` 4, `_real` 4), none skipped |
| IF-104 JS suite (`node --test tests/acceptance/contract/test_if_104_graph_api.test.mjs`) | 12: 6 pass (mock, TC-IF-104-01..06), 6 skipped (real, `REAL_NOT_READY` of `contract.mjs:9`) |
| In the image (`tools/run_in_image.sh` on a scratch export of HEAD, one container at a time) | node tests (12, 4, 3 skipped), IF-301 8, IF-102 20, IF-104 Python 10, `test_graph_api` 10, `test_storage` 17, `test_workflow_library` 13, N-3 steps 00–03: all OK |
| Full contract run, one process, in the image (`unittest discover -s tests/acceptance/contract -p "test_if_*.py"`) | 218 tests, 18 skipped, OK. With the real `_stops` mutated to the old truthy rule: 6 errors, all in `..._real` of TC-IF-301-04 (the by-path real side tests the real rules); the mock cases and IF-102 stay green (the IF-102 suite has no limit case) |
| Fuzz (50 000 random documents of odd values through `graph_tables.validate`) | 0 exceptions; every result is `None` or `{rule, detail}` (IF-301 v1 "never an exception") |
| Protected material vs. A-60 | `contracts/IF-301-graph-tables.md`, `tests/helpers/mocks/graph_rules.py`, `tests/helpers/mocks/if_104_graph_api.mjs`, IF-301 and IF-104 JS suites: byte-equal to their drafts (`cmp`). `contract.py:813-832` equals `amendments/A-60/real_graph_tables.py` (blank lines aside), `contract.py:19` the F9 line, `:839-840` the IF-301 branch. No commit after 849ac36 touches `tests/`, `contracts/`, `stages.yaml` or the node's code. The look-only run of `tools/apply_amendment_a60.sh` was denied by the session's permission check, so the comparison is by `cmp` |
| trace_check | exit 1 tree-wide (99 errors). For this node: ERROR `test-spec.md` has no `## Scenarios` (F8); 3 ERRORs on TD-06 (R1); WARN TD-06 trigger without a date; WARN TD-01..04 not listed here (listed below now) |
| test_doc_check (node's 4 test files) | 28 errors: the 26 of F8 plus 2 from the new protected case TC-IF-301-04 (owner-installed); every test added in v1-n32b passes the rule |
| `check_sysml_model.py` | OK |
| Static, security | no linter configured; manual review of the fix commits; no new dependency, no I/O in the node |

### Mutation checks (scratch export of HEAD, removed)
| Mutation | Caught by |
|---|---|
| edge endpoint type check removed (F1) | `test_a_malformed_stop_or_edge_endpoint_is_named_not_raised`; IF-301 TC-04 `_real` |
| `stop` not-a-dict guard removed (F1) | the same two |
| limit `>= 1` → `>= 0` (F2) | 4 tests of `test_graph_rules` incl. the property test; IF-301 `_real` |
| bool allowed / float allowed / `all` → `any` / old truthy rule (F2) | `test_a_session_limit_is_a_positive_integer`; IF-301 TC-04 `_real` |
| `null` counted as given (D-162) | the same two |
| duplicate-id check removed (F7) | `test_a_shared_input_appears_once_in_an_accepted_graph`, the property test, `test_each_rule_is_named` |
| mock `graph_rules.py`: truthy limit / `null` counted | IF-301 TC-04 `_mock` (and TC-02 `_mock` for the second) |
| JS mock `stops`: truthy limit / `null` counted / a string `stop` accepted | TC-IF-104-06 (mock) |

## Earlier findings
| # | Status | Evidence |
|---|---|---|
| F1 | closed | `graph_rules.py:32-34` (endpoint), `:47-48` (`stop`); tests above; `test_graph_api.py:127` (422, not 500) green in the image; 2 mutants caught |
| F2 | closed (D-160, D-162) | `graph_rules.py:44-54`; IF-301 v1 text; 6 mutants caught on real, mock and JS mock. `workflow_library.py:199` now only sees an int >= 1 or `None` (then 1) |
| F3 | deferred to FB-02 (D-160) | `feedback/FB-02.md:19`. The docstring `graph_rules.py:13` still claims a fixed rule order (R3) |
| F4 | tested part closed; rest deferred to FB-02 | `test_an_unknown_kind_or_an_empty_id_breaks_node_identity` (`test_graph_rules.py:46`; the log reports M2 and M11 caught, not re-run by me); duplicates, whitespace ids, session data nodes in FB-02:19 |
| F5 | decided (D-160): REQ-GTB-004 partly, TD-06 | `goals/G-V1/goal.md:73`, `deferred.md:65-79`; record format incomplete (R1) |
| F6 | closed | node `test-spec.md`, section "Evidence of the acceptance criteria outside this node"; both named tests green in the image |
| F7 | closed | the new check fails on the duplicate-id mutant, the old ones alone did not |
| F8 | open, backlog | unchanged (28 errors, see above) |
| F9 | closed in `contract.py:19` (A-60); `decomposition.yaml:431` still says IF-301 `version: v0` and the node `status: Draft` (`:236`) | R3 |

## Verification matrix (changes against the first report only)
| Requirement | Result now |
|---|---|
| REQ-GTB-001, -003 | Pass, unchanged; AC-15 and AC-10 evidence named (F6) |
| REQ-GTB-002 | Pass. Malformed parts and limits named by their rule on real, mock and JS mock; rule order and the three unspecified cases deferred (FB-02) |
| REQ-GTB-004 | Partly, accepted by the owner (D-160, TD-06); TC-GTB-005 skipped as recorded |
| IF-301 v1 | Pass: 8/8 alone and in the full run (by-path real side), golden 1–4 met, fuzz 0 exceptions, bound unchanged |

## Specification vs. code (M42), new items
| Direction | Item | Destination |
|---|---|---|
| specified, not run | TC-IF-104-06 is "1 (mock) and 2 (real)" (`specs/mia/test-spec.md`, row TC-IF-104-06), but the JS real side skips and the Python IF-104 suite (`test_if_104_graph_api.py`) has no such case; the real route is checked only by the node test `test_graph_api.py:143` of N-2.1 | R2 |
| unspecified | `max_cycles: 2.0` in a JSON body: Python (real) refuses it as a float, the JS mock accepts it (`Number.isInteger(2.0)`); IF-301 v1 lists `2.5`, not `2.0` | R2 |

## Open deferrals (M26)
| TD | Requirement | Interim criterion verified? | Target check state | Trigger |
|---|---|---|---|---|
| TD-06 | REQ-GTB-004 | yes: workflow documents are stored and checked through IF-301 and the library API (tests above); TC-GTB-005 skipped | skip (`test_seed_workflows.py:24`), not marked `deferred('TD-06')` (R1) | root task T-10 or the next Plan (no date, R1) |
| TD-01..04, TD-07 | not of this node | – | – | listed for trace_check only |

## New findings
| # | Finding | Severity | Destination / proposal |
|---|---|---|---|
| R1 | The TD-06 record does not meet the deferral format: trace_check gives 3 ERRORs (REQ-GTB-004 has no `Relaxed: TD-06` and no `Target` line, `requirements.md:45-53`; the target check is `TC-GTB-005`, not `skip: <reason>`, and no test carries `deferred('TD-06')`, `deferred.md:75`) and one WARN (trigger without a date, `:74`). Same pattern as TD-07 (N-4.1) | Low | amendment (text only): `Relaxed: TD-06` and `Target: TC-GTB-005 green on library/workflows` on REQ-GTB-004; TD-06 `Target check: skip: library/workflows missing (root T-10)`; a date in the trigger ("…, or 2026-12-31, whichever first"); the marker on `SeedWorkflows` comes with the rewrite of TC-GTB-005 (FB-03) |
| R2 | TC-IF-104-06 is never run against the real provider (see M42 above); and the mock and the real side disagree on `2.0` | Low | needs test / amendment: add the TC-IF-104-06 case to the Python IF-104 suite (its real side runs) with the next IF-104 amendment, or change the test-spec row to "1 (mock); real: `test_graph_api.py:143`". Owner: say in IF-301 whether `2.0` counts as an integer (proposal: refused, as the real side does; JS cannot tell, so accept the mock gap) |
| R3 | Plan and code text residue: `graph_rules.py:13` still says `violation()` reports the first broken rule "in this order", which F3 showed holds per edge only (deferred, but the sentence stays wrong until FB-02); `decomposition.yaml:431` IF-301 `version: v0` while the contract is v1 | Low | Phase 3 one-line docstring fix ("the first broken rule found; order per edge, FB-02"), and the version in `decomposition.yaml` at the gate (F9 rest) |

## Accepted deviations
| Deviation | Reason | Accepted by |
|---|---|---|
| REQ-GTB-004 partly (no seed folder) | D-160, TD-06, FB-03 | owner |
| Rule order per edge; duplicate edges, whitespace ids, a session on a data node accepted | D-160, FB-02 (networkx redesign) | owner |
| IF-104 real side not run by the JS suite | `REAL_NOT_READY` (N-2 serves the routes in Python; the Python suite covers 01–05) | to be confirmed with R2 |

## Not checked here
- CI: none; all results are local feedback runs.
- The whole test suite (only the node's files, its consumers named above, the contract suites and N-3 steps); the known failures (`test_amendment_report`, `test_harness` rt_edit, `tests/acceptance/test_benchmarks.py`) were not re-run.
- The look-only run of `tools/apply_amendment_a60.sh` (denied by the permission check; `cmp` instead).
- The log's claims that each fix test was red before its fix (checked indirectly: each fix is caught by a mutant that restores the old code).

## Notes for Phase 7
- Unchanged from the first report; with FB-02 the rule order and the three open cases get decided in the redesign.
