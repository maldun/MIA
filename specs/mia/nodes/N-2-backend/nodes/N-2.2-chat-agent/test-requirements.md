# Test requirements: Chat agent (N-2.2), speak again (A-132, TD-11)

Requirements on the checks TC-CHA-030 to TC-CHA-036, TC-VPB-006 and TC-VPB-007 (Draft, proposed in A-132, not approved). The older checks of N-2.2 have none yet (they predate test requirements, G-V1 decision D-180). The repository has no shared test-requirement catalog (M43), so no item has a `Source:` line. Protected like the checks from the plan gate on.

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | Stand-ins | The fakes for the voice route, the sound-server sink and the audio events, and how far they can be trusted | TR-VOICE-001, TR-VOICE-002, TR-VOICE-004, TR-VOICE-005 |
| 2 | Exact values | Sentences and order written by hand | TR-VOICE-003 |

### TR-VOICE-001 – the fake voice route records and obeys stop
- Applies to: TC-CHA-030, TC-CHA-031, TC-CHA-032, TC-CHA-033, TC-CHA-034, TC-CHA-037
- Requirement: REQ-CHA-030
- Group: Stand-ins
- Kind: setup
- Text: The fake voice route shall record each text it gets with the time of its start and end, shall block until its `should_stop` is true when the check asks for it, and shall raise `OSError` when the check asks for a failure.
- Rationale: these checks must run in stage 1 and 2 without sound, and they only prove the Chat agent's side of the call; the sound server's side is TC-CHA-036.
- Credibility aspect: stand-in fidelity
- Verified by: TC-CHA-036
- Status: Draft

### TR-VOICE-002 – the short hand check is the only check of the real engine
- Applies to: TC-CHA-035
- Requirement: REQ-CHA-030
- Group: Stand-ins
- Kind: setup
- Text: The hand check TC-CHA-035 shall be done on the host with the real sound server, the real engine and the real page by the owner after any change of the speak-again call, of `speak.py` or of `sound.js`, and its result shall be written into the verification report.
- Rationale: no automatic check hears the engine or the browser's real audio output; the fakes of TR-VOICE-001 and TR-VOICE-004 are only as good as this check shows. The check is kept short on purpose: order, queue, failure and mute are checked automatically.
- Credibility aspect: stand-in fidelity
- Verified by: verification report
- Status: Draft

### TR-VOICE-003 – sentences and order written by hand
- Applies to: TC-CHA-030, TC-CHA-031, TC-CHA-034, TC-CHA-036
- Requirement: REQ-CHA-031
- Group: Exact values
- Kind: unit
- Text: The expected sentences and their order shall be written into the test by hand and not taken from the splitting code under test.
- Rationale: a split that is wrong in the same way on both sides would pass; the example "One. Two. Three." gives three calls by hand, and the markup example gives two calls.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Status: Draft

### TR-VOICE-004 – the sound-server check runs the real server with a fake sink
- Applies to: TC-CHA-036
- Requirement: REQ-CHA-034
- Group: Stand-ins
- Kind: setup
- Text: The check shall run the real `SoundServer` and `SoundHandler` on a localhost port with real TCP clients, and only the speaker shall be a fake sink that records each chunk it is asked to play in order and honours `cancelled`.
- Rationale: the queue behind a live answer and the cancel on a closed connection are properties of the server and its single-threaded `TCPServer`; a fake of the server would only repeat what we believe. The sink hides the engine, which TR-VOICE-002 covers.
- Credibility aspect: stand-in fidelity
- Verified by: TC-CHA-035
- Status: Draft

### TR-VOICE-005 – the page checks use the real page code and the real audio message
- Applies to: TC-VPB-006, TC-VPB-007
- Requirement: REQ-VPB-006
- Group: Stand-ins
- Kind: setup
- Text: The page checks shall load the real `sound.js` with a fake clock and a fake audio element in the node test and the real page in Chromium in the browser check, and the mock server shall send `audio_reload` with the fields `url`, `serial` and `message` as `publish_audio` does.
- Rationale: the fault is in the page's drop window; a fake player would hide it. The mock is only as faithful as `publish_audio` and `AudioRouter.announce` in `web_app.py` and `audio_router.py`; the short hand check TC-CHA-035 compares it with the real thing.
- Credibility aspect: stand-in fidelity
- Verified by: TC-CHA-035
- Status: Draft
