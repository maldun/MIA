# Implementation log: Graph app (N-5)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Show graphs as nodes and edges | done (TC-GA-001 is the owner's demonstration) | `feat(graph-app)` | `tests/js/graph-view.test.mjs` (7 tests, REQ-GA-001: every node and edge of the lookup drawn, data and process nodes drawn differently, every edge to a later layer, no two nodes on one place, a library entry drawn from its `workflow`, a cycle or an edge to an unknown id still drawn, ids escaped); all JS tests 110 of 110 | plain SVG, no library (see Q-1); the page opens a JSON file (graph or library entry) until the IF-104 reading of T-03/T-04 exists |
| T-02 Edit nodes as JSON, graph rules before saving | stopped before start | – | – | Q-2, Q-3 |
| T-03 Versions, history, diff and context graphs | stopped before start | – | – | Q-3 |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| The seed entries (`library/workflows/<id>.json`, root T-10) do not exist yet, so no recorded lookup entry can be opened for TC-GA-001. The view accepts the graph itself and the provisional entry format of `tests/test_seed_workflows.py` (`{"workflow": {...}}`) | T-01 | `a library entry is drawn from its workflow` |
| A graph with a cycle or a dangling edge is refused on save, but must still be drawable (the user has to see what to fix) | T-01 | `a cycle and an edge to an unknown id still give a drawing` |

## Plan amendments
None.

## Open questions for the owner (decisions, not taken here)
- **Q-1 (REQ-GA-009, FR-22: "a vendored graph library").** T-01 draws with its own small layered layout as SVG markup (`graph_app/graph-view.js`, about 90 lines, no library). Recommendation: keep it and amend REQ-GA-009 / FR-22 / the `graphView` part to "plain SVG, no graph library" (fewer files to vendor and audit, nothing to load from outside, enough for graphs of at most 500 nodes in layers). Alternative: approve a vendored library (e.g. Cytoscape.js, MIT) for T-06; then T-01's drawing is replaced.
- **Q-2 (REQ-GA-003, plan note of T-02: "the rules are the shared graph rules module of N-3.2").** That module is Python (`graph_rules.py`); a plain JavaScript page cannot import it, and IF-104 has no route that checks without saving. Options: (a) a JavaScript copy `graph_app/graph-rules.js` with the same five rules in the same order, plus a parity test in `tests/js/` that runs the same cases through `graph_rules.py` and the JS copy (a second implementation of the rules, a new part in the model); (b) the app checks only through the save (422 `invalid` with `rule` from the backend), so "in the app" means "named in the app" (no second copy, but no check before the request); (c) a new IF-104 route `POST /api/{kind}/{id}/check` (contract change). Recommendation: (a), with the parity test so the copies cannot drift; the backend still validates (TB-edit).
- **Q-3 (test-spec setup "unit test against the mock of IF-104").** The mock `tests/helpers/mocks/if_104_graph_api.py` is an in-process Python object; the Graph app is JavaScript that speaks the HTTP routes of IF-104. There is no JavaScript mock of IF-104 and no HTTP server around the Python mock. Options: (a) a protected `tests/helpers/mocks/if_104_graph_api.mjs` (fake `fetch` on the routes, same behaviour as the Python mock, the IF-104 contract suite extended to it), written outside this session as for IF-111/IF-112; (b) a small HTTP wrapper of the Python mock in `tests/helpers/` that the JS tests start; (c) a fake `fetch` inside each JS test file (not "the mock of IF-104", so TC-GA-002..008 would not meet their stated setup). Recommendation: (a), installed by the owner before T-02; it also gives the consumer side of TC-IF-104-01..05 named in T-03.
