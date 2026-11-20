# Goal G-V4.EDIT – Graph viewer: editing in the web app

Proposed 2026-11-20 by the owner (maldun), D-360. Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: The owner edits nodes and edges of a graph in the web app, and the graph rules are applied before a change is saved.
- Exit criterion: an edit of a valid graph is saved as a new version and a rule-breaking edit is refused with the rule named (tests still to be written in Plan)
- Subgoals: –
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.edit
- Depends on: G-V4.VIEW; G-V4.GRAPHAPI (rules on the directed graph)
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a stored graph open in the web app, when the owner changes it in a way that keeps the graph rules, then the change is kept as a new version and the earlier version stays reachable | OC-8 of G-V4 (FR-22) |
| OC-2 | Given a change that breaks a graph rule, when the owner tries to keep it, then it is refused and the broken rule is named | OC-8 of G-V4 (FR-22) |

## Source
REQ-GA-002, REQ-GA-003 (N-5 T-02, open Q-2: where the rules run in the page); the backend still validates (TB-edit).

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.EDIT | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | open | |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | covered by G-V4.VALIDATE |
