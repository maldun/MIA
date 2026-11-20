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
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given the changes made in the web app to a graph, when the owner plays them back on the starting version, then the result is the graph as it was left | OC-8 of G-V4 (FR-16) |
| OC-2 | Given a graph changed in the web app, when the owner looks at the changes of a version, then every single change shows who made it, when, what it did and why, and two versions can be compared | OC-9 of G-V4 (FR-16) |

## Explore result (2026-11-20, D-363)
`../G-V4.VIEW/research.md`. Decisions: one edit-log entry per operation (add, remove or change a node or edge, change a field; moves are not among them, D-371) with account, time, start version, old and new value and an optional reason; undone changes are not logged; a save closes a group that makes one graph version; replay applies the entries to the start version. Node positions are a side record, not part of the graph version and (D-371) not in the edit log either. Retention: everything is kept (D-371). Open for Plan: where the log is stored (a table of the storage layer) and how the existing history and diff relate to it.

## Source
Owner 2026-11-20: an edit log of operations, replayable on a graph (not only version stepping). Links to REQ-GA-004 (versions, history, diff).

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-16 | partly | the edit log is a recorded history in the sense of FR-16 (FR-76 to FR-81, NFR-20); the run events themselves are not changed |
| REQ-GA-004 | out | its comparison part becomes FR-79 here, but the requirement as a whole is split in G-V4.EDIT's plan |
| FR-22 | out | the graph app is refined by the other subgoals; the edit log and playback are new items under FR-16 and FR-22, listed when Plan writes them |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-5 Graph app (page, vendored vis-network) | real | history, playback, comparison |
| N-2.1 API and accounts | stand-in | mocks of IF-104 v2 |
| N-3.3 Memories, history, feedback (record tables) | real | the table of the edit log |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | the log moves with the graph |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.REPLAY | [x] Stefan Reiterer (owner) | 2026-11-20 |

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
