# Requirements: Workflow execution (N-2.4, low level)

**Parent:** `specs/mia/nodes/N-2-backend/requirements.md` (N-2)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

Running a workflow under budgets: the pipeline runner, model management, verification, research, sandbox, run log and replay. Provides IF-202 and IF-105; consumes IF-103 (model server), IF-203 (the workflow to run) and IF-102 (run results). Expected to be cut again (runtime, verification, research, run log) when its turn comes. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-WFX-001 – Step-by-step account
- Level: low   Subject: TaskRuntime
- Text: When a user opens the account of an answer produced by a task, the Workflow execution shall deliver it from event data and without a model-written part.
- Rationale: refines REQ-BE-020
- Parent: REQ-BE-020
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-21: the account equals a rendering of the logged events (exact)
- Verified by: TC-LOG-001, TC-N24-001
- Status: Draft
- History: –

### REQ-WFX-002 – Internet tasks only on command
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall start a task that reaches the internet only by a command of a user.
- Rationale: refines REQ-BE-034
- Parent: REQ-BE-034
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: a chat message alone starts no internet task (exact)
- Verified by: TC-RUN-001, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-003 – Switch the model
- Level: low   Subject: TaskRuntime
- Text: When a user asks for the light or the full model and confirms, the Workflow execution shall switch the model for all users and free GPU memory on request.
- Rationale: refines REQ-BE-044
- Parent: REQ-BE-044
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-23: /light! and /full! switch after confirmation; memory is freed on request
- Verified by: TC-RUN-002, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-004 – Model server unreachable
- Level: low   Subject: TaskRuntime
- Text: If the model server is unreachable, then the Workflow execution shall say so in plain words.
- Rationale: refines REQ-BE-045
- Parent: REQ-BE-045
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: with the fake server down the user gets the plain message (exact)
- Verified by: TC-RUN-003, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-005 – Code checks first
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall offer the code checks number_check, quote_in_source and schema_check as tools for every workflow.
- Rationale: refines REQ-BE-046
- Parent: REQ-BE-046
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: in the run log the code checks precede the first model call of each claim
- Verified by: TC-TLS-001, TC-N24-002
- Status: Draft
- History: –

### REQ-WFX-006 – Lookup with sources
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall offer the tools web_search and fetch_passages (findings with title, address and short text; passages with verbatim quotes) for every workflow.
- Rationale: refines REQ-BE-051
- Parent: REQ-BE-051
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown
- Verified by: TC-TLS-002, TC-N24-002
- Status: Draft
- History: –

### REQ-WFX-007 – Source records and cut-off
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall offer the tools scholar_search and source_record, which return one record format with the origin, the trust class, the retraction state and a strictly applied date cut-off.
- Rationale: refines REQ-BE-056
- Parent: REQ-BE-056
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: 0 violations of the cut-off; retracted works are dropped and listed (exact)
- Verified by: TC-TLS-003, TC-N24-002
- Status: Draft
- History: –

### REQ-WFX-008 – Typed run events
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall write every run as typed, schema-checked events with one run id and the starting user, with secrets removed.
- Rationale: refines REQ-BE-058
- Parent: REQ-BE-058
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4: a secret fed to the writer does not appear in the log (exact); a log with a broken order is reported
- Verified by: TC-LOG-002, TC-N24-001
- Status: Draft
- History: –

### REQ-WFX-009 – Replay and comparison
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall replay a recorded run offline with an identical result and compare two runs.
- Rationale: refines REQ-BE-059
- Parent: REQ-BE-059
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4: replay equals the original (exact)
- Verified by: TC-LOG-003, TC-N24-001
- Status: Draft
- History: –

### REQ-WFX-010 – Statements traceable to a query
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall make every statement of an answer traceable to the query that found its source.
- Rationale: refines REQ-BE-060
- Parent: REQ-BE-060
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-4: on the recorded lookup run 100 % of statements link to a query
- Verified by: TC-LOG-004, TC-N24-001
- Status: Draft
- History: –

### REQ-WFX-011 – Optional learning
- Level: low   Subject: TaskRuntime
- Text: Where learning is switched on, the Workflow execution shall learn only from logged signals in discrete choices of configuration and graph weights and log every learned choice next to the default.
- Rationale: refines REQ-BE-061
- Parent: REQ-BE-061
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-22: a learned choice is logged with the default and can be switched off and reversed
- Verified by: TC-RUN-004, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-012 – Context window share
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall keep every model input inside 50 % of the context window.
- Rationale: refines REQ-BE-062
- Parent: REQ-BE-062
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: over the lookup suites 100 % of inputs are at most 4096 tokens at num_ctx 8192
- Verified by: TC-RUN-005, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-013 – Model calls of the first try
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall use fewer than 15 model calls for the first try of a question on the light model.
- Rationale: refines REQ-BE-063
- Parent: REQ-BE-063
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-22: on the lookup suites the maximum is below 15
- Verified by: TC-RUN-006, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-014 – Untrusted text is data
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall treat text from the web, papers, PDFs and users as data and never as instruction.
- Rationale: refines REQ-BE-064
- Parent: REQ-BE-064
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: injected instructions change no verdict and start no tool (red-team cases)
- Verified by: TC-TLS-004, TC-TLS-008, TC-N24-002
- Status: Draft
- History: –

### REQ-WFX-015 – Sandbox or refuse
- Level: low   Subject: TaskRuntime
- Text: If no isolating sandbox is present, then the Workflow execution shall refuse to run a model-written script or a hostile document.
- Rationale: refines REQ-BE-065
- Parent: REQ-BE-065
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: with the sandbox removed script checks report unavailable and nothing runs (exact)
- Verified by: TC-TLS-005, TC-N24-002
- Status: Draft
- History: –

### REQ-WFX-016 – No invented source
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall return every fetched passage with its source reference, so that the quote check compares the quote with the source text.
- Rationale: refines REQ-BE-067
- Parent: REQ-BE-067
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-3: 0 invented references and 100 % of cited quotes found in their source
- Verified by: TC-TLS-006, TC-N24-002
- Status: Draft
- History: –

### REQ-WFX-017 – Only queries leave the host
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall send off the host only the text of a web or scholarly query and, if configured, an e-mail address.
- Rationale: refines REQ-BE-068
- Parent: REQ-BE-068
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-5: the web log lists every query that left the machine
- Verified by: TC-TLS-007, TC-N24-002
- Status: Draft
- History: –

### REQ-WFX-018 – First text in 10 seconds
- Level: low   Subject: TaskRuntime
- Text: When a chat message is answered on the light model, the Workflow execution shall send the first text within 10 s.
- Rationale: refines REQ-BE-069
- Parent: REQ-BE-069
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-19: median over 20 runs is within 10 s, also while a review slice runs
- Verified by: TC-RUN-007, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-019 – Budgets and what is missing
- Level: low   Subject: TaskRuntime
- Text: If a task exceeds a budget of steps, seconds, calls or tokens, then the Workflow execution shall end it with what it has and say what is missing.
- Rationale: refines REQ-BE-070
- Parent: REQ-BE-070
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: each of the four budgets ends a scripted run with a message naming it
- Verified by: TC-RUN-008, TC-RUN-012, TC-TLS-008, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-020 – Chat before background
- Level: low   Subject: TaskRuntime
- Text: While a chat message waits, the Workflow execution shall let a long background task yield the model server.
- Rationale: refines REQ-BE-071
- Parent: REQ-BE-071
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: with a review slice running a chat message gets its first text within 10 s
- Verified by: TC-RUN-009, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-021 – One model at a time
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall use one language model at a time on the 16 GB GPU and serve several users by the queue.
- Rationale: refines REQ-BE-072
- Parent: REQ-BE-072
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: two simultaneous messages are answered one after the other
- Verified by: TC-RUN-010, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-022 – State only through the storage interface
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall store run results only through the storage interface IF-102.
- Rationale: refines REQ-BE-074
- Parent: REQ-BE-074
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: no database driver is imported outside the storage client
- Verified by: TC-LOG-005, TC-N24-001
- Status: Draft
- History: –

### REQ-WFX-023 – Use IF-103 only
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall use the model server only through the interface IF-103 as specified in contracts/IF-103-model-server.md.
- Rationale: refines IF-103
- Parent: IF-103
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: the contract suite test_if_103_model_server.py passes against the Workflow execution (stage 2)
- Verified by: TC-RUN-011, TC-RUN-013, TC-N24-003
- Status: Draft
- History: –

### REQ-WFX-024 – Realise IF-105
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall realise the evaluation interface IF-105 as specified in contracts/IF-105-evaluation-access.md by running a case through the same runner as IF-202, recording the model pin, seed and temperature in the run_start event and returning the cost.
- Rationale: refines IF-105
- Parent: IF-105
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2, AC-8: the contract suite test_if_105_evaluation_access.py passes against the Workflow execution (stage 2)
- Verified by: TC-RUN-015, TC-N24-003
- Status: Draft
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-202 – Run a workflow
- Level: low   Subject: TaskRuntime
- Text: The Workflow execution shall provide the Chat agent and the Workflow management with the run interface IF-202 as specified in contracts/IF-202-run-workflow.md (run a workflow version under a budget, the stream of run events, the end with what is missing, and the measured costs of a node).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-BE-070, REQ-BE-042
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19, AC-28: the contract suite test_if_202_run_workflow.py passes against the mock (stage 1) and the Workflow execution (stage 2)
- Verified by: TC-IF-202-01..05, TC-RUN-014, TC-N24-003
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)
