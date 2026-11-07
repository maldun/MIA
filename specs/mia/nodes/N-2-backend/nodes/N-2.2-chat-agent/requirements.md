# Requirements: Chat agent (N-2.2, low level)

**Parent:** `specs/mia/nodes/N-2-backend/requirements.md` (N-2)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The persona's side: the shared conversation, the answer queue, persona, mood, memory, behaviour rules, votes, adaptation, tasks and memos. Provides IF-201; consumes IF-202 (runs the answer pipelines), IF-204 (speech) and IF-102. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Groups
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | SA | Speak again: the answer is heard again through the voice route of live answers (A-132, TD-11). The older requirements of this file have no group yet; they predate the rule. | REQ-CHA-030, REQ-CHA-031, REQ-CHA-032, REQ-CHA-033, REQ-CHA-034, REQ-CHA-035, REQ-CHA-036 |

## Requirements

### REQ-CHA-001 – Chat events and streaming
- Level: low   Subject: ConversationCore
- Text: When the Chat agent receives a message through IF-201, it shall answer it as a stream of sentences with expression events.
- Rationale: refines REQ-BE-001
- Parent: REQ-BE-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the fake model each scripted answer arrives as ordered sentences
- Verified by: TC-CHA-001
- Status: Verified
- History: –

### REQ-CHA-002 – One shared MIA
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall answer all users in one conversation with one memory and one persona, and attribute each message to its sender.
- Rationale: refines REQ-BE-002
- Parent: REQ-BE-002
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: two users' messages appear with their names in the same history
- Verified by: TC-CHA-002
- Status: Verified
- History: –

### REQ-CHA-003 – Queue with positions
- Level: low   Subject: ConversationCore
- Text: While the model is busy, the Chat agent shall queue incoming chat messages, report each position through IF-201 and refuse a message only when the queue is full (at most 5 waiting messages in all and at most 2 per user).
- Rationale: refines REQ-BE-003
- Parent: REQ-BE-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: with 5 waiting messages the sixth is refused with a plain message; a third waiting message of one user is refused while another user can still send; positions are reported
- Verified by: TC-CHA-003
- Status: Verified
- History: –

### REQ-CHA-004 – Stop an answer
- Level: low   Subject: ConversationCore
- Text: When a user asks to stop, the Chat agent shall end the running generation.
- Rationale: refines REQ-BE-004
- Parent: REQ-BE-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: after a stop request no further sentence is sent (exact)
- Verified by: TC-CHA-004
- Status: Verified
- History: –

### REQ-CHA-005 – Bounded history
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall keep the visible history apart from the memory, bounded in size, and delete it after a confirmation by a user.
- Rationale: refines REQ-BE-005
- Parent: REQ-BE-005
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: the bound is held; deletion without confirmation is refused
- Verified by: TC-CHA-005
- Status: Approved
- Relaxed: TD-09
- Target: a user deletes the history on the page after a confirmation dialog, and the backend refuses a deletion without a confirmation
- History: A-69 (2026-11-01): Relaxed TD-09 (D-173)

### REQ-CHA-006 – Regenerate and speak again
- Level: low   Subject: ConversationCore
- Text: When a user requests it, the Chat agent shall regenerate the last answer or speak any answer again.
- Rationale: refines REQ-BE-006
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: two requests give a new answer and a new audio stream
- Verified by: TC-CHA-006
- Status: Verified
- History: –

### REQ-CHA-007 – Voice lines
- Level: low   Subject: ConversationCore
- Text: When a mood or event occurs, the Chat agent shall choose at random one of the voice lines assigned to it and stay silent if there is none.
- Rationale: refines REQ-BE-018
- Parent: REQ-BE-018
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-13: every mood of the map has a line or is declared silent; a missing file is logged and skipped
- Verified by: TC-CHA-007
- Status: Verified
- History: –

### REQ-CHA-008 – Persona from the file
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall behave as the shared persona file specifies, with its names, pronouns and form of address, and address every user as master unless the file says otherwise.
- Rationale: refines REQ-BE-021
- Parent: REQ-BE-021
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-8: check dialogues pass at a rate fixed in Plan against the recorded baseline, decided statistically
- Verified by: TC-CHA-008
- Status: Approved
- Relaxed: TD-10
- Target: AC-8 is decided: the check dialogues pass at the rate fixed in Plan against the recorded baseline
- History: A-69 (2026-11-01): Relaxed TD-10 (D-173)

### REQ-CHA-009 – Mood at all times
- Level: low   Subject: ConversationCore
- Text: While MIA is idle, thinking, speaking, waiting, greeting a user, reporting an error or offline, the Chat agent shall hold the corresponding mood, change it with events and settle it back over time.
- Rationale: refines REQ-BE-022
- Parent: REQ-BE-022
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-17: for each of the 7 situations the held mood equals the mood map
- Verified by: TC-CHA-009
- Status: Verified
- History: –

### REQ-CHA-010 – Score shifts the mood
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall shift the general mood by the overall feedback score.
- Rationale: refines REQ-BE-023
- Parent: REQ-BE-023
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-18: a scripted score change moves the mood offset in the right direction
- Verified by: TC-CHA-010
- Status: Verified
- History: –

### REQ-CHA-011 – Structured memory
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall keep facts, preferences and commitments as records with a kind, a time and a source, written in English, and give the model the most relevant records within a token budget.
- Rationale: refines REQ-BE-024; the design follows the literature (MemGPT, Generative Agents, Mem0, LongMemEval; specs/mia/eval-drafts/memory-design.md, D-78); English as the storage language by owner decision 2026-10-27 (D-83)
- Parent: REQ-BE-024
- Priority: Should
- Verification method: Measurement, Test
- Acceptance criterion: AC-24: (a) on the 11 holdout cases of the checked memory sample (specs/mia/eval-drafts/memory_sample.jsonl, labelled by the owner), 3 repeats, pin MP-light with the temperature of the skill memory_write, at least 9 of 11 cases are right (every wanted record is stored in English and nothing forbidden is stored); rule: at least 9 of 11 and a Wilson 95 % lower bound of 0.5, exact error rates for a good rate of 0.95 and a bad rate of 0.5 with the re-run rule: false alarm 0.0002, miss 0.064 (false_alarm.py); a failing check is re-run once with fresh repeats; (b) the memory block never exceeds memory_budget_tokens (test, exact) and on the 20 most recent user messages of the owner it costs fewer tokens than today's dreaming memory (tools/memory_cost.py)
- Verified by: TC-CHA-011
- Status: Verified
- History: A-12 (2026-10-27): reworded, was "keep structured facts, preferences and commitments linked to their source and retrieve what is relevant within the token budget" with AC-24 "the memory test set is passed at least as well as today's dreaming at equal or lower token cost" (owner: literature plus a checked sample of 30 instead of a large test set; n = 11 holdout cases can show a clear failure, not a small difference to dreaming). No Eval criterion line: the harness has no memory target and no suite EV-memory yet; the sample is scored by the same rules as tools/memory_dev_run.py, run by the verifier on the holdout

### REQ-CHA-012 – No memory from untrusted text
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall not store a fact about a user that came from web or file text.
- Rationale: refines REQ-BE-025
- Parent: REQ-BE-025
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: a page that states a fact about a user leaves the memory unchanged (exact)
- Verified by: TC-CHA-012
- Status: Verified
- History: –

### REQ-CHA-013 – Memory open to users
- Level: low   Subject: ConversationCore
- Text: When a user inspects, corrects or deletes a memory record, the Chat agent shall apply it and show the source of the record.
- Rationale: refines REQ-BE-026
- Parent: REQ-BE-026
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-24: the three actions work on a sample record
- Verified by: TC-CHA-013
- Status: Verified
- History: –

### REQ-CHA-014 – Silent repair of behaviour violations
- Level: low   Subject: ConversationCore
- Text: If a defined behaviour rule is violated, then the Chat agent shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory.
- Rationale: refines REQ-BE-027
- Parent: REQ-BE-027
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-25: the detectors keep their recorded precision and recall on the behaviour suite
- Verified by: TC-CHA-014
- Status: Verified
- History: –

### REQ-CHA-015 – Votes stored
- Level: low   Subject: ConversationCore
- Text: When a user votes, the Chat agent shall store the vote with user, time, subject and one of four categories (answer quality, reactions, character behaviour, service) and keep a score per category and overall.
- Rationale: refines REQ-BE-028
- Parent: REQ-BE-028
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-18: 100 % of scripted votes are stored complete and the scores equal their sums
- Verified by: TC-CHA-015
- Status: Verified
- History: –

### REQ-CHA-016 – A minus on a fact opens a case
- Level: low   Subject: ConversationCore
- Text: When a user gives a minus to a factual answer, the Chat agent shall open a benchmark case and leave the stated fact unchanged.
- Rationale: refines REQ-BE-029
- Parent: REQ-BE-029
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-18, AC-11: after the minus the answer text is unchanged (exact) and one case is proposed
- Verified by: TC-CHA-016
- Status: Verified
- History: –

### REQ-CHA-017 – Adaptation to negative feedback
- Level: low   Subject: ConversationCore
- Text: When a behaviour has received at least 5 net negative votes, the Chat agent shall show it with a chance of at most 1 % per opportunity and raise the chance again after positive votes.
- Rationale: refines REQ-BE-030
- Parent: REQ-BE-030
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-11: in 1000 opportunities after 5 net negative votes the behaviour appears at most 10 times
- Verified by: TC-CHA-017
- Status: Verified
- History: –

### REQ-CHA-018 – Counters visible and resettable
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall let every user see and reset the adaptation counters, and never apply the rule to facts or safety checks.
- Rationale: refines REQ-BE-031
- Parent: REQ-BE-031
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-11: a reset restores the default rate; a vote on a fact leaves counters of facts unchanged
- Verified by: TC-CHA-018
- Status: Verified
- History: –

### REQ-CHA-019 – Tasks and memos recited from records
- Level: low   Subject: ConversationCore
- Text: When a task falls due or a user asks, the Chat agent shall read the text of the task or memo from its record word for word.
- Rationale: refines REQ-BE-032
- Parent: REQ-BE-032
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12: 50 of 50 stored items are recited word for word on request and at their due time (exact)
- Verified by: TC-CHA-019
- Status: Verified
- History: –

### REQ-CHA-020 – State only through the storage interface
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall keep and read the conversation, memory, votes, tasks and memos only through the storage interface IF-102.
- Rationale: refines REQ-BE-074
- Parent: REQ-BE-074
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: no database driver is imported outside the storage client
- Verified by: TC-CHA-020
- Status: Verified
- History: –

### REQ-CHA-030 – Speak again is spoken
- Level: low   Subject: ConversationCore
- Text: When a user asks to speak a message of MIA again, the Chat agent shall have the stored text of that message spoken on the voice route that live answers use.
- Rationale: refines REQ-CHA-006; REQ-BE-006 says 'a new audio stream' but the check counted only audio_chunk events (D-276); the voice route is the sound server of live answers (A-132 option B). A message of MIA is any message with an id that MIA wrote: an answer, a spoken summary, a question of a skill (owner, D-277); a message of a user stays not_found (IF-201, unchanged)
- Parent: REQ-CHA-006
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: speak again of a stored answer of three sentences, and of a stored question of a skill, hands exactly their spoken sentences to the voice route; on the host the answer is heard
- Verified by: TC-CHA-030, TC-CHA-031, TC-CHA-035
- Status: Approved
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285)

### REQ-CHA-031 – Speak again keeps the order
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall hand the sentences of an answer that is spoken again to the voice route in the order of the answer.
- Rationale: refines REQ-CHA-006; the order of sentences is part of the voice (TD-11)
- Parent: REQ-CHA-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: the sentences of a stored answer reach the voice route in the order of the text (exact)
- Verified by: TC-CHA-030, TC-CHA-036
- Status: Approved
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285)

### REQ-CHA-032 – Stop ends speak again
- Level: low   Subject: ConversationCore
- Text: When a user presses stop, the Chat agent shall end a spoken-again playback that is running or waiting, also when no answer is being generated.
- Rationale: refines REQ-CHA-004; stop() today does nothing when no answer runs, and speak again has no answer running
- Parent: REQ-CHA-004
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: after a stop request no further sentence of the answer spoken again is handed to the voice route, and the playback in progress is cancelled
- Verified by: TC-CHA-032, TC-CHA-036, TC-CHA-035
- Status: Approved
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285)

### REQ-CHA-033 – Speak again without a voice route
- Level: low   Subject: ConversationCore
- Text: If the voice route is not available, then the Chat agent shall still answer a speak-again request with the number of sentences and log the failure once.
- Rationale: refines REQ-CHA-006; the chat continues without voice (IF-204, IF-101 audio_chunk); silent, one log line, no new text for the user (owner, D-277)
- Parent: REQ-CHA-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: with a failing voice route the request returns the sentence count, the next message is answered, one error line is logged and no text and no event but audio_chunk and chat_status is added to the page (A-133: the status is busy while the repeat runs)
- Verified by: TC-CHA-033
- Status: Approved
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285); AC-1 clarified in A-133 (the status events of REQ-CHA-035 are not an event added by the failure), confirmed by the owner 2026-11-08 (D-284)

### REQ-CHA-034 – One speak again at a time
- Level: low   Subject: ConversationCore
- Text: While a message is being spoken, the Chat agent shall have a spoken-again message wait until that speech has ended.
- Rationale: refines REQ-CHA-006; two voices at once are an echo (REQ-FE-011 for lines in the page); a speak-again during a live answer is queued behind the live voice (owner, D-277); the sound server takes one connection at a time, which TC-CHA-036 checks on the hand-over
- Parent: REQ-CHA-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: two speak-again requests in a row, and a speak-again while a live answer is spoken, reach the voice route one after the other, never overlapping (exact)
- Verified by: TC-CHA-034, TC-CHA-036
- Status: Approved
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285)

### REQ-CHA-035 – Stop is offered while a message is spoken again
- Level: low   Subject: ConversationCore
- Text: While a message is being spoken again or waits to be spoken again, the Chat agent shall report the status busy with the activity speaking.
- Rationale: refines REQ-CHA-032; the page offers its stop button only while the status is busy and speaking (REQ-CLV-002, mood.js followStatus), and a speak again has no running answer, so the host hand check TC-CHA-035 found no stop button during a repeat (owner, 2026-11-08; A-133). IF-101 chat_status already has these fields and values: no contract change
- Parent: REQ-CHA-032
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: with a fake voice route that blocks, after a speak-again request the chat_status event with busy true and activity speaking was published and the status says so, also for a second request that waits (exact); on the host the stop button is shown during the repeat
- Verified by: TC-CHA-037, TC-CHA-035
- Status: Approved
- Group: SA
- History: proposed in A-133; approved by the owner 2026-11-08 (D-283)

### REQ-CHA-036 – The status returns when the speak again has ended
- Level: low   Subject: ConversationCore
- Text: When the last message that is spoken again has been spoken or stopped, the Chat agent shall report the status as it was before, not busy and without the activity speaking.
- Rationale: refines REQ-CHA-035; a stop button that stays after the voice has ended would be wrong; an answer that is running keeps its own status (A-133)
- Parent: REQ-CHA-035
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: after the playback ended by itself, and after a stop, the last chat_status event has busy false and an activity other than speaking, and the status says so (exact)
- Verified by: TC-CHA-037
- Status: Approved
- Group: SA
- History: proposed in A-133; approved by the owner 2026-11-08 (D-283)

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-201 – Chat turn service (API to chat agent)
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall provide the API and accounts with the chat turn interface IF-201 as specified in contracts/IF-201-chat-turn.md (send a message for an account, stop, history, status, and the stream of events of the answer).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: REQ-BE-001, REQ-BE-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: the contract suite test_if_201_chat_turn.py passes against the mock (stage 1) and the Chat agent (stage 2)
- Verified by: TC-IF-201-01..04
- Status: Verified
- History: v0, amendment 5/7 (2026-10-25)
