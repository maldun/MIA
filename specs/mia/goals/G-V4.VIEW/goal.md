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
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a stored graph in the live store or in a set of files, when the owner opens it in the web app, then the graph is drawn with all its steps and connections, and it is the same picture from either place | OC-8 of G-V4 (FR-22) |
| OC-2 | Given a graph with several stored versions, when the owner opens its history, then the versions are listed with who stored each and when, and any one can be looked at | OC-8 of G-V4 (FR-22) |

## Explore result (2026-11-20, D-363)
`research.md` (shared by VIEW, EDIT, REPLAY). Prototype `prototype/graphview` (accepted by the owner, never merged): 15 of 15 stored graphs are pulled from files and from PostgreSQL and drawn completely; report `prototypes/graphview/prototype-report.md` on that branch (commit `e263f361`), carry-over table with proposed decisions for the owner to tick. The owner looked at it and asked for the detail panel on the left, vis-network physics, rounded edges and a settings menu; all four are in the prototype. Physics makes the layout non-reproducible, so REQ-GA-001 ("physics off") needs an amendment and saved positions (D-363) carry the stable picture. Open for Plan: the graph interface for the record form (amendment of IF-104), master nodes in the view, context graphs (Q-5), routing between the two containers.

## Source
N-5 log (`nodes/N-5-graph-app/implementation-log.md`): T-01 is a vis-network mockup that opens a JSON file; IF-104 mock A-36 is drafted, not installed; Q-5 and Q-6 (context graphs, node positions) open.

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| REQ-GA-001 | in | show a graph as nodes and edges; superseded by FR-48 to FR-55 and FR-96 (D-367) |
| REQ-GA-005 | in | the viewer works only through the graph interface IF-104 (v2, frozen at G-V4 level) |
| REQ-GA-007 | in | login required; NFR-12 refines it |
| REQ-GA-009 | in | plain page, vendored library (vis-network 10.1.2), no build step |
| REQ-GA-010 | in | no outside request; superseded by NFR-13 (D-367) |
| REQ-GA-011 | in | own container; the routing between page and backend is checked in the plan |
| REQ-GA-002, REQ-GA-003, REQ-GA-004 | out | editing, rule checks, saving and restore are G-V4.EDIT; comparison is G-V4.REPLAY (the history list is a new item of VIEW) |
| REQ-GA-006, REQ-GA-008 | out | context graph editing is G-V4.CONTEXT; export and seed are G-V4.GRAPHSTORE |
| FR-21, NFR-6, NFR-9 | out | accounts, secure access and containers as a whole are not changed; the viewer meets them through REQ-GA-007 and REQ-GA-011 |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-5 Graph app (page, vendored vis-network) | real | the page and the vendored library |
| N-2.1 API and accounts | stand-in | JS mock of IF-104 v2 for the page tests; real in the end-to-end check |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | files and the database behind the real backend for the demonstration |
| compose stack and web routing (Caddy) | real | one origin and session for page and API |
| local model server with the pinned models (Ollama) | real | for the search by description (FR-96); scripted replies in unit tests |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.VIEW | [x] Stefan Reiterer (owner) | 2026-11-20 |

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
