# Requirements: Evaluation and operation (N-4, high level)

**Parent:** `specs/mia/requirements.md` (top level N-0)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

Harness, suites, baselines, compose stack, backups, shutdown. The sub-part OperationLayer of the model belongs here. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-OPS-001 – Harness with repeats
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall run pipeline variants on fixed suites with repeats, intervals and cost counting.
- Rationale: refines FR-17
- Parent: FR-17
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: variants are compared on the same cases with 3 repeats and 95 % intervals
- Verified by: TC-N4-001
- Status: Draft
- History: –

### REQ-OPS-002 – Decisions on held-out cases
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall decide improvement claims only on held-out cases.
- Rationale: refines FR-17
- Parent: FR-17
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-2: a decision script refuses a dev-split run for a verdict
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-003 – Judge calibration
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall count the verdicts of a model used as a judge only after its calibration against the users' ratings.
- Rationale: refines FR-17
- Parent: FR-17
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-22: an uncalibrated judge's verdicts are marked not counted
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-004 – Versions recorded per run
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall record the workflow version, the model pin and the benchmark version of every run.
- Rationale: refines FR-26
- Parent: FR-26
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: 100 % of runs carry the three versions
- Verified by: TC-N4-001
- Status: Draft
- History: –

### REQ-OPS-005 – Baseline per shipped workflow
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall keep a recorded baseline for every shipped workflow.
- Rationale: refines FR-26, FR-20
- Parent: FR-26, FR-20
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-10: each shipped workflow has a baseline file
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-006 – Skill path documented
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall document the path from an idea to a promoted skill with its steps and checks.
- Rationale: refines FR-20
- Parent: FR-20
- Priority: Should
- Verification method: Inspection
- Acceptance criterion: AC-9: the lookup is documented as the example
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-007 – One file, one command
- Level: high   Subject: Evaluation
- Text: When the owner runs the start command on a fresh checkout with one configuration file, the Evaluation and operation node shall bring MIA up with its database.
- Rationale: refines FR-19
- Parent: FR-19
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-7: a fresh checkout starts to a working chat in the compose stack
- Verified by: TC-N4-002
- Status: Draft
- History: –

### REQ-OPS-008 – First account at installation
- Level: high   Subject: Evaluation
- Text: When MIA starts for the first time, the Evaluation and operation node shall let the owner create the first account.
- Rationale: refines FR-19, FR-21
- Parent: FR-19, FR-21
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: the first start offers the account creation exactly once
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-009 – Missing options reported
- Level: high   Subject: Evaluation
- Text: When MIA starts after an update, the Evaluation and operation node shall report the options missing in the configuration file.
- Rationale: refines FR-19
- Parent: FR-19
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: removing 2 options gives a report naming both (exact)
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-010 – Orderly shutdown
- Level: high   Subject: Evaluation
- Text: When MIA is stopped, the Evaluation and operation node shall shut it down in order and save her memory.
- Rationale: refines FR-19
- Parent: FR-19
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: after SIGTERM the history and memory are saved (exact)
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-011 – Backup and restore of all data
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall back up and restore the data of MIA including the database.
- Rationale: refines FR-19
- Parent: FR-19
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: backup, wipe and restore return the same data (exact)
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-012 – Runbook
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall provide a runbook with start, update of the model pins, backup and restore of the database and a retirement plan that ends in freezing the stack with the model digests.
- Rationale: refines FR-19
- Parent: FR-19
- Priority: Should
- Verification method: Inspection
- Acceptance criterion: AC-7: the runbook steps are run once on a clean machine
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-013 – Compose stack
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall provide a compose stack that starts the containers of N-2 to N-5 alone and together with one configuration file.
- Rationale: refines NFR-9
- Parent: NFR-9
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-29: each container starts alone against the mocks; all start together
- Verified by: TC-N4-002
- Status: Draft
- History: –

### REQ-OPS-014 – Private access only
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall expose MIA only over HTTPS inside the home network or the tailnet, with no public port.
- Rationale: refines NFR-6, CON-5
- Parent: NFR-6, CON-5
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-14: a port scan from outside the network finds nothing open; tailscale funnel is not used
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-015 – Free and open
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall provide the licence GPL-3.0-or-later and use no paid API.
- Rationale: refines CON-1, NFR-5
- Parent: CON-1, NFR-5
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: licence file present; no paid API host in the web log
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-016 – Hardware configuration
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall configure the model server to load one model at a time.
- Rationale: refines CON-2, NFR-7
- Parent: CON-2, NFR-7
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-19: OLLAMA_MAX_LOADED_MODELS equals 1 (exact)
- Verified by: TC-N4-002
- Status: Draft
- History: –

### REQ-OPS-017 – Measure latency and frame rate
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall measure the time to the first text of a chat answer and the frame rate of the character.
- Rationale: refines NFR-7
- Parent: NFR-7
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-19: the measurement tool reports both with the median of repeated runs
- Verified by: TC-N4-001
- Status: Draft
- History: –

### REQ-OPS-018 – Variants compared on equal cases
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall compare variants on the same cases with the same repeats.
- Rationale: refines NFR-2, FR-17
- Parent: NFR-2, FR-17
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: a comparison with different case lists is refused
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-019 – Benchmarks of the example workflows
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall hold the suites, baselines and eval criteria of the example workflows lookup, verify and review as the benchmark that decides their criteria.
- Rationale: refines FR-9, FR-10, FR-11, FR-26
- Parent: FR-9, FR-10, FR-11, FR-26
- Priority: Must
- Verification method: Inspection, Measurement
- Acceptance criterion: AC-2, AC-3: each example workflow has a suite with a holdout and a recorded baseline; the criteria are decided with the rule of the agent-app workflow
- Verified by: TC-N4-003
- Status: Draft
- History: –

### REQ-OPS-020 – Example workflows as proof of concept
- Level: high   Subject: Evaluation
- Text: The Evaluation and operation node shall run the lookup workflow end to end as the proof-of-concept scenario of the platform and the review workflow once it is promoted.
- Rationale: refines FR-20, NFR-2, NFR-4
- Parent: FR-20, NFR-2, NFR-4
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-9: the lookup scenario runs on the mocks (step 0 of the integration tests) and again with each real node; the time from idea to promotion is recorded
- Verified by: TC-N4-001
- Status: Draft
- History: –
