# Goal G-V4.BUILDER – Tool to build context graphs

Proposed 2026-11-20 by the owner (maldun), D-380: a subgoal for the context-graph builder (goal C of iteration 2: FR-41, FR-42, node N-6), which G-V4.CONTEXT deliberately left out (D-379). Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: The owner can build up a context graph from documents and manual entry (runs, reviews and web results follow in a later slice, D-381) with a tool that proposes items with their source, lets the owner confirm them, and lets only confirmed items be read by steps.
- Exit criterion: OC-1 to OC-4 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.builder
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE (context graphs in the stored form), G-V4.CONTEXT (editing and the rules for categories and budgets), G-V4.VIEW
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a document the owner adds, when the builder runs, then it proposes items and relations, each with the passage it comes from, and no step reads a proposal before the owner has confirmed it | FR-42 |
| OC-2 | Given the proposals built from documents, when the owner marks a random sample of at least 120 of them, then at most 4 are marked invented and at least 91 right | FR-42 (owner's bar of 2026-11-05, sample plan of 2026-11-07) |
| OC-3 | Given a confirmed context graph, when a skill that names it runs, then the step reads the confirmed part within its token budget and the run records which graph and version it read | FR-41 |
| OC-4 | Given the builder with its limits, when a document is too large or too slow, then the builder stops at the limit and says so | FR-42 |

## Source
`specs/mia/requirements.md` FR-41, FR-42; `specs/mia/explore-skill-rework/` (interview rows 18 and 21, `spikes.md` spike C, `n6-sample-plan.md` with the candidate FR-42 text, evidence 113 right and 0 invented of 120 on branch `explore-n6-sample`). Spike C decided: LightRAG is not the builder (7.7 % invented, bar 5 %); the base is an own builder. Node N-6 is standalone with its own container (NFR-9).

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.BUILDER | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | in progress | `top-level-spec.md` drafted from FR-41, FR-42 and the N-6 notes; scope decided (D-381); item-by-item review open |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | covered by G-V4.VALIDATE |
