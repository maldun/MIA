# Plan: Pipeline runner (N-2.4.1)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/test-spec.md   **Status:** Draft (Plan for node N-2.4.1, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Realise IF-202 and IF-105 under budgets | REQ-RUN-008, REQ-RUN-014, REQ-RUN-015 | TC-RUN-008, TC-RUN-014, TC-RUN-015 | T-01 of the root plan (mocks installed) |
| T-02 One model at a time, chat before background | REQ-RUN-009, REQ-RUN-010 | TC-RUN-009, TC-RUN-010 | T-01 |
| T-03 Switch the model, server unreachable, IF-103 only | REQ-RUN-002, REQ-RUN-003, REQ-RUN-011 | TC-RUN-002, TC-RUN-003, TC-RUN-011 | T-01 |
| T-04 Internet tasks only on command | REQ-RUN-001 | TC-RUN-001 | T-01 |
| T-05 Context window share, calls of the first try, optional learning | REQ-RUN-004, REQ-RUN-005, REQ-RUN-006 | TC-RUN-004, TC-RUN-005, TC-RUN-006 | T-01 |
| T-06 First text in 10 seconds | REQ-RUN-007 | TC-RUN-007 | T-01 |
| T-07 Interfaces only, no particular workflow | REQ-RUN-012, REQ-RUN-013 | TC-RUN-012, TC-RUN-013 | T-01 |
| T-08 The review as a workflow of the library (A-35) | REQ-RUN-013 (AC-9, the review entry) | TC-RUN-013, the review benchmark (TC-MIA-003) | T-07 |

## Tasks

### T-01: Realise IF-202 and IF-105 under budgets
- Implements: REQ-RUN-008, REQ-RUN-014, REQ-RUN-015
- Tests to turn green: TC-RUN-008, TC-RUN-014, TC-RUN-015
- Touches: `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-202 and IF-105; the evaluation access is a thin facade over the same run.

### T-02: One model at a time, chat before background
- Implements: REQ-RUN-009, REQ-RUN-010
- Tests to turn green: TC-RUN-009, TC-RUN-010
- Touches: `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-03: Switch the model, server unreachable, IF-103 only
- Implements: REQ-RUN-002, REQ-RUN-003, REQ-RUN-011
- Tests to turn green: TC-RUN-002, TC-RUN-003, TC-RUN-011
- Touches: `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Consumes IF-103.

### T-04: Internet tasks only on command
- Implements: REQ-RUN-001
- Tests to turn green: TC-RUN-001
- Touches: `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-05: Context window share, calls of the first try, optional learning
- Implements: REQ-RUN-004, REQ-RUN-005, REQ-RUN-006
- Tests to turn green: TC-RUN-004, TC-RUN-005, TC-RUN-006
- Touches: `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Measured on the lookup suites.

### T-06: First text in 10 seconds
- Implements: REQ-RUN-007
- Tests to turn green: TC-RUN-007
- Touches: `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Median of 20 runs; measured with the tool of N-4.1 T-05.

### T-07: Interfaces only, no particular workflow
- Implements: REQ-RUN-012, REQ-RUN-013
- Tests to turn green: TC-RUN-012, TC-RUN-013
- Touches: `pipeline.py`, `pipeline_model.py`, `harness.py`, `ollama_remote.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Consumes IF-203, IF-401, IF-402; the same code runs lookup, verify and review.

### T-08: The review as a workflow of the library (amendment A-35, approved by the owner 2026-10-31, D-125)
- Implements: REQ-RUN-013 (AC-9: the review entry runs with the same runner as lookup and verify)
- Tests to turn green: TC-RUN-013 (the review entry runs through `Runner`), the review benchmark of TC-MIA-003 against its recorded baseline (eval criterion, suite and repeats to be fixed at the plan gate of this amendment)
- Touches: `review_chat.py`, `extensions/review/`, `library/pipelines/` (a new review pipeline), `skills/review_*.md` (versions bumped)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-07
- Done when: `/review` runs a library pipeline through `Runner` (no Python control flow that names the review), the listed tests are green and the review benchmark is not worse than its baseline by the decision rule
- Notes: Why split: `review_chat.run_review` is Python control flow (slices, questions to the user, the monitor), not a pipeline; rebuilding it is design work with an eval criterion, outside the files of T-07. Open for the gate: whether the user questions of the review become `ask_user` nodes, how the slicing maps to `map`, and which eval suite decides. The redesign of FB-02 (networkx) may change the form of a workflow; decide at the gate whether T-08 waits for it.
