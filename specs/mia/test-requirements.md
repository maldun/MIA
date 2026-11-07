# Test requirements: MIA, goal G-V2.MODEL (skill record and graph model)

<!-- M41: requirements on the checks, apart from the product requirements. Written in Plan step 3 of G-V2.MODEL
     (2026-11-07) for TC-WFM-040..049 and TC-RUN-016..019 only; the other subgoals of G-V2 add their own groups.
     The repository has no shared test-requirement catalog (M43) yet, so no item has a Source line.
     Setup kind: written out with numbers and reviewed in detail. Unit kind: grouped, signed off as a group.
     Protected like the checks from the plan gate on. -->

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
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
