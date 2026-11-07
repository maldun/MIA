# Goal G-V2 – Skill rework, foundation (candidate goal A)

Drafted 2026-11-07 in Plan Step 0 from the approved HLS of iteration 2 (D-186). Scope decided by the owner on 2026-11-07: **goal A only**; B (skills window), C (context graphs, N-6) and D (testbench, debates) stay in the HLS and are planned later, in this order.

- Kind: iteration
- Parent: –
- Statement: Every existing skill runs from the new records (skill record, workflow graph of data, transform and master nodes, graphs stored as node and edge records, toolbox with trust status), or stays on the old runner for a named reason, with the same outcomes on its suite; the owner can take and restore a snapshot of the skill set.
- Exit criterion: AC-34 (per-skill equivalence with v0.1.0 on the same suite and pins) together with AC-31, AC-32, AC-38 and AC-40; a validation criterion VAL-007 is written in Plan Step 3 (not yet existing)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v2
- Subgoals: –
- Status: Proposed

## Scope
Acceptance criteria in scope: AC-31, AC-32, AC-34, AC-38, AC-40. Out: AC-33, AC-35, AC-36, AC-37, AC-39. Amendments carried by this goal: A-89 (FR-7, FR-22, FR-30 entries) and conflicts 1 to 3 of the Explore hand-over (owner-only trust marking as exception to CON-6; FR-40 against IF-301/IF-203; imported transforms untrusted, SC-09). Open for Plan: numbers inside the in-scope criteria (for example the conversion margin).

| Item | In/Out | Reason |
|---|---|---|
| FR-1 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-2 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-3 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-4 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-5 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-6 | partly | skill files and pipeline references are replaced by the skill record (FR-36); behaviour of chat/lookup/summarize stays, shown by the equivalence check |
| FR-7 | partly | revised by FR-37 (node types) and FR-40 (storage); amendment-style entry from note A-89 |
| FR-8 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-9 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-10 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-11 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-12 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-13 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-14 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-15 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-16 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-17 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-18 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-19 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-20 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-21 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-22 | partly | only the amendment of editing rights (A-89, SC-09); the redesigned window itself is goal B |
| FR-23 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-24 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-25 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-26 | partly | the per-workflow specification stays; the testbench with budgets (FR-44) is goal D |
| FR-27 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-28 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-29 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-30 | partly | only the amendment 'one context graph per skill by ID' (A-89); the context graph itself is goal C |
| FR-31 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-32 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-33 | out | built in G-V1 (v0.1.0); this goal does not change it |
| FR-34 | out | FB-01 skills panel and chat turns: replaced by FR-46 (goal B) |
| FR-35 | out | FB-01 skills panel and chat turns: replaced by FR-46 (goal B) |
| FR-36 | in | skill definition record |
| FR-37 | in | workflow graph model: data, transform, master node types; master node definition only as a record, debates run in goal D |
| FR-38 | in | toolbox with status untrusted/tested/trusted; exchange format; no review process, imported transforms are stored, not runnable (SC-09) |
| FR-39 | out | goal D (debates) |
| FR-40 | in | storage of graphs as node/edge records; amendment of IF-301 and IF-203 and their contract suites; document form stays readable during the transition |
| FR-41 | out | goal C (context graph) |
| FR-42 | out | goal C (N-6, standalone builder) |
| FR-43 | out | goal B (skills window) |
| FR-44 | out | goal D (testbench and budgets); conversion uses the existing suites |
| FR-45 | in | per-skill conversion with the equivalence check on the same suite and pins |
| FR-46 | out | goal B |
| FR-47 | in | snapshots of the skill set |
| NFR-1 | out | built in G-V1 (v0.1.0); this goal does not change it |
| NFR-2 | out | built in G-V1 (v0.1.0); this goal does not change it |
| NFR-3 | partly | applies to the toolbox: an untrusted transform never runs (TB-exchange) |
| NFR-4 | in | kept as built |
| NFR-5 | out | built in G-V1 (v0.1.0); this goal does not change it |
| NFR-6 | out | built in G-V1 (v0.1.0); this goal does not change it |
| NFR-7 | in | kept as built |
| NFR-8 | out | built in G-V1 (v0.1.0); this goal does not change it |
| NFR-9 | partly | only AC-38: the stack still starts all containers; the container of N-6 comes with goal C |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-3 storage (graph records) | real | node and edge tables, rebuild from type ID |
| N-2 runner and library (skill record, graph model, toolbox, converter, snapshots) | real | old runner stays side by side until a skill passes its equivalence check |
| N-5 graph app | stand-in | unchanged static page; redesign is goal B |
| N-6 context-graph builder | stand-in | not built; goal C |
| model server (Ollama) | real | pins from `eval-spec.md`, 12B for tests |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | no subgoals |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| – | – | no subgoals |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | HLS of iteration 2 approved 2026-11-05 (D-186) |
| Plan | in progress | started 2026-11-07, Step 0 |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
