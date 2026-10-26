# Test specification: Evaluation and operation (N-4)

**Requirements:** specs/mia/nodes/N-4-evaluation-operation/requirements.md   **Status:** Draft (Plan for node N-4, 2026-10-25)

The tests of the inner node: the harness and the operation layer put together. The two parts do not talk to each other (no interface between them); what the node as a whole shows is that the harness evaluates the stack that the operation layer brings up. Integration steps: step 0 the skeleton with both parts as mocks, step 1 Evaluation real (the interface IF-105 is a mock until N-2 is built), step 2 Operation real.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-N4-001 | REQ-OPS-001, REQ-OPS-004, REQ-OPS-017, REQ-OPS-020 | Integration | 3 | N-4 complete: the harness (N-4.1) runs a lookup case against the compose stack brought up by N-4.2 | the case is answered, its run header and cost are recorded, the latency tool reports the first-text time | exact |
| TC-N4-002 | REQ-OPS-007, REQ-OPS-013, REQ-OPS-016 | Integration | 3 | the stack from N-4.2 with the harness image started alone | the harness container starts alone against the mocks and in the stack with the same configuration file | exact |
| TC-N4-003 | REQ-OPS-002, REQ-OPS-003, REQ-OPS-005, REQ-OPS-006, REQ-OPS-008, REQ-OPS-009, REQ-OPS-010, REQ-OPS-011, REQ-OPS-012, REQ-OPS-014, REQ-OPS-015, REQ-OPS-018, REQ-OPS-019 | Integration | 3 | the tests of the two leaves in one run (stages 1 to 3) | all leaf tests pass; no requirement of N-4 lacks a passing test | exact |

## Assumptions and open numbers

- The assumptions of the leaves apply (ASM-N4-001..003).
