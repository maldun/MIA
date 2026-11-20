# Goal G-V4.GRAPHSTORE.TRANSFER – Files and database interchangeable, move and sync

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHSTORE is cut into three smaller subgoals. Draft for Plan; the top-level requirements are those of the group's spec (`../G-V4.GRAPHSTORE/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHSTORE
- Statement: Graphs behave the same in the live store and in a set of files, the whole store moves between them without loss, and the copy is kept in sync with the live store, which wins.
- Exit criterion: OC-1, OC-2 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphstore.transfer
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE.CORE (one stored truth)
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given the same operations carried out in the live store and in a copy, when the answers are compared, then they are the same, including versions, authors and refusals | OC-5 of G-V4.GRAPHSTORE |
| OC-2 | Given a live store and a copy used for daily running, when the owner syncs them on command, at start and at an orderly stop, then the copy equals the live store and nothing that exists only on the copy is lost | OC-4 of G-V4.GRAPHSTORE |

## Scope
Inside the scope of G-V4.GRAPHSTORE (`../G-V4.GRAPHSTORE/goal.md`). The new requirements of the group's top-level spec that this part takes are named in "Source"; they are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| NFR-8 | in | files and database behave the same behind the storage interface (FR-58, FR-59, FR-93, NFR-15 of the group spec) |
| REQ-GA-008 | in | export and seed of the library moved here from the graph app (D-367) |
| FR-40, FR-30 | out | the stored truth itself is G-V4.GRAPHSTORE.CORE |
| FR-47, FR-36, FR-45 | out | snapshots, skills and migration are G-V4.GRAPHSTORE.MIGRATION |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| cut again (the checker counts 26 to 42 requirements in scope) | keep together (proposed by the agent, the owner confirms in the plan review) | the number comes from the descendants of one or two top-level items, most of them verified in G-V1 and G-V2; the new work is a few requirements of the group spec; the cut into tasks follows in Plan step 5 | 2026-11-20 |

## Source
Group spec FR-58, FR-59, FR-93, NFR-15; decisions D-372 to D-374; `../G-V4.GRAPHSTORE/spikes.md`.

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | both backends and the copy operation |
| N-3.2 Workflows and context graphs (graph tables, rules) | real | the tables that are moved |
| N-2.3 Workflow management (library, graph model, snapshots, toolbox) | stand-in | not needed; operations are called directly |
| compose stack and web routing (Caddy) | stand-in | a second machine is simulated by a second folder |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHSTORE.TRANSFER | [x] Stefan Reiterer (owner) | 2026-11-20 |

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
