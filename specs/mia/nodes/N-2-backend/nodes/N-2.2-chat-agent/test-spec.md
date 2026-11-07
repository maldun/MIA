# Test specification: Chat agent (N-2.2)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md   **Status:** Draft (Plan for node N-2.2, 2026-10-26)

Tests of this part alone against the mocks of its neighbours. Interfaces: IF-201 (provider), each tested by its contract suite against the mock and the real part. Behaviour that depends on the model is decided by eval suites on the pinned model (`eval-spec.md`); here the fake model server stands in for it. Existing tests (`tests/test_*.py`) are extended, not rewritten. Stages (M27): 1 = commit gate, under 2 minutes; 2 = up to 10 minutes; 3 = up to 30 minutes; 4 = eval runs and measurements.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-CHA-001 | REQ-CHA-001 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-1: with the fake model each scripted answer arrives as ordered sentences | as stated |
| TC-CHA-002 | REQ-CHA-002 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: two users' messages appear with their names in the same history | as stated |
| TC-CHA-003 | REQ-CHA-003 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-19: with 5 waiting messages the sixth is refused with a plain message; a third waiting message of one user is refused while another user can still send; positions are reported | as stated |
| TC-CHA-004 | REQ-CHA-004 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: after a stop request no further sentence is sent | exact |
| TC-CHA-005 | REQ-CHA-005 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: the bound is held; deletion without confirmation is refused | as stated |
| TC-CHA-006 | REQ-CHA-006 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-1: two requests give a new answer and a new audio stream | as stated |
| TC-CHA-007 | REQ-CHA-007 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-13: every mood of the map has a line or is declared silent; a missing file is logged and skipped | as stated |
| TC-CHA-008 | REQ-CHA-008 | Eval / measurement | 4 | the suite or measurement named in the criterion, on the pinned model (agent-app rules: dev split for feedback, holdout for the decision) | AC-8: check dialogues pass at a rate fixed in Plan against the recorded baseline, decided statistically | per the criterion; never decided on one run |
| TC-CHA-009 | REQ-CHA-009 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-17: for each of the 7 situations the held mood equals the mood map | as stated |
| TC-CHA-010 | REQ-CHA-010 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-18: a scripted score change moves the mood offset in the right direction | as stated |
| TC-CHA-011 | REQ-CHA-011 | Measurement + component | 4 | (a) the holdout cases of the memory sample scored as in tools/memory_dev_run.py, run by the verifier and never by the implementer, pin MP-light, 3 repeats; (b) tests/test_memory_records.py (budget, exact) and tools/memory_cost.py on the owner's recent messages | AC-24: at least 9 of 11 holdout cases right (Wilson lower bound 0.5); the block within the budget and cheaper than dreaming | rule threshold, false alarm 0.0002 and miss 0.064 (n 11, good 0.95, bad 0.5, with the re-run); never decided on one run |
| TC-CHA-012 | REQ-CHA-012 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-6: a page that states a fact about a user leaves the memory unchanged | exact |
| TC-CHA-013 | REQ-CHA-013 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-24: the three actions work on a sample record | as stated |
| TC-CHA-014 | REQ-CHA-014 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-25: the detectors keep their recorded precision and recall on the behaviour suite | as stated |
| TC-CHA-015 | REQ-CHA-015 | Component | 1 | unit test with the fake model server and the mocks of the interfaces | AC-18: 100 % of scripted votes are stored complete and the scores equal their sums | as stated |
| TC-CHA-016 | REQ-CHA-016 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-18, AC-11: after the minus the answer text is unchanged and one case is proposed | exact |
| TC-CHA-017 | REQ-CHA-017 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-11: in 1000 opportunities after 5 net negative votes the behaviour appears at most 10 times | as stated |
| TC-CHA-018 | REQ-CHA-018 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-11: a reset restores the default rate; a vote on a fact leaves counters of facts unchanged | as stated |
| TC-CHA-019 | REQ-CHA-019 | Component | 2 | component test with the mocks of the neighbouring interfaces | AC-12: 50 of 50 stored items are recited word for word on request and at their due time | exact |
| TC-CHA-020 | REQ-CHA-020 | Inspection | 1 | the code and the log files of the repository | AC-15: no database driver is imported outside the storage client | as stated |
| TC-CHA-030 | REQ-CHA-030, REQ-CHA-031 | Component | 1 | `tests/test_chat_speak_again.py` with the fake voice route (A-132): a function that records the texts it gets and `should_stop` | AC-1: speak again of a stored answer of three sentences, and of a stored question of a skill, hands exactly their spoken sentences, in order, to the voice route; the result and the audio_chunk events are as before | exact |
| TC-CHA-031 | REQ-CHA-030 | Component | 1 | same test file; a stored answer whose text carries markup and a stage direction | AC-1: the voice route gets the stored text after the speech filter, nothing that the page does not show | exact |
| TC-CHA-032 | REQ-CHA-032 | Component | 2 | same test file; the fake voice route blocks until its `should_stop` is true; no answer is being generated | AC-1: a stop request makes `should_stop` true and ends the blocked playback; no further sentence is handed over | the end within 1 s (test limit; the fake polls every 0.05 s) |
| TC-CHA-033 | REQ-CHA-033 | Component | 1 | same test file; the fake voice route raises `OSError` | AC-1: the request returns the sentence count, the next message is answered, one error line is logged, no text and no event but audio_chunk and chat_status is added to the page (A-133: the status is busy while the repeat runs) | exact |
| TC-CHA-034 | REQ-CHA-034 | Component | 2 | same test file; the fake voice route sleeps 0.2 s per call and records start and end times | AC-1: with two requests in a row the second playback starts after the first has ended | exact order, no overlap |
| TC-CHA-035 | REQ-CHA-030, REQ-CHA-032 | Demonstration | 4 | the short hand check on the host with the real sound server and the real engine (the owner, about 5 minutes): only what automation cannot hear | AC-1: the speaker button is heard in the same voice and in order; Stop silences it; it is heard right after a Stop | as stated |
| TC-CHA-036 | REQ-CHA-031, REQ-CHA-032, REQ-CHA-034 | Component | 2 | `tests/test_sound_server_handover.py` (A-132): the real `SoundServer` and `SoundHandler` of `speak.py` on a localhost port with a fake speaker as sink (records each chunk it is asked to play, in order, and honours `cancelled`), real TCP clients | AC-1: the sentences of one request reach the sink in order; a second request that arrives during the first is played after it; a client that closes its connection cancels the rest | exact order, no overlap, cancel within 2 s (test limit) |
| TC-CHA-037 | REQ-CHA-035, REQ-CHA-036 | Component | 1 | `tests/test_chat_speak_again.py` with the fake voice route (A-133): the events `chat_status` and the status of the service | AC-1: while a speak again runs or waits the status is busy with the activity speaking; after it ended or was stopped it is not busy and not speaking | exact |

## Scenarios (speak again, A-132; the older checks of this file have none yet)

### TC-CHA-030 – speak again goes to the voice route
- Verifies: REQ-CHA-030, REQ-CHA-031
- Given: the Chat agent with a fake voice route, a stored answer "One. Two. Three." and a stored question of a skill "Shall I go on?"
- When: a user asks to speak the answer again, and then the question
- Then: the fake voice route got `One.`, `Two.`, `Three.` in that order, then `Shall I go on?`, and nothing else; the results are `{"sentences": 3}` and `{"sentences": 1}`; the audio_chunk events have the index 0, 1, 2 and 0

### TC-CHA-031 – the stored text is spoken
- Verifies: REQ-CHA-030
- Given: a stored answer "*waves* Hello **there**. Bye." and the fake voice route
- When: a user asks to speak it again
- Then: the fake got `Hello there.` and `Bye.` (no mark, no stage direction), the same words the speech filter gives a live answer

### TC-CHA-032 – stop ends speak again
- Verifies: REQ-CHA-032
- Given: a stored answer of three sentences, a fake voice route that blocks until it is told to stop, and no answer being generated
- When: a user asks to speak it again, and then presses stop
- Then: the fake was told to stop, its call ended, and no further sentence was handed over; a stop with nothing speaking changes nothing

### TC-CHA-033 – no voice route, no failure
- Verifies: REQ-CHA-033
- Given: a fake voice route that fails with a connection error
- When: a user asks to speak a stored answer of two sentences again, and then sends a normal message
- Then: the first request returned `{"sentences": 2}`, one error line is in the log, no text and no event but audio_chunk and chat_status was added for the page, the status is not busy afterwards, the normal message was answered

### TC-CHA-034 – one speak again at a time
- Verifies: REQ-CHA-034
- Given: a fake voice route whose call takes 0.2 s and records its start and end
- When: a user asks to speak answer 1 again and at once answer 2 again
- Then: the call of answer 2 started after the call of answer 1 had ended

### TC-CHA-035 – short hand check on the host
- Verifies: REQ-CHA-030, REQ-CHA-032
- Given: MIA running on the host with the real sound server and engine, the page open on localhost, an answer of three or more sentences just spoken
- When: the owner presses the speaker button under the answer; presses it and then Stop; presses Stop while an answer is spoken and the button within 3 s
- Then: the answer is heard again in order in the same voice; the repeat ends at Stop; the repeat is heard right after a Stop. Everything else (order, queue behind a live answer, failure of the route, mute) is checked by the automatic checks and is not part of this check

### TC-CHA-036 – the hand-over to the sound server
- Verifies: REQ-CHA-031, REQ-CHA-032, REQ-CHA-034
- Given: the real `SoundServer` and `SoundHandler` on a localhost port with a fake speaker as sink that records every chunk in order and stops on `cancelled`
- When: client 1 sends the sentences `One.`, `Two.`, `Three.` and the end marker slowly; client 2 connects during that and sends `Four.` and the end marker; in a second run client 1 closes its connection after `One.`
- Then: the sink got `One.`, `Two.`, `Three.` and only then `Four.`; in the second run it got `One.` and not `Two.` or `Three.`

### TC-CHA-037 – the status while a message is spoken again
- Verifies: REQ-CHA-035, REQ-CHA-036
- Given: the Chat agent with a fake voice route that blocks until it is told to stop, a stored answer of two sentences, no answer being generated
- When: a user asks to speak it again; later the user presses stop; in a second run the fake does not block and the playback ends by itself
- Then: after the request a chat_status event with busy true and activity speaking was published and the status says the same; after the stop, and after the playback that ended by itself, the last chat_status event has busy false and an activity other than speaking, and the status says the same

## Assumptions (checked in validation)

- ASM-N2-001: the model server is replaced by the fake model server of `pipeline.py` in all stage 1 to 3 tests; no test needs a GPU before stage 4.
- ASM-N2-002: the storage is the mock of IF-102 until N-3 is integrated (step 1 of N-0).
