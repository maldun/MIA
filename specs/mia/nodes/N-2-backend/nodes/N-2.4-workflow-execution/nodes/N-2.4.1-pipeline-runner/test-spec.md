# Test specification: Pipeline runner (N-2.4.1)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/requirements.md   **Status:** Draft (Plan for node N-2.4.1, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-202 and IF-105 (provider), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-RUN-001 | REQ-RUN-001 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: a chat message alone starts no internet task | exact |
| TC-RUN-002 | REQ-RUN-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: /light! and /full! switch after confirmation; memory is freed on request | as stated |
| TC-RUN-003 | REQ-RUN-003 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-23: with the fake server down the user gets the plain message | exact |
| TC-RUN-004 | REQ-RUN-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-22: a learned choice is logged with the default and can be switched off and reversed | as stated |
| TC-RUN-005 | REQ-RUN-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-22: over the lookup suites 100 % of inputs are at most 4096 tokens at num_ctx 8192 | as stated |
| TC-RUN-006 | REQ-RUN-006 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-22: on the lookup suites the maximum is below 15 | per the criterion; never decided on one run |
| TC-RUN-007 | REQ-RUN-007 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-19: median over 20 runs is within 10 s, also while a review slice runs | per the criterion; never decided on one run |
| TC-RUN-008 | REQ-RUN-008 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-19: each of the four budgets ends a scripted run with a message naming it | as stated |
| TC-RUN-009 | REQ-RUN-009 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19: with a review slice running a chat message gets its first text within 10 s | as stated |
| TC-RUN-010 | REQ-RUN-010 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19: two simultaneous messages are answered one after the other | as stated |
| TC-RUN-011 | REQ-RUN-011 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-23: the contract suite test_if_103_model_server.py passes against the Workflow execution (stage 2) | as stated |
| TC-RUN-012 | REQ-RUN-012 | Inspection | 1 | the code and the log files of the repository | AC-1: with the mocks of the three interfaces a scripted workflow runs end to end; no other import exists | as stated |
| TC-RUN-013 | REQ-RUN-013 | Inspection | 1 | the code and the log files of the repository | AC-9: the lookup, verify and review entries run with the same runner; a new valid entry runs without a change of code | as stated |
| TC-RUN-014 | REQ-RUN-014 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19, AC-28: the contract suite test_if_202_run_workflow.py passes against the Pipeline runner (stage 2) | as stated |
| TC-RUN-015 | REQ-RUN-015 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-2, AC-8: the contract suite test_if_105_evaluation_access.py passes against the Pipeline runner (stage 2) | as stated |
| TC-RUN-016 | REQ-RUN-016 | Component | 2 | unit test with the fake model server and scripted transforms | AC-31: a graph with three transforms runs in an order that respects its edges and the output data nodes hold the results | exact |
| TC-RUN-017 | REQ-RUN-017 | Component | 2 | unit test with a transform whose only effect is writing a marker file | AC-32: the marker is not written and the refusal names the node and its status untrusted; after the owner sets it trusted the same graph runs and writes the marker | exact |
| TC-RUN-018 | REQ-RUN-018 | Component | 2 | unit test with a master node between two data nodes | AC-31: the master node runs once after its input data node is written and its output data node holds the result | exact |
| TC-RUN-019 | REQ-RUN-019 | Component | 2 | unit test with three scripted transforms, the second failing | AC-31: the third transform does not run and the run result names the second | exact |
| TC-RUN-030 | REQ-RUN-030 | Component | 2 | unit test: a Stage with two inputs (one renamed by `as`), one output and a settings node | AC-31: the Stage receives exactly the three objects | exact |
| TC-RUN-031 | REQ-RUN-031 | Component | 2 | unit test: a Stage with two outputs; one that returns a plain value; one that names an unknown output | AC-31: two different values written; the plain value in both nodes; the unknown name fails the node and the result names it | exact |
| TC-RUN-032 | REQ-RUN-032 | Component | 2 | unit test: a plain function and a Stage in one graph | AC-31: the plain function is called as before; TC-RUN-016 to 019 unchanged | exact |
| TC-RUN-033 | REQ-RUN-033 | Component | 2 | unit test: two settings edges into one transform; two outputs with one name; the same graph corrected | AC-32: nothing ran and the refusal names the transform; the corrected graph runs | exact |
| TC-RUN-034 | REQ-RUN-034 | Component | 2 | unit test: a Stage with prepare, a graph node with a value, three runs (graph only, prepare, run values) | AC-31: the Stage gets the run value, else the prepare value, else the graph value, else nothing; prepare ran once before the Stage | exact |
| TC-RUN-035 | REQ-RUN-035 | Component | 2 | unit test: a transform with an order edge from a data node written by another transform | AC-31: the writer runs first and the Stage's inputs hold no entry for the order node | exact |

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).

## Scenarios (G-V2.MODEL; the older checks of this file have none yet)

### TC-RUN-016 – topological order
- Verifies: REQ-RUN-016
- Given: a graph D1 -> T1 -> D2 -> T2 -> D3 and D1 -> T3 -> D4, with scripted transforms that append their ID to a list and write a result
- When: the graph is run
- Then: T1 ran before T2; D2 and D3 hold the results of T1 and T2; D4 holds the result of T3; each transform got the contents of its input data nodes

### TC-RUN-017 – untrusted does not run
- Verifies: REQ-RUN-017
- Given: a graph with a trusted transform and an untrusted transform `T9` that writes a marker file when it runs
- When: the graph is run; then the owner sets `T9` trusted and it is run again
- Then: the first run is refused before any node ran, no marker exists and the refusal names `T9` and `untrusted`; the second run writes the marker

### TC-RUN-018 – master node runs like a transform
- Verifies: REQ-RUN-018
- Given: a graph D1 -> M1 -> D2 with a trusted master node `M1` (maximum of 3 repetitions) that writes a result; a copy where `M1` is untrusted
- When: each graph is run
- Then: in the first, `M1` ran once and D2 holds its result; the second is refused naming `M1` and `untrusted`

### TC-RUN-019 – failed node stops the run
- Verifies: REQ-RUN-019
- Given: a chain T1 -> T2 -> T3 where T2 raises an error
- When: the graph is run
- Then: T3 did not run and the run result names `T2`

## Scenarios (G-V2.CONVERT, checks TC-RUN-030 to 035)

### TC-RUN-030 – A Stage gets inputs, outputs and settings
- Verifies: REQ-RUN-030
- Given: a Stage on a transform with two input data nodes (one renamed by `as`), one output data node and a settings node
- When: the graph is run
- Then: the Stage receives exactly three objects: the two inputs by name (the renamed one under its `as`), the output by name, and the settings value

### TC-RUN-031 – Outputs are written one by one
- Verifies: REQ-RUN-031
- Given: a Stage with two outputs, in three runs: it returns `{"outputs": {a: 1, b: 2}}`, it returns a plain value, it names an unknown output
- When: each graph is run
- Then: two different values are written; the plain value is written to both nodes; the unknown name fails the node and the result names it

### TC-RUN-032 – Plain functions run as before
- Verifies: REQ-RUN-032
- Given: a plain function and a Stage in one graph
- When: the graph is run
- Then: the plain function is called with the contents of its input data nodes as before; `TC-RUN-016` to `TC-RUN-019` are unchanged

### TC-RUN-033 – Broken wiring is refused before anything runs
- Verifies: REQ-RUN-033
- Given: a graph with two settings edges into one transform, one with two outputs of one name, and the same graph corrected
- When: each is run
- Then: for the broken ones nothing ran and the refusal names the transform; the corrected graph runs

### TC-RUN-034 – Start values come in a fixed order
- Verifies: REQ-RUN-034
- Given: a Stage with `prepare` and a data node that has a graph value, in three runs (graph value only; with prepare; with a value given to the run)
- When: each is run
- Then: the Stage gets the run value, else the prepare value, else the graph value, else nothing; `prepare` ran once before the Stage

### TC-RUN-035 – An order edge orders and gives no input
- Verifies: REQ-RUN-035
- Given: a transform with an order edge from a data node written by another transform
- When: the graph is run
- Then: the writer runs first and the Stage's inputs hold no entry for the order node

## Test cases of G-V4.GRAPHAPI.RULES (moved at the merge 2026-11-22; test requirements TR-RULES-001 to 009)
All checks of RULES are exact (rule names, IDs, orders, counts, equalities): no statistical check, no benchmark (no hard bound, D-416 (4)). Accepted cases (`specs/mia/goals/G-V4/accepted-cases.md`): AC-017 is witnessed by TC-GTB-046 and TC-WFM-180, AC-018 by TC-RUN-036, TC-RUN-037 and TC-GTB-044. The validation criterion VAL-RULES-01 stays in the goal record `specs/mia/goals/G-V4.GRAPHAPI.RULES/test-spec.md`.

| Test ID | Verifies | Level | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|
| TC-RUN-036 | REQ-RUN-036 | component | seven graphs, one per refusal reason of HR-006 (cycle, two writers, connection to a missing step, two identical connections, unsupplied input, context graph, unknown kind); a marker function per step | each run ends `refused`; every marker was called 0 times; a sound twin runs and calls its markers | exact counts |
| TC-RUN-037 | REQ-RUN-037 | component | `wf-cycle` (`D1 → T1 → D2 → T2 → D1`); a graph whose connection `X8>T1` comes from a missing step; the converted `chat` skill without values | refused naming `D1, T1, D2, T2, D1`; `X8>T1`; `input.text` | exact lists |
| TC-RUN-038 | REQ-RUN-038 | component | a graph with a cycle and an untrusted transform; the same graph without the cycle | the first refused naming the cycle, no trust status; the second refused naming the untrusted transform and its status | exact |
| TC-RUN-039 | REQ-RUN-039 | component | the TC-RUN-034 graph (`DB` read by a Stage `T` with a prepare function, no value anywhere); the same graph with a plain function for `T` | the first runs (`done`); the second is refused naming `DB` and `T` was not called | exact |
| TC-RUN-040 | REQ-RUN-036, HR-006 | component | the 15 converted skill graphs, each with a value for each of its unsupplied inputs | each run check is ready; no skill is refused by a rule | 15 of 15 |

## Smoke tests of G-V4.GRAPHAPI.RULES (run in Phase 6, target environment)
| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-RULES-001 | REQ-RUN-036, HR-006 | the owner's host, the installed release, a throw-away files store | the 15 skills run checked with their usual inputs; the round 04 sample `sample.broken` run | each skill ready; `sample.broken` refused naming `e2`, no step run |

## Scenarios (G-V4.GRAPHAPI.RULES, approved by the owner 2026-11-22, D-422)

### TC-RUN-036 – No step runs when the run check refuses
- Verifies: REQ-RUN-036
- Given: seven graphs, one per refusal reason of HR-006: a cycle, two writers, a connection to a missing step, two identical connections, an unsupplied input, a context graph, a graph of kind `swarm`; every step is a marker function that counts its calls; a sound twin of the first
- When: each is run
- Then: each run ends `refused` and every marker was called 0 times
- And: the sound twin runs and every one of its markers was called once (the markers can fire)
- And: witnesses AC-018

### TC-RUN-037 – A refused run names every part, repeats kept
- Verifies: REQ-RUN-037
- Given: `wf-cycle` (`D1 → T1 → D2 → T2 → D1`); a graph whose connection `X8>T1` comes from the missing step `X8`; the converted `chat` skill
- When: each is run, `chat` without values
- Then: the runs are refused naming `D1, T1, D2, T2, D1`, then `X8>T1`, then `input.text`
- And: witnesses AC-018

### TC-RUN-038 – Trust is checked after the run check
- Verifies: REQ-RUN-038
- Given: a graph with a cycle and an untrusted transform `T2`; the same graph without the cycle
- When: each is run
- Then: the first is refused naming the cycle and no trust status
- And: the second is refused naming `T2` and its status `untrusted` (REQ-RUN-017)

### TC-RUN-039 – An input a prepare function may give is not refused
- Verifies: REQ-RUN-039
- Given: the graph of TC-RUN-034 (`DB` read by the Stage `T`, no value in the graph or the run), once with a prepare function on `T` that gives nothing, once with a plain function for `T`
- When: each is run
- Then: the first runs to `done` (D-418 (1))
- And: the second is refused naming `DB` and `T` was not called

### TC-RUN-040 – Today's skills still run
- Verifies: REQ-RUN-036, HR-006
- Given: the 15 converted skill graphs, each with the value `"x"` for each of its unsupplied inputs
- When: each is checked for a run
- Then: all 15 are ready; none is refused by a rule

### SMOKE-RULES-001 – Skills run, a broken graph does not
- Verifies: REQ-RUN-036, HR-006
- Given: the owner's host with the installed release; a throw-away files store
- When: each of the 15 skills is run checked with its usual inputs, and the round 04 sample `sample.broken` is run
- Then: each skill's run check is ready; `sample.broken` is refused naming `e2` and no step ran
- And: the throw-away store is removed afterwards; MIA's own store is not written
