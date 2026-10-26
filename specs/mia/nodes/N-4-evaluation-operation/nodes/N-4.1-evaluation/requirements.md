# Requirements: Evaluation (N-4.1, low level)

**Parent:** `specs/mia/nodes/N-4-evaluation-operation/requirements.md` (N-4)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The harness, the decisions on held-out cases, the baselines and benchmarks of the example workflows, the measurement tools and the proof-of-concept scenario. Consumes IF-105 (the Backend) and uses the eval material in `eval/` (protected). Knows no particular workflow. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-EVL-001 – Harness with repeats
- Level: low   Subject: Evaluation
- Text: The Evaluation shall run pipeline variants on fixed suites with repeats, intervals and cost counting.
- Rationale: refines REQ-OPS-001
- Parent: REQ-OPS-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: variants are compared on the same cases with 3 repeats and 95 % intervals
- Verified by: TC-EVL-001
- Status: Draft
- History: –

### REQ-EVL-002 – Decisions on held-out cases
- Level: low   Subject: Evaluation
- Text: The Evaluation shall decide improvement claims only on held-out cases.
- Rationale: refines REQ-OPS-002
- Parent: REQ-OPS-002
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-2: a decision script refuses a dev-split run for a verdict
- Verified by: TC-EVL-002
- Status: Draft
- History: –

### REQ-EVL-003 – Judge calibration
- Level: low   Subject: Evaluation
- Text: The Evaluation shall count the verdicts of a model used as a judge only after its calibration against the users' ratings.
- Rationale: refines REQ-OPS-003
- Parent: REQ-OPS-003
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-22: an uncalibrated judge's verdicts are marked not counted
- Verified by: TC-EVL-003
- Status: Draft
- History: –

### REQ-EVL-004 – Versions recorded per run
- Level: low   Subject: Evaluation
- Text: The Evaluation shall record the workflow version, the model pin and the benchmark version of every run.
- Rationale: refines REQ-OPS-004
- Parent: REQ-OPS-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: 100 % of runs carry the three versions
- Verified by: TC-EVL-004
- Status: Draft
- History: –

### REQ-EVL-005 – Baseline per shipped workflow
- Level: low   Subject: Evaluation
- Text: The Evaluation shall keep a recorded baseline for every shipped workflow.
- Rationale: refines REQ-OPS-005
- Parent: REQ-OPS-005
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-10: each shipped workflow has a baseline file
- Verified by: TC-EVL-005
- Status: Draft
- History: –

### REQ-EVL-006 – Skill path documented
- Level: low   Subject: Evaluation
- Text: The Evaluation shall document the path from an idea to a promoted skill with its steps and checks.
- Rationale: refines REQ-OPS-006
- Parent: REQ-OPS-006
- Priority: Should
- Verification method: Inspection
- Acceptance criterion: AC-9: the lookup is documented as the example
- Verified by: TC-EVL-006
- Status: Draft
- History: –

### REQ-EVL-007 – Measure latency and frame rate
- Level: low   Subject: Evaluation
- Text: The Evaluation shall measure the time to the first text of a chat answer and the frame rate of the character.
- Rationale: refines REQ-OPS-017
- Parent: REQ-OPS-017
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-19: the measurement tool reports both with the median of repeated runs
- Verified by: TC-EVL-007
- Status: Draft
- History: –

### REQ-EVL-008 – Variants compared on equal cases
- Level: low   Subject: Evaluation
- Text: The Evaluation shall compare variants on the same cases with the same repeats.
- Rationale: refines REQ-OPS-018
- Parent: REQ-OPS-018
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: a comparison with different case lists is refused
- Verified by: TC-EVL-008
- Status: Draft
- History: –

### REQ-EVL-009 – Benchmarks of the example workflows
- Level: low   Subject: Evaluation
- Text: The Evaluation shall hold the suites, baselines and eval criteria of the example workflows lookup, verify and review as the benchmark that decides their criteria.
- Rationale: refines REQ-OPS-019
- Parent: REQ-OPS-019
- Priority: Must
- Verification method: Inspection, Measurement
- Acceptance criterion: AC-2, AC-3: each example workflow has a suite with a holdout and a recorded baseline; the criteria are decided with the rule of the agent-app workflow
- Verified by: TC-EVL-009
- Status: Draft
- History: –

### REQ-EVL-010 – Example workflows as proof of concept
- Level: low   Subject: Evaluation
- Text: The Evaluation shall run the lookup workflow end to end as the proof-of-concept scenario of the platform and the review workflow once it is promoted.
- Rationale: refines REQ-OPS-020
- Parent: REQ-OPS-020
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-9: the lookup scenario runs on the mocks (step 0 of the integration tests) and again with each real node; the time from idea to promotion is recorded
- Verified by: TC-EVL-010
- Status: Draft
- History: –

### REQ-EVL-011 – Reach the platform only through IF-105
- Level: low   Subject: Evaluation
- Text: The Evaluation shall run workflows, read their cost and events and list the library only through the interface IF-105 as specified in contracts/IF-105-evaluation-access.md.
- Rationale: refines REQ-OPS-001, REQ-OPS-004
- Parent: REQ-OPS-001, REQ-OPS-004
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-22: with the mock of IF-105 every scenario of the harness runs; no other import of the platform exists
- Verified by: TC-EVL-011
- Status: Draft
- History: –
