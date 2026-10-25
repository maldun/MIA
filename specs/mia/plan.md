# Plan: MIA, top level (node N-0)

**Requirements:** specs/mia/requirements.md   **Test spec:** specs/mia/test-spec.md   **Decomposition:** specs/mia/decomposition.yaml   **Status:** Draft (Plan step 5 for the root node, 2026-10-25)

This is the plan of the whole tree, one task per node cycle in the order of the integration record (testability first, N-5 last by reason). Every node cycle repeats the same steps from its inputs in a fresh context: plan the node (requirements, test spec, plan), split it if it is not a leaf, build it against the mocks of its interfaces, integrate it. A task of this file is therefore larger than a task of a leaf plan; the leaf plans (`nodes/*/plan.md`) are written when the node's turn comes. The existing package `specs/number-gate` (T-01..T-14, paused at T-10) is the first iteration inside this tree; it keeps its folder and its numbering.

## Task list

| Task | Title | Implements | Green when | Depends on |
| --- | --- | --- | --- | --- |
| T-01 | *Owner:* install the contract drafts and run them | IF-101..IF-405 (mock side) | all mock-side contract tests green, real side skipped | – |
| T-02 | *Owner:* fix the open numbers OPEN-2..OPEN-6 (OPEN-1 and OPEN-3 wait for T-04) | TC-MIA-011, -015, -019, -028 | the owner's answers are in `test-spec.md` and `review-log.md` | – |
| T-03 | Red integration tests for the root: step 0 (walking skeleton, lookup on the mocks) and steps 1 to 5 | TC-MIA-001..029 (system level), AC-9 | step_00 fails for the right reason (assertion, not import) and is the first green target | T-01 |
| T-04 | Measure today's MIA: first-text time, frame rate, persona dialogues, estimate against measured time of the recorded lookup runs | BM-MIA-001, BM-MIA-002, OPEN-1, OPEN-3 | baselines recorded in `test-spec.md`; OPEN-1 and OPEN-3 can be answered | – |
| T-05 | Plausibility record and quality walk for the root and the high-level nodes (people rate, references back the rating) | all requirements and assumptions | `req_plausibility.py` and `quality_check.py` report no error | – |
| T-06 | Node cycle N-3 Database: N-3.2 Graph tables, N-3.3 Record tables, N-3.1 Storage layer, integration steps 1 to 3 | REQ-DB-*, IF-102, IF-301, IF-302; step_01 of N-0 | contract suites of IF-102, IF-301, IF-302 green on the real side; N-3 integration tests green | T-01, T-03 |
| T-07 | Node cycle N-4 Evaluation and operation: harness, suites, baselines, compose stack, backup, shutdown | REQ-OPS-*, NFR-9, FR-17, FR-19; AC-7, AC-29 | TC-MIA-007 and TC-MIA-029 green on the compose stack with mocks | T-01, T-03 |
| T-08 | Node cycle N-1 Web Frontend: N-1.3 Voice playback, N-1.2 Character view, N-1.1 Chat and login views | REQ-CLV-*, REQ-CHV-*, REQ-VPB-*, IF-111, IF-112; step_03 of N-0 | browser contract suites green on the real side; TC-MIA-001, -005, -013, -017 on the mocks | T-01, T-03 |
| T-09 | Node cycle N-2 Backend: N-2.5 Voice synthesis, N-2.3 Workflow management, N-2.4 Workflow execution (N-2.4.3 Run log, N-2.4.2 Tools and sandbox, N-2.4.1 Pipeline runner), N-2.2 Chat agent, N-2.1 API and accounts | REQ-BE-* and the low-level requirements, IF-101, IF-103, IF-104, IF-201..IF-204, IF-401, IF-402, IF-404, IF-405; step_04 of N-0 | all contract suites of N-2 green on the real side; TC-MIA-002..004, -006, -010, -012, -014, -018, -021..023 | T-06, T-07 |
| T-10 | The example workflows as proof of concept: seed entries lookup, verify, review, search, method transfer; specification, context graph and benchmark each; lookup promoted first | FR-9..FR-13, FR-20, FR-26, NFR-4, AC-2, AC-3, AC-9 | TC-MIA-002 decided on the holdout; the lookup scenario green end to end; review promoted within one month (VAL-002) | T-07, T-09 |
| T-11 | Node cycle N-5 Graph app (add-on, integrated last) | REQ-GA-*, IF-104; step_05 of N-0 | TC-MIA-016 green; contract suite of IF-104 on the real side | T-09 |
| T-12 | Root integration and acceptance: all steps of N-0, system-level tests, benchmarks | TC-MIA-001..029, BM-MIA-001, -002 | all TC-MIA green or deferred with a TD record; benchmarks within budget | T-06..T-11 |
| T-14 | Node requirements into the model: a generated block of `requirement def` for every REQ-id of the nodes (subject, satisfy, allocate to the node's part, a dependency to the parent), checked by the pilot parser | all REQ-* of `nodes/**`; `trace_check.py` | `trace_check.py` reports no error for ids missing in the model; `check_sysml.sh` passes | – |
| T-13 | Housekeeping: the model's subsystem names ResearchSuite and VerificationSuite stay as names of the tool packages; note in the architecture; the HLS section 4 "Agent profile" gets the platform/workflow split | HLS, architecture.sysml | model check and the SysML parser pass | – |

Parallel candidates: T-01, T-02, T-04, T-05 and T-13 are independent. T-06 and T-07 can run in parallel after T-01 and T-03; T-08 can start with T-06 (it only needs the mocks).

## Tasks

### T-01: install the contract drafts and run them
- Implements: IF-101..IF-405 (mock side)
- Green when: all mock-side contract tests green, real side skipped
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: –
- Notes: `! bash tools/install_contract_drafts.sh`, then `bash tools/install_contract_drafts.sh --run`; the agent may not write to the protected folders. After it: protect `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `contracts/`, `stages.yaml`, `decomposition.yaml`.

### T-02: fix the open numbers OPEN-2..OPEN-6 (OPEN-1 and OPEN-3 wait for T-04)
- Implements: TC-MIA-011, -015, -019, -028
- Green when: the owner's answers are in `test-spec.md` and `review-log.md`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: –
- Notes: OPEN-2 (the 0.5 % rate), OPEN-4 (the phone), OPEN-5 (5 s), OPEN-6 (queue length) can be answered now.

### T-03: Red integration tests for the root: step 0 (walking skeleton, lookup on the mocks) and steps 1 to 5
- Implements: TC-MIA-001..029 (system level), AC-9
- Green when: step_00 fails for the right reason (assertion, not import) and is the first green target
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-01
- Notes: Written in a session of their own, not by the implementing session; `tests/integration/N-0/step_00..step_05`. Protected paths: the owner installs them (same route as T-01).

### T-04: Measure today's MIA: first-text time, frame rate, persona dialogues, estimate against measured time of the recorded lookup runs
- Implements: BM-MIA-001, BM-MIA-002, OPEN-1, OPEN-3
- Green when: baselines recorded in `test-spec.md`; OPEN-1 and OPEN-3 can be answered
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: –
- Notes: Needs Ollama and, for the frame rate, the phone (OPEN-4). Spikes, not tests; the numbers become assumptions ASM-nnn.

### T-05: Plausibility record and quality walk for the root and the high-level nodes (people rate, references back the rating)
- Implements: all requirements and assumptions
- Green when: `req_plausibility.py` and `quality_check.py` report no error
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: –
- Notes: The agent proposes references; a person rates (plan-phase rule). `quality.md` exists; the walk against the requirements is done here.

### T-06: Node cycle N-3 Database: N-3.2 Graph tables, N-3.3 Record tables, N-3.1 Storage layer, integration steps 1 to 3
- Implements: REQ-DB-*, IF-102, IF-301, IF-302; step_01 of N-0
- Green when: contract suites of IF-102, IF-301, IF-302 green on the real side; N-3 integration tests green
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-01, T-03
- Notes: Each leaf is planned first (test-spec, plan), then built against the mocks. Order by the record: first in the integration order of N-0.

### T-07: Node cycle N-4 Evaluation and operation: harness, suites, baselines, compose stack, backup, shutdown
- Implements: REQ-OPS-*, NFR-9, FR-17, FR-19; AC-7, AC-29
- Green when: TC-MIA-007 and TC-MIA-029 green on the compose stack with mocks
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-01, T-03
- Notes: The harness features and baselines of `specs/number-gate` (its T-03, T-06, T-11, T-12, T-14) are executed here; that package keeps its folder and numbering.

### T-08: Node cycle N-1 Web Frontend: N-1.3 Voice playback, N-1.2 Character view, N-1.1 Chat and login views
- Implements: REQ-CLV-*, REQ-CHV-*, REQ-VPB-*, IF-111, IF-112; step_03 of N-0
- Green when: browser contract suites green on the real side; TC-MIA-001, -005, -013, -017 on the mocks
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-01, T-03
- Notes: Starts from today's code (`templates/static/chat/*`, `ui/godot`); the node is mostly a refactor to the contracts.

### T-09: Node cycle N-2 Backend: N-2.5 Voice synthesis, N-2.3 Workflow management, N-2.4 Workflow execution (N-2.4.3 Run log, N-2.4.2 Tools and sandbox, N-2.4.1 Pipeline runner), N-2.2 Chat agent, N-2.1 API and accounts
- Implements: REQ-BE-* and the low-level requirements, IF-101, IF-103, IF-104, IF-201..IF-204, IF-401, IF-402, IF-404, IF-405; step_04 of N-0
- Green when: all contract suites of N-2 green on the real side; TC-MIA-002..004, -006, -010, -012, -014, -018, -021..023
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-06, T-07
- Notes: N-2.4 holds the model-dependent parts: the number-gate package (`specs/number-gate`: its T-01, T-08 for the number check tool and the verify entry) runs inside N-2.4.2 and N-2.3. Each low node is planned just in time; the riskiest first.

### T-10: The example workflows as proof of concept: seed entries lookup, verify, review, search, method transfer; specification, context graph and benchmark each; lookup promoted first
- Implements: FR-9..FR-13, FR-20, FR-26, NFR-4, AC-2, AC-3, AC-9
- Green when: TC-MIA-002 decided on the holdout; the lookup scenario green end to end; review promoted within one month (VAL-002)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-07, T-09
- Notes: Workflows are data (D-50): the work is the entries, their specifications and benchmarks, not platform code.

### T-11: Node cycle N-5 Graph app (add-on, integrated last)
- Implements: REQ-GA-*, IF-104; step_05 of N-0
- Green when: TC-MIA-016 green; contract suite of IF-104 on the real side
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-09
- Notes: Independent tool; goes through the backend API; one login.

### T-12: Root integration and acceptance: all steps of N-0, system-level tests, benchmarks
- Implements: TC-MIA-001..029, BM-MIA-001, -002
- Green when: all TC-MIA green or deferred with a TD record; benchmarks within budget
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: T-06..T-11
- Notes: Then Verify (Phase 4) in a fresh context, Commit (5), Deploy (6) with SMOKE-MIA-001..003, Validate (7) with VAL-001..005.

### T-14: Node requirements into the model: a generated block of `requirement def` for every REQ-id of the nodes (subject, satisfy, allocate to the node's part, a dependency to the parent), checked by the pilot parser
- Implements: all REQ-* of `nodes/**`; `trace_check.py`
- Green when: `trace_check.py` reports no error for ids missing in the model; `check_sysml.sh` passes
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: –
- Notes: `trace_check.py` reads only `architecture.sysml`, so the ids of about 340 node requirements are missing there (the example tree of the decomposition skill has the same 65 errors). Generate the block from `requirements.md`, do not write it by hand; the `trace` step joins `stages.yaml` when this is done.

### T-13: Housekeeping: the model's subsystem names ResearchSuite and VerificationSuite stay as names of the tool packages; note in the architecture; the HLS section 4 "Agent profile" gets the platform/workflow split
- Implements: HLS, architecture.sysml
- Green when: model check and the SysML parser pass
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, eval/suites/, eval/baselines/, contracts/ (changes by amendment only)
- Depends on: –
- Notes: Small; can go with any task.
