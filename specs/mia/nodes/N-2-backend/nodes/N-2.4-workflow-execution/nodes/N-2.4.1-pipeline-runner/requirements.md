# Requirements: Pipeline runner (N-2.4.1, low-2 level)

**Parent:** `specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/requirements.md` (N-2.4)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

Runs a workflow step by step under budgets: model calls and model management, priority of the chat, learning choices. Provides IF-202; consumes IF-203 (the workflow), IF-103 (model server), IF-401 (events) and IF-402 (tools). A hub by nature: every step of a workflow passes it. Knows no particular workflow. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-RUN-001 – Internet tasks only on command
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall start a task that reaches the internet only by a command of a user.
- Rationale: refines REQ-WFX-002
- Parent: REQ-WFX-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: a chat message alone starts no internet task (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-002 – Switch the model
- Level: low-2   Subject: TaskRuntime
- Text: When a user asks for the light or the full model and confirms, the Pipeline runner shall switch the model for all users and free GPU memory on request.
- Rationale: refines REQ-WFX-003
- Parent: REQ-WFX-003
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-23: /light! and /full! switch after confirmation; memory is freed on request
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-003 – Model server unreachable
- Level: low-2   Subject: TaskRuntime
- Text: If the model server is unreachable, then the Pipeline runner shall say so in plain words.
- Rationale: refines REQ-WFX-004
- Parent: REQ-WFX-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: with the fake server down the user gets the plain message (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-004 – Optional learning
- Level: low-2   Subject: TaskRuntime
- Text: Where learning is switched on, the Pipeline runner shall learn only from logged signals in discrete choices of configuration and graph weights and log every learned choice next to the default.
- Rationale: refines REQ-WFX-011
- Parent: REQ-WFX-011
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-22: a learned choice is logged with the default and can be switched off and reversed
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-005 – Context window share
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall keep every model input inside 50 % of the context window.
- Rationale: refines REQ-WFX-012
- Parent: REQ-WFX-012
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: over the lookup suites 100 % of inputs are at most 4096 tokens at num_ctx 8192
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-006 – Model calls of the first try
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall use fewer than 15 model calls for the first try of a question on the light model.
- Rationale: refines REQ-WFX-013
- Parent: REQ-WFX-013
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-22: on the lookup suites the maximum is below 15
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-007 – First text in 10 seconds
- Level: low-2   Subject: TaskRuntime
- Text: When a chat message is answered on the light model, the Pipeline runner shall send the first text within 10 s.
- Rationale: refines REQ-WFX-018
- Parent: REQ-WFX-018
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-19: median over 20 runs is within 10 s, also while a review slice runs
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-008 – Budgets and what is missing
- Level: low-2   Subject: TaskRuntime
- Text: If a task exceeds a budget of steps, seconds, calls or tokens, then the Pipeline runner shall end it with what it has and say what is missing.
- Rationale: refines REQ-WFX-019
- Parent: REQ-WFX-019
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: each of the four budgets ends a scripted run with a message naming it
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-009 – Chat before background
- Level: low-2   Subject: TaskRuntime
- Text: While a chat message waits, the Pipeline runner shall let a long background task yield the model server.
- Rationale: refines REQ-WFX-020
- Parent: REQ-WFX-020
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: with a review slice running a chat message gets its first text within 10 s
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-010 – One model at a time
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall use one language model at a time on the 16 GB GPU and serve several users by the queue.
- Rationale: refines REQ-WFX-021
- Parent: REQ-WFX-021
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: two simultaneous messages are answered one after the other
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-011 – Use IF-103 only
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall use the model server only through the interface IF-103 as specified in contracts/IF-103-model-server.md.
- Rationale: refines REQ-WFX-023
- Parent: REQ-WFX-023
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: the contract suite test_if_103_model_server.py passes against the Workflow execution (stage 2)
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-012 – Use the library, the tools and the log only through their interfaces
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall fetch a workflow only through IF-203, call tools only through IF-402 and write events only through IF-401.
- Rationale: refines REQ-WFX-019
- Parent: REQ-WFX-019
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-1: with the mocks of the three interfaces a scripted workflow runs end to end; no other import exists
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-013 – Know no particular workflow
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall run any valid workflow of the library without code that names one workflow.
- Rationale: refines REQ-WFX-023
- Parent: REQ-WFX-023
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-9: the lookup, verify and review entries run with the same runner; a new valid entry runs without a change of code
- Verified by: –
- Status: Draft
- History: –

### REQ-RUN-014 – Realise IF-202
- Level: low-2   Subject: TaskRuntime
- Text: The Pipeline runner shall realise the interface IF-202 of the Workflow execution as specified in contracts/IF-202-run-workflow.md.
- Rationale: refines IF-202
- Parent: IF-202
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19, AC-28: the contract suite test_if_202_run_workflow.py passes against the Pipeline runner (stage 2)
- Verified by: –
- Status: Draft
- History: –
