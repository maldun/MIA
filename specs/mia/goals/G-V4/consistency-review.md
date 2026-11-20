# Consistency review of the G-V4 Explore artifacts (2026-11-20)

Done before the owner's Explore gate, as the owner chose on 2026-11-20. Fixed mechanically: stale wording in `G-V4/goal.md` and `G-V4.VALIDATE/goal.md`, order of the outcome rows, the Explore row of the Phases table. Everything below needs the owner's decision.

## 1. Old N-5 requirements against the new items
The approved `nodes/N-5-graph-app/requirements.md` (REQ-GA-001 to -011, written in G-V1) overlaps the new VIEW items (FR-48 to FR-56, NFR-10 to NFR-14) and the decisions D-363 and D-366. Proposal; the owner decides each row (keep, amend, supersede, move).

| Old requirement | Overlaps with | Proposal |
|---|---|---|
| REQ-GA-001 show as nodes and edges (test `tests/js/graph-view.test.mjs`: "layout is stable", physics off) | FR-48 to FR-53 | **supersede** by the VIEW requirements; its stable-layout tests conflict with physics (FR-52) and need a rewrite by amendment |
| REQ-GA-002 edit as JSON | G-V4.EDIT | **keep for EDIT**, to be refined there (the editor may offer more than JSON) |
| REQ-GA-003 graph rules before saving ("in the app and again by the backend") | D-363 check route, FR-7 | **amend**: the page asks the backend check route; one rule set |
| REQ-GA-004 versions, history, diff, restore | FR-55, FR-56 (VIEW), comparison (REPLAY), restore (EDIT) | **split** into three; supersede the old text |
| REQ-GA-005 only through the graph interface (IF-104) | FR-48 data path | **keep**; IF-104 gets a new version (record form, check route) by amendment |
| REQ-GA-006 edit context graphs | FR-30, G-V4.EDIT | **keep for EDIT** |
| REQ-GA-007 login required | NFR-12 | **keep**; NFR-12 refines it |
| REQ-GA-008 export and seed of the library | G-V4.GRAPHSTORE (files and database interchangeable) | **move** to GRAPHSTORE (the page's buttons are a Could) |
| REQ-GA-009 plain stack, vendored library | HR (vis-network 10.1.2 pinned) | **keep** |
| REQ-GA-010 no outside request | NFR-13 | **keep**; NFR-13 refines it |
| REQ-GA-011 own container | NFR-9 (partly in scope) | **keep** |

## 2. Findings that need a decision
| # | Finding | Proposal |
|---|---|---|
| C-1 | The system-wide high-level spec (`high-level-spec.md`) is in the old format: no HR items, no DEP table, no measures; the two-layer rule needs them | add one section "High-level requirements and dependencies of iteration 3 (G-V4)" in the new format instead of rewriting the old text; the old FR text stays as legacy (D-362) |
| C-2 | The subgoals' own top-level specs: only VIEW has one. GRAPHSTORE, GRAPHAPI, EDIT, REPLAY, LEFTOVER and VALIDATE have goal records with outcomes, which Plan can start from; a full TLS for each is not needed if the owner agrees | one TLS section for G-V4 as a whole is enough; keep the VIEW TLS as the model; the others get their outcomes from the goal records |
| C-3 | New requirement IDs: FR-48 to FR-56 and NFR-10 to NFR-14 are used only in the VIEW TLS (checked: no other use in `specs/mia` except the decision log). Subgoals EDIT, REPLAY and GRAPHAPI will need more | reserve the ranges per subgoal when Plan writes them into `requirements.md` |
| C-4 | The scope tables of GRAPHSTORE and GRAPHAPI list code items, not FR/NFR; EDIT, REPLAY, LEFTOVER, VALIDATE and VIEW have no scope table (GL3 errors); Parts and Frozen tables are empty | Plan step 0 (next) |
| C-5 | IF-104 (`contracts/IF-104-graph-api.md`) serves the document form; VIEW, EDIT and REPLAY all need a change (record form, versions, check route, edit log) | one joint amendment of IF-104 planned at G-V4 level, since three subgoals share it (frozen requirement) |
| C-6 | Spike S1 (GRAPHSTORE): 13 node IDs occur in several graphs, 4 with different content; the viewer shows nodes by ID | decide graph-scoped IDs in the GRAPHSTORE plan before VIEW is planned |
| C-7 | The prototype `prototype/graphview` has a carry-over table that is still unticked; its report was copied into this branch so the checks find it (`spec_check` PT3 errors are expected until the ticks) | owner ticks |
| C-8 | `trace_check` warnings that are not G-V4 (TD-90 in two verification reports, TR aspect names of G-V3 test requirements) | not part of this goal; listed so they are not mistaken for new findings |

## 3. Owner's gate (all empty boxes, not pre-filled)
- [ ] Owner approves the Explore results per subgoal: GRAPHSTORE, GRAPHAPI, VIEW, EDIT, REPLAY
- [ ] Owner decides the open rows of section 1 and section 2
- [ ] Owner ticks the carry-over of the prototype graphview
- [ ] Owner agrees to the split (the seven Agreement rows of `G-V4/goal.md`)
