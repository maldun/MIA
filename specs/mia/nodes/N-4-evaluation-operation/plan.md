# Plan: Evaluation and operation (N-4)

**Requirements:** specs/mia/nodes/N-4-evaluation-operation/requirements.md   **Test spec:** specs/mia/nodes/N-4-evaluation-operation/test-spec.md   **Status:** Draft (Plan for node N-4, 2026-10-25)

The integration of the node: the two parts are built in their own cycles, then put together in the order of `decomposition.yaml`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Step 0 of N-4: skeleton with both parts as mocks | REQ-OPS-001 | tests/integration/N-4/step_00 | T-01 of the root plan |
| T-02 Step 1: Evaluation real | REQ-OPS-001, REQ-OPS-004, REQ-OPS-017 | TC-N4-001 (with the stack still a mock) | N-4.1 built |
| T-03 Step 2: Operation real, node complete | REQ-OPS-007, REQ-OPS-013, REQ-OPS-016 and the rest | TC-N4-001..003 | N-4.2 built, T-02 |

## Tasks

### T-01: Step 0 of N-4: skeleton with both parts as mocks
- Implements: REQ-OPS-001
- Tests to turn green: tests/integration/N-4/step_00
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Written outside the implementing session and installed by the owner.

### T-02: Step 1: Evaluation real
- Implements: REQ-OPS-001, REQ-OPS-004, REQ-OPS-017
- Tests to turn green: TC-N4-001 (with the stack still a mock)
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-4.1 built
- Done when: the listed tests are green and all other tests are unchanged
- Notes: IF-105 stays a mock until N-2 is integrated.

### T-03: Step 2: Operation real, node complete
- Implements: REQ-OPS-007, REQ-OPS-013, REQ-OPS-016 and the rest
- Tests to turn green: TC-N4-001..003
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-4.2 built, T-02
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Then Verify (Phase 4) for the node.
