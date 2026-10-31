# Test specification: Evaluation (N-4.1)

**Requirements:** specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/requirements.md   **Status:** Draft (Plan for node N-4.1, 2026-10-25)

Tests of the harness and the measurement tools against the mock of IF-105; model-dependent criteria are decided by eval suites on the pinned model, never by this mock (agent-app rule). The harness features that `specs/number-gate` already specifies (REQ-EVAL-001..004: retired cases, pin in the header and the options, seeded sample, case input) are built there and only referenced here (its T-03). Stages (M27): 1 = commit gate, 2 = up to 10 minutes, 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-EVL-001 | REQ-EVL-001 | Component | 1 | the harness against the mock of IF-105; a suite of 5 cases with scripted outcomes (4 pass, 1 fails), 3 repeats | the report lists every case with its 3 repeats, the pass counts per case, the 95 % Wilson interval of the pass rate and the summed cost (calls, tokens, seconds) taken from the `cost` of the runs | exact for counts and sums; intervals to two decimals |
| TC-EVL-002 | REQ-EVL-002 | Component | 1 | `eval_decide.py` of the agent-app skill on a run of the dev split and on a run of the holdout split with a baseline, both for a verdict criterion | the dev-split run is refused (not decided, reason dev split); the holdout run is decided PASS, FAIL or NOT DECIDED by the rule; the harness never reads a case tagged `split:holdout` in a dev run | exact |
| TC-EVL-003 | REQ-EVL-003 | Component | 1 | a judge run without a calibration record; with a record of Cohen's kappa 0.7 against the users' ratings; with a record of kappa 0.4 (threshold: OPEN-7, decided 0.6) | the first and the third run mark the judge's verdicts "not counted"; the second counts them | exact |
| TC-EVL-004 | REQ-EVL-004 | Component | 1 | 10 harness runs through the mock of IF-105 | 100 % of the run headers carry workflow, workflow version, model pin, seed, temperature and benchmark version | exact |
| TC-EVL-005 | REQ-EVL-005 | Inspection | 1 | every library workflow with status tested or trusted, and the files in `eval/baselines/` | each such workflow has a baseline file `<suite>__<variant>__baseline.jsonl`; the check names the ones that lack it | exact |
| TC-EVL-006 | REQ-EVL-006 | Inspection + doc test | 2 | the document of the skill path (idea, skill file and pipeline, validation, specification and benchmark, declaration, draft and promotion, time record) with the lookup as its example | all steps are present; the shell and Python examples in it run with the fake model; links resolve | exact |
| TC-EVL-007 | REQ-EVL-007 | Component | 2 | the latency tool against a fake server that answers after 1.0, 2.0 and 3.0 s (20 runs after 3 warm-up runs, cycling); the frame-rate tool on a recorded list of frame times (16.7 ms and 33.3 ms) | the latency tool reports the median 2.0 s and the number of runs; the frame-rate tool reports 60 fps and 30 fps for the two lists | median within 0.1 s; fps within 1 |
| TC-EVL-008 | REQ-EVL-008 | Component | 1 | two result sets compared with the same case list, then with lists that differ in one case | the first is compared; the second is refused with the differing case named | exact |
| TC-EVL-009 | REQ-EVL-009 | Inspection | 1 | the suites of lookup and verify (and of review when it is promoted) and `agent_check.py` | each has a dev part, a holdout part and a recorded baseline; the A-checks of the agent-app workflow report no error for them | exact |
| TC-EVL-010 | REQ-EVL-010 | Integration | 3 | the lookup scenario: a question through IF-105 against the mocks (step 0), then against each real node as it is integrated; the library time stamps of the lookup | the answer carries a source and a verbatim quote or unknown; the library holds the time stamps idea and promotion of the lookup | exact |
| TC-EVL-011 | REQ-EVL-011 | Inspection | 1 | the imports of the harness package | the harness reaches the platform only through the interface IF-105 (no import of the runner, the library or the stores) | exact |

## Assumptions and open numbers

- ASM-N4-001: `eval_decide.py`, `agent_check.py` and `eval_*` helpers of the agent-app skill are the decision tools; they are read-only for this project (the skill is not part of the repository).
- **OPEN-7** (decided by the owner on 2026-10-26, to be optimised later): the judge counts only after a calibration of Cohen's kappa 0.6 or more against the users' ratings (the labels audit of 2026-10-24 reached 0.85 between the owner and the benchmark; 0.6 is the usual limit for "substantial"). Used by TC-EVL-003.

## Scenarios

Drafted in Phase 3 after Verify F10 (D-164), from the table above and the tests as built; for the owner's review (M39).

### TC-EVL-001 – Repeats, intervals and cost of a workflow suite
- Verifies: REQ-EVL-001
- Given: the harness against the mock of IF-105 and a suite of 5 cases whose outcomes are scripted (4 pass, 1 fails)
- When: the suite runs with 3 repeats and the pin MP-light
- Then: the report lists every case with 3 of 3 or 0 of 3 passes, 12 of 15 overall with the 95 % Wilson interval 0.55 to 0.93
- And: the cost is the sum of the runs' `cost`: 45 calls, 27000 tokens, 135 s

### TC-EVL-002 – Decisions only on held-out cases
- Verifies: REQ-EVL-002
- Given: a run of the dev split and a run of the holdout split (synthetic records), and `tools/decide_guard.py` around `eval_decide.py`
- When: a verdict criterion is decided on each, also with `--split dev` or a dev run as `--rerun` among the options
- Then: the dev run, the mix and every split option are NOT DECIDED with the reason named; the holdout run is decided PASS or FAIL by the rule
- And: a dev run of the harness never selects a case tagged `split:holdout`, and `tools/eval.py` neither lists, shows nor runs a holdout suite without `--holdout`

### TC-EVL-003 – A judge counts only after calibration
- Verifies: REQ-EVL-003
- Given: records of the judge judge-light and calibration records of Cohen's kappa 0.7, 0.4 and none
- When: the harness marks the records and the metrics count them
- Then: with 0.7 the verdicts count; with 0.4 and without a record they are "not counted" and left out of every number

### TC-EVL-004 – Versions recorded per run
- Verifies: REQ-EVL-004
- Given: the harness against the mock of IF-105 and the pin of `tools/eval.py` (id MP-light)
- When: 10 runs are made with seeds 0 to 9
- Then: every header carries workflow, workflow version, the pin (id, name, digest, seed, temperature) and the benchmark version
- And: `tools/eval.py run` refuses to start without `--pin`, and a suite of a skill records the skill, its version and the pipeline

### TC-EVL-005 – A baseline per shipped workflow
- Verifies: REQ-EVL-005
- Given: the workflows of the library with status tested or trusted and a folder of baselines
- When: `tools/check_baselines.py` runs
- Then: each workflow without its `<suite>__<variant>__baseline.jsonl` is named with the reason; one with its file is not

### TC-EVL-006 – The skill path is documented and its examples run
- Verifies: REQ-EVL-006
- Given: `docs/skill-path.md` with the lookup as its example
- When: the sections are read and the blocks marked `run` are executed with a scripted model
- Then: all seven steps have a section, every block ends with its expected exit code and every relative link resolves

### TC-EVL-007 – Time to the first text and frame rate
- Verifies: REQ-EVL-007
- Given: a fake server that answers after 1.0, 2.0 and 3.0 s in turn; a fake socket whose first text comes after 0.1 s and whose answer ends after 0.5 s
- When: the latency tool times 20 runs after 3 warm-ups, and 3 runs on the fake socket
- Then: the median is 2.0 s (within 0.1 s) with 20 runs, and 0.1 s on the socket (the wait for the previous answer is not timed)
- And: the frame-rate tool gives 60 fps for 16.7 ms frames and 30 fps for 33.3 ms (within 1 fps)

### TC-EVL-008 – Variants compared on equal cases
- Verifies: REQ-EVL-008
- Given: two runs of the same suite under two variants, a run without case c2, a run with other repeats and a run of another suite version
- When: they are compared
- Then: the first pair is compared; the others are refused with c2, the repeats or "suite version" named

### TC-EVL-009 – Suites of lookup and verify with holdout and baseline
- Verifies: REQ-EVL-009
- Given: the suites of lookup and verify in `eval/`
- When: `agent_check.py --spec-dir specs/mia --eval-dir eval` runs
- Then: each has a dev part, a holdout part and a recorded baseline, and the A-checks report no error for them

### TC-EVL-010 – The lookup as the proof of concept
- Verifies: REQ-EVL-010
- Given: the lookup scenario through IF-105 against the mocks (step 0), then against each real node as it is integrated
- When: a question is asked
- Then: the answer carries a source and a verbatim quote, or unknown
- And: the library holds the time stamps idea and promotion of the lookup

### TC-EVL-011 – The platform only through IF-105
- Verifies: REQ-EVL-011
- Given: the source of the harness adapter `eval_platform.py`
- When: its imports are collected
- Then: all of them are in the standard library: no runner, library or store
