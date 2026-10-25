# Requirements: Workflow management (N-2.3, low level)

**Parent:** `specs/mia/nodes/N-2-backend/requirements.md` (N-2)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The library of workflows and skills as versioned data, the graph rules, specification and benchmark records, context graphs, schedule and estimate, character variants. Provides IF-203; consumes IF-202 (measured costs) and IF-102. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-WFM-001 – Skills as tasks
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall perform each kind of work as a task defined by a skill file and a pipeline selectable by every user.
- Rationale: refines REQ-BE-033
- Parent: REQ-BE-033
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: the selectable list shows each skill; a selected skill runs its pipeline
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-002 – Versioned workflow library
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep every pipeline and workflow as validated data in a library with the lifecycle draft, tested, trusted and retired and store every edit as a new immutable version with author and time.
- Rationale: refines REQ-BE-035
- Parent: REQ-BE-035
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10, AC-16: an edit creates version n+1 and leaves version n unchanged (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-003 – No cycles
- Level: low   Subject: TaskRuntime
- Text: When a workflow is saved and before it runs, the Workflow management shall check by an algorithm that its graph has no cycle and name a cycle that it finds.
- Rationale: refines REQ-BE-036
- Parent: REQ-BE-036
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: a workflow with a cycle is refused with the cycle named; property test on generated graphs: every accepted graph has a topological order
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-004 – Graph rules
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall refuse a workflow with two adjacent data nodes or a session node without a maximum number of cycles or a maximum time.
- Rationale: refines REQ-BE-037
- Parent: REQ-BE-037
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: each of the three violations is refused with the rule named (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-005 – Model proposals stay drafts
- Level: low   Subject: TaskRuntime
- Text: When a model proposes a library entry, the Workflow management shall keep it as a draft until a user approves it, shown as a diff and tried on the test set.
- Rationale: refines REQ-BE-038
- Parent: REQ-BE-038
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: a proposed entry has status draft and cannot be run as trusted
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-006 – Specification before trust
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep a workflow without specification, context graph and benchmark with a baseline in draft status and refuse to promote it.
- Rationale: refines REQ-BE-039
- Parent: REQ-BE-039
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: promotion of a workflow lacking any of the three is refused (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-007 – Time from idea to promotion
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall record the time from the idea of a skill to its promotion.
- Rationale: refines REQ-BE-040
- Parent: REQ-BE-040
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-9: the record has two time stamps for each promoted skill
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-008 – Context graphs
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep one context graph per workflow and one for the chat and give each step the view that fits its token budget.
- Rationale: refines REQ-BE-041
- Parent: REQ-BE-041
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: the view of a step stays within its budget in tokens (exact on the recorded lookup run)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-009 – Workflow schedule and estimate
- Level: low   Subject: TaskRuntime
- Text: When a workflow is about to run, the Workflow management shall compute its order, critical path and an estimate of time, calls and tokens from its graph and the measured costs, and refuse a run whose estimate exceeds its budget.
- Rationale: refines REQ-BE-042
- Parent: REQ-BE-042
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-28: on the recorded lookup runs the estimate is within the factor set in Plan of the measured time
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-010 – Character variant per workflow
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall let a workflow name a character variant and send it to the frontend while the workflow runs.
- Rationale: refines REQ-BE-043
- Parent: REQ-BE-043
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-17: a run with a variant sends the variant name; a run without sends none
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-011 – State only through the storage interface
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall keep and read workflows and context graphs only through the storage interface IF-102.
- Rationale: refines REQ-BE-074
- Parent: REQ-BE-074
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: no database driver is imported outside the storage client
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-012 – Workflow and graph API
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall list, read, save as a new version, show the history and diff of, and restore workflows and context graphs through IF-203, and refuse an invalid graph with the broken rule named.
- Rationale: refines REQ-BE-076
- Parent: REQ-BE-076
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: with the fake storage each of the six operations works; an invalid graph is refused with the rule named (exact)
- Verified by: –
- Status: Draft
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-203 – Workflow library
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall provide the API and accounts, the Chat agent and the Workflow execution with the library interface IF-203 as specified in contracts/IF-203-workflow-library.md (list, read, save as a new version, history, diff, restore, the lifecycle status, and the estimate of a run).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-BE-035, REQ-BE-076
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10, AC-16, AC-28: the contract suite test_if_203_workflow_library.py passes against the mock (stage 1) and the Workflow management (stage 2)
- Verified by: TC-IF-203-01..04
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)
