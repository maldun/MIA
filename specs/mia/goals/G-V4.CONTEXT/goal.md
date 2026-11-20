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
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a stored context graph, when the owner changes and keeps it in the web app, then the same versions and restore apply as for a workflow graph and a change that breaks a structural, category or budget rule is refused with the rule named | OC-8 of G-V4 (FR-22, FR-30) |
| OC-2 | Given a finished run, when the owner chooses to see its context graph, then the graph rebuilt from the run's events is drawn read-only and each item can be traced to the event that made it | OC-8 of G-V4 (FR-22, FR-16, FR-30) |

## Source
`../G-V4.EDIT/top-level-spec.md` (FR-75 moved here), REQ-GA-006 (approved in G-V1, assigned to EDIT by D-367, now to this subgoal). Open for the owner: whether viewing and storing context graphs (FR-48 of VIEW, FR-57 of GRAPHSTORE) stay where they are, and whether goal C (builder, categories as schemas) joins this subgoal later.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.CONTEXT | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | open | `top-level-spec.md` drafted from the moved requirement |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | covered by G-V4.VALIDATE |
