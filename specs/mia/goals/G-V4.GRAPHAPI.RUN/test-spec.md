# Test specification: G-V4.GRAPHAPI.RUN

**Requirements:** `requirements.md` (REQ-GTB-053 to 060, REQ-WFM-166 to 168, REQ-RUN-040 to 045; changes of REQ-RUN-016 and REQ-WFM-110 to 115; REQ-RUN-030 to 035 taken in unchanged; reviewed by group 2026-11-24, D-478)   **High-level spec:** HR-001 to HR-007 (no hard bound, D-475 (4))   **Contract:** IF-301 v5 (`specs/mia/amendments/A-187/IF-301-graph-tables.md`, golden 32 to 35)   **Test requirements:** `test-requirements.md`   **Status:** Draft (2026-11-24, written by the agent, for the owner's review of the scenarios by group)

Where they go at the merge: the TC-GTB and TC-IF-301 rows into the test spec of N-3.2, the TC-WFM rows into N-2.3, the TC-RUN rows and SMOKE-RUN-001 into N-2.4.1, the statistical rows into the root `test-spec.md` (they replace the rows of TC-WFM-110 to 114 there, whose thresholds still show the values from before A-122: 0.82 for research and verify_computable). This file stays as the record of the goal.

Almost every check is exact: the expected value is an ID, an order, a list of calls, an output or an equality. The answers of today's code (the rule report, the run check, the order of steps, the model calls of the six skills without a stored graph) are recorded at `goal/v4` **before any code changes** as the oracle (TR-RUN-002), so "the same as before" is checked against a file, not against memory. Only the five equivalence runs of the skills with a model are statistical (TC-WFM-110 to 114). The checks of the stored-graph path save the converted graphs through CORE's save path into a throw-away files store and run from there (D-476); RUN does not wait for MIGRATION.

## Test cases
| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|---|
| TC-GTB-048 | REQ-GTB-053 | unit | 1 | the 15 converted skill graphs; golden 33 (two connections `e1`, `e2` from `d1` to `t1`) | for each graph the nodes are exactly its step IDs and the edge keys exactly its connection IDs; golden 33 gives two edges `d1 → t1` keyed `e1` and `e2` | exact |
| TC-GTB-049 | REQ-GTB-054, REQ-GTB-055, REQ-GTB-056 | unit | 1 | the 15 converted skill graphs; the converted `review_full` skill; a stored form with `kind`, `id`, `description` and the same without `kind` | every node's `data` equals the step's `data` and `position` its index; every edge's `data` equals the connection's and `position` its index; the step of `review_full` that reads six data steps has six incoming edges with six names; `G.graph` holds `kind`, `id`, `description`, and `kind` = `workflow` without it | exact |
| TC-GTB-050 | REQ-GTB-057, REQ-GTB-058 | unit | 0 | the malformed graphs of golden 31; a graph with two steps `d1`; `nodes` = `"x"`; `nodes` = `None`; golden 33 for the copies | no exception; the malformed items and every connection to a left-out step are not in the loaded graph; `"x"` and `None` give an empty graph; a change of the loaded graph leaves the stored form unchanged and a change of the stored form leaves the loaded graph unchanged | exact |
| TC-GTB-051 | REQ-GTB-059 | inspection | 0 | `graph_rule_set.py` after the change; the defect check of TR-RUN-008 | no function builds its own adjacency, writer or cycle view; no copy of a cycle finder; the rules about adjacency, one writer, session setting and stop limit, cycle and unsupplied inputs take the loaded graph from `load` | inspection checklist, every line yes |
| TC-GTB-052 | REQ-GTB-060, HR-006 | component | 1 | the oracle of TR-RUN-002: `rule_report` and `run_check` answers of IF-301 v4 on the 15 converted skill graphs, the 500 random graphs (TR-RUN-003) and golden 24 to 31 | every answer of the changed code equals the recorded answer | 0 differences |
| TC-IF-301-35 | REQ-GTB-053, REQ-GTB-054, REQ-GTB-055 | contract | 1 | golden 32, real side and mock side | as golden 32 | exact |
| TC-IF-301-36 | REQ-GTB-053, REQ-GTB-056 | contract | 0 | golden 33, both sides | as golden 33 | exact |
| TC-IF-301-37 | REQ-GTB-057 | contract | 0 | golden 34, both sides | as golden 34 | exact |
| TC-IF-301-38 | REQ-GTB-058 | contract | 0 | golden 35, both sides | as golden 35 | exact |
| TC-WFM-185 | REQ-WFM-166 | component | 1 | the 15 converted skill graphs and the acyclic ones of the 500 random graphs | each order holds every step once; every edge points from an earlier to a later step | exact |
| TC-WFM-186 | REQ-WFM-167, HR-006 | component | 1 | two independent steps listed `b`, `a` and `a`, `b`; steps `x`, `y`, `z` where `x` reads from `z`; the same where `x` reads from `y`; the recorded orders of the oracle | `b`, `a`; `a`, `b`; `y`, `z`, `x`; `y`, `z`, `x`; every order of the converted and the acyclic random graphs equals the recorded one | 0 differences |
| TC-RUN-041 | REQ-RUN-016 | component | 0 | two independent transforms `t2`, `t1` (listed in this order), each with a marker that records its call | `t2` is called before `t1`; listed `t1`, `t2`, `t1` first | exact |
| TC-RUN-042 | REQ-RUN-040 | component | 1 | a graph with four independent transforms whose functions record start and end (monotonic clock) and sleep 0.05 s | every start is at or after the end of the step before it in the order | exact order of times |
| TC-RUN-043 | REQ-RUN-041 | inspection and regression | 1 | `graph_run.py` after the change; TC-RUN-016 to 019 and 030 to 039 unchanged | `graph_run.py` scans no `graph["nodes"]` or `graph["edges"]`; it reads steps and connections only through a loaded graph; the named checks are green and their files unchanged against `goal/v4` | inspection yes; all green |
| TC-RUN-044 | REQ-RUN-042 | component | 1 | the converted graph of verify_claim saved into a throw-away files store; scripted replies; the read of N-2.3 wrapped to count | a run of verify_claim reads that graph once, newest version, and gives the answer of the in-memory converted run | exact |
| TC-RUN-045 | REQ-RUN-043 | component | 2 | an empty throw-away store; the six skills on the scripted replies of REQ-WFM-058; the oracle of TR-RUN-002 | each run makes the recorded model calls and gives the recorded answer | 0 differences |
| TC-RUN-046 | REQ-RUN-044 | component | 1 | the store of TC-RUN-044 with the graph saved twice (versions 1 and 2); an empty store | the run record has `graph` = `verify.single@1` and `graph_version` = 2; with the empty store the record has neither field | exact |
| TC-RUN-047 | REQ-RUN-045 | component | 1 | the store of TC-RUN-044 with a version 2 that has a cycle; a marker per step | the run ends `refused` naming `cycle`, `verify.single@1` and version 2; every marker was called 0 times; version 1 alone runs and calls the markers | exact counts |
| TC-WFM-187 | REQ-WFM-168 | component | 2 | the six skills, each saved into a throw-away store; the fake model server with the scripted replies of REQ-WFM-058 | for each skill the list of model calls (order, prompt, options) from the stored graph equals that of the old runner; a planted change of one option is reported with the first differing call | exact |
| TC-WFM-115 | REQ-WFM-115 | component | 2 | extract_claims_rules saved into a throw-away store; the 51 dev cases of EV-extraction; no model | the 51 outputs from the stored graph equal the 51 outputs of the old runner run in the same check; a planted difference is reported with a diff naming the case | exact |

TC-RUN-016 (AC-31) stays as it is and verifies REQ-RUN-016 together with TC-RUN-041. TC-RUN-030 to 035 verify REQ-RUN-030 to 035 unchanged and are part of the regression of TC-RUN-043.

## Edge inputs
| Requirement | Edge | Test ID | Expected result |
|---|---|---|---|
| REQ-GTB-053 | two connections between the same two steps | TC-GTB-048 | two edges, one per connection ID |
| REQ-GTB-053 | a graph with no steps (`nodes` = `[]`) | TC-GTB-050 | an empty loaded graph |
| REQ-GTB-057 | a connection to a step that was left out (second `d1` is a different object) | TC-GTB-050 | the connection points at the first `d1` and is kept; a connection to the step `5` is left out |
| REQ-GTB-057 and REQ-GTB-060 | malformed graphs in `rule_report` | TC-GTB-052 | the items of golden 31 unchanged: identity and ends still come from the stored form |
| REQ-WFM-167 | a self loop or a cycle | TC-WFM-185 | not ordered: the run check refuses it first (REQ-RUN-036); only acyclic random graphs are ordered |
| REQ-WFM-167 | an indirect read (`x` reads `z`, `y` free) | TC-WFM-186 | `y`, `z`, `x` |
| REQ-RUN-040 | a map step with `workers` 2 | TC-RUN-042 | its items may overlap inside the step; the next step starts after the map step ended (D-475, key decisions) |
| REQ-RUN-042 | the graph saved twice | TC-RUN-046 | version 2 runs |
| REQ-RUN-045 | version 2 refused, version 1 sound | TC-RUN-047 | refused; the runner does not fall back to version 1 |

## Statistical checks (M19)
The five skills with a model, run from their stored graph. Rule, pin, repeats, thresholds and false alarm are those of the `Eval criterion` lines (unchanged since A-122); the reference is the old-runner baseline of commit `1fb0c35`, recorded with 3 repeats. A FAIL is re-run once with fresh seeds; only the re-run counts. Stage 4, run once per task that changes the run path and before the Verify gate; before each run the other sessions are told (the Ollama server is shared).

| Test ID | Verifies | Statistic | n | Seeds | Criterion | Method | Where it runs |
|---|---|---|---|---|---|---|---|
| TC-WFM-110 | REQ-WFM-110 | share of dev cases of EV-research right, 3 repeats folded by majority, run from the stored graph | 20 | seed 7 as the harness assigns it; the re-run fresh seeds | at least 17 of 20 (0.85); false alarm 0.0003 | `eval_decide.py`, threshold rule, against `eval/baselines/research__escalate__baseline.jsonl` | the owner's host, MP-light |
| TC-WFM-111 | REQ-WFM-111 | the same, EV-plans | 36 | as above | at least 20 of 36 (0.54); false alarm 0.0122 | as above, `plans__free__baseline.jsonl` | as above |
| TC-WFM-112 | REQ-WFM-112 | the same, EV-verdicts | 50 | as above | at least 42 of 50 (0.83); false alarm 0.0001 | as above, `verdicts__single__baseline.jsonl` | as above |
| TC-WFM-113 | REQ-WFM-113 | the same, EV-computable | 39 | as above | at least 34 of 39 (0.87); false alarm 0.0000 | as above, `computable__computable2__baseline.jsonl` | as above |
| TC-WFM-114 | REQ-WFM-114 | the same, EV-extraction | 51 | as above | at least 31 of 51 (0.59); false alarm 0.0064 | as above, `extraction__llm__baseline.jsonl` | as above |

## Benchmarks and baselines
None: no hard bound (D-475 (4)). The smoke number for loading and ordering (all 15 converted graphs) is printed by TC-GTB-048 and TC-WFM-185 for the record, not asserted. The eval baselines exist (commit `1fb0c35`, 3 repeats); none is recorded new.

## Smoke tests (run in Phase 6, target environment)
| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-RUN-001 | REQ-RUN-042, REQ-RUN-044 | the owner's host, the installed release, a throw-away files store | verify_claim saved into the store and run once on MP-light with one claim of EV-verdicts dev | the run ends `done`; its run record names `verify.single@1` and version 1 |

## Validation criteria
None in this subgoal: RUN's Validate is the first test run of G-V5 (parked, D-386); the outcomes OC-1 to OC-4 are checked by the tests above.

## Scenarios
<!-- one block per check, in plain language, approved before the check is built -->

### TC-GTB-048 – One loaded graph with every step and connection
- Verifies: REQ-GTB-053
- Given: the 15 converted skill graphs, built at test time (TR-RUN-004); golden 33: steps `d1` (data) and `t1` (transform), connections `e1` and `e2` (`as` = `b`), both from `d1` to `t1`
- When: each is loaded
- Then: each loaded graph has exactly the step IDs of its stored form as nodes and exactly its connection IDs as edge keys
- And: golden 33 gives two edges from `d1` to `t1`, keyed `e1` and `e2`

### TC-GTB-049 – Everything the run needs is on the loaded graph
- Verifies: REQ-GTB-054, REQ-GTB-055, REQ-GTB-056
- Given: the 15 converted skill graphs, among them research and verify_computable with master steps and the skills with settings steps; the converted `review_full` skill; a stored form with `kind` = `workflow`, `id` = `g1`, `description` = `test`, and the same form without `kind`
- When: each is loaded
- Then: every step's `data` (type, tool, stop limit, settings values) is on its node unchanged, with its index as `position`
- And: every connection's `data` (role, name) is on its edge unchanged, with its index as `position`
- And: the step of `review_full` that reads six data steps has six incoming edges with six different names
- And: the graph attributes hold `kind`, `id` and `description`; without `kind` the attribute `kind` is `workflow`

### TC-GTB-050 – Malformed items are left out; loading copies
- Verifies: REQ-GTB-057, REQ-GTB-058
- Given: the malformed graphs of golden 31 (a step `5`, connection data `[]`, a step without `id`, a connection without `from`, `nodes` = `"x"`); a graph with two steps `d1`; `nodes` = `None`; golden 33
- When: each is loaded
- Then: no exception escapes; the malformed steps, the second `d1`, the connection without `from` and every connection to a left-out step are missing from the loaded graph; `"x"` and `None` give an empty graph
- And: setting `value` = 9 in the data of `d1` on the loaded golden 33 leaves the stored form equal to a deep copy taken before; changing the stored form's `d1` afterwards leaves the loaded graph as it was

### TC-GTB-051 – The rules read the loaded graph (inspection)
- Verifies: REQ-GTB-059
- Given: `graph_rule_set.py` after the change; the checklist of TR-RUN-008
- When: a reviewer reads the module with the checklist, and the defect check of TR-RUN-007 runs
- Then: no function in it builds its own adjacency, writer or cycle view, and no copy of a cycle finder remains
- And: the rules about adjacency, one writer, session setting and stop limit, cycle and unsupplied inputs take the graph that `load` gives
- And: the rules about step identity, kind of step, connection ends and duplicates still read the stored form (D-477 (3))

### TC-GTB-052 – The same rule answers as IF-301 v4
- Verifies: REQ-GTB-060, HR-006
- Given: the oracle recorded at `goal/v4` before any code change (TR-RUN-002): the `rule_report` and `run_check` answers of the 15 converted skill graphs, the 500 random graphs (seed 7, with self loops, TR-RUN-003) and golden 24 to 31
- When: the changed code answers the same inputs
- Then: every answer equals the recorded one: the same items, rule by rule, with the same parts in the same order and the same sentences (0 differences)

### TC-IF-301-35 to TC-IF-301-38 – Contract suite IF-301 v5
- Verifies: REQ-GTB-053 to REQ-GTB-058
- Given: golden 32 (`review_full`), 33 (parallel connections), 34 (left out), 35 (copies) of A-187; the real module and the IF-301 v5 mock
- When: the contract suite runs against each side
- Then: both sides give the results the golden examples state, case by case
- And: the suites of IF-301 v1 to v4 run unchanged and green (TR-RUN-010)

### TC-WFM-185 – Every step after the steps it reads from
- Verifies: REQ-WFM-166
- Given: the 15 converted skill graphs and the acyclic ones of the 500 random graphs
- When: the order of each is asked
- Then: each order lists every step of the graph exactly once
- And: for every connection, the step it comes from is earlier in the order than the step it goes to

### TC-WFM-186 – Ties in the order steps became ready, and the order as before
- Verifies: REQ-WFM-167, HR-006
- Given: two independent steps listed `b`, `a`; the same listed `a`, `b`; steps listed `x`, `y`, `z`, where `x` reads from `z` and `y` reads from nothing; steps listed `x`, `y`, `z`, where `x` reads from `y`; the orders recorded in the oracle (TR-RUN-002)
- When: the order of each is asked
- Then: `b`, `a`; `a`, `b`; `y`, `z`, `x`; `y`, `z`, `x` (the ready steps go in the order in which they became ready, not by position: `z` was ready before `x`)
- And: the order of every converted and acyclic random graph equals the recorded order of today's `order_of` (0 differences)

### TC-RUN-041 – The run follows the positions
- Verifies: REQ-RUN-016
- Given: a graph with two independent transforms listed `t2`, `t1`, each with a marker that appends its name to a list; the same graph listed `t1`, `t2`
- When: each graph is run
- Then: the first list is `t2`, `t1`; the second `t1`, `t2`

### TC-RUN-042 – One step at a time
- Verifies: REQ-RUN-040
- Given: a graph with four independent transforms; each function records its start and end on a monotonic clock and sleeps 0.05 s between them; a map step with `workers` 2 after them
- When: the graph is run
- Then: each step starts at or after the end of the step before it in the order
- And: the step after the map step starts after the map step ended (its items may overlap inside it)

### TC-RUN-043 – The run reads the loaded graph (inspection and regression)
- Verifies: REQ-RUN-041
- Given: `graph_run.py` after the change; TC-RUN-016 to 019 and TC-RUN-030 to 039 as they are on `goal/v4`
- When: a reviewer reads the module with the checklist of TR-RUN-008, and the named checks run
- Then: `graph_run.py` scans no list `graph["nodes"]` or `graph["edges"]`; types, roles and names come from the loaded graph
- And: the named checks are green and their files are unchanged against `goal/v4`

### TC-RUN-044 – A skill with a stored graph runs from it
- Verifies: REQ-RUN-042
- Given: a throw-away files store with the converted graph of verify_claim saved through CORE's save path as `verify.single@1`; the read of N-2.3 wrapped so that it counts its calls; scripted replies; the answer of the in-memory converted run of the same claim, taken in the same check
- When: verify_claim runs one claim
- Then: the graph was read once, by its ID, at its newest version
- And: the answer equals the answer of the in-memory converted run

### TC-RUN-045 – Without a stored graph, as before
- Verifies: REQ-RUN-043
- Given: an empty throw-away store; the scripted replies of REQ-WFM-058; the model calls and answers of the six skills recorded in the oracle at `goal/v4`
- When: each of the six skills runs its scripted input
- Then: each makes the recorded model calls (order, prompt, options) and gives the recorded answer (0 differences)

### TC-RUN-046 – The run record names graph and version
- Verifies: REQ-RUN-044
- Given: the store of TC-RUN-044 with `verify.single@1` saved twice (versions 1 and 2, the second with a changed description); an empty store
- When: verify_claim runs once against each store
- Then: the run record of the first run has `graph` = `verify.single@1` and `graph_version` = 2
- And: the run record of the second run has neither field

### TC-RUN-047 – A stored graph that cannot run is refused, named
- Verifies: REQ-RUN-045
- Given: the store of TC-RUN-044 with a version 2 of `verify.single@1` that has a cycle; a marker function per step
- When: verify_claim runs
- Then: the run ends `refused`, naming the rule `cycle`, the graph `verify.single@1` and version 2
- And: every marker was called 0 times, and the runner did not fall back to version 1
- And: with only version 1 in the store the run ends `done` and calls its markers (TR-RUN-006)

### TC-WFM-187 – The same model calls from the stored graph
- Verifies: REQ-WFM-168
- Given: the six skills, each saved into a throw-away store; the fake model server with the scripted replies of REQ-WFM-058 (TR-RUN-005)
- When: each skill runs its scripted input from the stored graph and on the old runner
- Then: for each skill the lists of model calls (order, prompt text, options) are equal
- And: with one option changed in the stored graph (temperature 0 to 0.2), the check fails and names the skill and its first differing call

### TC-WFM-115 – Same outputs of the rule-based skill from the stored graph
- Verifies: REQ-WFM-115
- Given: extract_claims_rules saved into a throw-away store; the 51 dev cases of EV-extraction; no model; a copy of the stored graph with one output changed
- When: the skill runs all 51 cases from the stored graph and on the old runner, in the same check
- Then: the 51 outputs are equal
- And: the changed copy is reported with a diff naming the case

### TC-WFM-110 – Equivalence of research from its stored graph
- Verifies: REQ-WFM-110
- Given: suite EV-research dev (20 cases, `split:dev`), pin MP-light (digest in `eval-spec.md`), 3 repeats folded by majority, research saved into a throw-away store and run from it, the old-runner baseline of commit `1fb0c35` (0.95, 57 of 60)
- When: one run of the suite on the stored-graph path (`python tools/eval.py run research --pin MP-light --repeats 3`, with the store named)
- Then: `eval_decide.py` on the criterion of REQ-WFM-110: PASS with at least 17 of 20 cases right (0.85); a FAIL is re-run once with fresh seeds and only the re-run counts
- And: the run header names the stored-graph path, the graph ID and its version; EV-research_compound is run and reported, not decided

### TC-WFM-111 – Equivalence of plan_question from its stored graph
- Verifies: REQ-WFM-111
- Given: suite EV-plans dev (36 cases), MP-light, 3 repeats, plan_question run from its stored graph, the baseline of `plan.free@1` (0.64)
- When: one run of the suite on the stored-graph path
- Then: PASS with at least 20 of 36 cases right (0.54); a FAIL is re-run once

### TC-WFM-112 – Equivalence of verify_claim from its stored graph
- Verifies: REQ-WFM-112
- Given: suite EV-verdicts dev (50 cases), MP-light, 3 repeats, verify_claim run from its stored graph, the baseline of `verify.single@1` at 3 repeats (0.93)
- When: one run of the suite on the stored-graph path
- Then: PASS with at least 42 of 50 cases right (0.83); a FAIL is re-run once
- And: EV-verdicts_injection and EV-verdicts_wikidata are run and reported, not decided

### TC-WFM-113 – Equivalence of verify_computable from its stored graph
- Verifies: REQ-WFM-113
- Given: suite EV-computable dev (39 cases), MP-light, 3 repeats, verify_computable run from its stored graph, the baseline `computable__computable2` (0.974, 114 of 117)
- When: one run of the suite on the stored-graph path
- Then: PASS with at least 34 of 39 cases right (0.87); a FAIL is re-run once

### TC-WFM-114 – Equivalence of extract_claims from its stored graph
- Verifies: REQ-WFM-114
- Given: suite EV-extraction dev (51 cases), MP-light, 3 repeats, extract_claims run from its stored graph, the baseline of `extract.llm@1` at 3 repeats (0.69)
- When: one run of the suite on the stored-graph path
- Then: PASS with at least 31 of 51 cases right (0.59); a FAIL is re-run once

### SMOKE-RUN-001 – One skill from its stored graph on the target
- Verifies: REQ-RUN-042, REQ-RUN-044
- Given: the owner's host with the installed release, MP-light, a throw-away files store with verify_claim saved
- When: verify_claim runs one claim of EV-verdicts dev
- Then: the run ends `done` and its run record names `verify.single@1` and version 1
