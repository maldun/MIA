# Prototype run 03: G-V4.GRAPHSTORE.CORE (MVP), to confirm the requirements of the subgoal

**Authorized by:** Stefan Reiterer (owner), by answer in the session on 2026-11-21
**Date:** 2026-11-21
**Level:** MVP        <!-- the minimum that works end to end for the outcomes in scope; no polish -->
**Scope:** the outcomes of G-V4.GRAPHSTORE.CORE: FR-57 (for workflow graphs and for context graphs), FR-60, NFR-16, tried against the measures HR-003, HR-004 and HR-005 of `specs/mia/goals/G-V4.GRAPHSTORE.CORE/high-level-spec.md` and the accepted cases AC-001 to AC-003. Not in this round: transfer, rules, viewer, editor, log, migration
**Budget:** 4 checkpoints of at most about an hour each; the run reports after every checkpoint; it stops at the budget or when an outcome looks unreachable
**Worktree:** ../MIA-prototype-g-v4        <!-- the living prototype continues in its worktree (same branch) -->
**Branch:** prototype/g-v4

## Slicing: checkpoints and breakpoints
| CP | Content | Outcome tried |
|---|---|---|
| CP13 | a context graph is saved, read, listed and changed through the same save path as a workflow graph, scoped member IDs, steps of every kind (data, processing, loop-controlling); files backend | FR-57, FR-60 |
| CP14 | the same cases on PostgreSQL 16 (throw-away database under podman): identical lists, versions and content as on files | FR-57 (HR-003) |
| CP15 | fault injection at every write position of a save, for both graph kinds, on files and PostgreSQL; refused saves (cycle, broken rule, unscoped ID) write nothing | NFR-16 (HR-005) |
| CP16 ★ | the owner's validation sheet for round 03; the requirements found unsound are written down as findings | FR-57, FR-60, NFR-16 |

## What the agent may do
Work only inside the worktree; extend the prototype (checks and code), write drafts of requirements of this subgoal as it needs them, with `Status: Draft`; use throw-away databases by name only.
## What the agent may not do
Change the top-level spec (proposals only), touch production data or product code paths outside the worktree, present the result as verified, sign anything.
## Stop rules
Stop at the budget, when a top-level outcome looks unreachable, or when the round would need something not allowed above. Write the report either way.

## TLS fingerprint (the protected part)
| Fingerprint | Date | Decided by | Reason |
|---|---|---|---|
| 7eadf4eb83d0 | 2026-11-21 | Stefan Reiterer | run authorized; the TLS is unchanged since round 02 |

## Validation plan
The owner validates with `rounds/03/validation.md` (one row per outcome), after CP15. Findings go to the requirements of this subgoal.
