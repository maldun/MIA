# Prototype run 05: G-V4.EDIT (MVP), to confirm the requirements of the subgoal

**Authorized by:** [X] Stefan Reiterer (owner)        <!-- empty until the owner authorizes; no checkpoint starts before -->
**Date:** 2026-11-27 (drafted by the agent, D-601)
**Level:** MVP        <!-- the minimum that works end to end for the outcomes in scope; no polish -->
**Scope:** what round 02 (CP8 to CP10) did not try for G-V4.EDIT, after the profile and kind decisions D-403, D-404, D-471 (2), D-602: FR-72, FR-73, FR-92, FR-94 of `specs/mia/goals/G-V4.EDIT/top-level-spec.md`, OC-5, OC-7, OC-9 of `specs/mia/goals/G-V4.EDIT/goal.md`, and the layout of the editing panel (round 02 carry-over "adapt: layout to the UI review", FB-1; reuse map R8). Starts from round 02's editor (`graph_app_v2/edit-model.js`, `edit-panel.js`, `undo-stack.js`, `copy-panel.js`; `cp8` to `cp10` checks) and from VIEW's real page `graph_app/` after `goal/v4` is merged in. Not in this round: undo and redo, keep, conflict and restore as such (validated in round 02, CP8 and CP9), the live store and its copy (TRANSFER, merged), TD-91 to TD-94 (small fixes, specified directly in Plan), the context profile and rule set (G-V4.CONTEXT), playback and comparison (REPLAY)
**Budget:** 5 checkpoints of at most about an hour each; the run reports after every checkpoint; it stops at the budget or when an outcome looks unreachable
**Worktree:** /home/maldun/prog/Python/MIA/.claude/worktrees/prototype-g-v4 (same branch; `goal/v4` at `5dd1ca13` or later is merged into it first)
**Branch:** prototype/g-v4

## Slicing: checkpoints and breakpoints
| CP | Content | Outcome tried |
|---|---|---|
| CP21 | **the profile from the backend**: a prototype route `GET /api/v2/kinds` answers, per kind of the registry (IF-301 v4 `kinds()`), its node types (ID, name, shape, marks) with their fields (name, label, input kind: text, number, JSON, choice; limits; start value), its connection fields, whether it can be edited, and whether it can run; `workflow` with the three types and the fields round 02 hard-coded, `context` marked not editable (D-602). `GET /api/v2/toolbox` answers the choice list of tools. `edit-model.js` builds the form and its checks from that answer instead of `START`, `KNOWN`, `formFor`; **inventory:** every place in the page that still names a workflow type, field or role is listed as a finding for Plan | FR-92 (OC-5) |
| CP22 | **kinds the editor cannot change**: a context graph and a graph of an unknown kind are opened: both drawn, no edit control offered, one line names why (context: "editing context graphs comes with G-V4.CONTEXT"; unknown: the kind named); keep, restore and copy sent anyway are refused by the backend with `unknown kind` (or the context refusal), nothing written; `proto_checks/cp22_check.py` | FR-72, FR-73 (OC-9) |
| CP23 | **copy within the kind**: `POST /api/v2/graphs/<id>/copy-step` copies a step into another workflow graph as an independent copy with its own history; a copy into a context graph or a graph of an unknown kind is refused naming both kinds; the copy keeps the form's checks of the target's profile; the round-02 `cp10` cases rerun on the merged code | FR-94 (OC-7) |
| CP24 | **the editing panel in VIEW's frame**: the editor's controls placed in the real page's areas after the owner's sketch (actions row: edit, keep, undo, redo, restore, copy; the left column in edit mode: the form and the other fields as text; the rule report beside the picture; the arrangement save). Two layouts at most, side by side behind a prototype switch, for the owner to choose | FR-68, FR-69, FR-74, FR-91, NFR-18 (FB-1, R8) |
| CP25 ★ | the owner's validation sheet for round 05 (`rounds/05/validation.md`): CP21 to CP24 tried in Firefox, the layout chosen, the inventory of CP21 and every requirement found unsound written down as findings, a carry-over table with proposed decisions | FR-72, FR-73, FR-92, FR-94, FB-1 |

## What the agent may do
Work only inside the worktree; merge `goal/v4` into `prototype/g-v4` before CP21; extend the prototype (checks and code), including copying VIEW's page into the prototype to place the editor in it; write drafts of IF-104 v3 routes and of requirements of this subgoal as it needs them, with `Status: Draft`; use throw-away stores and databases by name only.
## What the agent may not do
Change the top-level spec (proposals only); change protected material (tests, contracts, mocks) even inside the prototype (the inventory lists what Plan must amend); touch the owner's live store, `goal/v4`, `goal/v4.edit` or product code paths outside the worktree; use the model server (RUN T-04 runs real model runs, 2026-11-27); present the result as verified; sign anything.
## Stop rules
Stop at the budget, when a top-level outcome looks unreachable, or when the round would need something not allowed above. Write the report either way.

## TLS fingerprint (the protected part)
Recorded from this round on as the git blob ID (`git rev-parse --short=12 <commit>:<file>`) of the whole file, because the earlier fingerprint method could not be reproduced; the aggregate changed once since round 04 (the NFR-16 outcome, G-V4.GRAPHSTORE.TRANSFER).

| Fingerprint | File | Commit | Date | Decided by | Reason |
|---|---|---|---|---|---|
| 9cb01bfc723c | `specs/mia/goals/G-V4/top-level-spec.md` | `5dd1ca13` | 2026-11-27 | [ ] Stefan Reiterer | run authorized; no item of EDIT changed since D-405 |
| 6edccb2477f2 | `specs/mia/goals/G-V4.EDIT/top-level-spec.md` | `5dd1ca13` | 2026-11-27 | [ ] Stefan Reiterer | run authorized |

## Validation plan
The owner validates with `rounds/05/validation.md` (one row per outcome, one for the layout choice, one per open decision found), after CP24. Findings go to EDIT's requirements and to the draft of IF-104 v3 (amendment A-210); the carry-over table is decided by the owner before Plan step 1b.
