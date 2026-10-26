# Requirements: API and accounts (N-2.1, low level)

**Parent:** `specs/mia/nodes/N-2-backend/requirements.md` (N-2)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The gateway of the Backend: the Socket.IO and REST surface (IF-101, IF-104), accounts and sessions, the delivery of the frontend files, the broadcast to all devices. Calls the chat agent (IF-201) and the workflow library (IF-203); keeps accounts through IF-102. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-API-001 – Chat events and streaming
- Level: low   Subject: WebApplication
- Text: When a logged-in user sends a message, the API and accounts shall hand it to the chat agent through IF-201 and relay the events of the answer to every connected browser (IF-101).
- Rationale: refines REQ-BE-001
- Parent: REQ-BE-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the fake model each scripted answer arrives as ordered sentences
- Verified by: TC-API-001
- Status: Approved
- History: –

### REQ-API-002 – Changes reach all devices
- Level: low   Subject: WebApplication
- Text: When shared data changes in the Database, the API and accounts shall push the change to every connected device through IF-101.
- Rationale: refines REQ-BE-007
- Parent: REQ-BE-007
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a change by one user is visible on a second connection within 5 s with its author
- Verified by: TC-API-002
- Status: Approved
- History: –

### REQ-API-003 – Login and session
- Level: low   Subject: WebApplication
- Text: When a user gives the correct account and password, the API and accounts shall open a session for that device.
- Rationale: refines REQ-BE-008
- Parent: REQ-BE-008
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: correct credentials open a session; wrong ones do not (exact)
- Verified by: TC-API-003
- Status: Approved
- History: –

### REQ-API-004 – Throttled failed logins
- Level: low   Subject: WebApplication
- Text: If more than 5 logins fail within one minute for an account, then the API and accounts shall refuse further logins for that account until the minute has passed.
- Rationale: refines REQ-BE-009
- Parent: REQ-BE-009
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: the sixth failed attempt within a minute is refused even with the right password (exact)
- Verified by: TC-API-004
- Status: Approved
- History: –

### REQ-API-005 – Password handling
- Level: low   Subject: WebApplication
- Text: The API and accounts shall store only salted slow hashes of passwords and write no password to any log.
- Rationale: refines REQ-BE-010
- Parent: REQ-BE-010
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-14: a search of the database and all logs after 10 logins finds no password (exact)
- Verified by: TC-API-005
- Status: Approved
- History: –

### REQ-API-006 – Own password and owner-only accounts
- Level: low   Subject: WebApplication
- Text: The API and accounts shall let a user change their own password and let only the owner create an account.
- Rationale: refines REQ-BE-011
- Parent: REQ-BE-011
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: a non-owner's create request is refused (exact)
- Verified by: TC-API-006
- Status: Approved
- History: –

### REQ-API-007 – Every request authenticated
- Level: low   Subject: WebApplication
- Text: The API and accounts shall authenticate every request by an account, check the origin and limit message rates per user.
- Rationale: refines REQ-BE-012
- Parent: REQ-BE-012
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: a request without a session is refused; a foreign origin is refused; the rate limit value is set in Plan
- Verified by: TC-API-007
- Status: Approved
- History: –

### REQ-API-008 – Passwords only over a secure channel
- Level: low   Subject: WebApplication
- Text: If a password arrives over plain HTTP from an address other than localhost, then the API and accounts shall refuse it.
- Rationale: refines REQ-BE-013
- Parent: REQ-BE-013
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: plain HTTP from a LAN address is refused (exact)
- Verified by: TC-API-008
- Status: Approved
- History: –

### REQ-API-009 – Attribution of changes
- Level: low   Subject: WebApplication
- Text: When shared data changes, the API and accounts shall record the account that made the change.
- Rationale: refines REQ-BE-014
- Parent: REQ-BE-014
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: 100 % of changes in a scripted session carry the account
- Verified by: TC-API-009
- Status: Approved
- History: –

### REQ-API-010 – Everything visible to all users
- Level: low   Subject: WebApplication
- Text: The API and accounts shall give every logged-in user the same access to all data and apply a change to all users at once, without roles.
- Rationale: refines REQ-BE-015
- Parent: REQ-BE-015
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-20: a second user sees and changes a first user's workflow, preset and persona
- Verified by: TC-API-010
- Status: Approved
- History: –

### REQ-API-011 – Python versions
- Level: low   Subject: WebApplication
- Text: The Backend shall run every one of its parts on Python 3.12.
- Rationale: refines REQ-BE-073
- Parent: REQ-BE-073
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-20: the unit tests pass on 3.12 (exact)
- Verified by: TC-API-011
- Status: Approved
- History: –

### REQ-API-012 – State only through the storage interface
- Level: low   Subject: WebApplication
- Text: The API and accounts shall keep and read accounts only through the storage interface IF-102.
- Rationale: refines REQ-BE-074
- Parent: REQ-BE-074
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: no database driver is imported outside the storage client
- Verified by: TC-API-012
- Status: Approved
- History: –

### REQ-API-013 – Serve the frontend
- Level: low   Subject: WebApplication
- Text: The API and accounts shall serve the files of the Web Frontend and run in the Backend container.
- Rationale: refines REQ-BE-075
- Parent: REQ-BE-075
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: the container starts alone against the mocks and serves the chat page
- Verified by: TC-API-013
- Status: Approved
- History: –

### REQ-API-014 – Workflow and graph API
- Level: low   Subject: WebApplication
- Text: The API and accounts shall route the requests of IF-104 under the session of the Backend to the workflow library through IF-203.
- Rationale: refines REQ-BE-076
- Parent: REQ-BE-076
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: with the fake storage each of the six operations works; an invalid graph is refused with the rule named (exact)
- Verified by: TC-API-014
- Status: Approved
- History: –

### REQ-API-015 – Realise IF-101
- Level: low   Subject: WebApplication
- Text: The API and accounts shall realise the interface IF-101 of the Backend as specified in contracts/IF-101-chat-api.md.
- Rationale: refines IF-101
- Parent: IF-101
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1, AC-14: the contract suite test_if_101_chat_api.py passes against the API and accounts (stage 2)
- Verified by: TC-API-015
- Status: Approved
- History: –

### REQ-API-016 – Realise the routes of IF-104
- Level: low   Subject: WebApplication
- Text: The API and accounts shall realise the routes of the interface IF-104 of the Backend as specified in contracts/IF-104-graph-api.md.
- Rationale: refines IF-104
- Parent: IF-104
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16: the contract suite test_if_104_graph_api.py passes against the API and accounts (stage 2)
- Verified by: TC-API-016
- Status: Approved
- History: –
