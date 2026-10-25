# Test specification: Graph tables (N-3.2)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md   **Status:** Draft (Plan for node N-3.2, 2026-10-25)

Tests of this part alone against the mocks of its neighbours: unit tests with plain data, no database. The interface IF-301 is tested by its contract suite against the mock and the real part. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-GTB-001 | REQ-GTB-001 | Unit | 1 | definitions() of the Graph tables | exactly the tables workflows and context_graphs, both versioned, neither deletable | exact |
| TC-GTB-002 | REQ-GTB-002 | Unit | 1 | validate(workflows, doc) for one valid graph (the lookup graph) and one minimal document per rule: duplicate id, an edge to an unknown id, two adjacent data nodes, two adjacent process nodes, a session node with no stopping criterion, a cycle p->d->p | None for the valid graph; the rule name node_identity, node_identity, adjacent_data_nodes, adjacent_process_nodes, session_stopping_criterion, cycle in turn; the cycle is named by its ids with the first id repeated at the end | exact |
| TC-GTB-003 | REQ-GTB-002 | Property | 1 | 1000 generated graphs (seeds 1 to 1000) with random nodes, edges, shared inputs and session nodes; the reference is `graphlib.TopologicalSorter` on the same graph | a graph is accepted exactly when the reference finds no cycle and no other rule is broken; every accepted graph has a topological order; a data node read by two processes appears once | 0 failures over 1000 seeds |
| TC-GTB-004 | REQ-GTB-003 | Unit | 1 | validate(context_graphs, doc) for a valid context graph and for one with a broken rule; definitions() | the valid graph gives None, the broken one its rule; the table is versioned and not deletable | exact |
| TC-GTB-005 | REQ-GTB-004 | Component | 1 | the five seed entries (lookup, verify, review, search, method_transfer) read from `library/` and `skills/` of the repository | all five pass validate(workflows, ...); each names a specification, a context graph and a benchmark reference; method_transfer is marked off by default | exact |

Contract test cases of IF-301: TC-IF-301-01 to the last of the suite (listed in the root `test-spec.md`).

## Assumptions (checked in validation)

- ASM-N3-004: the graph rules are the ones of FR-7 and `contracts/IF-301-graph-tables.md`; `graphlib` of the standard library is the reference in the property test.
