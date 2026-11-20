# Consistency review of the G-V4 Explore artifacts (2026-11-20)

Done before the owner's Explore gate, as the owner chose on 2026-11-20. Fixed mechanically: stale wording in `G-V4/goal.md` and `G-V4.VALIDATE/goal.md`, order of the outcome rows, the Explore row of the Phases table. Everything below needs the owner's decision.

## 1. Old N-5 requirements against the new items: decisions of the owner (maldun, 2026-11-20, D-367)
The approved `nodes/N-5-graph-app/requirements.md` (REQ-GA-001 to -011, written in G-V1) overlaps the new VIEW items. The decisions below are applied by plan amendments in Plan (the approved text is not edited now).

| Old requirement | Decision | What the amendment does |
|---|---|---|
| REQ-GA-001 show as nodes and edges | **supersede** by FR-48 to FR-53 | history names the new items; the stable-layout, physics-off tests of `tests/js/graph-view.test.mjs` are rewritten by amendment |
| REQ-GA-002 edit as JSON | **keep, refine in EDIT** | text unchanged; EDIT decides JSON text, form or both |
| REQ-GA-003 graph rules before saving | **amend** | the page asks the backend check route (D-363); one rule set (GRAPHAPI); needs the IF-104 amendment; belongs to EDIT |
| REQ-GA-004 versions, history, diff, restore | **split into four, supersede** | save and restore to EDIT, history list and viewing a version to VIEW (FR-55, FR-56), diff to REPLAY |
| REQ-GA-005 only through IF-104 | **keep as written** | IF-104 changes by the joint amendment (C-5) |
| REQ-GA-006 edit context graphs | **keep, assign to EDIT** | after GRAPHSTORE moves context graphs into the same stored form |
| REQ-GA-007 login required | **keep, NFR-12 refines it** | no change |
| REQ-GA-008 export and seed | **move to GRAPHSTORE** | transfer between files and database is GRAPHSTORE's (OC-6); page buttons stay a Could, none built unless the owner asks |
| REQ-GA-009 plain stack, vendored library | **keep as written** | the high-level spec records vis-network 10.1.2 as a dependency |
| REQ-GA-010 no outside request | **supersede by NFR-13** | its test moves to the measure of NFR-13 |
| REQ-GA-011 own container | **keep, check the routing in Plan** | VIEW's plan adds a check that page and API share one origin and session in the stack |

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
- [x] Owner decided the rows of section 1 (D-367)
- [ ] Owner decides the open rows of section 2
- [ ] Owner ticks the carry-over of the prototype graphview
- [ ] Owner agrees to the split (the seven Agreement rows of `G-V4/goal.md`)
