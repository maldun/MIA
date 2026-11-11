# Test requirements: Chat agent (N-2.2), speak again (A-132, TD-11)

Requirements on the checks TC-CHA-030 to TC-CHA-036, TC-VPB-006 and TC-VPB-007 (Draft, proposed in A-132, not approved). The older checks of N-2.2 have none yet (they predate test requirements, G-V1 decision D-180). The repository has no shared test-requirement catalog (M43), so no item has a `Source:` line. Protected like the checks from the plan gate on.

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | Stand-ins | The fakes for the voice route, the sound-server sink and the audio events, the memory writer and storage, and how far they can be trusted | TR-VOICE-001, TR-VOICE-002, TR-VOICE-004, TR-VOICE-005, TR-MEM-001, TR-MEM-003, TR-MEM-004 |
| 2 | Exact values | Sentences and order written by hand; the cost check names its record count | TR-VOICE-003, TR-MEM-002 |

### TR-VOICE-001 – the fake voice route records and obeys stop
- Applies to: TC-CHA-030, TC-CHA-031, TC-CHA-032, TC-CHA-033, TC-CHA-034, TC-CHA-037
- Requirement: REQ-CHA-030
- Group: Stand-ins
- Kind: setup
- Text: The fake voice route shall record each text it gets with the time of its start and end, shall block until its `should_stop` is true when the check asks for it, and shall raise `OSError` when the check asks for a failure.
- Rationale: these checks must run in stage 1 and 2 without sound, and they only prove the Chat agent's side of the call; the sound server's side is TC-CHA-036.
- Credibility aspect: stand-in fidelity
- Verified by: TC-CHA-036
- Status: Approved

### TR-VOICE-002 – the short hand check is the only check of the real engine
- Applies to: TC-CHA-035
- Requirement: REQ-CHA-030
- Group: Stand-ins
- Kind: setup
- Text: The hand check TC-CHA-035 shall be done on the host with the real sound server, the real engine and the real page by the owner after any change of the speak-again call, of `speak.py` or of `sound.js`, and its result shall be written into the verification report.
- Rationale: no automatic check hears the engine or the browser's real audio output; the fakes of TR-VOICE-001 and TR-VOICE-004 are only as good as this check shows. The check is kept short on purpose: order, queue, failure and mute are checked automatically.
- Credibility aspect: stand-in fidelity
- Verified by: verification report
- Status: Approved

### TR-VOICE-003 – sentences and order written by hand
- Applies to: TC-CHA-030, TC-CHA-031, TC-CHA-034, TC-CHA-036
- Requirement: REQ-CHA-031
- Group: Exact values
- Kind: unit
- Text: The expected sentences and their order shall be written into the test by hand and not taken from the splitting code under test.
- Rationale: a split that is wrong in the same way on both sides would pass; the example "One. Two. Three." gives three calls by hand, and the markup example gives two calls.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Status: Approved

### TR-VOICE-004 – the sound-server check runs the real server with a fake sink
- Applies to: TC-CHA-036
- Requirement: REQ-CHA-034
- Group: Stand-ins
- Kind: setup
- Text: The check shall run the real `SoundServer` and `SoundHandler` on a localhost port with real TCP clients, and only the speaker shall be a fake sink that records each chunk it is asked to play in order and honours `cancelled`.
- Rationale: the queue behind a live answer and the cancel on a closed connection are properties of the server and its single-threaded `TCPServer`; a fake of the server would only repeat what we believe. The sink hides the engine, which TR-VOICE-002 covers.
- Credibility aspect: stand-in fidelity
- Verified by: TC-CHA-035
- Status: Approved

### TR-VOICE-005 – the page checks use the real page code and the real audio message
- Applies to: TC-VPB-006, TC-VPB-007
- Requirement: REQ-VPB-006
- Group: Stand-ins
- Kind: setup
- Text: The page checks shall load the real `sound.js` with a fake clock and a fake audio element in the node test and the real page in Chromium in the browser check, and the mock server shall send `audio_reload` with the fields `url`, `serial` and `message` as `publish_audio` does.
- Rationale: the fault is in the page's drop window; a fake player would hide it. The mock is only as faithful as `publish_audio` and `AudioRouter.announce` in `web_app.py` and `audio_router.py`; the short hand check TC-CHA-035 compares it with the real thing.
- Credibility aspect: stand-in fidelity
- Verified by: TC-CHA-035
- Status: Approved

## Structured memory (T-04, TC-CHA-011 to 013; Draft, written 2026-11-11 after the first Verify, for the owner's review)

### TR-MEM-001 – the holdout is run by a verifier, once, with the fixed repeats
- Applies to: TC-CHA-011
- Requirement: REQ-CHA-011
- Group: Stand-ins
- Kind: setup
- Text: The holdout part of TC-CHA-011 shall be run by a verifier who did not tune the skill, with pin MP-light, 3 repeats and the temperature of the skill; a FAIL shall be re-run once with fresh repeats and only the second result counts; the texts of the holdout cases shall not be copied into prompts, cases or notes.
- Rationale: the implementer saw all dev cases and tuned the prompt against them; the rule of A-12 (9 of 11, lower bound 0.5) has the error rates given in the check only with one re-run.
- Credibility aspect: reviewer independence
- Verified by: verification report
- Status: Draft

### TR-MEM-002 – the cost check says how many records it saw
- Applies to: TC-CHA-011
- Requirement: REQ-CHA-011
- Group: Exact values
- Kind: setup
- Text: The result of `tools/memory_cost.py` shall be reported together with the number of records in the store it ran on, and a result with fewer than 10 records shall be called a formal pass only.
- Rationale: on 2026-11-11 the store held 0 records, so the block was empty for all 20 questions and "not higher than dreaming" held trivially.
- Credibility aspect: measurement conditions
- Verified by: verification report
- Status: Draft

### TR-MEM-003 – the writer is a fake that fails when asked
- Applies to: TC-CHA-012
- Requirement: REQ-CHA-012
- Group: Stand-ins
- Kind: setup
- Text: The check shall use a fake writer that fails the check when it is called, so that a text that is not the user's is shown to be refused before the model is asked, and the only caller of `remember` shall be read in the verification report.
- Rationale: a fake that returns an empty list would hide a call that happens and finds nothing; the rule is a code rule, not a property of the model.
- Credibility aspect: stand-in fidelity
- Verified by: verification report
- Status: Draft

### TR-MEM-004 – the routes run on a real storage, the tab is not covered
- Applies to: TC-CHA-013
- Requirement: REQ-CHA-013
- Group: Stand-ins
- Kind: setup
- Text: The check shall run the real items routes on a real file storage in a temporary folder; the Memory tab of the page is shown to the owner by hand after a change of the tab, and the result is written into the verification report.
- Rationale: no automatic check in this file loads the tab; the routes carry the rules, the tab only shows them.
- Credibility aspect: stand-in fidelity
- Verified by: verification report
- Status: Draft
