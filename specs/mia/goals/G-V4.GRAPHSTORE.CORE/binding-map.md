# Binding map: G-V4.GRAPHSTORE.CORE

<!-- The binding pass of Plan (dev-workflow/references/binding.md, M52): which low-level requirements are FIXED (must survive
     a rebuild: something observable notices when they change) and which stay OPEN (the agent's freedom).
     Step 1: `binding_check.py --presort`, run on this folder together with the round records of the parent goal
             (`specs/mia/goals/G-V4/prototype/rounds/`, `accepted-cases.md`), because a subgoal keeps none of its own:
             all 19 requirements without an explicit binding trace to an item the owner validated in round 03 (FR-57, FR-60, NFR-16 met).
     Step 2: probes on a scratch copy of the prototype (2026-11-21): one requirement loosened at a time, the oracle run, the code restored.
             Oracle: the checks that witness the accepted cases AC-001 (TC-WFM-166, 167, 176, 177), AC-002 (TC-GTB-033, 034, TC-WFM-163),
             AC-003 (TC-WFM-165, 168, 169), the HLS measures HR-003 to HR-005 (realized by the same checks on the fixtures), the contract
             suite IF-301 v3 (real side) and TC-GTB-036. A requirement's own check is noted but does not decide. Baseline before and after:
             70 tests green, PostgreSQL not skipped.
     Step 3: the owner decides (below) and signs. -->

Reviewed by:
Date:
Iteration: 0 (plan gate)
Share fixed: 19 of 22 LLS requirements, 86 % (proposed); Persistence 4 of 4, TaskRuntime 15 of 18. Above the 30 % warning of BD3: CORE is the storage boundary that every later subgoal builds on, and every item traces to a validated outcome.

| Requirement | Subject | Traces to (validated outcome) | Pre-sort | Probe (changed, result) | Witness | Binding | Decided by |
|---|---|---|---|---|---|---|---|
| REQ-GTB-029 | Persistence | FR-60 | candidate fixed | removed the `unscoped_id` check of a step or connection ID: TC-GTB-033, TC-GTB-036, IF-301 real fail | TC-GTB-033 (AC-002) | fixed (proposed) | |
| REQ-GTB-030 | Persistence | FR-60 | candidate fixed | removed the check of a header member of another graph: TC-GTB-034, TC-GTB-036, IF-301 real fail | TC-GTB-034 (AC-002) | fixed (proposed) | |
| REQ-GTB-031 | Persistence | FR-60 | candidate fixed | split at the last slash instead of the first: TC-GTB-036 fails (own check TC-GTB-035 too) | TC-GTB-036 (thin: only its `look/up`, `/lookup` cases) | fixed (proposed) | |
| REQ-WFM-160 | TaskRuntime | FR-60 | candidate fixed | member test `startswith(graph id + "/")`, so `look/up` is accepted: TC-GTB-036 fails (own TC-WFM-178 too) | TC-GTB-036 (thin, as above) | fixed (proposed) | |
| REQ-WFM-144 | TaskRuntime | FR-60 | candidate fixed | `read_graph` returns record IDs instead of local IDs: TC-WFM-163, 165, 166, 168, 169, 177 fail | TC-WFM-163 (AC-002) | fixed (proposed) | |
| REQ-WFM-145 | TaskRuntime | FR-60 | candidate fixed | (a) all stored versions listed, pinned or not: nothing fails; (b) newest first: TC-WFM-163 fails; (c) no account and time: TC-WFM-163 fails | TC-WFM-163 (AC-002); clause "only pinned versions" unwitnessed | fixed (proposed), see question 2 | |
| REQ-WFM-146 | TaskRuntime | NFR-16 | candidate fixed | pre-write record and header checks removed: TC-GTB-036 fails (own TC-WFM-164 too) | TC-GTB-036 | fixed (proposed) | |
| REQ-WFM-147 | TaskRuntime | NFR-16 | candidate fixed | header written before the members (with `unknown_member` off to make it reachable): TC-WFM-165, 169 fail | TC-WFM-165 (AC-003) | fixed (proposed) | |
| REQ-WFM-148 | TaskRuntime | FR-57 | candidate fixed | every member written as a new version: TC-WFM-165, 166, 167, 169 fail | TC-WFM-166 (AC-001) | fixed (proposed) | |
| REQ-WFM-149 | TaskRuntime | FR-57 | candidate fixed | "unchanged graph, no version" removed: TC-WFM-167, 169 fail | TC-WFM-167 (AC-001) | fixed (proposed) | |
| REQ-WFM-150 | TaskRuntime | NFR-16 | candidate fixed | (a) header pre-check removed: TC-GTB-036 fails; (b) refusal names nothing: TC-WFM-168, TC-GTB-036 fail; (c) record refusals unnamed: TC-GTB-036 fails | TC-WFM-168 (AC-003), TC-GTB-036 | fixed (proposed) | |
| REQ-WFM-151 | TaskRuntime | NFR-16 | candidate fixed | a save that meets a leftover version refuses instead of finishing: TC-WFM-169 fails | TC-WFM-169 (AC-003) | fixed (proposed) | |
| REQ-WFM-152 | TaskRuntime | FR-57 | candidate fixed | context members mapped to the workflow tables: TC-WFM-165, 169, 177 fail (own TC-WFM-170 too) | TC-WFM-165 (AC-003) | fixed (proposed) | |
| REQ-WFM-153 | TaskRuntime | FR-57 | candidate fixed | no kind refused, or treated as context: nearly every oracle item fails | TC-WFM-163 (AC-002) and more | fixed (proposed) | |
| REQ-WFM-154 | TaskRuntime | FR-57 | candidate fixed | an unknown kind treated as workflow: TC-GTB-036 fails (own TC-WFM-172 too) | TC-GTB-036 | fixed (proposed) | |
| REQ-WFM-155 | TaskRuntime | FR-57 | open (explicit) | – | – | open: the rule set of the context kind is CONTEXT's decision (ASM-4 of round 03) | |
| REQ-WFM-161 | TaskRuntime | FR-57 | open (explicit) | – | – | open: as REQ-WFM-155 | |
| REQ-WFM-156 | TaskRuntime | FR-57 | open (explicit) | – | – | open: as REQ-WFM-155 | |
| REQ-WFM-157 | TaskRuntime | FR-57 | candidate fixed | `read_graph` drops `kind: context`: TC-WFM-165, 169, 177 fail | TC-WFM-165 (AC-003) | fixed (proposed) | |
| REQ-WFM-158 | TaskRuntime | FR-57 | candidate fixed | (a) versions without account and time: TC-WFM-176 fails; (b) newest first: TC-WFM-176, 168 fail | TC-WFM-176 (AC-001) | fixed (proposed) | |
| REQ-WFM-159 | TaskRuntime | FR-57 | candidate fixed | (a) header always read at the newest version: TC-WFM-177 fails; (b) members at the newest version: TC-WFM-165, 177 fail | TC-WFM-177 (AC-001) | fixed (proposed) | |
| REQ-GTB-032 | Persistence | FR-57 | candidate fixed | `Storage.put` skips the graph record checks on PostgreSQL only: TC-GTB-036 fails | TC-GTB-036 | fixed (proposed) | |

## Questions for the owner (step 3)
1. **The fixed set as a whole:** 19 fixed, 3 open (the context rule set, for CONTEXT). 86 % is above the 30 % warning; the reason is above.
2. **REQ-WFM-145, clause "only the versions the headers pin":** no oracle item sees leftover versions of an interrupted save in a step history (TC-WFM-163 has no interrupted save; the owner kept it so). Either add an accepted case (an interrupted save, then the step history lists only pinned versions), or leave that clause open.
3. **REQ-GTB-031 and REQ-WFM-160:** witnessed only by the slash cases of TC-GTB-036, no accepted case. Accept the thin witness, or add an accepted case.

## History
| Iteration | Date | Requirement | From → to | Evidence | Amendment | Decided by |
|---|---|---|---|---|---|---|
