# Plan: Web Frontend (N-1)

**Requirements:** specs/mia/nodes/N-1-web-frontend/requirements.md   **Test spec:** specs/mia/nodes/N-1-web-frontend/test-spec.md   **Status:** Draft (Plan for node N-1, 2026-10-25)

The integration of the Web Frontend: the parts are built in their own cycles, then put together in the order of `decomposition.yaml`: N-1.3, N-1.2, N-1.1.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Step 0 of N-1: skeleton with all three parts as mocks | REQ-FE-030 | tests/integration/N-1/step_00 | T-01 of the root plan |
| T-02 Step 1: Voice playback real | REQ-FE-011, REQ-FE-012, REQ-FE-013 | TC-N1-001 | N-1.3 built |
| T-03 Step 2: Character view real | REQ-FE-006, REQ-FE-008, REQ-FE-010 | TC-N1-002 | N-1.2 built, T-02 |
| T-04 Step 3: Chat and login views real, node complete | all requirements of N-1 | TC-N1-003..006 and the tests of the parts | N-1.1 built, T-03 |

## Tasks

### T-01: Step 0 of N-1: skeleton with all three parts as mocks
- Implements: REQ-FE-030
- Tests to turn green: tests/integration/N-1/step_00
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Written outside the implementing session and installed by the owner.

### T-02: Step 1: Voice playback real
- Implements: REQ-FE-011, REQ-FE-012, REQ-FE-013
- Tests to turn green: TC-N1-001
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-1.3 built
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The chat page and the character view stay mocks.

### T-03: Step 2: Character view real
- Implements: REQ-FE-006, REQ-FE-008, REQ-FE-010
- Tests to turn green: TC-N1-002
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-1.2 built, T-02
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The chat page stays a mock.

### T-04: Step 3: Chat and login views real, node complete
- Implements: all requirements of N-1
- Tests to turn green: TC-N1-003..006 and the tests of the parts
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-1.1 built, T-03
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Then Verify (Phase 4) for the node; IF-101 stays a mock until N-2 is integrated.
