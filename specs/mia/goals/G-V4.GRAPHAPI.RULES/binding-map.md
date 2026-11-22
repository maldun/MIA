# Binding map: G-V4.GRAPHAPI.RULES

<!-- The binding pass of Plan (dev-workflow/references/binding.md, M52): which low-level requirements are FIXED (must survive a rebuild: something
     observable notices when they change) and which stay OPEN (the agent's freedom).
     Step 1, pre-sort: every requirement traces to an outcome the owner validated in round 04 (FR-63, FR-64 met; AC-017, AC-018) or to the IF-301 v4
     contract the consumers test against (D-417, D-419).
     Step 2, probes: the deliberate defects of TR-RULES-008. Two ran on the scratch copy of 2026-11-22 (prototype rule set in front of the runner);
     the others run in the task that builds the requirement (plan.md, "Done when") and are logged in implementation-log.md.
     Step 3: decided by the agent by delegation (D-423); the owner's box below. -->

Reviewed by: [ ] (the owner ticks)
Date: 2026-11-22 (agent by delegation, D-423)
Iteration: 0 (plan gate)
Share fixed: 31 of 31 (28 new, 3 changed; corrected from "30 of 30, 27 new", Verify V-5), 100 %. Above the 30 % warning of BD3: every item is part of the IF-301 v4 contract that the save path, the runner and later EDIT and CONTEXT consume, or is what a person sees in a refusal (AC-017, AC-018); none is an internal choice.

| Requirement | Subject | Traces to (validated outcome) | Pre-sort | Probe (defect, result) | Witness | Binding | Decided by |
|---|---|---|---|---|---|---|---|
| REQ-GTB-033 | Persistence | FR-63, IF-301 v4 | candidate fixed | planned T-01: `kinds()` returns a shared dict (a caller's change sticks) | TC-IF-301-27 | fixed | agent by delegation (D-423) |
| REQ-GTB-034 | Persistence | FR-63 (D-375) | candidate fixed | planned T-01: two rules swapped in the registry | TC-GTB-046 (AC-017), TC-IF-301-29 | fixed | agent by delegation (D-423) |
| REQ-GTB-035 | Persistence | FR-63 (Q-3) | candidate fixed | planned T-01: rule 4 left out of the context kind | TC-IF-301-31 | fixed | agent by delegation (D-423) |
| REQ-GTB-036 | Persistence | FR-64 | candidate fixed | planned T-01: context marked as running | TC-IF-301-32 | fixed | agent by delegation (D-423) |
| REQ-GTB-037 | Persistence | FR-63, OC-1 | candidate fixed | planned T-01: the first broken rule only | TC-GTB-046 (AC-017) | fixed | agent by delegation (D-423) |
| REQ-GTB-038 | Persistence | FR-63 | candidate fixed | planned T-01: no kind treated as unknown | TC-IF-301-28 | fixed | agent by delegation (D-423) |
| REQ-GTB-039 | Persistence | FR-63 (D-404, Q-7) | candidate fixed | planned T-01: an unknown kind checked with the workflow rules | TC-IF-301-32 | fixed | agent by delegation (D-423) |
| REQ-GTB-040 | Persistence | IF-301 v4 (A-60 contract, D-418 (2)) | candidate fixed | planned T-01: a step that is not an object reaches `.get` | TC-IF-301-34 | fixed | agent by delegation (D-423) |
| REQ-GTB-041 | Persistence | FR-63 (D-375, Q-4) | candidate fixed | planned T-01: a slash refused in a step ID | TC-GTB-042, TC-IF-301-34 | fixed | agent by delegation (D-423) |
| REQ-GTB-042 | Persistence | FR-63 | candidate fixed | planned T-01: rule 2 off | TC-GTB-042 | fixed | agent by delegation (D-423) |
| REQ-GTB-043 | Persistence | FR-63, FR-64 | candidate fixed | planned T-01: rule 3 off | TC-GTB-046 (AC-017), TC-IF-301-30 | fixed | agent by delegation (D-423) |
| REQ-GTB-044 | Persistence | FR-63 (D-375) | candidate fixed | planned T-01: identical connections with different IDs not compared | TC-GTB-046 (AC-017), TC-IF-301-31 | fixed | agent by delegation (D-423) |
| REQ-GTB-045 | Persistence | FR-63 | candidate fixed | planned T-01: rule 5 off | TC-GTB-042 | fixed | agent by delegation (D-423) |
| REQ-GTB-046 | Persistence | FR-63 (AC-017) | candidate fixed | planned T-01: rule 6 off | TC-GTB-046 (AC-017), TC-IF-301-29 | fixed | agent by delegation (D-423) |
| REQ-GTB-047 | Persistence | FR-63 (Q-1, ASM-3) | candidate fixed | planned T-01: the data-step pass of rule 7 off | TC-GTB-046 (AC-017) | fixed | agent by delegation (D-423) |
| REQ-GTB-048 | Persistence | FR-63 (Q-5) | candidate fixed | planned T-01: the cycle asked while rule 3 is broken | TC-GTB-046 (AC-017), TC-IF-301-30 | fixed | agent by delegation (D-423) |
| REQ-GTB-049 | Persistence | FR-64 (ASM-7) | candidate fixed | planned T-01: the rules of a context graph listed beside its kind | TC-RUN-036 (AC-018), TC-IF-301-32 | fixed | agent by delegation (D-423) |
| REQ-GTB-050 | Persistence | FR-64 (D-416 (3)) | candidate fixed | planned T-01: inputs listed before rules | TC-RUN-036 (AC-018), TC-IF-301-33 | fixed | agent by delegation (D-423) |
| REQ-GTB-051 | Persistence | FR-64 (AC-018) | candidate fixed | planned T-01: a settings connection counted as an input | TC-GTB-044 (AC-018), TC-IF-301-33 | fixed | agent by delegation (D-423) |
| REQ-GTB-052 | Persistence | Q-6 | candidate fixed | planned T-01: a document-form suite edited (TC-GTB-045 compares with goal/v4) | TC-GTB-045 | fixed | agent by delegation (D-423) |
| REQ-WFM-162 | TaskRuntime | FR-63 | candidate fixed | planned T-02: save path left on `check_graph` | TC-WFM-179, TC-GTB-046 (AC-017) | fixed | agent by delegation (D-423) |
| REQ-WFM-163 | TaskRuntime | FR-63 (AC-017) | candidate fixed | planned T-02: `rules` left empty | TC-WFM-180 (AC-017), TC-GTB-046 | fixed | agent by delegation (D-423) |
| REQ-WFM-164 | TaskRuntime | FR-63; three protected tests call `check_graph` | candidate fixed | planned T-02: repeats removed from the flat list | TC-WFM-181; `test_pipeline_graph.py`, `test_skill_binding.py`, `test_graph_order.py` | fixed | agent by delegation (D-423) |
| REQ-WFM-165 | TaskRuntime | FR-57 (CORE V-3, D-414) | candidate fixed | planned T-02: versions of an unknown graph answered with [] | TC-WFM-182 | fixed | agent by delegation (D-423) |
| REQ-WFM-150 (changed) | TaskRuntime | NFR-16, FR-63 (AC-003, AC-017) | candidate fixed | planned T-02: the first broken rule only | TC-WFM-180 (AC-017), TC-WFM-168 (AC-003) | fixed | agent by delegation (D-423) |
| REQ-WFM-154 (changed) | TaskRuntime | FR-57 (CORE V-2, D-414) | candidate fixed | planned T-02: `"kind": None` treated as no kind | TC-WFM-183 | fixed | agent by delegation (D-423) |
| REQ-WFM-155 (changed) | TaskRuntime | FR-57, FR-63 (Q-3) | candidate fixed | planned T-02: `context_problems` kept in the save path | TC-WFM-184 | fixed (was open in CORE: the context rule set is now the registry's; CONTEXT changes it by amendment) | agent by delegation (D-423) |
| REQ-RUN-036 | TaskRuntime | FR-64 (AC-018) | candidate fixed | planned T-03: the first step run before the run check | TC-RUN-036 (AC-018) | fixed | agent by delegation (D-423) |
| REQ-RUN-037 | TaskRuntime | FR-64, OC-2 | candidate fixed | **ran 2026-11-22**: repeats removed from `named`: TC-RUN-037 cases and three cycle checks of `test_graph_run_findings.py` fail | TC-RUN-037 (AC-018) | fixed | agent by delegation (D-423) |
| REQ-RUN-038 | TaskRuntime | FR-64 (D-416 (3)) | candidate fixed | planned T-03: trust checked before the run check | TC-RUN-038 | fixed | agent by delegation (D-423) |
| REQ-RUN-039 | TaskRuntime | FR-64, REQ-RUN-034 (D-418 (1)) | candidate fixed | **ran 2026-11-22**: prepare inputs not counted as given: TC-RUN-034 refused in two cases | TC-RUN-039, TC-RUN-034 | fixed | agent by delegation (D-423) |

## History
| Iteration | Date | Requirement | From → to | Evidence | Amendment | Decided by |
|---|---|---|---|---|---|---|
| 0 | 2026-11-22 | all 30 | candidate → fixed | two probes on the scratch copy (table), the rest planned per task | – | agent by delegation (D-423) |
