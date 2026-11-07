# Test requirements: Chat agent (N-2.2), speak again (A-132, TD-11)

Requirements on the checks TC-CHA-030 to TC-CHA-035 and TC-VPB-006 (Draft, proposed in A-132, not approved). The older checks of N-2.2 have none yet (they predate test requirements, G-V1 decision D-180). The repository has no shared test-requirement catalog (M43), so no item has a `Source:` line. Protected like the checks from the plan gate on.

## Groups
| Order | Group | What it covers | Test requirements |
|---|---|---|---|
| 1 | Stand-ins | The fake voice route and how far it can be trusted | TR-VOICE-001, TR-VOICE-002 |
| 2 | Exact values | Sentences and order written by hand | TR-VOICE-003 |

### TR-VOICE-001 – the fake voice route records and obeys stop
- Applies to: TC-CHA-030, TC-CHA-031, TC-CHA-032, TC-CHA-033, TC-CHA-034
- Requirement: REQ-CHA-030
- Group: Stand-ins
- Kind: setup
- Text: The fake voice route shall record each text it gets with the time of its start and end, shall block until its `should_stop` is true when the check asks for it, and shall raise `OSError` when the check asks for a failure.
- Rationale: the real route is the sound server and an engine; these checks must run in stage 1 and 2 without sound, and they only prove the Chat agent's side of the call.
- Credibility aspect: stand-in fidelity
- Verified by: TC-CHA-035
- Status: Draft

### TR-VOICE-002 – the hand test is the only check of the real route
- Applies to: TC-CHA-035, TC-VPB-006
- Requirement: REQ-CHA-030
- Group: Stand-ins
- Kind: setup
- Text: The hand test TC-CHA-035 shall be done on the host with the real sound server and the real page by the owner after any change of the speak-again call or of `sound.js`, and its result shall be written into the verification report.
- Rationale: no automated check reaches the sound server, the engine or the browser's autoplay; the fake of TR-VOICE-001 is only as good as this check shows (the stack has no sound server today, see TD-24 and TD-25).
- Credibility aspect: stand-in fidelity
- Verified by: verification report
- Status: Draft

### TR-VOICE-003 – sentences and order written by hand
- Applies to: TC-CHA-030, TC-CHA-031, TC-CHA-034
- Requirement: REQ-CHA-031
- Group: Exact values
- Kind: unit
- Text: The expected sentences and their order shall be written into the test by hand and not taken from the splitting code under test.
- Rationale: a split that is wrong in the same way on both sides would pass; the example "One. Two. Three." gives three calls by hand, and the markup example gives two calls.
- Credibility aspect: reference accuracy
- Verified by: known answer
- Status: Draft
