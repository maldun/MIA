# Goal G-V4.GRAPHAPI – The stored graph as a networkx DiGraph for execution

Proposed 2026-11-19 by the owner (maldun): the interface between the database and the execution of a workflow is a networkx directed graph. Depends on G-V4.GRAPHSTORE.

- Kind: subgoal
- Parent: G-V4
- Statement: A stored graph is turned into a networkx directed graph in one place, and the graph rules, the order of the nodes and the runner work on that graph.
- Exit criterion: OC-1 to OC-3 below, checked by tests still to be written in Plan (no ids yet)
- Supervision: supervised
- Accepted by: pending (the owner records the agreement in the table below)
- Line of work: goal/v4.graphapi (to be created)
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE (the loader reads the one stored form)
- Status: Proposed

## Where we are (checked in the code on 2026-11-19)
- No production module imports `networkx`. It was approved on 2026-11-07 (D-187, "graph rules") and is named in the goal files of G-V2 and G-V2.MODEL, but it is not in the requirements files and not in the code (only a spike input uses it).
- The same work is done by plain Python: `graph_rules.py` (cycle, adjacent data nodes, session stopping criterion), `graph_model.py` (`topological_order`), `graph_order.py` (order rule of converted skills), `graph_run.py` (`GraphRunner`, runs nodes in topological order). The interface between the stored graph and the runner today is a dict `{"nodes", "edges"}`.

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any stored graph, when a workflow is run or checked, then the stored graph reaches the execution as one directed graph, built in one place from the database | owner 2026-11-19 |
| OC-2 | Given the graphs and runs of the current tests, when the order, the rules and the run use the directed graph, then every result is the same as before (same order up to equal choices, same refusals with the same named nodes, same run result) | no regression |
| OC-3 | Given a graph with master nodes, session nodes or a transform that reads several data nodes, when it is loaded, then everything the runner needs (node kind, type, stop criterion, edge role and `as` name) is on the loaded graph | REQ-RUN-030 to 035 |

## Dependencies and bounds
| Item | Real or stand-in | Note |
|---|---|---|
| `networkx` | real | approved D-187; added to `requirements.txt` in Implement, never earlier (CLAUDE.md: no dependency without approval; re-confirm in Plan) |
| G-V4.GRAPHSTORE | real | a loader needs one stored form |
| Pipeline runner N-2.4.1, Workflow management N-2.3 | real | |

## Scope (candidate, to be confirmed in Plan)
| Item | In/Out | Reason |
|---|---|---|
| A loader module: stored graph (record form) to `networkx.DiGraph` with node and edge attributes | in | OC-1, OC-3 |
| Cycle check and topological order on the DiGraph | in | OC-2 |
| `graph_run` reads the DiGraph | in | OC-1 |
| Plain order and rule code | in | keep as a test oracle during the move, remove after the owner agrees |
| Drawing, layout, the Graph app | out | N-5 works through IF-104 |

## Decision of 2026-11-20 (D-360)
Code may be stored in a graph: a code snippet is a data node attached to a transform node, and the toolbox reference of the transform (for example a `python-exec` tool) calls it, with its trust and sandbox. The runner never executes code itself. It needs an entry in the threat model (untrusted code text in a stored graph) before Plan.

## Open questions (for the owner, before Plan)
1. Spike first? A short capability spike can check on real graphs that a master node, session nodes, edge roles and the `order` edge fit a DiGraph without loss. (Recommended before requirements are written.)
2. Is the DiGraph a read-only view for execution, or does the editor path (graph rules before saving) also build one?
3. Performance and memory bounds: none known; graphs are small (tens of nodes). Is a bound needed?

## Candidate tasks (not a plan)
1. Spike: load real stored graphs into a DiGraph and compare with `topological_order` and the rules (throwaway).
2. Requirements and red tests: loader, attributes, order, rules, run parity.
3. Loader and `graph_model` order on it; then the rules; then `graph_run`.
4. Remove the plain code after the oracle comparison and the owner's agreement.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI | [ ] Stefan Reiterer (owner) | |
