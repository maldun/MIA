# Plan: Database (N-3)

**Requirements:** specs/mia/nodes/N-3-database/requirements.md   **Test spec:** specs/mia/nodes/N-3-database/test-spec.md   **Status:** Draft (Plan for node N-3, 2026-10-25)

The integration of the Database: the parts are built in their own cycles (below), then put together in the order of `decomposition.yaml`: N-3.2, N-3.3, N-3.1.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 *Owner:* approve the dependency psycopg 3 | ASM-N3-003 | the answer is recorded in `review-log.md` | – |
| T-02 Step 0 of N-3: skeleton with all three parts as mocks | REQ-DB-002 | tests/integration/N-3/step_00 (written outside the implementing session, installed by the owner) | T-01 of the root plan |
| T-03 Step 1: Graph tables real | REQ-DB-004, REQ-DB-011 | TC-N3-004, TC-N3-010 (with the Storage layer still a mock) | N-3.2 built |
| T-04 Step 2: Record tables real | REQ-DB-010, REQ-DB-012..015 | TC-N3-009, TC-N3-011 (with the Storage layer still a mock) | N-3.3 built, T-03 |
| T-05 Step 3: Storage layer real, node complete | REQ-DB-001..009, REQ-DB-016..018 | TC-N3-001..012 | N-3.1 built, T-04 |

## Tasks

### T-01: approve the dependency psycopg 3
- Implements: ASM-N3-003
- Tests to turn green: the answer is recorded in `review-log.md`
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Needed before N-3.1 T-06.

### T-02: Step 0 of N-3: skeleton with all three parts as mocks
- Implements: REQ-DB-002
- Tests to turn green: tests/integration/N-3/step_00 (written outside the implementing session, installed by the owner)
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Write, read back and validate one workflow through the three mocks.

### T-03: Step 1: Graph tables real
- Implements: REQ-DB-004, REQ-DB-011
- Tests to turn green: TC-N3-004, TC-N3-010 (with the Storage layer still a mock)
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-3.2 built
- Done when: the listed tests are green and all other tests are unchanged
- Notes: First in the integration order.

### T-04: Step 2: Record tables real
- Implements: REQ-DB-010, REQ-DB-012..015
- Tests to turn green: TC-N3-009, TC-N3-011 (with the Storage layer still a mock)
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-3.3 built, T-03
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-05: Step 3: Storage layer real, node complete
- Implements: REQ-DB-001..009, REQ-DB-016..018
- Tests to turn green: TC-N3-001..012
- Touches: –
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: N-3.1 built, T-04
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Then Verify (Phase 4) for the node; its parent treats it as one finished child.
