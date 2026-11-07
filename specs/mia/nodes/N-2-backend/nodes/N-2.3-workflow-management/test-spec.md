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
| TC-WFM-034 | REQ-WFM-034 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: run mode asks nothing below the cap; the time cap is 1800 s of work time and waiting for the user uses none of it; at the cap continue, summarize and stop do what the requirement says, no answer summarizes; slice mode asks at each limit | exact |
| TC-WFM-035 | REQ-WFM-035 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: a new model is asked once and never again; a paid model gives the warning and slice; /model local changes the class | exact |
| TC-WFM-036 | REQ-WFM-036 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: the result message is later in the history than the last question and its answer; a failing task leaves a result with the reason | exact |
| TC-WFM-037 | REQ-WFM-037 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: a stored file is listed and downloaded; the result ends with a link for each file; bad names and types and files over a limit are refused; a file deleted in the volume leaves the list | exact |
| TC-WFM-038 | REQ-WFM-038 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-3: the record read back equals the report; the markdown and LaTeX files hold every work; special characters are escaped | exact |
| TC-WFM-039 | REQ-WFM-039 | Component | 2 | component test with a temporary extensions folder; inspection of the core files | AC-23: a folder with a manifest is loaded, listed, parsed and run; no core file names a skill id | exact |

## Test cases of G-V2.CONVERT (REQ-WFM-057 to 066, 069, 115)

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-WFM-057 | REQ-WFM-057 | Component | 2 | component test with the mocks of the neighbouring interfaces; one skill marked unconverted, one marked converted, each with an old and a converted version | AC-34: the unconverted skill runs its old skill file and pipeline and its converted version is never used; the converted skill runs the converted version | exact |
| TC-WFM-058 | REQ-WFM-058 | Component | 2 | the fake model server of `pipeline.py` with scripted replies; old runner and converted skill run the same input for each of the 5 converted skills that call a model | AC-34: the recorded lists of model calls (order, prompt, options) are equal; one changed option or prompt makes the check fail and names the first differing call | exact |
| TC-WFM-059 | REQ-WFM-059 | Component | 2 | scripted run files of `eval_decide.py` for three skills: 17 of 20 right, 15 of 20 right twice, and a run of another suite | AC-34: the first skill is accepted; the second stays unconverted after the re-run; the third is not decided and stays unconverted | exact |
| TC-WFM-060 | REQ-WFM-060 | Inspection | 1 | the record of the 15 skills of v0.1.0 read by a script and by a person | AC-34: each skill names its form and either a verdict with suite, run and pins or a reason; the nine interface skills carry the reason of the owner of 2026-11-07 | exact |
| TC-WFM-061 | REQ-WFM-061 | Component | 2 | component test with the mocks of the neighbouring interfaces; a state of 2 skills, 2 workflow graphs, 1 context graph, 3 transforms (trusted tested, trusted draft, untrusted retired) and the pin MP-light | AC-40: the snapshot "before-rework" holds all 8 items with version, trust and lifecycle and the pin | exact |
| TC-WFM-062 | REQ-WFM-062 | Component | 2 | component test with the mocks of the neighbouring interfaces; two snapshots taken at two different times by the owner | AC-40: both are listed with name, time and author | exact |
| TC-WFM-063 | REQ-WFM-063 | Component | 2 | component test with the mocks of the neighbouring interfaces; state S2 differs from snapshot "a" | AC-40: restoring "a" first creates a snapshot of S2; restoring that snapshot gives S2 back | exact |
| TC-WFM-064 | REQ-WFM-064 | Component | 2 | component test with the mocks of the neighbouring interfaces; after "a" a skill, a workflow graph, a context graph and a transform status are changed | AC-40: after the restore each item has the version, trust and lifecycle of "a"; the transform untrusted in "a" is untrusted | exact |
| TC-WFM-065 | REQ-WFM-065 | Component | 2 | component test with the mocks of the neighbouring interfaces; the lists of versions of every item before and after a restore | AC-40: each list before is a prefix of the list after (no version deleted) | exact |
| TC-WFM-066 | REQ-WFM-066 | Component | 2 | component test with the mocks of the neighbouring interfaces; a non-owner account and the owner account | AC-40: the non-owner is refused for take and restore and the state is unchanged; the owner succeeds | exact |
| TC-WFM-069 | REQ-WFM-069 | Component | 2 | component test with the mocks of the neighbouring interfaces; the equivalence settings at version 1 (margin 0.10, repeats 3, rule threshold) and a change of the margin to 0.05 | AC-34: version 2 is created; a new result names 2; the earlier result still names 1 and is not decided again | exact |
| TC-WFM-115 | REQ-WFM-115 | Component | 2 | the old runner and the converted skill extract_claims_rules on the 51 dev cases of EV-extraction, no model | AC-34: the 51 outputs are equal; a planted difference in one output is reported as a diff | exact |

TC-WFM-110 to 114 (the five eval criteria of the converted skills) are statistical checks at stage 4 and are in the table "Statistical checks" of the root `test-spec.md`. The eval runs need the cases tagged `split:dev` (amendment A-120, proposed) and the v0.1.0 baselines recorded with 3 repeats (see `eval-spec.md`, section G-V2.CONVERT).

## Scenarios (G-V2.CONVERT, for the owner's review, M39)

### TC-WFM-057 – Old runner until proven
- Verifies: REQ-WFM-057
- Given: skills A (unconverted) and B (converted), each with its old file and pipeline and a converted record, the fake model server
- When: a command of A and a command of B are run
- Then: A runs its old skill file and pipeline (the converted record of A is not read); B runs the converted record
- And: marking A converted without a passed check is refused

### TC-WFM-058 – Same model calls
- Verifies: REQ-WFM-058
- Given: the fake model server with scripted replies and, for each of the 5 converted skills that call a model (research, plan_question, verify_claim, verify_computable, extract_claims), one input
- When: the old runner and the converted skill run that input
- Then: the lists of model calls (order, prompt text, options) are equal; with one option changed in the converted version (temperature 0 to 0.2) the check fails and names call 1 of that skill

### TC-WFM-059 – Accept only on the criterion
- Verifies: REQ-WFM-059
- Given: three scripted run files for criterion lines of REQ-WFM-110: 17 of 20 cases right, 15 of 20 right in the first run and again in the re-run, and a run whose header names the suite plans
- When: `eval_decide.py` decides each and the acceptance rule applies the result
- Then: 17 of 20 (0.85, limit 0.82) is PASS and the skill is accepted; 15 of 20 (0.75) is FAIL after the re-run and the skill stays unconverted; the wrong-suite run is NOT DECIDED and the skill stays unconverted

### TC-WFM-060 – Record of the check
- Verifies: REQ-WFM-060
- Given: the record of the 15 skills of v0.1.0: chat, check_speech, memory_write, summarize, research, plan_question, verify_claim, verify_computable, extract_claims, extract_claims_rules, review_abstract, review_full, review_keywords, review_section, review_summary
- When: a script lists the record and a person reads it
- Then: every skill names the form it runs on; the six skills with an equivalence requirement carry suite, run, pins and verdict (or the reason that it stays old); the nine others (chat, check_speech, memory_write, summarize and the five review skills) carry the reason "part of the user interface, stays on the old runner, revisited in a later goal" (owner, 2026-11-07)

### TC-WFM-061 – Take a snapshot
- Verifies: REQ-WFM-061
- Given: a state of 2 skills, 2 workflow graphs, 1 context graph and 3 transforms (trusted and tested, trusted and draft, untrusted and retired), the pin MP-light, and the owner account
- When: the owner takes the snapshot "before-rework"
- Then: the snapshot holds 8 items, each with version; the 3 transforms also with trust and lifecycle; and the pin MP-light

### TC-WFM-062 – List snapshots
- Verifies: REQ-WFM-062
- Given: two snapshots "a" and "b" taken at two times by the owner
- When: the owner lists the snapshots
- Then: two entries, each with name, time and author (3 fields)

### TC-WFM-063 – Restore keeps the former state
- Verifies: REQ-WFM-063
- Given: state S1 stored as snapshot "a"; later state S2 differs from S1 in 4 items
- When: the owner restores "a"
- Then: before anything is replaced a snapshot of S2 exists; the state equals S1; restoring that new snapshot gives S2 again

### TC-WFM-064 – Restore gives version and statuses
- Verifies: REQ-WFM-064
- Given: snapshot "a"; afterwards a skill gets a new version, a workflow graph and a context graph are edited, one transform is set trusted that was untrusted in "a", another is retired
- When: the owner restores "a"
- Then: each of the 4 changed items equals the stored one in version, trust and lifecycle; the transform untrusted in "a" is untrusted

### TC-WFM-065 – Restore deletes nothing
- Verifies: REQ-WFM-065
- Given: the lists of versions of 8 items before a restore
- When: the owner restores a snapshot that is older than the last 3 versions
- Then: for every item the list before the restore is a prefix of the list after it

### TC-WFM-066 – Snapshots only by the owner
- Verifies: REQ-WFM-066
- Given: the owner account and an account that is not the owner; snapshot "a" and a changed state
- When: the other account asks to take a snapshot and to restore "a"; then the owner does both
- Then: both requests of the other account are refused and the list of snapshots and the state are unchanged; the owner succeeds

### TC-WFM-069 – Settings are versioned configuration
- Verifies: REQ-WFM-069
- Given: settings version 1 (margin 0.10, repeats 3, rule threshold) and one result recorded with it
- When: the margin is changed to 0.05 and a second result is recorded
- Then: settings version 2 exists; the new result names 2; the earlier result still names 1 and is not decided again

### TC-WFM-115 – Same outputs of the rule-based skill
- Verifies: REQ-WFM-115
- Given: the old runner and the converted extract_claims_rules, the 51 dev cases of EV-extraction (no model); a copy of the converted skill with one output changed
- When: both run all 51 cases
- Then: the 51 outputs are equal; the changed copy is reported with a diff naming the case

### TC-WFM-110 – Equivalence of research
- Verifies: REQ-WFM-110
- Given: suite EV-research dev (20 cases, tagged split:dev), pin MP-light (digest in eval-spec.md), 3 repeats folded by majority, the converted skill research, the v0.1.0 baseline recorded at 3 repeats (reference 0.92)
- When: one run of the suite with `python tools/eval.py run research --pin MP-light --repeats 3`
- Then: `eval_decide.py` on the criterion of REQ-WFM-110: PASS with at least 17 of 20 cases right (0.82); a FAIL is re-run once with fresh seeds and only the re-run counts
- And: the secondary suite EV-research_compound is run and reported, not decided

### TC-WFM-111 – Equivalence of plan_question
- Verifies: REQ-WFM-111
- Given: suite EV-plans dev (36 cases, split:dev), MP-light, 3 repeats, the converted skill plan_question, baseline of plan.free@1 (reference 0.64)
- When: one run of the suite
- Then: PASS with at least 20 of 36 cases right (0.54); a FAIL is re-run once

### TC-WFM-112 – Equivalence of verify_claim
- Verifies: REQ-WFM-112
- Given: suite EV-verdicts dev (50 cases, split:dev), MP-light, 3 repeats, the converted skill verify_claim, baseline of verify.single@1 re-recorded at 3 repeats (reference 0.93 from 1 run)
- When: one run of the suite
- Then: PASS with at least 42 of 50 cases right (0.83); a FAIL is re-run once
- And: EV-verdicts_injection and EV-verdicts_wikidata are run and reported, not decided

### TC-WFM-113 – Equivalence of verify_computable
- Verifies: REQ-WFM-113
- Given: suite EV-computable dev (39 cases, split:dev), MP-light, 3 repeats, the converted skill verify_computable, baseline of verify.computable@2 re-recorded at 3 repeats (reference 0.92 from 1 run)
- When: one run of the suite
- Then: PASS with at least 32 of 39 cases right (0.82); a FAIL is re-run once

### TC-WFM-114 – Equivalence of extract_claims
- Verifies: REQ-WFM-114
- Given: suite EV-extraction dev (51 cases, split:dev), MP-light, 3 repeats, the converted skill extract_claims, baseline of extract.llm@1 re-recorded at 3 repeats (reference 0.69 from 1 run)
- When: one run of the suite
- Then: PASS with at least 31 of 51 cases right (0.59); a FAIL is re-run once

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
