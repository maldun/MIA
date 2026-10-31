# Implementation log: Graph tables (N-3.2)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Graph rules with property test | done | `feat(graph_rules)` | `tests/test_graph_rules.py` (8 tests: TC-GTB-002, TC-GTB-003, the 500-node bound) | the contract suite of IF-301 stays green on the mock |
| T-02 Table definitions of workflows and context graphs | done | `feat(graph_tables)` | `tests/test_graph_tables.py` (4 tests: TC-GTB-001, TC-GTB-004); the contract suite of IF-301 with `graph_tables` as the real provider (scratch run, 3 tests, `_real` side) | provides IF-301 |
| T-03 Check the five seed entries | done (skipped) | `test(seed)` | `tests/test_seed_workflows.py`: 3 tests skipped because `library/workflows` does not exist (root task T-10); in a scratch copy with five dummy entries they pass and a broken entry fails | the entry format is provisional, T-10 confirms it |

## Reuse check (owner rule: use existing code)
- `graph_rules.py` and `graph_tables.py` are new: no module of the repository checks the process/data graph rules of FR-7. `context_graph.py` is the provenance graph of run events (a different thing) and `library.py` validates the old pipeline format; both stay as they are.

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

## Verify findings (verification-report.md, decision D-160), branch v1-n32b
Each fix is test-first: the new test was red before the change and green after (reported, not verified). Rule order, duplicate edges, whitespace ids and a session on a data node (F3, rest of F4) are deferred to FB-02 (D-160) and not touched.

| Finding (report) | Fix | Covered by test (red before) |
|---|---|---|
| F1 a malformed `stop` or edge endpoint raised (`AttributeError`, `TypeError`), so `PUT /api/workflows/<id>` answered HTTP 500 | `graph_rules.violation`: an edge endpoint that is not a text id is `node_identity`; a session's `stop` that is not a dict is `session_stopping_criterion` (`_stops`). A `stop` on a node that is not a session is still not looked at (FB-02) | `test_graph_rules.test_a_malformed_stop_or_edge_endpoint_is_named_not_raised`; `test_graph_api.test_a_malformed_graph_is_422_with_a_rule_not_500` (N-2.1 file, in the image: 500 before, 422 `invalid` with the rule after) |
| F2 R4 took any truthy limit (`-1`, `"0"`, `True`, `NaN`); `-5` was stored through IF-104 and lowered the cost estimate | `graph_rules._stops`: a session needs at least one of `max_cycles`, `max_seconds`, and every one given is an `int` >= 1 that is not a bool (D-160). A `null` limit counts as not given (my reading, so a form that sends an empty field still works; A-60 writes it into IF-301, owner to confirm). `workflow_library.py:199` (`max_cycles` × costs) reads only stored records, and every stored record passed this rule on `put`, so the estimate sees an int >= 1 or no value (then 1) | `test_graph_rules.test_a_session_limit_is_a_positive_integer` (12 sub-cases red before: -1, "0", "3", True, NaN, inf, 2.5, [3], -5, 1.0, a valid `max_cycles` with `max_seconds: -1`, `"x"` with a valid `max_seconds`); `test_graph_api.test_a_session_limit_that_is_not_a_positive_integer_is_422` (`-5` was 200 before) |
| F4 (part) unknown `kind` and empty id had no test (surviving mutants M2, M11) | no code change: the rule was right, only untested. Duplicate edges, whitespace ids and a session on a data node stay as they are (FB-02, D-160) | `test_graph_rules.test_an_unknown_kind_or_an_empty_id_breaks_node_identity` (kind `tool`, no kind, id `""`, no id). Not red before (nothing to fix); instead the mutants of the report were run on a scratch copy: M2 (kind check removed) and M11 (`not nid` removed) each make only this test fail |
