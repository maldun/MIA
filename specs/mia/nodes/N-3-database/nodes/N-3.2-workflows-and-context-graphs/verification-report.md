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
