# Requirements: Voice synthesis (N-2.5, low level)

**Parent:** `specs/mia/nodes/N-2-backend/requirements.md` (N-2)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

Speech on the host: filter the text, synthesise sentence by sentence with the open TTS (Kokoro), apply the anime effect, make the voice lines. Provides IF-204. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-VOI-001 – Voice synthesis
- Level: low   Subject: VoiceSubsystem
- Text: When an answer is written, the Voice synthesis shall synthesise it sentence by sentence with an open text-to-speech engine behind one interface on the host and apply the anime voice effect.
- Rationale: refines REQ-BE-016
- Parent: REQ-BE-016
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: each sentence of a 5-sentence answer yields one audio chunk
- Verified by: TC-VOI-001
- Status: Draft
- History: –

### REQ-VOI-002 – Speak only what is meant to be heard
- Level: low   Subject: VoiceSubsystem
- Text: The Voice synthesis shall remove markup and stage directions from the text before synthesis.
- Rationale: refines REQ-BE-017
- Parent: REQ-BE-017
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: on 10 answers with markup the synthesis input contains none (exact)
- Verified by: TC-VOI-002
- Status: Draft
- History: –

### REQ-VOI-003 – Voice lines
- Level: low   Subject: VoiceSubsystem
- Text: When the Chat agent names a voice line, the Voice synthesis shall deliver its audio, skipping a missing audio file with a log entry.
- Rationale: refines REQ-BE-018
- Parent: REQ-BE-018
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-13: every mood of the map has a line or is declared silent; a missing file is logged and skipped
- Verified by: TC-VOI-003
- Status: Draft
- History: –

### REQ-VOI-004 – Default voice lines generated
- Level: low   Subject: VoiceSubsystem
- Text: The Voice synthesis shall generate the default voice lines with its own text-to-speech engine and voice effect.
- Rationale: refines REQ-BE-019
- Parent: REQ-BE-019
- Priority: Should
- Verification method: Inspection
- Acceptance criterion: AC-13: no default line is a third-party recording
- Verified by: TC-VOI-004
- Status: Draft
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-204 – Speech synthesis
- Level: low   Subject: VoiceSubsystem
- Text: The Voice synthesis shall provide the Chat agent with the speech interface IF-204 as specified in contracts/IF-204-speech.md (synthesise a sentence to an audio chunk, deliver a voice line, in order, with the errors unavailable and empty text).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-BE-016, REQ-BE-017
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: the contract suite test_if_204_speech.py passes against the mock (stage 1) and the Voice synthesis (stage 2)
- Verified by: TC-IF-204-01..03
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)
