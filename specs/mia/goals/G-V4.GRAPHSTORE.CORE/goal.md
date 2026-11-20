# Goal G-V4.GRAPHSTORE.CORE – One stored truth for graphs

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHSTORE is cut into three smaller subgoals. Draft for Plan; the top-level requirements are those of the group's spec (`../G-V4.GRAPHSTORE/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHSTORE
- Statement: Every workflow and every context graph has exactly one stored truth, its steps and connections belong to that graph alone, and a refused or interrupted save never leaves a half-stored graph.
- Exit criterion: OC-1 to OC-3 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphstore.core
- Subgoals: –
- Depends on: –; first of the group
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a workflow graph or a context graph, when it is saved, read, changed and listed, then there is one stored truth for it, with every edit a new version and no version deleted | OC-1 of G-V4.GRAPHSTORE |
| OC-2 | Given two graphs with a step of the same local name but different content, when one is changed, then the other graph and its history are untouched | OC-1 of G-V4.GRAPHSTORE |
| OC-3 | Given a save that is refused or interrupted, when graphs are read afterwards, then each is entirely as before or entirely new and a refused save is no version | OC-1 of G-V4.GRAPHSTORE |

## Scope
Inside the scope of G-V4.GRAPHSTORE (`../G-V4.GRAPHSTORE/goal.md`). The new requirements of the group's top-level spec that this part takes are named in "Source"; they are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-40 | in | one stored truth, versions, graph-scoped steps (FR-57, FR-60, NFR-16 of the group spec); the scoped-ID amendment of A-92 / REQ-GTB-021 |
| FR-30 | partly | context graphs share the stored form; their content and editing are other subgoals |
| REQ-GA-006 | out | editing context graphs is G-V4.CONTEXT |
| NFR-8, FR-47, FR-36, FR-45, REQ-GA-008 | out | interchange of files and database and the transfer are G-V4.GRAPHSTORE.TRANSFER; snapshots, skills and migration are G-V4.GRAPHSTORE.MIGRATION |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| cut again (the checker counts 26 to 42 requirements in scope) | keep together (proposed by the agent, the owner confirms in the plan review) | the number comes from the descendants of one or two top-level items, most of them verified in G-V1 and G-V2; the new work is a few requirements of the group spec; the cut into tasks follows in Plan step 5 | 2026-11-20 |

## Source
Group spec FR-57, FR-60, NFR-16; `../G-V4.GRAPHSTORE/research.md`, `spikes.md` (finding S1); D-368.

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | files backend; PostgreSQL for the contract suite |
| N-3.2 Workflows and context graphs (graph tables, rules) | real | tables and the refusal of unscoped IDs |
| N-2.3 Workflow management (library, graph model, snapshots, toolbox) | stand-in | a fake library on the storage mock |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHSTORE.CORE | [x] Stefan Reiterer (owner) | 2026-11-20 |

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
