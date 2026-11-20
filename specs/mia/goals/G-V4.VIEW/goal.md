# Goal G-V4.VIEW – Graph viewer: pull from the data source and draw

Proposed 2026-11-20 by the owner (maldun), D-360. Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: A minimal prototype of the Graph app (N-5) reads a stored graph through the backend API from the real data source (files or database) and draws it in the web app.
- Exit criterion: the same graph is drawn from the files and from the database, as the owner checks in the web app (tests still to be written in Plan)
- Subgoals: –
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.view
- Depends on: G-V4.GRAPHSTORE (one stored form; IF-104 stays or is amended)
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a stored graph in the live store or in a set of files, when the owner opens it in the web app, then the graph is drawn with all its steps and connections, and it is the same picture from either place | OC-8 of G-V4 (FR-22) |

## Explore result (2026-11-20, D-363)
`research.md` (shared by VIEW, EDIT, REPLAY). Prototype `prototype/graphview` (accepted by the owner, never merged): 15 of 15 stored graphs are pulled from files and from PostgreSQL and drawn completely; report `prototypes/graphview/prototype-report.md` on that branch (commit `e263f361`), carry-over table with proposed decisions for the owner to tick. The owner looked at it and asked for the detail panel on the left, vis-network physics, rounded edges and a settings menu; all four are in the prototype. Physics makes the layout non-reproducible, so REQ-GA-001 ("physics off") needs an amendment and saved positions (D-363) carry the stable picture. Open for Plan: the graph interface for the record form (amendment of IF-104), master nodes in the view, context graphs (Q-5), routing between the two containers.

## Source
N-5 log (`nodes/N-5-graph-app/implementation-log.md`): T-01 is a vis-network mockup that opens a JSON file; IF-104 mock A-36 is drafted, not installed; Q-5 and Q-6 (context graphs, node positions) open.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.VIEW | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | `research.md`, prototype `prototype/graphview` (report, carry-over to be ticked by the owner), D-363 |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | covered by G-V4.VALIDATE |
