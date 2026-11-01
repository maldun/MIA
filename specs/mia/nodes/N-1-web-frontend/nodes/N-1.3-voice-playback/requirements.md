# Requirements: Voice playback (N-1.3, low level)

**Parent:** `specs/mia/nodes/N-1-web-frontend/requirements.md` (N-1)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

Playing the audio of the answers and the voice lines in this browser: queue, claim of the voice by one page, mute, stop. Provides IF-112. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-VPB-001 – Voice playback
- Level: low   Subject: WebFrontEnd
- Text: When audio for a sentence arrives, the Voice playback shall play the sentences in order.
- Rationale: refines REQ-FE-011
- Parent: REQ-FE-011
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: with 5 scripted audio chunks the playback order equals the arrival order and no sentence overlaps
- Verified by: TC-VPB-001
- Status: Approved
- History: –

### REQ-VPB-002 – Mute and stop per user
- Level: low   Subject: WebFrontEnd
- Text: When a user mutes or stops the voice, the Voice playback shall silence it on that device only.
- Rationale: refines REQ-FE-012
- Parent: REQ-FE-012
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: after mute no audio plays on this device; a second device still plays; after Stop no line of the stopped answer plays on this device, also one that arrives later, until the next answer begins or 3 s after the Stop, whichever comes first (its lines play, and so does a line that arrives later, such as the shocked line of a minus vote)
- Verified by: TC-VPB-002
- Status: Approved
- History: 2026-10-31 D-157: the acceptance criterion adds the lines of a stopped answer that arrive after the Stop (owner check A3); lines carry no answer id, so "the stopped answer" ends when the next one begins (`chat_start`); 2026-10-31 D-165: the drop ends 3 s after the Stop at the latest, so lines outside the stopped answer (the shocked line of a minus vote, IF-101 v13) still play (re-verification 3, R1)

### REQ-VPB-003 – Voice lines
- Level: low   Subject: WebFrontEnd
- Text: When the backend sends a voice line, the Voice playback shall play it, and if its audio file is missing, skip it and report it through the IF-112 callback `onLineError`; no event goes to the backend.
- Rationale: refines REQ-FE-013
- Parent: REQ-FE-013
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-13: a line with a missing file produces one report through `onLineError` and no error shown; the conversation continues
- Verified by: TC-VPB-003
- Status: Approved
- History: 2026-10-31 A-50 (D-140): narrowed, the report ends at the IF-112 callback (the page writes it to the browser console); no backend event

### REQ-VPB-004 – No request leaves the host
- Level: low   Subject: WebFrontEnd
- Text: The Voice playback shall load no resource from outside the host.
- Rationale: refines REQ-FE-026
- Parent: REQ-FE-026
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-5: a browser test records every request of a session and finds 0 outside the host (exact)
- Verified by: TC-VPB-004
- Status: Approved
- History: –

### REQ-VPB-005 – Delivered by the backend
- Level: low   Subject: WebFrontEnd
- Text: The Voice playback shall consist of static files that the backend container serves.
- Rationale: refines REQ-FE-030
- Parent: REQ-FE-030
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: the chat page loads from the backend container; the frontend has no container of its own
- Verified by: TC-VPB-005
- Status: Approved
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-112 – Voice player
- Level: low   Subject: WebFrontEnd
- Text: The Voice playback shall provide the Chat and login views with the player interface IF-112 as specified in contracts/IF-112-voice-player.md (enqueue a line, mute, stop, claim the voice, and the speaking signal that follows the queue).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-FE-011, REQ-FE-012
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: the contract suite test_if_112_voice_player.test.mjs passes against the mock (stage 1) and the Voice playback (stage 2)
- Verified by: TC-IF-112-01..05
- Status: Approved
- History: v0, amendment 5/7 (2026-10-25)
