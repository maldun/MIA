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
- Depends on: G-V4.VIEW (merged into `goal/v4` at `34fb0534`: IF-104 v2 routes, the page); G-V4.GRAPHAPI.RULES (merged at `ceb7097a`: IF-301 v4 `kinds()` and `rule_report`); G-V4.GRAPHSTORE.TRANSFER (merged at `f6ccde75`: the live store and its copy, for FR-95); IF-104 v3 written by EDIT's plan (D-471 (2))
- Status: Agreed
- History: agreed 2026-11-20; Plan step 0 drafted by the agent 2026-11-27 from D-600 to D-605 (scope rows per item, TD-91 to TD-94, OC-9 and OC-10 drafted, dependencies, split check), for the owner's gate

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a stored graph open in the web app, when the owner changes it in a way that keeps the graph rules, then the change is kept as a new version and the earlier version stays reachable | OC-8 of G-V4 (FR-22) |
| OC-2 | Given a change that breaks a graph rule, when the owner tries to keep it, then it is refused and the broken rule is named | OC-8 of G-V4 (FR-22) |
| OC-3 | Given a graph in which the owner has placed steps, when the owner opens it again, then the steps are where they were last left, the same for everyone who opens the graph, without this being a new version of the graph | OC-8 of G-V4 (FR-22); moved here from the VIEW review (owner, 2026-11-20, D-366) |
| OC-4 | Given changes in an open editing session that are not yet kept, when the owner undoes and redoes them, then the picture follows and nothing is kept or recorded as a version | OC-8 of G-V4 (FR-22) |
| OC-5 | Given a step of any kind, when the owner opens it for change, then its known fields are a checked form and any other field is editable text | OC-8 of G-V4 (FR-22) |
| OC-6 | Given an account other than the owner's, when it opens a graph, then it can look and cannot change anything | OC-8 of G-V4 (FR-21, NFR-6) |
| OC-7 | Given a step in one graph, when the owner copies it into another graph, then the other graph has an independent copy with its own history | OC-8 of G-V4 (FR-22) |
| OC-8 | Given MIA running on a copy of the graphs, when the owner keeps a change, then it is stored in the live store and reaches the copy at the next sync; when the live store cannot be reached, then the editor is read-only and says so | OC-6, OC-8 of G-V4 (FR-22, NFR-8) |
| OC-9 | Given a graph of a kind the editor cannot change (a context graph, or a kind the program does not know), when the owner opens it, then it can be looked at, nothing can be changed, kept, copied or restored, and the page says why | OC-8 of G-V4 (FR-22; FR-72, FR-73, FR-94; D-404, D-602). Drafted 2026-11-27, for the owner's gate |
| OC-10 | Given the viewer that EDIT builds on, when opening a graph fails for any reason, or two graphs are chosen quickly, or a step is untrusted or missing, then the failure is named in one line and the picture stays, only the graph chosen last is drawn, an untrusted step and a missing step differ at a glance, and every processing step shows its trust in the left column | OC-8 of G-V4 (FR-22); the list and picture of G-V4.VIEW, TD-91 to TD-94 (D-600 (2)). Drafted 2026-11-27, for the owner's gate |

## Explore result (2026-11-20, D-363)
`../G-V4.VIEW/research.md`. Decision: the graph rules are checked by a backend check route that the page asks before saving (one rule set after G-V4.GRAPHAPI; the route is an amendment of IF-104 in Plan); the backend still validates on save. Open for Plan: the protected mock of the graph interface for the JavaScript tests (A-36 drafts), conflict handling (`expected_version`).

**Plan start (2026-11-27, D-600 to D-605):** numbers D-600 to D-629 and A-210 to A-224; TD-91 to TD-94 in scope; a prototype round 05 for the editor before the requirements (D-601, `run.md` to be authorized by the owner); a context graph is read-only in EDIT with a note (D-602); `rt_edit` handed to G-V4.GRAPHAPI.CODE, THR-009 updated (D-603); EDIT agrees to RUN's A-189 (D-604); REQ-API-048 stays (D-605).

**Plan points decided before Plan (2026-11-23, D-471):** Plan starts when VIEW is merged into `goal/v4`; IF-104 v3 adds `copy-step`, `kinds` and `toolbox` (joint amendment at G-V4); EDIT builds the live-store writes while MIA runs on a copy in its last task, after TRANSFER is merged; EDIT stays one goal with its tasks ordered core first. VIEW builds the backend side of FR-70 to FR-74, FR-95 and NFR-19 (D-430 (7)).

## Source
REQ-GA-002, REQ-GA-003 (N-5 T-02, open Q-2: where the rules run in the page); the backend still validates (TB-edit).

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| REQ-GA-002 | in | edit nodes and edges; refined by FR-68, FR-92 (a form per kind of step plus text) |
| REQ-GA-003 | in | graph rules before saving; amended so that the page asks the backend check route (D-363, D-367) |
| REQ-GA-004 | in | versions, history, diff and restore: split in Plan; save and restore (FR-71, FR-73) stay here, history goes to VIEW, comparison to REPLAY |
| FR-7 | out | the rules themselves are owned by G-V4.GRAPHAPI; the editor uses them |
| REQ-GA-001, REQ-GA-005, REQ-GA-007, REQ-GA-009, REQ-GA-010, REQ-GA-011 | out | the viewer's requirements are G-V4.VIEW; the editor builds on them |
| REQ-GA-006 | out | context graph editing is G-V4.CONTEXT |
| FR-68 | in | add, remove and change steps and connections and their fields in a working copy (page) |
| FR-69 | in | the rule report of the graph's kind after every change, through the check route (page; the route is VIEW's) |
| FR-70 | in | page side: keeping disabled while a rule is broken, the refusal shown with the rule; backend side built by VIEW (D-430 (7)) |
| FR-71 | in | page side: keep as a new version with an optional reason; backend side VIEW's |
| FR-72 | in | page side: `expected_version` sent, the conflict told without losing the working copy; an unknown kind refused (D-404) |
| FR-73 | in | page side: restore a version from the history list; backend side VIEW's |
| FR-74 | in | page side: the arrangement save (the backend route is VIEW's; AC-014's save step witnessed here, D-425 B) |
| FR-91 | in | undo and redo over the working copies of the session; nothing kept or recorded |
| FR-92 | in | the form built from the kinds answer of IF-104 v3 (workflow profile), other fields as text; the tool list from the toolbox answer of IF-104 v3 |
| FR-94 | in | copy of a step into another graph of the same kind: route `copy-step` of IF-104 v3 and the page |
| FR-95 | in | writes go to the live store while MIA runs on a copy; read-only from `store.live_reachable` and `me.owner` (D-471 (3)); last task, TRANSFER is merged |
| NFR-18 | in | validation criterion (first change in under three minutes without instructions; settled in Validate, G-V5) |
| NFR-19 | in | page side: the editor offered only to the owner; a changed trusted step marked (the mark's data, `changed_since_trusted`, becomes real in G-V4.GRAPHAPI.CODE, REQ-API-028) |
| REQ-GA-045 | in | TD-91: one line in the status band for any other failure, the picture stays (D-600 (2)) |
| REQ-GA-027 | in | TD-92, its Target: an untrusted and a missing step differ at a glance (D-600 (2)) |
| REQ-GA-037 | in | TD-93, its Target: every processing or loop-controlling step shows its trust fields (D-600 (2)) |
| REQ-GA-021 | in | TD-94, its Target: only the graph chosen last is drawn (D-600 (2)) |
| REQ-API-027 | out | TD-95: the made-up toolbox reason is G-V4.GRAPHAPI.CODE's |
| REQ-API-032, REQ-API-033, REQ-API-034, REQ-API-036, REQ-API-041, REQ-API-044, REQ-API-048, REQ-API-050 | out | the backend side of keep, conflict, restore, arrangement save and refusals, Verified in G-V4.VIEW; EDIT's page uses them unchanged; REQ-API-048 is not tightened (D-605) |

Also out, by decision: editing a context graph (read-only in EDIT with a note; the context profile and its rule set are G-V4.CONTEXT's, D-602); the target of the red-team suite `rt_edit` (THR-009, RT-012; handed to G-V4.GRAPHAPI.CODE, D-603).

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-5 Graph app (page, vendored vis-network) | real | editor panel and checks |
| N-2.1 API and accounts | real | VIEW's IF-104 v2 routes; EDIT adds the v3 routes `kinds`, `toolbox`, `copy-step`; the page's JavaScript tests use the protected JS mock of IF-104 (extended by the v3 amendment) |
| N-3.2 Workflows and context graphs (graph tables, rules) | real | the one rule set behind the check route |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | writes go to the live store |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.EDIT | [x] Stefan Reiterer (owner) | 2026-11-20 |

As a consumer of IF-301, EDIT agrees to RUN's joint amendment A-189 (D-604, 2026-11-27).

## Dependencies and bounds
| Item | Real or stand-in | Note |
|---|---|---|
| IF-104 v3 (`kinds`, `toolbox`, `copy-step`; amendment A-210, joint at G-V4: VIEW, REPLAY, CONTEXT agree) | real; JS and Python mocks for the page tests | written in EDIT's Plan; v2's other points unchanged (D-605) |
| IF-301 v4 `kinds()` and `rule_report` (RULES) | real | the one rule set per kind behind the check and save routes |
| IF-302 v15 `arrangements`, `graph_changes` (VIEW) | real | the arrangement save and the record of changes |
| live store and its copy (TRANSFER, `move_graph`) | real | FR-95; the move of the owner's live store to the database stays a later owner gate (D-460 (1)) |
| vis-network 10.1.2 (vendored), Playwright for Python with Firefox (`requirements-browser.txt`) | real | as in VIEW (D-430 (4)); no new dependency planned |
| model server | not used | EDIT has no model step; no eval suite is decided in EDIT (D-603) |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| EDIT as one goal (12 top-level items, 8 outcome criteria) | keep together (D-471 (4)) | tasks ordered core first, then arrangement save, copy of a step, live store | 2026-11-23 |
| EDIT with TD-91 to TD-94 added (16 items, 10 outcome criteria) | proposed by the agent: keep together, the four as one task early in the order | the four are small (about 6 hours) and touch the same `viewer.js` paths the editor reworks; a separate goal would cost a second plan and merge for no earlier outcome. For the owner's gate | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | `top-level-spec.md` approved 2026-11-20 (D-389 to D-391) |
| Plan | open | started 2026-11-27 on `goal/v4.edit` (D-600); step 0 drafted; prototype round 05 waits for the owner's authorization of its `run.md` (D-601) |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
