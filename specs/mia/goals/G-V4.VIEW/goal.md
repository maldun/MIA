# Goal G-V4.VIEW – Graph viewer: pull from the data source and draw

Proposed 2026-11-20 by the owner (maldun), D-360. Draft for Explore and Plan; no requirements or tests exist yet.

- Kind: subgoal
- Parent: G-V4
- Statement: The Graph app (N-5) gets its whole frame (the owner's layout, D-425) and, inside it, a read-only viewer that reads stored graphs through the graph interface IF-104 v2 from the real data source (files or database, chosen by configuration) and draws them; the areas of EDIT, REPLAY and RUN are in the frame but stay empty until their subgoals fill them.
- Exit criterion: OC-1 to OC-8 shown (OC-7 through the IF-104 v2 contract suite on the real backend) on the owner's host: the same graphs listed and drawn from the files and from the database, as the owner checks in the web app, with the acceptance cases AC-009 to AC-013, AC-015, AC-016, AC-035 met and AC-014 met up to its save step (the save step is witnessed in EDIT, D-425 B)
- Subgoals: –
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4.view
- Depends on: G-V4.GRAPHSTORE.CORE (verified, one stored form); IF-104 v2, written by VIEW's own plan as amendment A-171 (D-425 A; the D-368 prerequisite); G-V4.GRAPHSTORE.TRANSFER carries the record table `arrangements` that VIEW introduces (D-425 B). Not needed: G-V4.GRAPHAPI.RULES (IF-301 v4 `kinds()` is used once RULES is merged), RUN. Order: VIEW is planned ahead of TRANSFER and RUN (D-425).
- Status: Agreed
- History: agreed 2026-11-20; statement, exit criterion, outcome criteria and scope updated and agreed by the owner 2026-11-22 (D-430), the backend side of EDIT and REPLAY items added by D-430 (7), the look by D-431

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given stored graphs in the live store or in a set of files, when the owner opens the graph app, then all of them are listed with their kind, the list narrows by part of a name or description, and the chosen graph is drawn with all its steps and connections; it is the same list and the same picture from either place, and what cannot be drawn is named beside the picture | OC-8 of G-V4 (FR-22); FR-48, FR-49, REQ-GA-005 |
| OC-2 | Given a graph with several stored versions, when the owner opens its history, then the versions are listed newest first with who stored each and when, and any one can be looked at, read-only | OC-8 of G-V4 (FR-22); FR-55 |
| OC-3 | Given a drawn graph, when the owner looks at it, then the kinds of step differ by shape and words, steps that need attention (untrusted, changed since trusted, code) carry a small mark, and selecting a step or connection shows its full content read-only in the left column; text inside a graph is shown as text only | FR-50, FR-51, FR-54 (D-426) |
| OC-4 | Given a graph, when it is opened, then it uses the arrangement saved for it if there is one, otherwise it settles the same way on every opening; the owner can move steps, return to a layered arrangement and change the look in one settings place, remembered on that device | FR-52, FR-53 (D-425 B) |
| OC-5 | Given the graph app, when the owner opens it, then the whole frame of the owner's layout is there (graph list, search band, other things, left column, picture, actions, history and replay row, graph status); the status shows the version and who stored it; the areas of later subgoals are present but empty, and nothing can be changed | layout of D-425; FR-22, NFR-10 |
| OC-6 | Given someone not logged in, nothing is shown; given the owner logged in once, no second login is needed; while it is used nothing is requested from outside, it reads in light and dark and works by keyboard, and opening a graph of about fifty steps is not a wait | NFR-11 to NFR-14, REQ-GA-007, REQ-GA-010 |
| OC-7 | Given the store behind the graph app, when a changed graph is handed to it, then the owner's change is kept as a new version with who and when, a change based on an older version or from another account is refused with the reason, a restore keeps the former content as a new version, a saved arrangement is the one the next opening uses, a graph that breaks a rule is refused with the rule named, and every kept version has its record of changes; if the store cannot be reached, nothing is changed and that is said | FR-70 to FR-74, FR-95, NFR-19, FR-76, FR-77, FR-80, FR-81 (backend side, D-430) |
| OC-8 | Given the main app and the graph app side by side, when the owner looks at both in light and in dark, then they share fonts, colours, panels and controls | NFR-14 (D-431) |

## Explore result (2026-11-20, D-363)
`research.md` (shared by VIEW, EDIT, REPLAY). Prototype `prototype/graphview` (accepted by the owner, never merged): 15 of 15 stored graphs are pulled from files and from PostgreSQL and drawn completely; report `prototypes/graphview/prototype-report.md` on that branch (commit `e263f361`), carry-over table with proposed decisions for the owner to tick. The owner looked at it and asked for the detail panel on the left, vis-network physics, rounded edges and a settings menu; all four are in the prototype. Physics makes the layout non-reproducible, so REQ-GA-001 ("physics off") needs an amendment and saved positions (D-363) carry the stable picture. Open for Plan then: the graph interface for the record form (amendment of IF-104), master nodes in the view, context graphs (Q-5), routing between the two containers. Settled since: master nodes by prototype round 02; context graphs drawn generically (D-425 C); routing by `deploy/Caddyfile` (`/graph/` to the graph app's container, D-133); the interface by A-171 (D-425 A).

## Source
N-5 log (`nodes/N-5-graph-app/implementation-log.md`): T-01 is a vis-network mockup that opens a JSON file; the IF-104 v1 mocks of A-36 are installed (`tests/helpers/mocks/if_104_graph_api.py`, `.mjs`); Q-5 and Q-6 (context graphs, node positions) are settled by D-425 (C, B).

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-48 | in | list, filter by name or description (AC-009), kind named; a graph of an unknown kind drawn plain and read-only; listing kinds from a newer store comes with TRANSFER/MIGRATION (D-415 Q-7) |
| FR-49 | in | draw every step and connection; problems are only what cannot be drawn (D-425 A); rule reports are EDIT's |
| FR-50 | in | kinds by shape and words; minimal mark on steps that need attention, full text in the left column (D-426) |
| FR-51 | in | read-only content in the left column (D-425 layout) |
| FR-52 | in | reads a saved arrangement; physics with a fixed seed; layered reset; saving the arrangement is EDIT's FR-74 (D-425 B) |
| FR-53 | in | one settings place, remembered on the device |
| FR-54 | in | text only; code steps marked (D-426) |
| FR-55 | in | history list and earlier versions, read-only |
| NFR-10 | in | validation criterion (first use without help) |
| NFR-11 | in | no hard bound; a measured smoke number (D-425 E-H) |
| NFR-12 | in | login required, one login; refines REQ-GA-007 |
| NFR-13 | in | nothing from outside; automated check plus validation; supersedes REQ-GA-010 |
| NFR-14 | in | light and dark, keyboard: validation criteria with automated parts (keyboard reach); in the main app's look, its design tokens copied unchanged and kept identical (D-431) |
| FR-70 to FR-74, FR-95, NFR-19 (backend side) | in | D-430 (7): the real backend serves all IF-104 v2 routes (check, save as a new version, conflict refused, restore, arrangement save, store unreachable, owner only); the page side of these items stays G-V4.EDIT; the check route uses IF-301 v4 once RULES is merged |
| FR-76, FR-77, FR-80, FR-81 (backend side) | in | D-430 (7): the write-once record of changes behind the `changes` route, a table of the IF-302 amendment; playback and comparison (FR-78, FR-79) stay G-V4.REPLAY |
| FR-96 | out | search by description is its own later slice (D-425 E-H); the band keeps its place in the frame |
| REQ-GA-001 | in | show a graph as nodes and edges; superseded by FR-48 to FR-55 (D-367); its "physics off" text is amended (D-425 B) |
| REQ-GA-005 | in | the viewer works only through the graph interface IF-104 v2 (frozen at G-V4 level) |
| REQ-GA-007 | in | login required; NFR-12 refines it |
| REQ-GA-009 | in | plain page, vendored library (vis-network 10.1.2), no build step |
| REQ-GA-010 | in | no outside request; superseded by NFR-13 (D-367) |
| REQ-GA-011 | in | own container; `/graph/` routed by Caddy (D-133) |
| REQ-GA-002, REQ-GA-003, REQ-GA-004 | out | editing, rule checks, saving and restore are G-V4.EDIT; comparison is G-V4.REPLAY (the history list is a new item of VIEW) |
| REQ-GA-006, REQ-GA-008 | out | context graph editing is G-V4.CONTEXT; export and seed are G-V4.GRAPHSTORE |
| FR-21, NFR-6, NFR-9 | out | accounts, secure access and containers as a whole are not changed; the viewer meets them through REQ-GA-007 and REQ-GA-011 |

Not yet a top-level item: the chat with MIA about the open graph, a new item for a later goal (D-425 layout); its band keeps its place in the frame.

## Split check
Thirteen top-level items in scope (FR-48 to FR-55, NFR-10 to NFR-14) plus the IF-104 v2 amendment: above the size signal of about 8. Owner 2026-11-22 (D-430 (2)): one goal, two tracks: the interface and backend track first (IF-104 v2 with mocks and contract suite, IF-302 tables, all routes, store setting), then the page track (frame, viewer, browser checks). With the backend side of EDIT and REPLAY added (D-430 (7)) the goal holds about 25 items; the agent suggested subgoals G-V4.VIEW.API and G-V4.VIEW.PAGE; the owner keeps one goal and splits the effort within it (D-432): Track A (interface and backend) and Track B (page), each with its own requirement groups, review sittings and task block, see `high-level-spec.md` section 6.

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-5 Graph app (page, vendored vis-network) | real | the page and the vendored library |
| N-2.1 API and accounts | real | all IF-104 v2 routes, a blueprint in the MIA backend (D-430 (8)); the JS mock of IF-104 v2 stands in for the page tests |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | files and the database behind the real backend for the demonstration |
| compose stack and web routing (Caddy) | real | one origin and session for page and API |
| N-3.1 record tables `arrangements` and `graph_changes` (IF-302 amendment) | real | introduced by VIEW, carried by TRANSFER; written through the IF-104 v2 routes (the page writes nothing until EDIT) |
| N-3.2 rule set (IF-301 v4) | real | after RULES' merge: the check route and the save path; until then the save path keeps CORE's rules |
| trust source (R10 stand-in) | stand-in | "changed since trusted" is always no until G-V4.GRAPHAPI.CODE; contract test of the field |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.VIEW | [x] Stefan Reiterer (owner) | 2026-11-20 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | `top-level-spec.md` approved 2026-11-20 (D-389 to D-391) |
| Plan | done | plan package approved, plan gate ticked by the owner 2026-11-23 (D-447); red tests `82327296`, tag `plan-baseline-g-v4-view`; `plan.md` |
| Implement | open | started 2026-11-23 with T-01; `implementation-log.md` |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
