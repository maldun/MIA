# Plan: Evaluation (N-4.1)

**Requirements:** specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/requirements.md   **Test spec:** specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/test-spec.md   **Status:** Draft (Plan for node N-4.1, 2026-10-25)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 The harness reaches the platform through IF-105 | REQ-EVL-001, REQ-EVL-004, REQ-EVL-008, REQ-EVL-011 | TC-EVL-001, TC-EVL-004, TC-EVL-008, TC-EVL-011 | T-01 of the root plan (mocks installed); T-03 of `specs/number-gate` |
| T-02 Decisions only on held-out cases | REQ-EVL-002 | TC-EVL-002 | T-01 |
| T-03 Judge calibration flag | REQ-EVL-003 | TC-EVL-003 | T-01 |
| T-04 Baseline and suite checks | REQ-EVL-005, REQ-EVL-009 | TC-EVL-005, TC-EVL-009 | – |
| T-05 Measurement tools for first text and frame rate | REQ-EVL-007 | TC-EVL-007; BM-MIA-001 and BM-MIA-002 baselines (root task T-04) | – |
| T-06 Document of the skill path | REQ-EVL-006 | TC-EVL-006 | – |
| T-07 Proof-of-concept scenario | REQ-EVL-010 | TC-EVL-010 | N-2 and N-3 steps of the root plan |

## Tasks

### T-01: The harness reaches the platform through IF-105
- Implements: REQ-EVL-001, REQ-EVL-004, REQ-EVL-008, REQ-EVL-011
- Tests to turn green: TC-EVL-001, TC-EVL-004, TC-EVL-008, TC-EVL-011
- Touches: `harness.py`, `metrics.py`, `tools/eval.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed); T-03 of `specs/number-gate`
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Today the harness calls the pipeline directly; it gets a thin adapter for IF-105 so that the mock and the real Backend are interchangeable.

### T-02: Decisions only on held-out cases
- Implements: REQ-EVL-002
- Tests to turn green: TC-EVL-002
- Touches: `tools/` (a check around `eval_decide.py`)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Never reads or opens `*.holdout` suites or cases tagged `split:holdout` in a dev run.

### T-03: Judge calibration flag
- Implements: REQ-EVL-003
- Tests to turn green: TC-EVL-003
- Touches: `harness.py`, `tools/label_agreement.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Threshold decided (OPEN-7): Cohen's kappa 0.6 or more.

### T-04: Baseline and suite checks
- Implements: REQ-EVL-005, REQ-EVL-009
- Tests to turn green: TC-EVL-005, TC-EVL-009
- Touches: `tools/` (a check script)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Read-only on `eval/suites/` and `eval/baselines/`.

### T-05: Measurement tools for first text and frame rate
- Implements: REQ-EVL-007
- Tests to turn green: TC-EVL-007; BM-MIA-001 and BM-MIA-002 baselines (root task T-04)
- Touches: `tools/measure_latency.py`, `tools/measure_fps.mjs` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The baselines of today's MIA are measured first; the tools are tested on fakes.

### T-06: Document of the skill path
- Implements: REQ-EVL-006
- Tests to turn green: TC-EVL-006
- Touches: `ui/README.md` (section Core) or a new document under `docs/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Executable examples; the lookup is the example.

### T-07: Proof-of-concept scenario
- Implements: REQ-EVL-010
- Tests to turn green: TC-EVL-010
- Touches: `tests/integration/N-0/` (written outside this session, installed by the owner)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2 and N-3 steps of the root plan
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The thinnest end-to-end scenario; runs on the mocks first.
