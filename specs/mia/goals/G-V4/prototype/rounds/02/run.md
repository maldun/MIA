# Prototype run 02 ("run 1"): G-V4 graph path slice (MVP)

**Authorized by:** Stefan Reiterer (owner), by instruction in the session on 2026-11-20
**Date:** 2026-11-20
**Level:** MVP        <!-- the minimum that already works and fulfils the outcomes in scope, end to end; thin where not cheap; no polish -->
**Scope:** the graph path slice, these subgoals in this order: G-V4.GRAPHSTORE.CORE (FR-57, FR-60, NFR-16), G-V4.GRAPHSTORE.TRANSFER (FR-58, FR-59, FR-93, NFR-15), G-V4.GRAPHAPI.RULES (FR-63, FR-64), G-V4.VIEW (FR-48 to FR-55, NFR-10 to NFR-14), G-V4.EDIT (FR-68 to FR-74, FR-91, FR-92, FR-94, FR-95, NFR-18, NFR-19), G-V4.REPLAY (FR-76 to FR-81, NFR-20). Not in this run: MIGRATION (FR-61, FR-62), RUN and CODE (FR-65 to FR-67, NFR-17), CONTEXT, BUILDER, the search by description (FR-96); the phone layout is out of scope (D-389)
**Budget:** 12 checkpoints of at most about an hour each (about 12 hours in all); the run reports after every checkpoint and continues from checkpoint to checkpoint unless the owner stops it; **the owner's first validation session starts at a later checkpoint, when there is more to work with (the owner, 2026-11-20, D-398); the subgoal breakpoints (★) are report points until then**
**Worktree:** ../MIA-prototype-g-v4
**Branch:** prototype/g-v4

<!-- git worktree add ../MIA-prototype-g-v4 -b prototype/g-v4 <commit of the approved TLS and this run.md> -->

## Slicing: checkpoints and breakpoints
**Order changed on 2026-11-20 (D-399):** the owner wants to validate the earlier subgoals through the viewer, so VIEW (CP5 to CP7) is built next; the sync (CP3) and the rules (CP4) follow after CP7. The table keeps the original numbers.

A checkpoint ends with: the demonstrator runs, `status.md` updated, a commit on the branch, one short report line. A breakpoint (★) is the end of a subgoal: the report section is written. **Change of 2026-11-20 (D-398):** the run does not stop at a breakpoint for validation; the owner starts validating at a later checkpoint (the agent proposes one), with `rounds/02/validation.md` (one row per item).

| Checkpoint | Subgoal | What the demonstrator shows afterwards (the question: what is new?) | Items |
|---|---|---|---|
| CP1 ★ | GRAPHSTORE.CORE | graph-scoped steps (`<graph>/<local>`), the 15 converted graphs and `review` stored and read back, two graphs with a step of the same local name that do not disturb each other, a refused or interrupted save that leaves nothing half-stored | FR-57, FR-60, NFR-16 |
| CP2 | GRAPHSTORE.TRANSFER | the same operations give the same answers in files and database; the whole store moves in both directions, repeatably and all-or-nothing | FR-58, FR-59 |
| CP3 ★ | GRAPHSTORE.TRANSFER | one-way sync from the live store to a copy on command and at start and stop, the lag shown, differing versions of the copy saved aside, a set of files that works on another folder | FR-93, NFR-15 |
| CP4 ★ | GRAPHAPI.RULES | the eight rules in one fixed order, all broken rules listed, the check route, refusal before a run with the broken parts named | FR-63, FR-64 |
| CP5 | VIEW | a backend for graphs (list of both kinds, read, versions, history) behind a login, and the viewer listing graphs with a name filter, drawing them, marking what cannot be drawn | FR-48, FR-49, NFR-12 |
| CP6 | VIEW | kinds at a glance (data, processing, loop-controlling; trust and changed marks), the left panel with read-only fields and the full text, text-only display, the settings menu remembered per browser, light and dark, keyboard use | FR-50, FR-51, FR-53, FR-54, NFR-13, NFR-14 |
| CP7 ★ | VIEW | the shared arrangement (settled, saved, reset to layers), the history list with previous and next and any version shown, a smoke look at speed and first use | FR-52, FR-55, NFR-10, NFR-11 |
| CP8 | EDIT | add, remove and change steps and connections, a form for the known fields plus text, the rule problem shown while editing and a broken change refused | FR-68, FR-69, FR-70, FR-92 |
| CP9 | EDIT | a kept change is a new version written to the live store (the editor read-only when it is unreachable), a conflicting change refused, restore, only the owner changes, undo and redo | FR-71, FR-72, FR-73, FR-91, FR-95, NFR-19 |
| CP10 ★ | EDIT | the arrangement saved from the editor, copy a step into another graph, a first-change check without instructions | FR-74, FR-94, NFR-18 |
| CP11 | REPLAY | one log entry per change with old and new value and an optional reason, append-only, no moves and no undone changes, entries that move with the graph | FR-76, FR-77, FR-80, FR-81 |
| CP12 ★ | REPLAY | playback step forward and back, comparison of two versions as a list and a marked picture, older versions shown as made before the record | FR-78, FR-79, NFR-20 |

## What the agent may do
- Work **only inside the worktree**, with its own dependency environment and ports; build the prototype at the level above, as small as the outcomes in scope allow (no extra features, no polish, existing libraries first, tests only where they answer a question).
- Choose technology, **split the prototype into modules (sub-nodes) with explicit interfaces wherever that keeps rework local** (a light `decomposition.yaml`: nodes, interfaces, why), and write and rewrite the specs, architecture, tests and code as it sees fit, no gate in between. Specs are drafts (`Status: Draft`) in the worktree; every item traces to a top-level item and has a basis: seen, measured, assumed, imposed.
- Use the frozen interfaces as the interface starting point: IF-104 v2 is drafted in the prototype (the frozen v1 stays working), the scoped IDs amend A-92 only as a draft.
- Start from round 01 (`graphview`): its code is brought into the branch and reused.

## What the agent may not do
- Change the top-level spec (the aggregate `../../top-level-spec.md` and the subgoal specs). Where an outcome looks unreachable, wrong or incomplete it **proposes** a change (report section "Proposed TLS changes") and goes on or stops.
- Touch the goal's line of work or product code paths outside the worktree, production data, credentials, or anything with an effect outside the machine (the running MIA containers included).
- Present the result as verified, or promote any draft to Approved.
- Authorize a further run itself.

## Stop rules
Stop at the budget, when a top-level outcome looks unreachable, or when the run would need something not allowed above. Write the report either way.

## TLS fingerprint (the protected part)
| Fingerprint | Date | Decided by | Reason |
|---|---|---|---|
| 7eadf4eb83d0 | 2026-11-20 | Stefan Reiterer | run authorized |

## Validation plan
The owner validates from a later checkpoint on (D-398) with `rounds/02/validation.md` (one row per item). Findings go to the next checkpoint or to Plan.
