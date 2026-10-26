# Implementation log: Graph tables (N-3.2)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Graph rules with property test | done | see `git log` (`feat(graph_rules)`) | `tests/test_graph_rules.py` (8 tests: TC-GTB-002, TC-GTB-003, the 500-node bound); the contract suite of IF-301 stays green on the mock | the real side of TC-IF-301-01..03 runs at the integration step (see open questions) |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| The mock of `graph_rules` reports an edge between two nodes of the same kind in one pass; the real module does the same but checks node identity of both ends first | T-01 | `test_each_rule_is_named` (node_identity for an edge to an unknown id) |
| A document that is not a graph (None, a list, `nodes` not a list) must give a rule name, not an exception | T-01 | `test_a_document_that_is_not_a_graph_is_refused` |

## Plan amendments
None.

## Decisions
- The cycle search is iterative so a long chain cannot reach the recursion limit (REQ-GTB-002 does not bound the size; IF-301 names 500 nodes in 200 ms: measured well below that, 500 nodes in a few ms).
- The order of the rules is fixed (identity, adjacent data, adjacent process, session stopping, cycle) so that a user always sees the same first violation.

## Open questions for Phase 4 and the integration step
- The contract suite of IF-301 only has the mock as provider. Giving it the real `graph_tables` as provider is a change of the protected `tests/helpers/contract.py` (REAL_NOT_READY) at the integration step 1 of N-3; this needs the owner (amendment). T-02 provides the module that the adapter will call.
