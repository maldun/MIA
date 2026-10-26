# Test specification: Evaluation (N-4.1)

**Requirements:** specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/requirements.md   **Status:** Draft (Plan for node N-4.1, 2026-10-25)

Tests of the harness and the measurement tools against the mock of IF-105; model-dependent criteria are decided by eval suites on the pinned model, never by this mock (agent-app rule). The harness features that `specs/number-gate` already specifies (REQ-EVAL-001..004: retired cases, pin in the header and the options, seeded sample, case input) are built there and only referenced here (its T-03). Stages (M27): 1 = commit gate, 2 = up to 10 minutes, 3 = up to 30 minutes.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-EVL-001 | REQ-EVL-001 | Component | 1 | the harness against the mock of IF-105; a suite of 5 cases with scripted outcomes (4 pass, 1 fails), 3 repeats | the report lists every case with its 3 repeats, the pass counts per case, the 95 % Wilson interval of the pass rate and the summed cost (calls, tokens, seconds) taken from the `cost` of the runs | exact for counts and sums; intervals to two decimals |
| TC-EVL-002 | REQ-EVL-002 | Component | 1 | `eval_decide.py` of the agent-app skill on a run of the dev split and on a run of the holdout split with a baseline, both for a verdict criterion | the dev-split run is refused (not decided, reason dev split); the holdout run is decided PASS, FAIL or NOT DECIDED by the rule; the harness never reads a case tagged `split:holdout` in a dev run | exact |
| TC-EVL-003 | REQ-EVL-003 | Component | 1 | a judge run without a calibration record; with a record of Cohen's kappa 0.7 against the users' ratings; with a record of kappa 0.4 (threshold: OPEN-7, proposal 0.6) | the first and the third run mark the judge's verdicts "not counted"; the second counts them | exact |
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
- **OPEN-7** (proposal, to be confirmed): the judge counts only after a calibration of Cohen's kappa 0.6 or more against the users' ratings (the labels audit of 2026-10-24 reached 0.85 between the owner and the benchmark; 0.6 is the usual limit for "substantial"). Used by TC-EVL-003.
