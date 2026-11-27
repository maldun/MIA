# Goal G-V4.GRAPHAPI – The stored graph as a networkx DiGraph for execution

Proposed 2026-11-19 by the owner (maldun): the interface between the database and the execution of a workflow is a networkx directed graph. Depends on G-V4.GRAPHSTORE.

- Kind: subgoal
- Parent: G-V4
- Statement: A stored graph reaches the checks and the runner as one graph, built in one place, and the graph rules, the order of the steps and the run all work on it (networkx is the chosen means, a decision for the high-level spec).
- Exit criterion: OC-1 to OC-3 below, checked by tests still to be written in Plan (no ids yet)
- Supervision: supervised
- Accepted by: pending (the owner records the agreement in the table below)
- Line of work: goal/v4.graphapi
- Subgoals: G-V4.GRAPHAPI.RULES, G-V4.GRAPHAPI.RUN, G-V4.GRAPHAPI.SWITCH (after RUN, D-474), G-V4.GRAPHAPI.CODE
- Depends on: G-V4.GRAPHSTORE (the loader reads the one stored form)
- Status: Agreed

## Where we are (checked in the code on 2026-11-19)
- No production module imports `networkx`. It was approved on 2026-11-07 (D-187, "graph rules") and is named in the goal files of G-V2 and G-V2.MODEL, but it is not in the requirements files and not in the code (only a spike input uses it).
- The same work is done by plain Python: `graph_rules.py` (cycle, adjacent data nodes, session stopping criterion), `graph_model.py` (`topological_order`), `graph_order.py` (order rule of converted skills), `graph_run.py` (`GraphRunner`, runs nodes in topological order). The interface between the stored graph and the runner today is a dict `{"nodes", "edges"}`.

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any stored graph, when a workflow is run or checked, then the stored graph reaches the execution as one graph, built in one place from the stored graph | OC-7 of G-V4 (FR-6) |
| OC-2 | Given the graphs and runs of the current tests, when the order, the rules and the run use the directed graph, then every result is the same as before (same order up to equal choices, same refusals with the same named nodes, same run result) | OC-7 of G-V4 (FR-6) |
| OC-3 | Given a graph with master nodes, session nodes or a transform that reads several data nodes, when it is loaded, then everything the runner needs (node kind, type, stop criterion, edge role and `as` name) is on the loaded graph | OC-7 of G-V4 (REQ-RUN-030 to 035) |
| OC-4 | Given a graph that breaks several rules, when it is checked while saving, while editing and before a run, then the same broken rules are listed in the same order and a run is refused before any step runs | FR-7 (OC-7 of G-V4) |
| OC-5 | Given a graph with a code step, when the owner has not trusted it, then the run is refused; when trusted, it runs only through its trusted tool, and a changed step keeps its trust with a mark | FR-38, NFR-3 (OC-7 of G-V4) |

## Dependencies and bounds
| Item | Real or stand-in | Note |
|---|---|---|
| `networkx` | real | approved D-187; added to `requirements.txt` in Implement, never earlier (CLAUDE.md: no dependency without approval; re-confirm in Plan) |
| G-V4.GRAPHSTORE | real | a loader needs one stored form |
| Pipeline runner N-2.4.1, Workflow management N-2.3 | real | |


## Explore result (2026-11-20, D-362)
`research.md`, `spikes.md`. The loader must keep several edges between two nodes (a `MultiDiGraph`). Two sets of graph rules exist and must become one. Open for Plan: the single rule set and its order, whether the run applies the rules (today it does not, F4), the threat entry THR-013.

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

## Split into parts (owner, 2026-11-20, D-392)
Three parts: **RULES** (eight rules in one order, refusal before running; independent of storage), **RUN** (the stored graph as one graph for the order and the run, equivalence with the old runner; needs GRAPHSTORE.CORE and RULES) and **CODE** (code steps through trusted tools, trust kept with a mark, THR-013; needs RUN). The requirements of the group's top-level spec are allocated: RULES FR-63, FR-64; RUN FR-65, NFR-17; CODE FR-66, FR-67.

**Fourth part (owner, 2026-11-23, D-473, D-474):** RUN now also moves every skill to the graph path and removes the old runner (D-473); this is cut: **RUN** keeps the loader, one networkx graph for order, rules and run, the six skills with equivalence suites on the stored-graph path and NFR-17 decided on their suites; **SWITCH** (after RUN) moves the nine skills the owner kept on the old runner as part of the user interface (2026-11-07), checked by scripted replies and the owner's look in the app, then removes the old runner with the owner's agreement.

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-7 | in | one set of eight graph rules in one fixed order (FR-63, FR-64) |
| FR-37 | in | the graph model: rules, order of steps, run order (FR-63 to FR-65) |
| FR-6 | partly | skills run on the stored graph (FR-65, NFR-17); the live trust, lifecycle, budgets and stop are parked in G-V5 |
| FR-38 | partly | code in a graph runs only through a trusted tool and step; trust stays on change with a mark (FR-66, FR-67); exchange of transforms is unchanged |
| NFR-3 | in | stored code and imported steps stay data until the toolbox runs them (THR-013); harmful imports with a recorded case are parked in G-V5 |
| REQ-GA-003 | out | graph rules before saving are refined in G-V4.EDIT, which asks the backend check route; the rules themselves are FR-7 here |
| FR-16 | out | the run record naming the graph and version is a requirement under FR-6 here; the edit log is G-V4.REPLAY |
| FR-30, FR-36, FR-40, FR-45, FR-47, NFR-8 | out | storing, moving and snapshots are G-V4.GRAPHSTORE |
| FR-21, FR-22, FR-41, FR-42, NFR-6, NFR-9 | out | the graph app, access, the builder and containers are other subgoals |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.4.1 Pipeline runner (graph run, converter) | real | the runner |
| N-2.4.2 Tools and sandbox | real | code steps |
| N-2.3 Workflow management (library, graph model, snapshots, toolbox) | real | toolbox and trust |
| N-3.2 Workflows and context graphs (graph tables, rules) | real | rules at the storage door |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | stand-in | a fake storage for the unit tests |
| N-4.1 Evaluation (suites, harness) | real | equivalence suites |
| local model server with the pinned models (Ollama) | real | for the equivalence runs; scripted replies elsewhere |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|

None yet; the shared interfaces are marked in the next step of Plan step 0.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI.RULES | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.GRAPHAPI.RUN | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.GRAPHAPI.SWITCH | [ ] Stefan Reiterer (owner) | |
| G-V4.GRAPHAPI.CODE | [x] Stefan Reiterer (owner) | 2026-11-20 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | research and spikes in this folder, `top-level-spec.md` approved 2026-11-20 (D-389 to D-391) |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
