# Test specification: Workflow management (N-2.3)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md   **Status:** Draft (Plan for node N-2.3, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-203 (provider), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-WFM-001 | REQ-WFM-001 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: the selectable list shows each skill; a selected skill runs its pipeline | as stated |
| TC-WFM-002 | REQ-WFM-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-10, AC-16: an edit creates version n+1 and leaves version n unchanged | exact |
| TC-WFM-003 | REQ-WFM-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-27: a workflow with a cycle is refused with the cycle named; property test on generated graphs: every accepted graph has a topological order | as stated |
| TC-WFM-004 | REQ-WFM-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-27: each of the three violations is refused with the rule named | exact |
| TC-WFM-005 | REQ-WFM-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-10: a proposed entry has status draft and cannot be run as trusted | as stated |
| TC-WFM-006 | REQ-WFM-006 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-10: promotion of a workflow lacking its specification or its benchmark is refused (exact) | exact |
| TC-WFM-007 | REQ-WFM-007 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-9: the record has two time stamps for each promoted skill | as stated |
| TC-WFM-008 | REQ-WFM-008 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-10: the view of a step stays within its budget in tokens (exact on the recorded lookup run) | as stated |
| TC-WFM-009 | REQ-WFM-009 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-28: on the recorded lookup runs the estimate is within the factor set in Plan of the measured time | as stated |
| TC-WFM-010 | REQ-WFM-010 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-17: a run with a variant sends the variant name; a run without sends none | as stated |
| TC-WFM-011 | REQ-WFM-011 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2: in the run log the code checks precede the first model call of each claim | as stated |
| TC-WFM-012 | REQ-WFM-012 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2: for 10 claims with a number and no evidence there are 0 model calls and the verdict is unclear | exact |
| TC-WFM-013 | REQ-WFM-013 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2: the judge input contains the check line; the verdict is the judge's | exact |
| TC-WFM-014 | REQ-WFM-014 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-2: decided with the rule of the agent-app workflow against the baseline | per the criterion; never decided on one run |
| TC-WFM-015 | REQ-WFM-015 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-2: stability limit 0.90 (lower bound of the 95 % interval, at least) on the dev suites (REQ-VER-005, REQ-VER-006) | per the criterion; never decided on one run |
| TC-WFM-016 | REQ-WFM-016 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown | as stated |
| TC-WFM-017 | REQ-WFM-017 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: /search returns the list and starts no pipeline | as stated |
| TC-WFM-018 | REQ-WFM-018 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-3: per tier source recall and precision against the baseline | per the criterion; never decided on one run |
| TC-WFM-019 | REQ-WFM-019 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: after the abstract screening or the first slice (60 s) the run waits for agreement; without it nothing more is read | exact |
| TC-WFM-020 | REQ-WFM-020 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-3: with a fake model that always says done, the run still continues until the code check holds | as stated |
| TC-WFM-021 | REQ-WFM-021 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: 0 violations of the cut-off; retracted works are dropped and listed | exact |
| TC-WFM-022 | REQ-WFM-022 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-26: the known method is in the top 3 on the retro-discovery cases | per the criterion; never decided on one run |
| TC-WFM-023 | REQ-WFM-023 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: each result shows its limits | as stated |
| TC-WFM-024 | REQ-WFM-024 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-3: 0 invented references and 100 % of cited quotes found in their source | per the criterion; never decided on one run |
| TC-WFM-025 | REQ-WFM-025 | Inspection | 1 | the code and the log files of the repository | AC-15: no database driver is imported outside the storage client | as stated |
| TC-WFM-026 | REQ-WFM-026 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-16: with the fake storage each of the six operations works; an invalid graph is refused with the rule named | exact |
| TC-WFM-027 | REQ-WFM-027 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: a term below N works is never proposed; a proposed term is searched only after approval | exact |
| TC-WFM-028 | REQ-WFM-028 | Component | 2 | component test with the fake model server and the mocks of the interfaces | AC-3: every statement quotes its source; the combined grade follows the rule; grade and eligibility are independent; abstract only is marked | exact |
| TC-WFM-029 | REQ-WFM-029 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: the list of commands shows each skill under its id; a duplicate id is refused; a new skill file appears without a change of code | exact |
| TC-WFM-030 | REQ-WFM-030 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: options run, list, are refused when unknown, configured defaults are overridden by the call | exact |
| TC-WFM-031 | REQ-WFM-031 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: the card shows exactly the reported figures; two reports within half a second give one update; the final figures stay | exact |
| TC-WFM-032 | REQ-WFM-032 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: on a scripted run list = processed + to process and included + maybe + excluded = processed after every step; every limit shows used and limit | exact |
| TC-WFM-033 | REQ-WFM-033 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: after pause no step starts and the used time is constant; resume goes on from the same step; stop ends a paused task | exact |
| TC-WFM-034 | REQ-WFM-034 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: run mode asks nothing below the cap and ends at the cap with the cap named; slice mode asks at each limit | exact |
| TC-WFM-035 | REQ-WFM-035 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: a new model is asked once and never again; a paid model gives the warning and slice; /model local changes the class | exact |
| TC-WFM-036 | REQ-WFM-036 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: the result message is later in the history than the last question and its answer | exact |
| TC-WFM-037 | REQ-WFM-037 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: a stored file is listed and downloaded byte for byte; bad names and types and files over a limit are refused; a file deleted in the volume leaves the list | exact |
| TC-WFM-038 | REQ-WFM-038 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: the record read back equals the report; the markdown and LaTeX files hold every work; special characters are escaped | exact |
| TC-WFM-039 | REQ-WFM-039 | Component | 2 | component test with a temporary extensions folder; inspection of the core files | AC-23: a folder with a manifest is loaded, listed, parsed and run; no core file names a skill id | exact |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
