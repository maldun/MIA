# Goal G-V4.GRAPHAPI.RUN – The stored graph as one graph for the run

Proposed 2026-11-20 by the owner (maldun), D-392: G-V4.GRAPHAPI is cut into three smaller subgoals. Draft for Plan; the top-level requirements are those of the group's spec (`../G-V4.GRAPHAPI/top-level-spec.md`), allocated below.

- Kind: subgoal
- Parent: G-V4.GRAPHAPI
- Statement: A stored graph reaches the order of steps, the rules and the run as one graph built in one place, the steps run one after the other in a fixed order, and the six skills with equivalence suites run from their stored graph with the same results as before.
- Exit criterion: OC-1 to OC-4 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.graphapi.run
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE.CORE (the loader reads the stored form); G-V4.GRAPHAPI.RULES
- Status: Agreed
- History: agreed 2026-11-20; updated 2026-11-23 by D-473 (the path from a stored graph to a run is RUN's; networkx; NFR-17 rule) and D-474 (the nine user-interface skills and the removal of the old runner cut out to G-V4.GRAPHAPI.SWITCH); the update is to be agreed by the owner (Agreement)

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any stored graph, when a workflow is run or checked, then the stored graph reaches the execution as one graph, built in one place from the stored graph | OC-1 of G-V4.GRAPHAPI |
| OC-2 | Given the graphs and runs of the current tests, when the order, the rules and the run use that graph, then every result is the same as before | OC-2 of G-V4.GRAPHAPI |
| OC-3 | Given a graph with loop-controlling steps, session settings or a step that reads several data nodes, when it is loaded, then everything the run needs is on the loaded graph | OC-3 of G-V4.GRAPHAPI |
| OC-4 | Given each of the six skills with an equivalence suite (research, plan_question, verify_claim, verify_computable, extract_claims, extract_claims_rules) stored as a graph, when it runs from its stored graph, then its results on its dev suite are the same as on the old runner, by the rule of G-V2 against the old-runner baselines | OC-2 of G-V4.GRAPHAPI (D-473 (3)) |

## Scope
Inside the scope of G-V4.GRAPHAPI (`../G-V4.GRAPHAPI/goal.md`). The new requirements of the group's top-level spec that this part takes are named in "Source"; they are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-37 | in | the graph model, order of steps and run order: FR-65 of the group spec (one step after the other in a fixed order), and NFR-17 of the group spec for the six skills with equivalence suites on the stored-graph path (D-473 (3)); the nine without suites are G-V4.GRAPHAPI.SWITCH (D-474) |
| FR-6 | partly | skills run on the stored graph; the live trust, lifecycle, budgets and stop are parked in G-V5 |
| FR-7, FR-38, NFR-3 | out | the rules are G-V4.GRAPHAPI.RULES, code in graphs is G-V4.GRAPHAPI.CODE |

Also out: the nine user-interface skills and the removal of the old runner (G-V4.GRAPHAPI.SWITCH, D-474); storing the converted skills and switching a skill to its stored graph (G-V4.GRAPHSTORE.MIGRATION, through RUN's loader, D-473 (1)).

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| networkx (new dependency, owner D-473 (2)) | real | the loaded graph; version pinned in the high-level spec |
| MP-light `gemma4:12b-it-qat` (eval-spec.md) | real | the equivalence runs of OC-4; scripted replies in unit tests |
| the old-runner baselines of commit `1fb0c35` (A-122, D-244) | real | the reference of OC-4 for the five skills with a model; extract_claims_rules is compared with the old runner in the same check (D-477 (1)) |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| cut out the nine user-interface skills and the removal of the old runner | split (owner, D-474) | RUN finishes and is checked before the user-interface skills move; G-V4.GRAPHAPI.SWITCH after RUN | 2026-11-23 |
| cut again (the checker counts 26 to 42 requirements in scope) | keep together (proposed by the agent, the owner confirms in the plan review) | the number comes from the descendants of one or two top-level items, most of them verified in G-V1 and G-V2; the new work is a few requirements of the group spec; the cut into tasks follows in Plan step 5 | 2026-11-20 |

## Source
Group spec FR-65, NFR-17; `../G-V4.GRAPHAPI/spikes.md` (networkx spike); D-375; D-473, D-474 (survey of the run path, 2026-11-23: no production path from storage to a run yet; about seven places build their own view of a graph; the converted graphs of research and verify_computable have master steps, against the GRAPHSTORE spike).

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.4.1 Pipeline runner (graph run, converter) | real | the loader, the order, the run |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | stand-in | a fake storage serves stored graphs |
| N-4.1 Evaluation (suites, harness) | real | the suites of the converted skills |
| N-2.4.3 Run log | real | the run record gets the fields `graph` and `graph_version` (REQ-RUN-044; additive, no interface fixes the record's fields; Plan step 2, 2026-11-24) |
| local model server with the pinned models (Ollama) | real | the pinned model for the equivalence runs; scripted replies in unit tests |
| N-2.4.2 Tools and sandbox | stand-in | scripted tools |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHAPI.RUN | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.GRAPHAPI.RUN, update of 2026-11-23 (D-473, D-474) | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | the group's research, spikes and top-level spec (approved 2026-11-20, D-389, D-390) |
| Plan | open | step 0 (goal update, D-473, D-474) and step 1a (`high-level-spec.md`, D-475, D-476) reviewed, the owner's boxes open; step 1b (`requirements.md`) reviewed by group 2026-11-24 (D-477, D-478), the owner's signatures open; step 2 (A-187 text staged, `architecture.sysml`) drafted; step 3 (`test-spec.md`, `test-requirements.md`) reviewed by group 2026-11-24 (D-479), the owner's signatures open; next step 4 (oracle, red tests, A-187's suite and mock) |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
