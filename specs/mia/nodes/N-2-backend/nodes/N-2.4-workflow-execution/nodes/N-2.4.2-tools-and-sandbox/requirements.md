# Requirements: Tools and sandbox (N-2.4.2, low-2 level)

**Parent:** `specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/requirements.md` (N-2.4)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The tools that any workflow can call, each counted against the budgets of the run and marked with the trust of its output: the code checks (number, quote, schema), web search and fetch, scholarly sources and source records, and the sandbox for model-written scripts. Provides IF-402; consumes IF-401, IF-404 (web) and IF-405 (scholarly sources). Knows no particular workflow. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-TLS-001 – Code checks first
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall offer the code checks number_check, quote_in_source and schema_check as tools for every workflow.
- Rationale: refines REQ-WFX-005
- Parent: REQ-WFX-005
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: in the run log the code checks precede the first model call of each claim
- Verified by: TC-TLS-001
- Status: Approved
- History: –

### REQ-TLS-002 – Lookup with sources
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall offer the tools web_search and fetch_passages (findings with title, address and short text; passages with verbatim quotes) for every workflow.
- Rationale: refines REQ-WFX-006
- Parent: REQ-WFX-006
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown
- Verified by: TC-TLS-002
- Status: Approved
- History: –

### REQ-TLS-003 – Source records and cut-off
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall offer the tools scholar_search and source_record, which return one record format with the origin, the trust class, the retraction state and a strictly applied date cut-off.
- Rationale: refines REQ-WFX-007
- Parent: REQ-WFX-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: 0 violations of the cut-off; retracted works are dropped and listed (exact)
- Verified by: TC-TLS-003
- Status: Approved
- History: –

### REQ-TLS-004 – Untrusted text is data
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall treat text from the web, papers, PDFs and users as data and never as instruction.
- Rationale: refines REQ-WFX-014
- Parent: REQ-WFX-014
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: injected instructions change no verdict and start no tool (red-team cases)
- Verified by: TC-TLS-004
- Status: Approved
- History: –

### REQ-TLS-005 – Sandbox or refuse
- Level: low-2   Subject: VerificationSuite
- Text: If no isolating sandbox is present, then the Tools and sandbox shall refuse to run a model-written script or a hostile document.
- Rationale: refines REQ-WFX-015
- Parent: REQ-WFX-015
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: with the sandbox removed script checks report unavailable and nothing runs (exact)
- Verified by: TC-TLS-005
- Status: Approved
- History: –

### REQ-TLS-006 – No invented source
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall return every fetched passage with its source reference, so that the quote check compares the quote with the source text.
- Rationale: refines REQ-WFX-016
- Parent: REQ-WFX-016
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-3: 0 invented references and 100 % of cited quotes found in their source
- Verified by: TC-TLS-006
- Status: Approved
- History: –

### REQ-TLS-007 – Only queries leave the host
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall send off the host only the text of a web or scholarly query and, if configured, an e-mail address.
- Rationale: refines REQ-WFX-017
- Parent: REQ-WFX-017
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-5: the web log lists every query that left the machine
- Verified by: TC-TLS-007
- Status: Approved
- History: –

### REQ-TLS-008 – Budget and trust label per tool call
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall count every tool call against the budgets of the run and mark the output of a tool with its trust (data from code, data from the web, data from a model).
- Rationale: refines REQ-WFX-014, REQ-WFX-019
- Parent: REQ-WFX-014, REQ-WFX-019
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: a call over the budget is refused with the budget named; every output carries its trust label
- Verified by: TC-TLS-008
- Status: Approved
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-402 – Tool calls
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall provide the Pipeline runner with the tool interface IF-402 as specified in contracts/IF-402-tool-calls.md (call a tool by name with arguments under the budgets of a run: number_check, quote_in_source, schema_check, run_script, web_search, fetch_passages, scholar_search, source_record).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-WFX-005, REQ-WFX-014, REQ-WFX-015
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2, AC-5, AC-6: the contract suite test_if_402_tool_calls.py passes against the mock (stage 1) and the Tools and sandbox (stage 2)
- Verified by: TC-IF-402-01..05
- Status: Approved
- History: v0, amendment 5/7 (2026-10-25)

### IF-404 – Web search and fetch (external)
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall use the open web only through the interface IF-404 as specified in contracts/IF-404-web.md (search and fetch; private addresses, odd ports and unsupported content are refused).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-WFX-017, REQ-WFX-014
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-5, AC-6: the contract suite test_if_404_web.py passes against the mock (stage 1) and the real web client with SearXNG (stage 2)
- Verified by: TC-IF-404-01..04
- Status: Approved
- History: v0, amendment 5/7 (2026-10-25)

### IF-405 – Scholarly sources (external)
- Level: low-2   Subject: VerificationSuite
- Text: The Tools and sandbox shall use scholarly sources only through the interface IF-405 as specified in contracts/IF-405-scholarly-sources.md (search with a strict date cut-off, one record format, retraction state, errors of single sources listed).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-WFX-007, REQ-WFX-017
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: the contract suite test_if_405_scholarly_sources.py passes against the mock (stage 1) and the real APIs (stage 2)
- Verified by: TC-IF-405-01..04
- Status: Approved
- History: v0, amendment 5/7 (2026-10-25)
