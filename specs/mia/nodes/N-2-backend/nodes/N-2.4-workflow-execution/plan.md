# Plan: Workflow execution (N-2.4)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/test-spec.md   **Status:** Draft (Plan for node N-2.4, 2026-10-26)

The integration of the node: the parts are built in their own cycles, then put together in the order of `decomposition.yaml`: N-2.4.3, N-2.4.2, N-2.4.1.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Step 0: skeleton with all three parts as mocks | the skeleton | tests/integration/N-2.4/step_00 | T-01 of the root plan |
| T-02 Step 1: Run log real | the requirements of step 1 | TC-N24-001 | N-2.4.3 built |
| T-03 Step 2: Tools and sandbox real | the requirements of step 2 | TC-N24-002 | N-2.4.2 built, T-02 |
| T-04 Step 3: Pipeline runner real, node complete | the requirements of step 3 | TC-N24-003 | N-2.4.1 built, T-03 |

## Tasks

### T-01: Step 0: skeleton with all three parts as mocks
- Implements: the skeleton
- Tests to turn green: tests/integration/N-2.4/step_00
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Written outside the implementing session and installed by the owner.

### T-02: Step 1: Run log real
- Implements: the requirements of step 1
- Tests to turn green: TC-N24-001
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.4.3 built
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The runner and the tools stay mocks.

### T-03: Step 2: Tools and sandbox real
- Implements: the requirements of step 2
- Tests to turn green: TC-N24-002
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.4.2 built, T-02
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The runner stays a mock.

### T-04: Step 3: Pipeline runner real, node complete
- Implements: the requirements of step 3
- Tests to turn green: TC-N24-003
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.4.1 built, T-03
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Then Verify (Phase 4) for the node.
