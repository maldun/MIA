# Goal G-V4.REPLAY – Graph viewer: store the edits and play them back

Proposed 2026-11-20 by the owner (maldun), D-360. Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: Every edit made in the web app is stored as an operation of an edit log next to the graph versions, and the log can be played back on a graph.
- Exit criterion: replaying the log on the starting version gives the same graph as the stored version (tests still to be written in Plan)
- Subgoals: –
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.replay
- Depends on: G-V4.EDIT
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given the changes made in the web app to a graph, when the owner plays them back on the starting version, then the result is the graph as it was left | OC-8 of G-V4 (FR-22) |
| OC-2 | Given a graph changed in the web app, when the owner looks at the changes of a version, then every single change shows who made it, when, what it did and why, and two versions can be compared | OC-9 of G-V4 (FR-22) |

## Explore result (2026-11-20, D-363)
`../G-V4.VIEW/research.md`. Decisions: one edit-log entry per operation (add, remove or change a node or edge, change a field, move a node) with account, time, start version and a reason; a save closes a group that makes one graph version; replay applies the entries to the start version. Node positions are a side record, not part of the graph version and (D-371) not in the edit log either. Open for Plan: where the log is stored (a table of the storage layer), the retention, and how the existing history and diff relate to it.

## Source
Owner 2026-11-20: an edit log of operations, replayable on a graph (not only version stepping). Links to REQ-GA-004 (versions, history, diff).

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.REPLAY | [ ] Stefan Reiterer (owner) | |

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
