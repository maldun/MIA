# Prototype run 04: G-V4.GRAPHAPI.RULES (MVP), to confirm the requirements of the subgoal

**Authorized by:** Stefan Reiterer (owner), by answer in the session on 2026-11-22 ("Authorize as drafted")
**Date:** 2026-11-22
**Level:** MVP        <!-- the minimum that works end to end for the outcomes in scope; no polish -->
**Scope:** the outcomes of G-V4.GRAPHAPI.RULES: FR-63 and FR-64 of `specs/mia/goals/G-V4.GRAPHAPI/top-level-spec.md` (FR-7), OC-1 and OC-2 of `specs/mia/goals/G-V4.GRAPHAPI.RULES/goal.md`, tried against the accepted cases AC-017 and AC-018 and reuse-map row R3. Starts from `graph_rules_proto.py` (CP4, `cp4_check.py` 25 pass). Not in this round: the order of steps and the real run (RUN), code steps and trust (CODE), the editor's own rules before saving (EDIT, REQ-GA-003), the rule set of context graphs beyond identity and ends (CONTEXT, FR-75, ASM-4)
**Budget:** 4 checkpoints of at most about an hour each; the run reports after every checkpoint; it stops at the budget or when an outcome looks unreachable
**Worktree:** ../MIA-prototype-g-v4        <!-- the living prototype continues in its worktree (same branch); goal/v4 (CORE, Verified) is merged into it first -->
**Branch:** prototype/g-v4

## Slicing: checkpoints and breakpoints
| CP | Content | Outcome tried |
|---|---|---|
| CP17 | **one place, chosen by kind** (D-404): a registry of kinds next to `MEMBER_TABLES` names the rule set of each kind: `workflow` = the eight rules of `graph_rules_proto.py` in their fixed order, `context` = identity and ends (today's `context_problems`, moved, not changed); an unknown kind gives one broken item naming the kind. The save path of `graph_model.py`, the check route and the run route call this one function; the older `graph_rules.py` (five rules, first broken rule only) is no longer called by them. Its tests (`tests/test_graph_rules.py`) are run against the new set and every case is mapped: same verdict / other name / other order / other verdict. **Inventory:** every place that names today's rule names or expects only the first broken rule (code, protected tests such as TC-WFM-164 and TC-WFM-168, IF-301 `validate`, mocks, the page), listed as findings for Plan; nothing protected is changed | FR-63 |
| CP18 | **rule 7, the session setting** (ASM-3): the prototype's definition (a session setting on a data step, more than one settings connection into one step, a loop-controlling step without a valid stop limit) is tried on all stored graphs (converted skills and the round-02 samples): how many break it, and with which part; the same for the candidate rule "a processing step needs a tool", **as a count only** (FR-63 says eight rules; a ninth is a TLS amendment for the owner). Both go to the validation sheet for the owner's decision | FR-63 |
| CP19 | **the same list everywhere, refused before any step runs**: one graph that breaks several rules (cycle, two writers, a missing and a duplicate connection, an unsupplied input) is checked while saving, through the check route and before a run; `proto_checks/cp19_check.py` compares the three lists item by item (rule, parts, order). The run is refused before the first step for: each broken rule, an input with no writer, no start value and no value given with the run, a graph of kind `context` (cannot run) and a graph of an unknown kind (the kind named). Regression: every stored skill graph with its inputs given is `ready`, as with today's rules | FR-63 (OC-1), FR-64 (OC-2) |
| CP20 ★ | the owner's validation sheet for round 04 (`rounds/04/validation.md`): AC-017, AC-018, the kind cases of CP19, the decisions of CP18; the requirements found unsound and the inventory of CP17 are written down as findings | FR-63, FR-64 |

## What the agent may do
Work only inside the worktree; merge `goal/v4` into `prototype/g-v4` before CP17 (as before round 03); extend the prototype (checks and code); write drafts of requirements of this subgoal as it needs them, with `Status: Draft`; use throw-away databases by name only.
## What the agent may not do
Change the top-level spec (proposals only, e.g. a ninth rule); change protected material (tests, contracts, mocks) even inside the prototype (the inventory lists what Plan must amend); touch production data or product code paths outside the worktree; present the result as verified; sign anything.
## Stop rules
Stop at the budget, when a top-level outcome looks unreachable, or when the round would need something not allowed above. Write the report either way.

## TLS fingerprint (the protected part)
| Fingerprint | Date | Decided by | Reason |
|---|---|---|---|
| cb0a21233175 | 2026-11-22 | Stefan Reiterer | run authorized; no top-level spec changed since the amendments of D-405 (round 03) |

## Validation plan
The owner validates with `rounds/04/validation.md` (one row per outcome and one per open decision of CP18), after CP19. Findings go to the requirements of this subgoal and, for the inventory of CP17, to the amendments Plan proposes.
