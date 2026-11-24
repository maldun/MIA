# Goal G-V4.BUILDER – Tool to build context graphs

Proposed 2026-11-20 by the owner (maldun), D-380: a subgoal for the context-graph builder (goal C of iteration 2: FR-41, FR-42, node N-6), which G-V4.CONTEXT deliberately left out (D-379). Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: The owner can build up a context graph from documents and manual entry (runs, reviews and web results follow in a later slice, D-381) with a tool that proposes items with their source, lets the owner confirm them, and lets only confirmed items be read by steps.
- Exit criterion: OC-1 to OC-5 (tests still to be written in Plan; OC-5 approved 2026-11-24, D-520)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.builder
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE (context graphs in the stored form), G-V4.CONTEXT (editing and the rules for categories and budgets), G-V4.VIEW, G-V4.GRAPHAPI.RUN (runs from stored graphs; the builder is a workflow, D-520)
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a document the owner adds, when the builder runs, then it proposes items, relations, definitions and stated facts, each with the passage it comes from, and no step reads a proposal before the owner has confirmed it | FR-42 |
| OC-2 | Given the proposals built from documents, when the owner marks random samples of the proposals, then the proposals meet the owner's quality bar for right and invented items, separately for items and relations and for definitions and facts (the sample sizes and limits are those of NFR-23 in the top-level spec) | FR-42 (owner's bar of 2026-11-05, sample plan of 2026-11-07) |
| OC-3 | Given a confirmed context graph, when a skill that names it runs, then the step reads the confirmed part within its token budget and the run records which graph and version it read | FR-41 |
| OC-4 | Given the builder with its limits, when a document is too large or too slow, then the builder stops at the limit and says so | FR-42 |
| OC-5 | Given the builder, when the owner opens it, then its steps are a workflow shown, checked and versioned like any other, and every builder run is recorded like any other run (approved 2026-11-24, D-520) | FR-42 (TLS FR-110) |

## Source
`specs/mia/requirements.md` FR-41, FR-42; `specs/mia/explore-skill-rework/` (interview rows 18 and 21, `spikes.md` spike C, `n6-sample-plan.md` with the candidate FR-42 text, evidence 113 right and 0 invented of 120 on branch `explore-n6-sample`). Spike C decided: LightRAG is not the builder (7.7 % invented, bar 5 %); the base is an own builder. Node N-6 is standalone with its own container (NFR-9).

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-41 | in | context graphs with categories as schemas, reading the confirmed part within a budget (FR-104) |
| FR-42 | in | the builder: proposals with source, confirmation, limits, the builder as a workflow (FR-98 to FR-103, FR-105, FR-110, NFR-23 to NFR-25) |
| FR-30 | out | the stored form is G-V4.GRAPHSTORE, editing G-V4.CONTEXT |
| NFR-3 | out | untrusted input for the builder is handled by NFR-25 of its spec; the graph-side rule is G-V4.GRAPHAPI |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-6 Context-graph builder (new; its workflow, checks and page; no container of its own, D-520) | real | the builder's workflow, its checks and its page in the web app |
| local model server with the pinned models (Ollama) | real | the pinned light model; scripted replies for unit tests |
| N-3.2 Workflows and context graphs (graph tables, rules) | real | context tables for the confirmed graph |
| N-2.4.1 Pipeline runner (graph run, converter) | real | runs the builder's workflow (D-520); a step reads the confirmed part within its budget |
| N-5 Graph app (page, vendored vis-network) | stand-in | the viewer is used as it is; no change here |
| documents | stand-in | the owner's sample documents and the marked samples |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.BUILDER | [x] Stefan Reiterer (owner) | 2026-11-20 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | `top-level-spec.md` approved 2026-11-20 (D-389 to D-391) |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
