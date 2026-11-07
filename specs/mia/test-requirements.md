# Test requirements: MIA

Requirements on the checks of `test-spec.md` (M41): under which conditions a verdict counts. Protected like the checks; changed only by amendment. This file starts with goal G-V2.CONVERT (REQ-WFM-057 to 066, 069, 110 to 115); other goals add their items with their own prefix. No catalog item is adopted: `dev-workflow/assets/test-requirements-catalog.md` is a blank template, so there is no `Source:` line.
# Test requirements: MIA, goal G-V2.MODEL (skill record and graph model)

<!-- M41: requirements on the checks, apart from the product requirements. Written in Plan step 3 of G-V2.MODEL
     (2026-11-07) for TC-WFM-040..049 and TC-RUN-016..019 only; the other subgoals of G-V2 add their own groups.
     The repository has no shared test-requirement catalog (M43) yet, so no item has a Source line.
     Setup kind: written out with numbers and reviewed in detail. Unit kind: grouped, signed off as a group.
     Protected like the checks from the plan gate on. -->

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | Conversion eval runs | conditions under which an equivalence decision of a converted skill counts | TR-CONVERT-001, TR-CONVERT-002, TR-CONVERT-003, TR-CONVERT-004, TR-CONVERT-005 |
| 2 | Conversion stand-ins | the fake model server of the same-calls check | TR-CONVERT-006 |
| 3 | Conversion exact values | hand-checked expected values of the deterministic conversion and snapshot tests | TR-CONVERT-007 |

### TR-CONVERT-001 – Equivalence runs use the pinned model
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall run the old and the converted version of a skill on the model with the digest of pin MP-light and the options num_ctx, temperature and seed of eval-spec.md.
- Rationale: a model tag can point to new weights after a pull and another temperature changes the rates; the baselines of v0.1.0 were measured on this pin (eval-spec.md, Model pins)
- Credibility aspect: numerical settings
- Verified by: inspection
- Status: Draft

### TR-CONVERT-002 – Three repeats, fresh seeds for the re-run
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall run 3 repeats per case, fold them by majority, and decide a failing criterion only on one re-run with fresh seeds.
- Rationale: repeats of one case are not independent observations; the false alarm in the criterion lines (0.0001 to 0.0122) includes the re-run (M19)
- Credibility aspect: repetitions and seeds
- Verified by: inspection of the run header and `eval_decide.py --rerun`
- Status: Draft

### TR-CONVERT-003 – Power of the equivalence rule
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall have a false alarm of at most 0.02 and a miss of at most 0.13 at a true loss of 0.25 right cases, computed with false_alarm.py with the re-run for the size of its suite.
- Rationale: computed on 2026-11-07: false alarm 0.0001 to 0.0122, miss 0.0171 to 0.1242 at a loss of 0.25; at a loss of 0.15 the miss is 0.36 to 0.51, so a small loss is not caught by these suites, which is why REQ-WFM-058 is the main guard
- Credibility aspect: power and false-alarm rate
- Verified by: power analysis (false_alarm.py, commands in test-spec.md, statistical checks)
- Status: Draft

### TR-CONVERT-004 – The baseline is recorded before the converted run
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall use as reference the run of the v0.1.0 version of the skill with 3 repeats on the same cases and the same pin, recorded before the first run of its converted version, and its minimum shall not change after a converted run was seen.
- Rationale: the minimum is the baseline rate minus the margin; four of the five baselines were measured with one repeat (summaries of 2026-10-18 and 2026-10-19), so they are re-recorded at 3 repeats first (M19)
- Credibility aspect: reference accuracy
- Verified by: inspection of the baseline files and their dates
- Status: Draft

### TR-CONVERT-005 – Dev cases are tagged and unchanged
- Applies to: EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction, TC-WFM-110, TC-WFM-111, TC-WFM-112, TC-WFM-113, TC-WFM-114
- Requirement: REQ-WFM-110, REQ-WFM-111, REQ-WFM-112, REQ-WFM-113, REQ-WFM-114
- Group: Conversion eval runs
- Kind: setup
- Text: The check shall run only cases tagged split:dev, and no case shall change between the baseline run and the converted run.
- Rationale: without the tag `eval_decide.py` selects 0 cases for split=dev and fails (checked on a synthetic run on 2026-11-07, amendment A-120); the suites are starter suites seen during prompt work, so the check shows equivalence with the old version, not quality
- Credibility aspect: validity domain
- Verified by: inspection of the case files and `agent_check.py` (A6)
- Status: Draft

### TR-CONVERT-006 – The fake model server is as faithful as the real one
- Applies to: TC-WFM-058
- Requirement: REQ-WFM-058
- Group: Conversion stand-ins
- Kind: setup
- Text: The check shall use a fake model server that passes the contract suite of the model server interface, and a fake model server shall never decide an eval criterion.
- Rationale: the check compares lists of calls, so the fake has to record prompt and options as the real client sends them; rates are decided on the real pinned model only
- Credibility aspect: stand-in fidelity
- Verified by: contract suite
- Status: Draft

### TR-CONVERT-007 – Exact values of the conversion and snapshot tests
- Applies to: TC-WFM-057, TC-WFM-059, TC-WFM-060, TC-WFM-061, TC-WFM-062, TC-WFM-063, TC-WFM-064, TC-WFM-065, TC-WFM-066, TC-WFM-069, TC-WFM-115
- Requirement: REQ-WFM-057, REQ-WFM-059, REQ-WFM-060, REQ-WFM-061, REQ-WFM-062, REQ-WFM-063, REQ-WFM-064, REQ-WFM-065, REQ-WFM-066, REQ-WFM-069, REQ-WFM-115
- Group: Conversion exact values
- Kind: unit
- Text: Each check shall compare exact expected values that are written out in its scenario in test-spec.md and can be recalculated by hand.
- Rationale: counts (8 items, 51 outputs, 17 of 20), versions and statuses are exact
- Credibility aspect: numerical settings
- Verified by: known answer
| 1 | Stand-ins | The fakes that stand in for storage, models and transforms | TR-MODEL-001, TR-MODEL-004 |
| 2 | Rule checks | Checks that must refuse a wrong graph and accept a right one | TR-MODEL-002, TR-MODEL-003 |
| 3 | Exact values | Names and IDs in messages, versions | TR-MODEL-005 |

### TR-MODEL-001 – storage stand-in is a minimal fake with a known gap
- Applies to: TC-WFM-040, TC-WFM-041, TC-WFM-042, TC-WFM-044, TC-WFM-049
- Requirement: REQ-WFM-040
- Group: Stand-ins
- Kind: setup
- Text: The checks shall use a minimal fake of the graph tables that keeps versions and fields, and the fake shall be run against the contract suite of IF-301 v2 as soon as that suite exists.
- Rationale: owner decision 2026-11-07: the checks do not wait for the IF-301 v2 mock of STORE. The fake is only as faithful as the contract suite shows; until the suite exists the gap is known, and a fake that fails the suite later is a finding for these checks.
- Credibility aspect: stand-in fidelity
- Verified by: contract suite
- Status: Draft
- History: changed at review (2026-11-07) from "use only the IF-301 v2 mock" at the owner's answer

### TR-MODEL-002 – every refusal has an accepted twin
- Applies to: TC-WFM-042, TC-WFM-043, TC-WFM-045, TC-WFM-046, TC-WFM-048
- Requirement: REQ-WFM-043
- Group: Rule checks
- Kind: setup
- Text: Each check that expects a refusal shall also save a graph or record that differs only in the broken rule and expect it to be accepted.
- Rationale: a check that refuses every input would pass all refusal tests; the twin shows that the rule, and not the check, makes the difference (discriminating power).
- Credibility aspect: power and false-alarm rate
- Verified by: mutation (a stub that refuses everything makes the twin step fail)
- Status: Draft

### TR-MODEL-003 – cycle check on generated graphs
- Applies to: TC-WFM-047
- Requirement: REQ-WFM-047
- Group: Rule checks
- Kind: setup
- Text: The check shall use 200 generated graphs with seeds 1 to 200, at least 60 with a cycle of 2 to 5 nodes and at least 60 without, and shall test the topological order by checking that every edge points forward, not by calling the function under test again.
- Rationale: seeds are fixed so a failure is reproducible; the lower counts keep both outcomes covered at this size; an independent oracle avoids a check that agrees with a wrong implementation. Not a statistical acceptance check: the expected failure count is exactly 0.
- Credibility aspect: repetitions and seeds
- Verified by: known answer (three hand-drawn graphs with their cycles) and mutation
- Status: Draft

### TR-MODEL-004 – scripted nodes, observable effects
- Applies to: TC-RUN-016, TC-RUN-017, TC-RUN-018, TC-RUN-019
- Requirement: REQ-RUN-016
- Group: Stand-ins
- Kind: setup
- Text: The checks shall use scripted transforms and a scripted master node, no model server, and shall observe a run by an ordered list of node IDs and a marker file in a fresh temporary folder.
- Rationale: the runner's order, refusal and stop do not depend on a model; an observed side effect (marker) shows that a node did not run, which a returned status alone does not. Model behaviour is out of scope (no model step is new in this goal).
- Credibility aspect: stand-in fidelity
- Verified by: review
- Status: Draft

### TR-MODEL-005 – IDs and versions are exact, wording is not
- Applies to: TC-WFM-040, TC-WFM-042, TC-WFM-043, TC-WFM-045, TC-WFM-046, TC-WFM-048, TC-RUN-017, TC-RUN-019
- Requirement: REQ-WFM-042
- Group: Exact values
- Kind: unit
- Text: The checks shall compare the node, edge, skill or data node ID and the version number named in a refusal or result exactly, and shall not compare the sentence around it.
- Rationale: the requirements demand the name, not a wording; a test on the sentence breaks at every rephrasing.
- Credibility aspect: reference accuracy
- Verified by: review
- Sign-off: skimmed as a group
- Status: Draft
