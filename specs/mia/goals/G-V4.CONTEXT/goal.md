# Goal G-V4.CONTEXT – Context graphs in the graph app

Proposed 2026-11-20 by the owner (maldun), D-369: editing context graphs is its own subgoal of G-V4. Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: The owner can change a stored context graph in the web app with the same checks, versions and restore as a workflow graph.
- Exit criterion: OC-1, OC-2 (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.context
- Subgoals: –
- Depends on: G-V4.GRAPHSTORE (context graphs in the stored form), G-V4.VIEW, G-V4.EDIT (the editor)
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a stored context graph, when the owner changes and keeps it in the web app, then the same versions and restore apply as for a workflow graph and a change that breaks a structural, category or budget rule is refused with the rule named | OC-8 of G-V4 |
| OC-2 | Given a finished run, when the owner chooses to see its context graph, then the graph rebuilt from the run's events is drawn read-only and each item can be traced to the event that made it | OC-8 of G-V4 |

## Source
`../G-V4.EDIT/top-level-spec.md` (FR-75 moved here), REQ-GA-006 (approved in G-V1, assigned to EDIT by D-367, now to this subgoal). Settled by the owner: viewing stored context graphs stays in VIEW (FR-48) and storing them in GRAPHSTORE (FR-57); CONTEXT adds only the run's rebuilt context graph, read-only (FR-97; D-379, `../G-V4/consistency-review.md`). Goal C (builder, categories as schemas) does not join: it is G-V4.BUILDER, after CONTEXT (D-379, D-380).

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| REQ-GA-006 | in | edit a context graph (FR-75); the rules for categories and budgets are an extension of the one rule set (FR-7 of G-V4.GRAPHAPI) |
| FR-30 | out | the stored form of context graphs is G-V4.GRAPHSTORE; here only editing and the view of a run's context graph (FR-97) |
| REQ-GA-002, REQ-GA-003, REQ-GA-004 | out | the general editor is G-V4.EDIT; CONTEXT adds the context-graph part on top |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-5 Graph app (page, vendored vis-network) | real | context graph editing and the run view |
| N-3.2 Workflows and context graphs (graph tables, rules) | real | context tables and rules |
| N-2.4.3 Run log | real | the run log from which a run's context graph is rebuilt |
| N-2.1 API and accounts | stand-in | mocks of IF-104 v2 |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.CONTEXT | [x] Stefan Reiterer (owner) | 2026-11-20 |

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
