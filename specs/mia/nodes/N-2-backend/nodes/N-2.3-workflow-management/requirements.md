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

### REQ-WFM-011 – Code checks first
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify as a library entry whose model steps come after every code check that exists for the claim.
- Rationale: refines REQ-BE-046
- Parent: REQ-BE-046
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: in the run log the code checks precede the first model call of each claim
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-012 – Unclear without evidence
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify so that a claim with a number and no evidence gets the verdict unclear without a model call.
- Rationale: refines REQ-BE-047
- Parent: REQ-BE-047
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: for 10 claims with a number and no evidence there are 0 model calls and the verdict is unclear (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-013 – A failed check informs the judge
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify so that a failed code check reaches the judgement step as a contradiction found by code.
- Rationale: refines REQ-BE-048
- Parent: REQ-BE-048
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: the judge input contains the check line (exact); the verdict is the judge's
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-014 – Judgement quality
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow verify so that on the holdout it passes fewer wrong claims than the single voice and loses no more true claims among those with evidence.
- Rationale: refines REQ-BE-049
- Parent: REQ-BE-049
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-2: decided with the rule of the agent-app workflow against the baseline
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-015 – Stable verdicts
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows verify and lookup so that a repeated run on the same input and the same sources gives the same verdicts and the same set of facts.
- Rationale: refines REQ-BE-050
- Parent: REQ-BE-050
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-2: stability limit 0.90 (lower bound of the 95 % interval, at least) on the dev suites (REQ-VER-005, REQ-VER-006)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-016 – Lookup with sources
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow lookup as a library entry that answers a factual question with the sources and verbatim quotes that back it, or with unknown when nothing backs an answer.
- Rationale: refines REQ-BE-051
- Parent: REQ-BE-051
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-017 – Search command
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the search command as a library entry that lists the findings of the metasearch (title, address, short text) without composing or verifying an answer.
- Rationale: refines REQ-BE-052
- Parent: REQ-BE-052
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-23: /search returns the list and starts no pipeline
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-018 – Review report
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow review as a library entry that produces a report of kept and dropped sources with reasons, findings per sub-question with verbatim anchors, conflicts and open gaps.
- Rationale: refines REQ-BE-053
- Parent: REQ-BE-053
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-3: per tier source recall and precision against the baseline
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-019 – Review in time slices
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow review so that it works in time slices, gives an intermediate report with a recommendation at the end of each slice and continues only when the requesting user agrees.
- Rationale: refines REQ-BE-054
- Parent: REQ-BE-054
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: after the first slice (60 s) the run waits for agreement (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-020 – Review stops by a code check
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflow review so that it ends when a code check finds every sub-question answered or a budget is used up.
- Rationale: refines REQ-BE-055
- Parent: REQ-BE-055
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: with a fake model that always says done, the run still continues until the code check holds
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-021 – Source records and cut-off
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows lookup and review so that they record where a source comes from and how far it is trusted, keep the users' edits of that trust and honour a time cut-off strictly.
- Rationale: refines REQ-BE-056
- Parent: REQ-BE-056
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: 0 violations of the cut-off; retracted works are dropped and listed (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-022 – Method transfer
- Level: low   Subject: TaskRuntime
- Text: Where method transfer is switched on, the Workflow management shall deliver the example workflow method_transfer as a library entry that offers few ranked candidate methods marked as hypotheses unless an executable test on a toy instance passed.
- Rationale: refines REQ-BE-057
- Parent: REQ-BE-057
- Priority: Could
- Verification method: Measurement
- Acceptance criterion: AC-26: the known method is in the top 3 on the retro-discovery cases
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-023 – Confidence by code
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows so that confidence figures are computed by tool calls of code from anchored evidence and the limits are reported with every result.
- Rationale: refines REQ-BE-066
- Parent: REQ-BE-066
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: each result shows its limits
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-024 – No invented source
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall deliver the example workflows so that no source appears in an answer that a tool did not retrieve.
- Rationale: refines REQ-BE-067
- Parent: REQ-BE-067
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-3: 0 invented references and 100 % of cited quotes found in their source
- Verified by: –
- Status: Draft
- History: –

### REQ-WFM-025 – State only through the storage interface
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

### REQ-WFM-026 – Workflow and graph API
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
