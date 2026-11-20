# Consistency review of G-V4 after the item-by-item reviews (updated 2026-11-20; Explore gate passed, D-391)

First written before the owner's Explore gate (D-367, D-368); updated after every subgoal's top-level spec was reviewed item by item. The leftovers and the validation moved to the parked goal G-V5 (D-385, D-386). Fixed mechanically in this update: the stale text about saved positions in the copy of the prototype report. Everything marked **owner** needs a decision or a tick.

## 1. Where each subgoal stands
| Subgoal | Top-level spec | Reviewed by the owner | Requirement IDs (provisional) | `spec_check` |
|---|---|---|---|---|
| GRAPHSTORE | `G-V4.GRAPHSTORE/top-level-spec.md` | D-372 to D-374, approved D-389 | FR-57 to FR-62, FR-93, NFR-15, NFR-16 | no errors |
| GRAPHAPI | `G-V4.GRAPHAPI/top-level-spec.md` | D-375 | FR-63 to FR-67, NFR-17 | no errors |
| VIEW | `G-V4.VIEW/top-level-spec.md` | D-376 to D-378 | FR-48 to FR-55, FR-96, NFR-10 to NFR-14 | 9 errors, all PT3: the carry-over of the prototype graphview is not ticked (owner) |
| EDIT | `G-V4.EDIT/top-level-spec.md` | D-369, D-370 | FR-68 to FR-74, FR-91, FR-92, FR-94, FR-95, NFR-18, NFR-19 | no errors |
| REPLAY | `G-V4.REPLAY/top-level-spec.md` | D-371 | FR-76 to FR-81, NFR-20 | no errors |
| CONTEXT | `G-V4.CONTEXT/top-level-spec.md` | D-379 | FR-75, FR-97 | no errors |
| BUILDER | `G-V4.BUILDER/top-level-spec.md` | D-380 to D-384 | FR-98 to FR-105, NFR-23 to NFR-25 | no errors |

IDs are unique across the seven specs. Gaps are deliberate: FR-56 is retired (merged into FR-55); FR-82 to FR-90, FR-106 to FR-109 and NFR-21, NFR-22 are reserved for the parked G-V5 drafts. Plan writes the IDs into `requirements.md`.

## 2. Old N-5 requirements (decisions D-367, changed by D-369)
| Old requirement | Decision | What the amendment does |
|---|---|---|
| REQ-GA-001 show as nodes and edges | **supersede** by FR-48 to FR-55 | the stable-layout, physics-off tests of `tests/js/graph-view.test.mjs` are rewritten by amendment |
| REQ-GA-002 edit as JSON | **keep, refine in EDIT** | EDIT decided a form per kind of step for known fields plus text (FR-92) |
| REQ-GA-003 graph rules before saving | **amend** | the page asks the backend check route; one rule set of eight rules (GRAPHAPI FR-63) |
| REQ-GA-004 versions, history, diff, restore | **split into four, supersede** | save and restore to EDIT (FR-71, FR-73), history and viewing a version to VIEW (FR-55), diff to REPLAY (FR-79) |
| REQ-GA-005 only through IF-104 | **keep** | IF-104 changes by the joint amendment (section 4) |
| REQ-GA-006 edit context graphs | **keep, assign to G-V4.CONTEXT** (D-369; was EDIT) | FR-75 |
| REQ-GA-007 login required | **keep, NFR-12 refines it** | every logged-in account may look, only the owner changes (NFR-19) |
| REQ-GA-008 export and seed | **move to GRAPHSTORE** | FR-59 (whole store) and FR-93 (sync) |
| REQ-GA-009 plain stack, vendored library | **keep** | vis-network 10.1.2 recorded as a dependency |
| REQ-GA-010 no outside request | **supersede by NFR-13** | its test moves to the measure of NFR-13 |
| REQ-GA-011 own container | **keep, check the routing in Plan** | page and backend under one origin and session |

## 3. Earlier findings
| # | Finding | State |
|---|---|---|
| C-1 | the system-wide `high-level-spec.md` is in the old format (no HR items, no DEP table, no measures) | **decided (D-387):** add one section in the new format for G-V4 and leave the old text as legacy (D-362); Plan writes it |
| C-2 | top-level specs of the subgoals | **done:** seven reviewed specs |
| C-3 | new requirement IDs | **decided (D-387):** the drafted numbers stay (gaps included); Plan writes them into `requirements.md` |
| C-4 | scope tables, Parts and Frozen tables of the subgoals (GL3, GL6 errors) | **open for Plan step 0** |
| C-5 | IF-104 | **decided (D-368):** one IF-104 v2 written whole at G-V4 level, frozen for the subgoals that share it; v1 stays until the migration is confirmed. The contents list is in section 4 |
| C-6 | spike S1: node IDs shared by several graphs | **decided (D-368):** record IDs scoped by graph, the storage layer refuses an unscoped ID (amends A-92 / REQ-GTB-021) |
| C-7 | carry-over of the prototype `graphview` | **owner:** the table in its report has proposed decisions, every box empty |
| C-8 | `trace_check` warnings that are not G-V4 | carried by the parked G-V5 (`parked/G-V5/README.md`) |

## 4. Cross-checks between the seven specs (made in this update)
No contradiction was found; the points below are consistent only because of the owner's decisions and need to stay so.

| Pair | Why it could conflict | Why it is consistent |
|---|---|---|
| EDIT FR-95 and GRAPHSTORE FR-93 | MIA runs on a copy that is synced one way | the editor writes to the live store directly; the copy receives the change at the next sync (D-374) |
| VIEW FR-52 and EDIT FR-74 | the viewer opens with an arrangement the editor saved | one shared arrangement per graph; the viewer uses it if it exists (D-377, D-369) |
| REPLAY FR-76 and EDIT FR-74 | moves of steps could fill the log | moves are a record of their own, not in the edit log (D-371) |
| VIEW FR-55 and REPLAY FR-79 | history list against comparison | VIEW lists versions and shows one; REPLAY compares and explains (D-366, D-377) |
| VIEW FR-48 and CONTEXT FR-97 | both show context graphs | VIEW shows stored context graphs, CONTEXT adds a run's rebuilt graph, read-only (D-379) |
| GRAPHAPI FR-66, FR-67 and EDIT NFR-19 | who trusts a step | only the owner changes graphs and trusts a step; any change of code, tool or settings drops trust (D-370, D-375) |
| GRAPHSTORE FR-62 and GRAPHAPI NFR-17 | a skill without a stored graph | it runs as before until imported; equivalence is decided on converted skills (D-373, D-375) |
| BUILDER FR-104 and GRAPHAPI FR-65 | a step reads a graph during a run | the order and the run record of GRAPHAPI hold; BUILDER adds only the budgeted reading of confirmed items (D-381) |

**Shared by several subgoals (candidate frozen requirements for Plan step 0, owner):**
- **IF-104 v2:** list both kinds of graph, read a graph and a version, the version list, the check route, save with the expected version and an optional reason, restore, the edit-log entries, the arrangement, the run's context graph, and in the data of a step: its trust and lifecycle and a code mark. Shared by VIEW, EDIT, REPLAY and CONTEXT.
- **Scoped record IDs (`<graph id>/<local id>`):** GRAPHSTORE, used by everything that reads graphs.
- **One rule set of eight rules and its order:** GRAPHAPI FR-63, used by EDIT, CONTEXT and the run.
- **The arrangement record:** EDIT FR-74, used by VIEW FR-52.

## 5. Decisions of the owner that replaced earlier ones
- D-363 (2) positions as a side record per graph and account → one shared arrangement per graph (D-369); D-363 (2) and (3) moves in the edit log → a record of their own (D-371).
- D-367 REQ-GA-006 to EDIT → to CONTEXT (D-369).
- D-364 earlier versions to REPLAY → back to VIEW (D-365), with the comparison staying in REPLAY (D-366).
- D-360 leftovers and validation inside G-V4 → parked G-V5 (D-385, D-386).

## 6. New work these specs create (for Plan, not decided here)
- **Agent-app items:** VIEW FR-96 (search by description with a local model) and the whole BUILDER subgoal need an agent profile, evaluation cases and injection checks; THR-013 (code in graphs) needs its threat entry and red-team cases with the owner.
- **New part:** the builder as its own part N-6 with its own container (D-381).
- **New records:** the edit log, the arrangement record, the saved-aside versions of a sync, and the builder's proposals with their sources.
- **Owner time:** the samples the owner marks for NFR-23 (about 120 for definitions and facts, more if the full model is to count) and the confirmation of NFR-10, NFR-11, NFR-18 as thresholds in validation.

## 7. Owner's gate (all empty boxes, not pre-filled)
- [x] Owner decided the REQ-GA rows (D-367, D-369)
- [x] Owner decided C-5 and C-6 (D-368)
- [x] Owner reviewed the seven top-level specs item by item (D-369 to D-384)
- [x] Owner decided C-1 and C-3 (2026-11-20, D-387): one new section in the existing `high-level-spec.md`, old text stays legacy; the IDs stay as drafted
- [x] Owner decided the carry-over of the prototype graphview (C-7, D-387, D-388)
- [x] Owner approved the seven top-level specs (D-389 to D-391); GRAPHAPI as revised (trust stays on change, with a mark), VIEW with the phone aspects out of scope
- [x] Owner agreed to the split (the seven Agreement rows of `G-V4/goal.md`, 2026-11-20, D-391)
