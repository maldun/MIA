# Goal G-V4.REPLAY – Graph viewer: store the edits and play them back

Proposed 2026-11-20 by the owner (maldun), D-360. Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: Every edit made in the web app is stored as an operation of an edit log next to the graph versions, and the log can be played back on a graph.
- Exit criterion: replaying the log on the starting version gives the same graph as the stored version (tests still to be written in Plan)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.replay (to be created)
- Depends on: G-V4.EDIT
- Status: Proposed

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
