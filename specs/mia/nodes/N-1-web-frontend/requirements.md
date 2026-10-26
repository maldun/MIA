# Requirements: Web Frontend (N-1, high level)

**Parent:** `specs/mia/requirements.md` (top level N-0)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

GUI, chat and prompt, character view, login and user views, voice playback. Static files served by the backend container (NFR-9). Talks to the backend only through IF-101. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-FE-001 – Chat view with sender and streaming
- Level: high   Subject: WebFrontEnd
- Text: When a user sends a message, the Web Frontend shall show the message with its sender and the answer as it arrives, sentence by sentence (IF-101).
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the mock of IF-101, two users' messages show their names and the scripted answer appears sentence by sentence
- Verified by: TC-N1-003, TC-CLV-001, TC-CLV-021
- Status: Approved
- History: –

### REQ-FE-002 – Stop and queue position
- Level: high   Subject: WebFrontEnd
- Text: While a message waits, the Web Frontend shall show its position in the queue and offer a stop button for the running answer.
- Rationale: refines FR-1, NFR-7
- Parent: FR-1, NFR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with a mock queue of 3, the positions 1, 2, 3 are shown; stop sends the stop event once
- Verified by: TC-N1-003, TC-CLV-002
- Status: Approved
- History: –

### REQ-FE-003 – Shared history after reload
- Level: high   Subject: WebFrontEnd
- Text: When the page loads or reloads, the Web Frontend shall show the shared history from IF-101 and add every new message live.
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: after reload the last 50 messages of the mock appear in order; a message sent by the mock from another user appears within 2 s
- Verified by: TC-N1-003, TC-CLV-003
- Status: Approved
- History: –

### REQ-FE-004 – Connection state and drafts
- Level: high   Subject: WebFrontEnd
- Text: While the connection is lost, the Web Frontend shall show the connection state, reconnect by itself and keep the unsent draft.
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the mock connection cut for 5 s the state shows offline, the draft text stays, the page reconnects without a reload
- Verified by: TC-N1-003, TC-CLV-004
- Status: Approved
- History: –

### REQ-FE-005 – Regenerate and speak again
- Level: high   Subject: WebFrontEnd
- Text: When a user asks for it, the Web Frontend shall request a regenerated last answer or the spoken form of any answer through IF-101.
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: the two controls send one event each; the mock answers are shown
- Verified by: TC-N1-003, TC-CLV-005
- Status: Approved
- History: –

### REQ-FE-006 – Chat without the character
- Level: high   Subject: WebFrontEnd
- Text: If the character cannot load, then the Web Frontend shall keep the chat usable.
- Rationale: refines FR-2
- Parent: FR-2
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the character iframe blocked, a message is sent and answered (exact)
- Verified by: TC-N1-002, TC-CLV-006, TC-CHV-001
- Status: Approved
- History: –

### REQ-FE-007 – Character as stage
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall show the character filling the window with the chat as a side panel on wide screens and a bottom sheet on phones, collapsible to the character and a caption of the last answer.
- Rationale: refines FR-2
- Parent: FR-2
- Priority: Should
- Verification method: Demonstration
- Acceptance criterion: AC-1: viewports 360, 768 and 1440 px show the layout; collapsed view shows the caption
- Verified by: TC-N1-003, TC-CLV-007
- Status: Approved
- History: –

### REQ-FE-008 – One expression API
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall drive the character only through one central expression API reached by a message bridge.
- Rationale: refines FR-2, FR-23
- Parent: FR-2, FR-23
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-17: a scripted list of 14 presets and 5 gestures played through the API shows each on the character; no other call path exists
- Verified by: TC-N1-002, TC-CHV-002
- Status: Approved
- History: –

### REQ-FE-009 – Living character
- Level: high   Subject: WebFrontEnd
- Text: While the character speaks, the Web Frontend shall move its mouth with the audio, blend expressions smoothly, blink and play idle motion.
- Rationale: refines FR-2
- Parent: FR-2
- Priority: Should
- Verification method: Demonstration
- Acceptance criterion: AC-1: reviewer checklist for mouth, blending, blinking, idle motion on desktop and phone
- Verified by: TC-N1-002, TC-CHV-003
- Status: Approved
- History: –

### REQ-FE-010 – Mood shown by the mood map
- Level: high   Subject: WebFrontEnd
- Text: When the mood changes, the Web Frontend shall show the expression and gesture of the mood map for it, and neutral for an unknown mood.
- Rationale: refines FR-23
- Parent: FR-23
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-17: for every mood of the map and for 1 unknown mood the shown expression is the mapped one or neutral (exact)
- Verified by: TC-N1-002, TC-CHV-004
- Status: Approved
- History: –

### REQ-FE-011 – Voice playback
- Level: high   Subject: WebFrontEnd
- Text: When audio for a sentence arrives, the Web Frontend shall play the sentences in order.
- Rationale: refines FR-3
- Parent: FR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: with 5 scripted audio chunks the playback order equals the arrival order and no sentence overlaps
- Verified by: TC-N1-001, TC-VPB-001
- Status: Approved
- History: –

### REQ-FE-012 – Mute and stop per user
- Level: high   Subject: WebFrontEnd
- Text: When a user mutes or stops the voice, the Web Frontend shall silence it on that device only.
- Rationale: refines FR-3
- Parent: FR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: after mute no audio plays on this device; a second device still plays
- Verified by: TC-N1-001, TC-VPB-002
- Status: Approved
- History: –

### REQ-FE-013 – Voice lines
- Level: high   Subject: WebFrontEnd
- Text: When the backend sends a voice line, the Web Frontend shall play it, and if its audio file is missing, skip it and report it to the backend.
- Rationale: refines FR-31
- Parent: FR-31
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-13: a line with a missing file produces one report event and no error shown; the conversation continues
- Verified by: TC-N1-001, TC-VPB-003
- Status: Approved
- History: –

### REQ-FE-014 – Status line and account of a task
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall show the status line with mood and activity and open for an answer of a task the step-by-step account delivered by the backend.
- Rationale: refines FR-4
- Parent: FR-4
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-21: the status line shows the mock mood and activity; opening an answer shows the mock account
- Verified by: TC-N1-003, TC-CLV-008
- Status: Approved
- History: –

### REQ-FE-015 – Editors for expressions, gestures and persona
- Level: high   Subject: WebFrontEnd
- Text: When a user saves an expression, gesture, background, mood phrase, emotion or the persona, the Web Frontend shall send it as data, and show a change saved by another user without a reload.
- Rationale: refines FR-5
- Parent: FR-5
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-17: a change pushed by the mock appears within 2 s without reload
- Verified by: TC-N1-002, TC-CLV-009, TC-CHV-005
- Status: Approved
- History: –

### REQ-FE-016 – Voting controls and score
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall offer a plus and a minus on answers, reactions and behaviours with their category, and show the scores per category and overall over time.
- Rationale: refines FR-27, FR-29
- Parent: FR-27, FR-29
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-18: a vote sends one event with category and subject; the mock scores are drawn per category and overall
- Verified by: TC-N1-003, TC-CLV-010
- Status: Approved
- History: –

### REQ-FE-017 – Shocked reaction
- Level: high   Subject: WebFrontEnd
- Text: When a user gives a minus, the Web Frontend shall show the shocked expression and play the shocked line sent by the backend.
- Rationale: refines FR-29, FR-31
- Parent: FR-29, FR-31
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-11: on a mock negative-vote answer the shocked expression is shown (exact)
- Verified by: TC-N1-002, TC-CHV-006
- Status: Approved
- History: –

### REQ-FE-018 – Tasks, memos and memory views
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall show all tasks, memos and memory records and let a logged-in user change or delete each of them.
- Rationale: refines FR-28, FR-14
- Parent: FR-28, FR-14
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12, AC-24: with 50 mock records all are listed; an edit and a delete send one event each
- Verified by: TC-N1-003, TC-CLV-011
- Status: Approved
- History: –

### REQ-FE-019 – Source trust edit
- Level: high   Subject: WebFrontEnd
- Text: When a user edits the trust value of a source, the Web Frontend shall send the edit with the source id.
- Rationale: refines FR-12
- Parent: FR-12
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-3: the edit event carries source id, old and new value
- Verified by: TC-N1-003, TC-CLV-012
- Status: Approved
- History: –

### REQ-FE-020 – Character model selection
- Level: high   Subject: WebFrontEnd
- Text: When a user selects a VRoid model, the Web Frontend shall load it and list the presets and gestures it cannot map.
- Rationale: refines FR-24
- Parent: FR-24
- Priority: Should
- Verification method: Demonstration, Test
- Acceptance criterion: AC-17: a second .vrm model loads and the unmapped list is shown
- Verified by: TC-N1-002, TC-CHV-007
- Status: Approved
- History: –

### REQ-FE-021 – Variant label
- Level: high   Subject: WebFrontEnd
- Text: While a workflow with a character variant runs, the Web Frontend shall show the variant on the character and a small label in the chat.
- Rationale: refines FR-32
- Parent: FR-32
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-17: a mock run with a variant changes the outfit and shows the label; a run without keeps the chat's variant
- Verified by: TC-N1-002, TC-CLV-013, TC-CHV-008
- Status: Approved
- History: –

### REQ-FE-022 – Login views and password change
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall offer the login, the change of the user's own password and the account of a kept session.
- Rationale: refines FR-21
- Parent: FR-21
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: the three views send one event each
- Verified by: TC-N1-003, TC-CLV-014
- Status: Approved
- History: –

### REQ-FE-023 – Login page states visibility
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall state on the login page that everything is visible to all users.
- Rationale: refines CON-6, NFR-5
- Parent: CON-6, NFR-5
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: the login page text is present (exact)
- Verified by: TC-N1-006, TC-CLV-015
- Status: Approved
- History: –

### REQ-FE-024 – Accessibility and devices
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall be usable by keyboard and screen reader in a dark and a light theme with reduced motion at widths from 320 to 2560 px in current Chrome, Firefox and Safari (iOS 16 and later), with touch targets of at least 44 px.
- Rationale: refines NFR-1
- Parent: NFR-1
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: browser checks at 360, 768 and 1440 px in both themes; touch targets measured at 44 px or more (exact)
- Verified by: TC-N1-003, TC-CLV-016, TC-CHV-009
- Status: Approved
- History: –

### REQ-FE-025 – Frame rate
- Level: high   Subject: WebFrontEnd
- Text: While the character is shown, the Web Frontend shall render at 30 frames per second or more on a phone inside the network and on a desktop browser.
- Rationale: refines NFR-7
- Parent: NFR-7
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-19: median of 10 runs of 30 s reaches 30 fps on any phone inside the network (no particular device) and on the desktop
- Verified by: TC-N1-005, TC-CHV-010
- Status: Approved
- History: –

### REQ-FE-026 – No request leaves the host
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall load no resource from outside the host.
- Rationale: refines NFR-5
- Parent: NFR-5
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-5: a browser test records every request of a session and finds 0 outside the host (exact)
- Verified by: TC-N1-004, TC-CLV-017, TC-CLV-021, TC-CHV-011, TC-VPB-004
- Status: Approved
- History: –

### REQ-FE-027 – Character in a secure context
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall load the character only on localhost or over HTTPS.
- Rationale: refines CON-4, NFR-6
- Parent: CON-4, NFR-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: over plain HTTP to a LAN address the character does not load (exact)
- Verified by: TC-N1-004, TC-CHV-012
- Status: Approved
- History: –

### REQ-FE-028 – Password over a secure channel
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall send a password only over HTTPS or to localhost.
- Rationale: refines CON-4, NFR-6
- Parent: CON-4, NFR-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: over plain HTTP to a LAN address the login form sends nothing (exact)
- Verified by: TC-N1-004, TC-CLV-018
- Status: Approved
- History: –

### REQ-FE-029 – Plain stack
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall be plain HTML, CSS and ES modules without a build step or a UI framework, with the character as a Godot 4.6.1 web export in the Compatibility renderer.
- Rationale: refines CON-3, NFR-1
- Parent: CON-3, NFR-1
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: no bundler files; the Godot version string is 4.6.1 (exact)
- Verified by: TC-N1-006, TC-CLV-019, TC-CHV-013
- Status: Approved
- History: –

### REQ-FE-030 – Delivered by the backend
- Level: high   Subject: WebFrontEnd
- Text: The Web Frontend shall consist of static files that the backend container serves.
- Rationale: refines NFR-9
- Parent: NFR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: the chat page loads from the backend container; the frontend has no container of its own
- Verified by: TC-N1-006, TC-CLV-020, TC-CHV-014, TC-VPB-005
- Status: Approved
- History: –
