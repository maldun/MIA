# Implementation log: Graph tables (N-3.2)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Graph rules with property test | done | `feat(graph_rules)` | `tests/test_graph_rules.py` (8 tests: TC-GTB-002, TC-GTB-003, the 500-node bound) | the contract suite of IF-301 stays green on the mock |
| T-02 Table definitions of workflows and context graphs | done | `feat(graph_tables)` | `tests/test_graph_tables.py` (4 tests: TC-GTB-001, TC-GTB-004); the contract suite of IF-301 with `graph_tables` as the real provider (scratch run, 3 tests, `_real` side) | provides IF-301 |
| T-03 Check the five seed entries | open | | | waits for the seed entries (root task T-10); the test is skipped with that reason, not weakened |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| A document that is not a graph (None, a list, `nodes` not a list) must give a rule name, not an exception | T-01 | `test_a_document_that_is_not_a_graph_is_refused` |
| `definitions()` must hand out a copy, otherwise a caller could make a table deletable | T-02 | `test_the_definitions_are_a_copy` |

## Plan amendments
None.

## Decisions
- The cycle search is iterative so a long chain cannot reach the recursion limit (a graph of 500 nodes, IF-301 bound 200 ms, takes a few ms).
- The order of the rules is fixed (identity, adjacent data, adjacent process, session stopping, cycle) so that a user always sees the same first violation.

## Open questions for Phase 4 and the integration step
- The contract suite of IF-301 has the mock as the only provider that runs. Making `graph_tables` the real provider is a change of the protected `tests/helpers/contract.py` at integration step 1 of N-3 (owner, amendment). The scratch check `run_contract_real.py` (job temp folder, not committed) patched `subject_for` for one run and passed all three tests.
