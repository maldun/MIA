# Requirements: Run log (N-2.4.3, low-2 level)

**Parent:** `specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/requirements.md` (N-2.4)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The log is the source of truth: typed events with a run id, replay and comparison, the step-by-step account. Provides IF-401; consumes IF-102 (storage). Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-LOG-001 – Step-by-step account
- Level: low-2   Subject: Observability
- Text: When a user opens the account of an answer produced by a task, the Run log shall deliver it from event data and without a model-written part.
- Rationale: refines REQ-WFX-001
- Parent: REQ-WFX-001
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-21: the account equals a rendering of the logged events (exact)
- Verified by: TC-LOG-001
- Status: Approved
- History: –

### REQ-LOG-002 – Typed run events
- Level: low-2   Subject: Observability
- Text: The Run log shall write every run as typed, schema-checked events with one run id and the starting user, with secrets removed.
- Rationale: refines REQ-WFX-008
- Parent: REQ-WFX-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4: a secret fed to the writer does not appear in the log (exact); a log with a broken order is reported
- Verified by: TC-LOG-002
- Status: Approved
- History: –

### REQ-LOG-003 – Replay and comparison
- Level: low-2   Subject: Observability
- Text: The Run log shall replay a recorded run offline with an identical result and compare two runs.
- Rationale: refines REQ-WFX-009
- Parent: REQ-WFX-009
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4: replay equals the original (exact)
- Verified by: TC-LOG-003
- Status: Approved
- History: –

### REQ-LOG-004 – Statements traceable to a query
- Level: low-2   Subject: Observability
- Text: The Run log shall make every statement of an answer traceable to the query that found its source.
- Rationale: refines REQ-WFX-010
- Parent: REQ-WFX-010
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-4: on the recorded lookup run 100 % of statements link to a query
- Verified by: TC-LOG-004
- Status: Approved
- History: –

### REQ-LOG-005 – Run events as append-only files, no database driver
- Level: low-2   Subject: Observability
- Text: The Run log shall keep the events of a run as append-only files in its own log folder, shall import no database driver, and shall leave the results of benchmark runs to the storage interface IF-102 (REQ-WFX-022).
- Rationale: narrows REQ-WFX-022 (owner 2026-10-29, D-107): the events of a run are a stream of logs, not the shared state that NFR-8 puts into the database (history, summaries, chat log, feedback, presets, gestures, library entries, accounts); append-only files fit the stream, the replay and the account, and are what the tools read today
- Parent: REQ-WFX-022
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: no database driver is imported by the code of the Run log or outside the storage client; the events of a run are appended to a file of the log folder and none is rewritten (exact)
- Verified by: TC-LOG-005
- Status: Approved
- History: A-28 reworded (was: run events and run results only through the storage interface IF-102)


## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-401 – Run event log
- Level: low-2   Subject: Observability
- Text: The Run log shall provide the Pipeline runner and the Tools and sandbox with the event interface IF-401 as specified in contracts/IF-401-run-events.md (emit a typed event of a run, read the events of a run in order, the step-by-step account, the comparison of two runs).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-WFX-008, REQ-WFX-009
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4, AC-21: the contract suite test_if_401_run_events.py passes against the mock (stage 1) and the Run log (stage 2)
- Verified by: TC-IF-401-01..04
- Status: Approved
- History: v0, amendment 5/7 (2026-10-25)
