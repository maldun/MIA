# Plan: Backend (N-2)

**Requirements:** specs/mia/nodes/N-2-backend/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/test-spec.md   **Status:** Draft (Plan for node N-2, 2026-10-26)

The integration of the node: the parts are built in their own cycles, then put together in the order of `decomposition.yaml`: N-2.5, N-2.3, N-2.4, N-2.2, N-2.1.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Step 0: skeleton with all five parts as mocks | the skeleton | tests/integration/N-2/step_00 | T-01 of the root plan |
| T-02 Step 1: Voice synthesis real | the requirements of step 1 | TC-N2-001 | N-2.5 built |
| T-03 Step 2: Workflow management real | the requirements of step 2 | TC-N2-002 | N-2.3 built, T-02 |
| T-04 Step 3: Workflow execution real | the requirements of step 3 | TC-N2-003 | N-2.4 built, T-03 |
| T-05 Step 4: Chat agent real | the requirements of step 4 | TC-N2-004 | N-2.2 built, T-04 |
| T-06 Step 5: API and accounts real, node complete | the requirements of step 5 | TC-N2-005 | N-2.1 built, T-05 |

## Tasks

### T-01: Step 0: skeleton with all five parts as mocks
- Implements: the skeleton
- Tests to turn green: tests/integration/N-2/step_00
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Written outside the implementing session and installed by the owner.

### T-02: Step 1: Voice synthesis real
- Implements: the requirements of step 1
- Tests to turn green: TC-N2-001
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.5 built
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-03: Step 2: Workflow management real
- Implements: the requirements of step 2
- Tests to turn green: TC-N2-002
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.3 built, T-02
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-04: Step 3: Workflow execution real
- Implements: the requirements of step 3
- Tests to turn green: TC-N2-003
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.4 built, T-03
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Risky first: the model-dependent part (FR-9, FR-11); needs the complete plan of N-2.4.

### T-05: Step 4: Chat agent real
- Implements: the requirements of step 4
- Tests to turn green: TC-N2-004
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.2 built, T-04
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-06: Step 5: API and accounts real, node complete
- Implements: the requirements of step 5
- Tests to turn green: TC-N2-005
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-2.1 built, T-05
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Then Verify (Phase 4) for the node.
