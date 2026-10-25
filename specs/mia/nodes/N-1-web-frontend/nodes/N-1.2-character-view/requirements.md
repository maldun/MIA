# Requirements: Character view (N-1.2, low level)

**Parent:** `specs/mia/nodes/N-1-web-frontend/requirements.md` (N-1)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The 3D character in an iframe (Godot web export): expressions, gestures, mouth, mood map, editors for expressions and gestures, model selection, variants, frame rate. Provides IF-111. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-CHV-001 – Chat without the character
- Level: low   Subject: WebFrontEnd
- Text: If the Character view cannot load, then it shall report the failure to the Chat and login views through IF-111 and stay hidden.
- Rationale: refines REQ-FE-006
- Parent: REQ-FE-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the character iframe blocked, a message is sent and answered (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-002 – One expression API
- Level: low   Subject: WebFrontEnd
- Text: The Character view shall drive the character only through one central expression API reached by a message bridge.
- Rationale: refines REQ-FE-008
- Parent: REQ-FE-008
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-17: a scripted list of 14 presets and 5 gestures played through the API shows each on the character; no other call path exists
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-003 – Living character
- Level: low   Subject: WebFrontEnd
- Text: While the character speaks, the Character view shall move its mouth with the audio, blend expressions smoothly, blink and play idle motion.
- Rationale: refines REQ-FE-009
- Parent: REQ-FE-009
- Priority: Should
- Verification method: Demonstration
- Acceptance criterion: AC-1: reviewer checklist for mouth, blending, blinking, idle motion on desktop and phone
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-004 – Mood shown by the mood map
- Level: low   Subject: WebFrontEnd
- Text: When the mood changes, the Character view shall show the expression and gesture of the mood map for it, and neutral for an unknown mood.
- Rationale: refines REQ-FE-010
- Parent: REQ-FE-010
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-17: for every mood of the map and for 1 unknown mood the shown expression is the mapped one or neutral (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-005 – Editors for expressions, gestures and persona
- Level: low   Subject: WebFrontEnd
- Text: When a user saves an expression, gesture, background, mood phrase or emotion, the Character view shall send it as data and show a change saved by another user without a reload.
- Rationale: refines REQ-FE-015
- Parent: REQ-FE-015
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-17: a change pushed by the mock appears within 2 s without reload
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-006 – Shocked reaction
- Level: low   Subject: WebFrontEnd
- Text: When a user gives a minus, the Character view shall show the shocked expression and play the shocked line sent by the backend.
- Rationale: refines REQ-FE-017
- Parent: REQ-FE-017
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-11: on a mock negative-vote answer the shocked expression is shown (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-007 – Character model selection
- Level: low   Subject: WebFrontEnd
- Text: When a user selects a VRoid model, the Character view shall load it and list the presets and gestures it cannot map.
- Rationale: refines REQ-FE-020
- Parent: REQ-FE-020
- Priority: Should
- Verification method: Demonstration, Test
- Acceptance criterion: AC-17: a second .vrm model loads and the unmapped list is shown
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-008 – Variant label
- Level: low   Subject: WebFrontEnd
- Text: When the Chat and login views pass a variant (IF-111), the Character view shall show the character in that variant, and in the chat's variant otherwise.
- Rationale: refines REQ-FE-021
- Parent: REQ-FE-021
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-17: a mock run with a variant changes the outfit and shows the label; a run without keeps the chat's variant
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-009 – Accessibility and devices
- Level: low   Subject: WebFrontEnd
- Text: While the user prefers reduced motion, the Character view shall reduce its idle motion.
- Rationale: refines REQ-FE-024
- Parent: REQ-FE-024
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: browser checks at 360, 768 and 1440 px in both themes; touch targets measured at 44 px or more (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-010 – Frame rate
- Level: low   Subject: WebFrontEnd
- Text: While the character is shown, the Character view shall render at 30 frames per second or more on a mid-range phone and 60 on desktop.
- Rationale: refines REQ-FE-025
- Parent: REQ-FE-025
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-19: median of 10 runs of 30 s on the reference phone and desktop reaches the rates
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-011 – No request leaves the host
- Level: low   Subject: WebFrontEnd
- Text: The Character view shall load no resource from outside the host.
- Rationale: refines REQ-FE-026
- Parent: REQ-FE-026
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-5: a browser test records every request of a session and finds 0 outside the host (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-012 – Character in a secure context
- Level: low   Subject: WebFrontEnd
- Text: The Character view shall load the character only on localhost or over HTTPS.
- Rationale: refines REQ-FE-027
- Parent: REQ-FE-027
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: over plain HTTP to a LAN address the character does not load (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-013 – Plain stack
- Level: low   Subject: WebFrontEnd
- Text: The Character view shall be a Godot 4.6.1 web export in the Compatibility renderer.
- Rationale: refines REQ-FE-029
- Parent: REQ-FE-029
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: no bundler files; the Godot version string is 4.6.1 (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-CHV-014 – Delivered by the backend
- Level: low   Subject: WebFrontEnd
- Text: The Character view shall consist of static files that the backend container serves.
- Rationale: refines REQ-FE-030
- Parent: REQ-FE-030
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: the chat page loads from the backend container; the frontend has no container of its own
- Verified by: –
- Status: Draft
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-111 – Character bridge
- Level: low   Subject: WebFrontEnd
- Text: The Character view shall provide the Chat and login views with the character bridge IF-111 as specified in contracts/IF-111-character-bridge.md (JSON messages by postMessage on the same origin: expression, speaking, viewport_inset, view, background, variant, model; and from the character: ready, failed, unmapped).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-FE-008, REQ-FE-006
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1, AC-17: the contract suite test_if_111_character_bridge.test.mjs passes against the mock (stage 1) and the Character view (stage 2)
- Verified by: TC-IF-111-01..06
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)
