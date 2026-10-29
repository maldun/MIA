# Requirements: Chat and login views (N-1.1, low level)

**Parent:** `specs/mia/nodes/N-1-web-frontend/requirements.md` (N-1)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The chat page: messages, queue, history, status line, voting, tasks and memos, editors for the persona, login and password views, accessibility. Owns the one socket to the Backend (IF-101) and passes what the other two nodes need on to them (IF-111, IF-112). Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-CLV-001 – Chat view with sender and streaming
- Level: low   Subject: WebFrontEnd
- Text: When a user sends a message, the Chat and login views shall show the message with its sender and the answer as it arrives, sentence by sentence (IF-101).
- Rationale: refines REQ-FE-001
- Parent: REQ-FE-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the mock of IF-101, two users' messages show their names and the scripted answer appears sentence by sentence
- Verified by: TC-CLV-001
- Status: Approved
- History: –

### REQ-CLV-002 – Stop and queue position
- Level: low   Subject: WebFrontEnd
- Text: While a message waits, the Chat and login views shall show its position in the queue and offer a stop button for the running answer.
- Rationale: refines REQ-FE-002
- Parent: REQ-FE-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with a mock queue of 3, the positions 1, 2, 3 are shown; stop sends the stop event once
- Verified by: TC-CLV-002
- Status: Approved
- History: –

### REQ-CLV-003 – Shared history after reload
- Level: low   Subject: WebFrontEnd
- Text: When the page loads or reloads, the Chat and login views shall show the shared history from IF-101 and add every new message live.
- Rationale: refines REQ-FE-003
- Parent: REQ-FE-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: after reload the last 50 messages of the mock appear in order; a message sent by the mock from another user appears within 2 s
- Verified by: TC-CLV-003
- Status: Approved
- History: –

### REQ-CLV-004 – Connection state and drafts
- Level: low   Subject: WebFrontEnd
- Text: While the connection is lost, the Chat and login views shall show the connection state, reconnect by itself and keep the unsent draft.
- Rationale: refines REQ-FE-004
- Parent: REQ-FE-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the mock connection cut for 5 s the state shows offline, the draft text stays, the page reconnects without a reload
- Verified by: TC-CLV-004
- Status: Approved
- History: –

### REQ-CLV-005 – Regenerate and speak again
- Level: low   Subject: WebFrontEnd
- Text: When a user asks for it, the Chat and login views shall request a regenerated last answer or the spoken form of any answer through IF-101.
- Rationale: refines REQ-FE-005
- Parent: REQ-FE-005
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: the two controls send one event each; the mock answers are shown
- Verified by: TC-CLV-005
- Status: Approved
- History: –

### REQ-CLV-006 – Chat without the character
- Level: low   Subject: WebFrontEnd
- Text: If the character cannot load, then the Chat and login views shall keep the chat usable.
- Rationale: refines REQ-FE-006
- Parent: REQ-FE-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the character iframe blocked, a message is sent and answered (exact)
- Verified by: TC-CLV-006
- Status: Approved
- History: –

### REQ-CLV-007 – Character as stage
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall show the character filling the window with the chat as a side panel on wide screens and a bottom sheet on phones, collapsible to the character and a caption of the last answer.
- Rationale: refines REQ-FE-007
- Parent: REQ-FE-007
- Priority: Should
- Verification method: Demonstration
- Acceptance criterion: AC-1: viewports 360, 768 and 1440 px show the layout; collapsed view shows the caption
- Verified by: TC-CLV-007
- Status: Approved
- History: –

### REQ-CLV-008 – Status line and account of a task
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall show the status line with mood and activity and open for an answer of a task the step-by-step account delivered by the backend.
- Rationale: refines REQ-FE-014
- Parent: REQ-FE-014
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-21: the status line shows the mock mood and activity; opening an answer shows the mock account
- Verified by: TC-CLV-008
- Status: Approved
- History: –

### REQ-CLV-009 – Editors for expressions, gestures and persona
- Level: low   Subject: WebFrontEnd
- Text: When a user saves the persona, the Chat and login views shall send it as data and show a change saved by another user without a reload.
- Rationale: refines REQ-FE-015
- Parent: REQ-FE-015
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-17: a change pushed by the mock appears within 2 s without reload
- Verified by: TC-CLV-009
- Status: Approved
- History: –

### REQ-CLV-010 – Voting controls and score
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall offer a plus and a minus on answers, reactions and behaviours with their category, and show the scores per category and overall over time.
- Rationale: refines REQ-FE-016
- Parent: REQ-FE-016
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-18: a vote sends one event with category and subject; the mock scores are drawn per category and overall
- Verified by: TC-CLV-010
- Status: Approved
- History: –

### REQ-CLV-011 – Tasks, memos and memory views
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall show all tasks, memos and memory records and let a logged-in user change or delete each of them.
- Rationale: refines REQ-FE-018
- Parent: REQ-FE-018
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12, AC-24: with 50 mock records all are listed; an edit and a delete send one event each
- Verified by: TC-CLV-011
- Status: Approved
- History: –

### REQ-CLV-012 – Source trust edit
- Level: low   Subject: WebFrontEnd
- Text: When a user edits the trust value of a source, the Chat and login views shall send the edit with the source id.
- Rationale: refines REQ-FE-019
- Parent: REQ-FE-019
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-3: the edit event carries source id, old and new value
- Verified by: TC-CLV-012
- Status: Approved
- History: –

### REQ-CLV-013 – Variant label
- Level: low   Subject: WebFrontEnd
- Text: While a workflow with a character variant runs, the Chat and login views shall show a small label with the variant name in the chat and pass the variant to the Character view (IF-111).
- Rationale: refines REQ-FE-021
- Parent: REQ-FE-021
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-17: a mock run with a variant changes the outfit and shows the label; a run without keeps the chat's variant
- Verified by: TC-CLV-013
- Status: Approved
- History: –

### REQ-CLV-014 – Login views and password change
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall offer the login, the change of the user's own password and the account of a kept session.
- Rationale: refines REQ-FE-022
- Parent: REQ-FE-022
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: the three views send one event each
- Verified by: TC-CLV-014
- Status: Approved
- History: –

### REQ-CLV-015 – Login page states visibility
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall state on the login page that everything is visible to all users.
- Rationale: refines REQ-FE-023
- Parent: REQ-FE-023
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: the login page text is present (exact)
- Verified by: TC-CLV-015
- Status: Approved
- History: –

### REQ-CLV-016 – Accessibility and devices
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall be usable by keyboard and screen reader in a dark and a light theme with reduced motion at widths from 320 to 2560 px in current Chrome, Firefox and Safari (iOS 16 and later), with touch targets of at least 44 px.
- Rationale: refines REQ-FE-024
- Parent: REQ-FE-024
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: browser checks at 360, 768 and 1440 px in both themes; touch targets measured at 44 px or more (exact)
- Verified by: TC-CLV-016
- Status: Approved
- History: –

### REQ-CLV-017 – No request leaves the host
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall load no resource from outside the host.
- Rationale: refines REQ-FE-026
- Parent: REQ-FE-026
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-5: a browser test records every request of a session and finds 0 outside the host (exact)
- Verified by: TC-CLV-017
- Status: Approved
- History: –

### REQ-CLV-018 – Password over a secure channel
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall send a password only over HTTPS or to localhost.
- Rationale: refines REQ-FE-028
- Parent: REQ-FE-028
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: over plain HTTP to a LAN address the login form sends nothing (exact)
- Verified by: TC-CLV-018
- Status: Approved
- History: –

### REQ-CLV-019 – Plain stack
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall be plain HTML, CSS and ES modules without a build step or a UI framework.
- Rationale: refines REQ-FE-029
- Parent: REQ-FE-029
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: no bundler files; the Godot version string is 4.6.1 (exact)
- Verified by: TC-CLV-019
- Status: Approved
- History: –

### REQ-CLV-020 – Delivered by the backend
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall consist of static files that the backend container serves.
- Rationale: refines REQ-FE-030
- Parent: REQ-FE-030
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: the chat page loads from the backend container; the frontend has no container of its own
- Verified by: TC-CLV-020
- Status: Approved
- History: –

### REQ-CLV-021 – Use IF-101 only
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall talk to the Backend only through the interface IF-101 as specified in contracts/IF-101-chat-api.md.
- Rationale: refines REQ-FE-001, REQ-FE-026
- Parent: REQ-FE-001, REQ-FE-026
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the mock of IF-101 every scenario of the chat page runs; no other request leaves the page
- Verified by: TC-CLV-021
- Status: Approved
- History: –

### REQ-CLV-022 – Logout
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall offer a logout that ends the session at the server, closes the socket and shows the login.
- Rationale: refines REQ-FE-031; the owner found after testing that the login has no logout (2026-10-26)
- Parent: REQ-FE-031
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: one logout request is sent, the socket is closed, the login dialog is shown, a reload shows the login (exact)
- Verified by: TC-CLV-022
- Status: Approved
- History: A-04 (2026-10-26)

### REQ-CLV-023 – Status card of a task
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall show each running task on one status card that is updated in place from the event task_status with the phase, every budget as used and limit and every count the task reports, offer pause, resume and stop on it, and keep the card with the final figures after the task has ended.
- Rationale: refines REQ-FE-014; the owner's hand review of /review 2026-10-29 (numbers instead of "...", pause for a long run)
- Parent: REQ-FE-014
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-17: a task_status of the mock draws the figures it carries; a second one with the same id changes the same card; pause sends one pause request and the button becomes resume; a status after done does not change the card (exact)
- Verified by: TC-CLV-023
- Status: Draft
- History: A-24 new

### REQ-CLV-024 – Files list
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall list the files of the files volume in the workspace with name, size, time and task, offer each as a download, show a new file without a reload from the event files_changed, and offer no way to delete a file.
- Rationale: refines REQ-FE-018; generated files are not buttons on a message (owner 2026-10-29), deleting is done in the volume
- Parent: REQ-FE-018
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-17: the list of the mock is drawn newest first, each entry links to /api/files/<name>, an event files_changed draws the list again, no delete control exists (exact)
- Verified by: TC-CLV-024
- Status: Draft
- History: A-24 new
