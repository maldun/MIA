# Goal G-V4.GRAPHAPI.RUN – The stored graph as one graph for the run

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHAPI is cut into three smaller subgoals. Draft for Plan; the top-level requirements are those of the group's spec (`../G-V4.GRAPHAPI/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHAPI
- Statement: A stored graph reaches the order of steps and the run as one graph built in one place, the steps run one after the other in a fixed order, and every converted skill gives the same results as before.
- Exit criterion: OC-1 to OC-3 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphapi.run
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE.CORE (the loader reads the stored form); G-V4.GRAPHAPI.RULES
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any stored graph, when a workflow is run or checked, then the stored graph reaches the execution as one graph, built in one place from the stored graph | OC-1 of G-V4.GRAPHAPI |
| OC-2 | Given the graphs and runs of the current tests, when the order, the rules and the run use that graph, then every result is the same as before | OC-2 of G-V4.GRAPHAPI |
| OC-3 | Given a graph with loop-controlling steps, session settings or a step that reads several data nodes, when it is loaded, then everything the run needs is on the loaded graph | OC-3 of G-V4.GRAPHAPI |

## Scope
Inside the scope of G-V4.GRAPHAPI (`../G-V4.GRAPHAPI/goal.md`). The new requirements of the group's top-level spec that this part takes are named in "Source"; they are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-37 | in | the graph model, order of steps and run order (FR-65, NFR-17 of the group spec) |
| FR-6 | partly | skills run on the stored graph; the live trust, lifecycle, budgets and stop are parked in G-V5 |
| FR-7, FR-38, NFR-3 | out | the rules are G-V4.GRAPHAPI.RULES, code in graphs is G-V4.GRAPHAPI.CODE |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| cut again (the checker counts 26 to 42 requirements in scope) | keep together (proposed by the agent, the owner confirms in the plan review) | the number comes from the descendants of one or two top-level items, most of them verified in G-V1 and G-V2; the new work is a few requirements of the group spec; the cut into tasks follows in Plan step 5 | 2026-11-20 |

## Source
Group spec FR-65, NFR-17; `../G-V4.GRAPHAPI/spikes.md` (networkx spike); D-375.

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.4.1 Pipeline runner (graph run, converter) | real | the loader, the order, the run |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | stand-in | a fake storage serves stored graphs |
| N-4.1 Evaluation (suites, harness) | real | the suites of the converted skills |
| local model server with the pinned models (Ollama) | real | the pinned model for the equivalence runs; scripted replies in unit tests |
| N-2.4.2 Tools and sandbox | stand-in | scripted tools |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI.RUN | [x] Stefan Reiterer (owner) | 2026-11-20 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | the group's research, spikes and top-level spec (approved 2026-11-20, D-389, D-390) |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
