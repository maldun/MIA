# Requirements: Operation (N-4.2, low level)

**Parent:** `specs/mia/nodes/N-4-evaluation-operation/requirements.md` (N-4)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

Installing, configuring, starting and stopping MIA: the compose stack with one container per node, the configuration file and its report, the first account, orderly shutdown, backup and restore, private access, the licence, the runbook. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-OPR-001 – One file, one command
- Level: low   Subject: OperationLayer
- Text: When the owner runs the start command on a fresh checkout with one configuration file, the Operation shall bring MIA up with its database.
- Rationale: refines REQ-OPS-007
- Parent: REQ-OPS-007
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-7: a fresh checkout starts to a working chat in the compose stack
- Verified by: TC-OPR-001
- Status: Verified
- History: –

### REQ-OPR-002 – First account at installation
- Level: low   Subject: OperationLayer
- Text: When MIA starts for the first time, the Operation shall let the owner create the first account.
- Rationale: refines REQ-OPS-008
- Parent: REQ-OPS-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: the first start offers the account creation exactly once
- Verified by: TC-OPR-002
- Status: Verified
- History: –

### REQ-OPR-003 – Missing options reported
- Level: low   Subject: OperationLayer
- Text: When MIA starts after an update, the Operation shall report the options missing in the configuration file.
- Rationale: refines REQ-OPS-009
- Parent: REQ-OPS-009
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: removing 2 options gives a report naming both (exact)
- Verified by: TC-OPR-003
- Status: Verified
- History: –

### REQ-OPR-004 – Orderly shutdown
- Level: low   Subject: OperationLayer
- Text: When MIA is stopped, the Operation shall shut it down in order and save her memory.
- Rationale: refines REQ-OPS-010
- Parent: REQ-OPS-010
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: after SIGTERM the history and memory are saved (exact)
- Verified by: TC-OPR-004
- Status: Verified
- History: –

### REQ-OPR-005 – Backup and restore of all data
- Level: low   Subject: OperationLayer
- Text: The Operation shall back up and restore the data of MIA including the database.
- Rationale: refines REQ-OPS-011
- Parent: REQ-OPS-011
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-7: backup, wipe and restore return the same data (exact)
- Verified by: TC-OPR-005
- Status: Verified
- History: –

### REQ-OPR-006 – Runbook
- Level: low   Subject: OperationLayer
- Text: The Operation shall provide a runbook with start, update of the model pins, backup and restore of the database, and a retirement plan that ends in freezing the stack with the model digests.
- Rationale: refines REQ-OPS-012
- Parent: REQ-OPS-012
- Priority: Should
- Verification method: Inspection
- Acceptance criterion: AC-7: the runbook steps are run once on a clean machine
- Verified by: TC-OPR-006
- Status: Verified
- History: –

### REQ-OPR-007 – Compose stack
- Level: low   Subject: OperationLayer
- Text: The Operation shall provide a compose stack that starts the containers of N-2 (`mia`), N-3 (`db`) and N-5 (`graph`) alone and together with one configuration file.
- Rationale: refines REQ-OPS-013; N-4 has no container of its own, the evaluation runs as a command in the mia image (D-127)
- Parent: REQ-OPS-013
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-29: each container starts alone against the mocks; all start together
- Verified by: TC-OPR-007
- Status: Verified
- History: 2026-10-31 A-37 (D-127): the containers named (was "the containers of N-2 to N-5")

### REQ-OPR-008 – Private access only
- Level: low   Subject: OperationLayer
- Text: The Operation shall expose MIA only over HTTPS inside the home network or the tailnet, with no public port.
- Rationale: refines REQ-OPS-014
- Parent: REQ-OPS-014
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-14: a port scan from outside the network finds nothing open; tailscale funnel is not used
- Verified by: TC-OPR-008
- Status: Verified
- History: –

### REQ-OPR-009 – Free and open
- Level: low   Subject: OperationLayer
- Text: The Operation shall provide the licence GPL-3.0-or-later and use no paid API.
- Rationale: refines REQ-OPS-015
- Parent: REQ-OPS-015
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: licence file present; no paid API host in the web log
- Verified by: TC-OPR-009
- Status: Verified
- History: –

### REQ-OPR-010 – Hardware configuration
- Level: low   Subject: OperationLayer
- Text: The Operation shall configure the model server to load one model at a time.
- Rationale: refines REQ-OPS-016
- Parent: REQ-OPS-016
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-19: OLLAMA_MAX_LOADED_MODELS equals 1 (exact)
- Verified by: TC-OPR-010
- Status: Verified
- History: –

## Iteration 4 (goal G-V4.VIEW, graph viewer and the IF-104 v2 backend; moved at the merge 2026-11-25)
Requirements of the subgoal G-V4.VIEW (goal record `specs/mia/goals/G-V4.VIEW/`: plan, test requirements TR-VIEW-001 to 021, verification report). Verified 2026-11-24 (both boxes ticked by the owner); Verify findings decided in D-501: V-1, V-2, V-4, V-5, V-8, V-9, V-10, V-13 fixed, V-15 closed by the owner's image build, V-3 handed to G-V4.GRAPHSTORE.TRANSFER, V-6, V-7, V-11, V-12, V-14 accepted; the specification points of the merge in D-502. The routes are offered through IF-104 v2 (`contracts/`, A-171, A-174), the record tables through IF-302 v15 (A-172).

Terms (store setting, owner, record of changes, entry, what cannot be drawn): see the section "Terms of G-V4.VIEW" in `specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/requirements.md`.

## Groups of G-V4.VIEW
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | SA | Store and setting: which store is read, how it is chosen, the image (HR-004, D-430 (6), (9), D-460) | REQ-OPR-011 |

### REQ-OPR-011 – Database driver in the release image
- Level: low   Subject: OperationLayer
- Group: SA
- Text: The Operation shall build the release image with the packages of `requirements-db.txt`, so that the PostgreSQL store opens from the image.
- Rationale: D-430 (9); the image of v0.2.1 has no psycopg (CORE deployment finding, handover section 5)
- Parent: HR-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: in the built image `import psycopg` succeeds and the IF-104 v2 store route answers `database` against the owner's database (exact)
- Verified by: TC-OPR-011, SMOKE-VIEW-001
- Status: Verified
- History: G-V4.VIEW Plan step 1b, 2026-11-22, new (Track A; basis: IF-104 v2 A-171, IF-302 v15 A-172, prototype round 02 R5); verified (G-V4.VIEW verification report, both boxes ticked by the owner 2026-11-24) and moved here from `specs/mia/goals/G-V4.VIEW/requirements.md` at the merge (plan.md, "At the merge").
