# Goal G-V4.GRAPHAPI.SWITCH – Every skill on the graph path, the old runner removed

Proposed 2026-11-23 by the agent on the owner's split decision (D-474): G-V4.GRAPHAPI.RUN grew by D-473 (every skill to the graph path, the old runner removed) and is cut in two. Draft for Plan; agreement by the owner below is still open.

- Kind: subgoal
- Parent: G-V4.GRAPHAPI
- Statement: The skills that still run on the old runner run on their graph with the same results, and the old runner is removed, so that a skill has one way of running.
- Exit criterion: OC-1 and OC-2 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphapi.switch
- Subgoals: –
- Depends on: G-V4.GRAPHAPI.RUN (the loader, one graph for order, rules and run, NFR-17 decided for the six suite skills); G-V4.GRAPHSTORE.MIGRATION where a skill runs from its stored graph
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given each of the skills kept on the old runner as part of the user interface (chat, check_speech, memory_write, review_abstract, review_full, review_keywords, review_section, review_summary, summarize), when it runs on its graph with the same scripted model replies, then it makes the same model calls and gives the same outputs as on the old runner, and the owner sees no difference in the app | OC-2 of G-V4.GRAPHAPI (D-473 (3); the owner's decision of 2026-11-07 revisited) |
| OC-2 | Given MIA after the switch, when any skill runs, then it runs on its graph; there is no second way of running a skill | OC-1 of G-V4.GRAPHAPI (D-473 (4)) |

## Scope
Inside the scope of G-V4.GRAPHAPI (`../G-V4.GRAPHAPI/goal.md`); the items are named when Plan step 1b writes them.

| Item | In/Out | Reason |
|---|---|---|
| FR-37 | out | the graph model, the order and the run are G-V4.GRAPHAPI.RUN's; SWITCH uses them |

Its items are named in its Plan, after RUN's plan is approved (D-474); SWITCH starts only after RUN, so no item is shared while both run and nothing needs freezing. In words: the nine skills without suites on their graph (NFR-17 of the group spec, by scripted replies, D-473 (3)); skills run on their graph (part of FR-6; live trust, lifecycle, budgets and stop stay parked in G-V5); the order and the run (FR-65 of the group spec) and the six skills with suites are RUN's.

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| cut from RUN | split (owner, D-474) | the user-interface skills carry their own risk and the owner's look in the app; RUN can finish and be checked before they move | 2026-11-23 |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.4.1 Pipeline runner (graph run, converter) | real | the old runner is removed |
| N-2 the app (chat, speech) | real | the user-interface skills |
| local model server with the pinned models (Ollama) | stand-in | scripted replies decide; the owner's look uses the pinned model |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI.SWITCH | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | the group's research and top-level spec (D-389, D-390); the cut from RUN (D-473, D-474) |
| Plan | open | after RUN's plan is approved |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
