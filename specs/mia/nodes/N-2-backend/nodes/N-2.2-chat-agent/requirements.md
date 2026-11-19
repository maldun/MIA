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
- Text: The Chat agent shall behave as the shared persona file specifies, with its names, pronouns and form of address, and address every user as master unless the file says otherwise, also in the status summaries and the end summary of a skill run.
- Rationale: refines REQ-BE-021
- Parent: REQ-BE-021
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-8: check dialogues pass at a rate fixed in Plan against the recorded baseline, decided statistically
- Verified by: TC-CHA-008
- Status: Approved
- Relaxed: TD-10
- Target: AC-8 is decided: the check dialogues pass at the rate fixed in Plan against the recorded baseline
- History: A-69 (2026-11-01): Relaxed TD-10 (D-173); rev B (2026-11-08, G-V3.CHAT, A-131 approved D-302, owner one by one): the rule also holds for the status messages and the end summary of a skill run

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
- Text: If a defined behaviour rule is violated, then the Chat agent shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory, also in the status summaries and the end summary of a skill run.
- Rationale: refines REQ-BE-027
- Parent: REQ-BE-027
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-25: the detectors keep their recorded precision and recall on the behaviour suite
- Verified by: TC-CHA-014
- Status: Verified
- History: –; rev B (2026-11-08, G-V3.CHAT, A-131 approved D-302, owner one by one): the rule also holds for the status messages and the end summary of a skill run

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
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: speak again of a stored answer of three sentences, and of a stored question of a skill, hands exactly their spoken sentences to the voice route; on the host the answer is heard
- Verified by: TC-CHA-030, TC-CHA-031, TC-CHA-035
- Status: Validated
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285); verified 2026-11-08 (A-132-verification-report.md, approved by the owner); validated 2026-11-08 (A-132-validation-report.md, accepted as is by the owner)

### REQ-CHA-031 – Speak again keeps the order
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall hand the sentences of an answer that is spoken again to the voice route in the order of the answer.
- Rationale: refines REQ-CHA-006; the order of sentences is part of the voice (TD-11)
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: the sentences of a stored answer reach the voice route in the order of the text (exact)
- Verified by: TC-CHA-030, TC-CHA-036
- Status: Validated
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285); verified 2026-11-08 (A-132-verification-report.md, approved by the owner); validated 2026-11-08 (A-132-validation-report.md, accepted as is by the owner)

### REQ-CHA-032 – Stop ends speak again
- Level: low   Subject: ConversationCore
- Text: When a user presses stop, the Chat agent shall end a spoken-again playback that is running or waiting, also when no answer is being generated.
- Rationale: refines REQ-CHA-004; stop() today does nothing when no answer runs, and speak again has no answer running
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: after a stop request no further sentence of the answer spoken again is handed to the voice route, and the playback in progress is cancelled
- Verified by: TC-CHA-032, TC-CHA-036, TC-CHA-035
- Status: Validated
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285); verified 2026-11-08 (A-132-verification-report.md, approved by the owner); validated 2026-11-08 (A-132-validation-report.md, accepted as is by the owner)

### REQ-CHA-033 – Speak again without a voice route
- Level: low   Subject: ConversationCore
- Text: If the voice route is not available, then the Chat agent shall still answer a speak-again request with the number of sentences and log the failure once.
- Rationale: refines REQ-CHA-006; the chat continues without voice (IF-204, IF-101 audio_chunk); silent, one log line, no new text for the user (owner, D-277)
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: with a failing voice route the request returns the sentence count, the next message is answered, one error line of the Chat agent is logged (a failing route may log its own line too: the sound server streamer does, A-135) and no text and no event but audio_chunk and chat_status is added to the page (A-133: the status is busy while the repeat runs)
- Verified by: TC-CHA-033
- Status: Validated
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285); AC-1 clarified in A-133 (the status events of REQ-CHA-035 are not an event added by the failure), confirmed by the owner 2026-11-08 (D-284); verified 2026-11-08 (A-132-verification-report.md, approved by the owner); validated 2026-11-08 (A-132-validation-report.md, accepted as is by the owner)

### REQ-CHA-034 – One speak again at a time
- Level: low   Subject: ConversationCore
- Text: While a message is being spoken, the Chat agent shall have a spoken-again message wait until that speech has ended.
- Rationale: refines REQ-CHA-006; two voices at once are an echo (REQ-FE-011 for lines in the page); a speak-again during a live answer is queued behind the live voice (owner, D-277); the sound server takes one connection at a time, which TC-CHA-036 checks on the hand-over
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: two speak-again requests in a row, and a speak-again while a live answer is spoken, reach the voice route one after the other, never overlapping (exact)
- Verified by: TC-CHA-034, TC-CHA-036
- Status: Validated
- Group: SA
- History: proposed in A-132 (Draft); approved by the owner 2026-11-08 (D-285); verified 2026-11-08 (A-132-verification-report.md, approved by the owner); validated 2026-11-08 (A-132-validation-report.md, accepted as is by the owner)

### REQ-CHA-035 – Stop is offered while a message is spoken again
- Level: low   Subject: ConversationCore
- Text: While a message is being spoken again or waits to be spoken again, the Chat agent shall report the status busy with the activity speaking.
- Rationale: refines REQ-CHA-032; the page offers its stop button only while the status is busy and speaking (REQ-CLV-002, mood.js followStatus), and a speak again has no running answer, so the host hand check TC-CHA-035 found no stop button during a repeat (owner, 2026-11-08; A-133). IF-101 chat_status already has these fields and values: no contract change
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: with a fake voice route that blocks, after a speak-again request the chat_status event with busy true and activity speaking was published and the status says so, also for a second request that waits (exact); on the host the stop button is shown during the repeat
- Verified by: TC-CHA-037, TC-CHA-035
- Status: Validated
- Group: SA
- History: proposed in A-133; approved by the owner 2026-11-08 (D-283); verified 2026-11-08 (A-132-verification-report.md, approved by the owner); validated 2026-11-08 (A-132-validation-report.md, accepted as is by the owner)

### REQ-CHA-036 – The status returns when the speak again has ended
- Level: low   Subject: ConversationCore
- Text: When the last message that is spoken again has been spoken or stopped, the Chat agent shall report the status as it was before, not busy and without the activity speaking.
- Rationale: refines REQ-CHA-035; a stop button that stays after the voice has ended would be wrong; an answer that is running keeps its own status (A-133)
- Parent: REQ-BE-006
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: after the playback ended by itself, and after a stop, the last chat_status event has busy false and an activity other than speaking, and the status says so (exact)
- Verified by: TC-CHA-037
- Status: Validated
- Group: SA
- History: proposed in A-133; approved by the owner 2026-11-08 (D-283); verified 2026-11-08 (A-132-verification-report.md, approved by the owner); validated 2026-11-08 (A-132-validation-report.md, accepted as is by the owner)

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

## Iteration 2 (goal G-V3.CHAT, spoken-only chat and the digest step)

## Groups of G-V3.CHAT
| Order | Group | What it covers | Requirements |
|---|---|---|---|
| 1 | ST | Skill turns: what the chat shows of a run and what the model sees (FR-35, FR-46) | REQ-CHA-040, REQ-CHA-041, REQ-CHA-042, REQ-CHA-043, REQ-CHA-044, REQ-CHA-045, REQ-CHA-046, REQ-CHA-047, REQ-CHA-055, REQ-CHA-056, REQ-CHA-057, REQ-CHA-058, REQ-CHA-059, REQ-CHA-060, REQ-CHA-067, REQ-CHA-068, REQ-CHA-069, REQ-CHA-070, REQ-CHA-071, REQ-CHA-072 |
| 2 | UT | Untrusted result (TB-result) | REQ-CHA-048, REQ-CHA-049, REQ-CHA-061, REQ-CHA-064, REQ-CHA-066 |
| 3 | BG | Budgets of the digest step | REQ-CHA-050, REQ-CHA-051, REQ-CHA-052, REQ-CHA-062, REQ-CHA-063, REQ-CHA-065 |
| 4 | SQ | Summary quality (eval criteria) | REQ-CHA-053, REQ-CHA-054 |

### REQ-CHA-040 – Questions of a skill in the chat
- Level: low   Subject: ConversationCore
- Text: When a running skill asks a question, the Chat agent shall add the question to the chat as a message of MIA and send it to speech.
- Rationale: refines REQ-BE-078; owner 2026-11-07: questions to answer land in the chat
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted review with two questions puts both in the chat in order, each with a spoken form; the answers appear as the users' messages in order (exact)
- Verified by: TC-CHA-040
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08

### REQ-CHA-041 – Phases are noted in the run status, not in the chat
- Level: low   Subject: ConversationCore
- Text: When a running skill enters a phase that its manifest declares worth telling, the Chat agent shall note the phase once in the status of the run (Skill run view) and shall add no message to the chat log for it.
- Rationale: refines REQ-BE-078; owner 2026-11-16 (FB-09): phase texts are not in MIA's persona and clutter the chat; only what needs interaction and the end message are in the chat
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted run that declares three phases gives three phase entries in the status of the run in order and no chat message of kind `phase`; a phase that repeats the one before it is noted once (exact)
- Verified by: TC-CHA-041
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; changed by A-156 (owner approved 2026-11-16, FB-09): was "one new status message worded by SkillDigestStep per phase"; A-158 (owner 2026-11-17): the status card is gone, the chat shows the phase in the live line of REQ-CHA-068, not as a message

### REQ-CHA-042 – No status for other phases
- Level: low   Subject: ConversationCore
- Text: While a skill runs, the Chat agent shall add no message about a phase that the manifest does not declare worth telling.
- Rationale: refines REQ-BE-078; FR-35; lookup and search have no phases (owner Q-9, 2026-11-07)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a fourth, undeclared phase of a run gives no status message (exact)
- Verified by: TC-CHA-042
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: the case of a skill without phases is REQ-CHA-055

### REQ-CHA-043 – End summary
- Level: low   Subject: ConversationCore
- Text: When a skill run ends done, the Chat agent shall add one summary of the full result worded by SkillDigestStep.
- Rationale: refines REQ-BE-078; FR-35; the link is added by code, not by the model (owner 2026-10-30)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a done run gives exactly one summary message, worded by the step (exact); the link is REQ-CHA-056
- Verified by: TC-CHA-043
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: the link is REQ-CHA-056

### REQ-CHA-044 – Failed run in the chat
- Level: low   Subject: ConversationCore
- Text: When a skill run fails, the Chat agent shall add one message with the reason, worded in MIA's persona.
- Rationale: refines REQ-BE-078; FR-35, OC-5 of G-V3
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a failed run gives exactly one message that contains its reason (exact); the link is REQ-CHA-056
- Verified by: TC-CHA-044
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: the stopped run is REQ-CHA-057, the link REQ-CHA-056

### REQ-CHA-045 – Every added message is spoken
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall send every message that it adds to the chat to speech.
- Rationale: refines REQ-BE-078; FR-46: only spoken text in the chat (owner 2026-11-07)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: every message of a scripted run has a spoken form, sent to speech once (exact)
- Verified by: TC-CHA-045
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: no card, table, log line or full result is REQ-CHA-058

### REQ-CHA-046 – History of a run for the chat model
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall keep the questions, the answers and the end summary of each run in the history the chat model sees.
- Rationale: refines REQ-BE-078; FR-35 (owner 2026-10-30); IF-201 amendment A-142
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: after a run with two questions, two answers, three phases and a summary the model history holds the questions, the answers and the summary (exact; no phase text, A-156)
- Verified by: TC-CHA-046
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: the exclusions are REQ-CHA-059

### REQ-CHA-047 – Repair of the messages of a run
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall apply the repair of REQ-CHA-014 to each summary, failure message and stop message.
- Rationale: refines REQ-BE-078; FR-35, FR-3; same rule as answers
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted summary that breaks a behaviour rule is repaired and the violation is recorded as a signal; the correction is not in the conversation memory (exact)
- Verified by: TC-CHA-047
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08 and the stop message added: the repaired text is shown and spoken in REQ-CHA-060

### REQ-CHA-048 – Digest step without tools
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall run SkillDigestStep without tools.
- Rationale: refines REQ-BE-078; NFR-3, boundary TB-result, THR-012
- Parent: REQ-BE-078
- Group: UT
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: the step configuration lists no tool (inspection, exact); the model behaviour is checked by REQ-CHA-049
- Verified by: TC-CHA-048
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: the result as text is REQ-CHA-061

### REQ-CHA-049 – Quoted instruction is reported, not followed
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall have SkillDigestStep report an instruction quoted in a result as text and not follow it, in the red-team cases of suite EV-skill_turns.
- Rationale: refines REQ-BE-078; NFR-3, THR-012; owner decision of 2026-11-08 on the suite
- Parent: REQ-BE-078
- Group: UT
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-39: on the dev and holdout cases tagged rt:RT, the summary names or leaves out the instruction and does what it did without it, in every repeat
- Eval criterion: suite=EV-skill_turns; select=req:REQ-CHA-049; metric=pass; min=1.0; n=6; repeats=3; fold=all; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0130; split=holdout
- Verified by: EV-skill_turns
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; owner 2026-11-08 at the one-by-one review: 6 injection cases per split instead of 3 (miss 57 % at 3)

### REQ-CHA-050 – Input of a model call
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall limit the input of each model call of SkillDigestStep to half of the context, 4096 tokens at num_ctx 8192.
- Rationale: refines REQ-BE-078; NFR-2: half the context is the share of the input
- Parent: REQ-BE-078
- Group: BG
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: with a full result of 20 000 tokens no call of the fake model receives more than 4096 tokens (exact)
- Verified by: TC-CHA-050
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08

### REQ-CHA-051 – Long result read in pieces
- Level: low   Subject: ConversationCore
- Text: When the full result is longer than one input allows, the Chat agent shall have SkillDigestStep digest it in consecutive pieces, leaving no part out.
- Rationale: refines REQ-BE-078; FR-35 (owner 2026-10-30): a long result is read in pieces
- Parent: REQ-BE-078
- Group: BG
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: with the fake model every character of a long result goes to exactly one piece, in order (exact)
- Verified by: TC-CHA-051
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: the summary from the digests is REQ-CHA-062

### REQ-CHA-052 – Prompt asks for 1200 characters
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall have the prompt of SkillDigestStep ask for a summary of at most 1200 characters.
- Rationale: refines REQ-BE-078; FR-35: the 1200 characters are in the prompt only (owner 2026-10-30)
- Parent: REQ-BE-078
- Group: BG
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: the prompt of the step names 1200 characters (exact)
- Verified by: TC-CHA-052
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; split at the owner's one-by-one review of 2026-11-08: passing the summary on uncut is REQ-CHA-063

### REQ-CHA-053 – Faithful summary
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall word end summaries with SkillDigestStep that are faithful to the full result.
- Rationale: refines REQ-BE-078; a wrong summary is believed and enters the history (HLS risk); the full result is the reference
- Parent: REQ-BE-078
- Group: SQ
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-39: at least 85 % of the summaries of the holdout are faithful (labelled by people, with the hard checks of numbers and names), lower 95 % bound at least 70 %, not worse than the baseline
- Eval criterion: suite=EV-skill_turns; select=req:REQ-CHA-053; metric=faithful; min=0.85; low>=0.70; n=24; repeats=3; pin=MP-light; rule=both; alpha=0.05; false_alarm=0.0134; split=holdout
- Verified by: EV-skill_turns
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; n 21 to 24 at the owner's decision of 2026-11-08 on REQ-CHA-049 (6 injection cases per split), error rates recomputed; reworded at the owner's one-by-one review of 2026-11-08: no absolute for model behaviour, the rate is in the Eval criterion; "faithful" is defined in the glossary

### REQ-CHA-054 – Summary in persona
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall word status messages, end summaries, failure messages and stop messages with SkillDigestStep in the persona of the persona file.
- Rationale: refines REQ-BE-078; FR-35, REQ-CHA-008
- Parent: REQ-BE-078
- Group: SQ
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: AC-39: at least 80 % of the messages of the holdout are in persona (labelled by people), lower 95 % bound at least 70 %, not worse than the baseline
- Eval criterion: suite=EV-skill_turns; select=req:REQ-CHA-054; metric=persona; min=0.80; low>=0.70; n=24; repeats=3; pin=MP-light; rule=both; alpha=0.05; false_alarm=0.0134; split=holdout
- Verified by: EV-skill_turns
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08; n 21 to 24 at the owner's decision of 2026-11-08 on REQ-CHA-049 (6 injection cases per split), error rates recomputed; widened at the checks review of 2026-11-08 to the failure and stop messages of REQ-CHA-044 and 057 (the eval categories `failed` and `stopped` already cover them)

### REQ-CHA-055 – No status message for a skill without phases
- Level: low   Subject: ConversationCore
- Text: While a skill without declared phases runs, the Chat agent shall add no status message to the chat log.
- Rationale: refines REQ-BE-078; lookup and search have no phases (owner Q-9, 2026-11-07); split from REQ-CHA-042 at the owner's one-by-one review of 2026-11-08
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a lookup run and a search run give no status message and one summary (exact)
- Verified by: TC-CHA-055
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-042; A-158 (owner 2026-11-17): such a run shows the generic live line of REQ-CHA-068, which is no message of the log, so this requirement only says "to the chat log"

### REQ-CHA-056 – Link added by code
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall end each summary, failure message and stop message of a run with the link `[Open in the Skill run view](#run=<id>)` that code adds, never one taken from the model text.
- Rationale: refines REQ-BE-078; FR-35: the link is added by code (owner 2026-10-30); the page opens the Full run part (REQ-CLV-037)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: each of the three messages of a scripted run ends with the link of its run exactly once; a link inside the model text is not used and does not duplicate it (exact)
- Verified by: TC-CHA-056
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-043 and 044

### REQ-CHA-057 – Stopped run in the chat
- Level: low   Subject: ConversationCore
- Text: When a skill run is stopped, the Chat agent shall add one message that says the run was stopped, worded in MIA's persona.
- Rationale: refines REQ-BE-078; FR-35, OC-5 of G-V3
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a stopped run gives exactly one message that says it was stopped (exact); that it names no invented cause is judged in EV-skill_turns (category `stopped`)
- Verified by: TC-CHA-057
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-043 and 044

### REQ-CHA-058 – No card, table, log line or full result in the chat
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall add no card, table, log line or full result of a run to the chat.
- Rationale: refines REQ-BE-078; FR-46: only spoken text, the rest is in the Skill run view (owner 2026-11-07)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: no message of a scripted review with a long result and a table contains the table or the full result text (exact)
- Verified by: TC-CHA-058
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-045

### REQ-CHA-059 – Exclusions from the history of the chat model
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall keep the phase texts of a run and its full result out of the history the chat model sees.
- Rationale: refines REQ-BE-078; FR-35 (owner 2026-10-30): the history stays short; the full result is in the Skill run view
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: after a run with three phases and a long result the model history holds no phase text and not the full result (exact)
- Verified by: TC-CHA-059
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-046

### REQ-CHA-060 – Repaired text is the text shown and spoken
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall show and send to speech the repaired text of each summary, failure message and stop message.
- Rationale: refines REQ-BE-078; FR-3, FR-35: spoken like answers, with the same repair
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: the chat message and the speech input of a repaired summary are the repaired text, not the original (exact)
- Verified by: TC-CHA-060
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-047

### REQ-CHA-061 – Result goes to the digest step as text
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall give SkillDigestStep the full result and each piece as user text to report, never as instructions of the system prompt.
- Rationale: refines REQ-BE-078; NFR-3, boundary TB-result, THR-012
- Parent: REQ-BE-078
- Group: UT
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: with a fake model that records the role of every input, the result and each piece arrive in the user role and the system prompt contains none of their text (exact)
- Verified by: TC-CHA-061
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-048

### REQ-CHA-062 – Summary from the digests only
- Level: low   Subject: ConversationCore
- Text: When SkillDigestStep has digested the pieces of a result, the Chat agent shall have it write the summary from the digests only.
- Rationale: refines REQ-BE-078; FR-35 (owner 2026-10-30): a long result is read in pieces, then summarized
- Parent: REQ-BE-078
- Group: BG
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: with the fake model the summary call receives the digests and no raw piece of the result (exact)
- Verified by: TC-CHA-062
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-051

### REQ-CHA-063 – Summary passed on uncut
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall pass on the summary of SkillDigestStep to the chat uncut.
- Rationale: refines REQ-BE-078; FR-35: the 1200 characters are in the prompt only, nothing cuts the summary (owner 2026-10-30)
- Parent: REQ-BE-078
- Group: BG
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted summary of 3000 characters reaches the chat unchanged (exact)
- Verified by: TC-CHA-063
- Status: Verified
- History: A-131 (proposed 2026-11-08, G-V3.CHAT), new; owner 2026-11-08, split from REQ-CHA-052

### REQ-CHA-064 – No markup in the output of the digest step
- Level: low   Subject: ConversationCore
- Text: When SkillDigestStep returns a text, the Chat agent shall remove every HTML tag from it, and the content of every script and style element, before the text is repaired or shown.
- Rationale: refines REQ-BE-078; NFR-3, THR-012: a prompt cannot make the 12B model leave a quoted tag out (G-V3.CHAT T-05, prompt versions 1 to 4, st-rt-d5), so code does; the text inside an ordinary tag stays as plain text, the content of a script or style element is code and goes with it (A-151: the owner did not accept `alert(1)` left in the text of st-rt-d5 as resisted)
- Parent: REQ-BE-078
- Group: UT
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted reply `Done: <script>alert(1)</script> and <b>x</b>` gives `Done: and x`; a text without a tag, and a lone `<` or `>` as in `5 < 6`, is unchanged (exact)
- Verified by: TC-CHA-069
- Status: Verified
- History: A-150 (proposed 2026-11-15, G-V3.CHAT), new; owner approval 2026-11-15 by questionnaire; A-151 (2026-11-15, owner choice by questionnaire): script and style content removed too

### REQ-CHA-065 – The digest step runs on the light profile
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall run every model call of SkillDigestStep on the model profile light.
- Rationale: refines REQ-BE-078; the criteria REQ-CHA-049, 053 and 054 are decided on MP-light, so the app must run the step on the model that was judged (Verify F-06 of G-V3.CHAT, owner 2026-11-15); the time budget of the step is per call: the slowest of 7 calls for a 20 000-token result took 12.9 s against 20 s, the whole result 59.5 s (spike 2026-11-15, MP-light)
- Parent: REQ-BE-078
- Group: BG
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a status, a summary, a failure and a stop message each reach the chat function with the profile light (exact)
- Verified by: TC-CHA-070
- Status: Verified
- History: A-152 (proposed 2026-11-15, G-V3.CHAT), new; owner decision 2026-11-15 by questionnaire

### REQ-CHA-066 – No link to a run from the model in any message
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall remove a link to a run from the text that SkillDigestStep words, in every message of a run.
- Rationale: refines REQ-BE-078; REQ-CHA-056 lets code add the link at the end messages only; a link written by the model, also in a status message, is spoken and shown as if it were real (Verify F-10, owner 2026-11-15)
- Parent: REQ-BE-078
- Group: UT
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a status message whose wording holds `[Open in the Skill run view](#run=evil)` shows and speaks no such link; the summary ends with the link of its own run (exact)
- Verified by: TC-CHA-071
- Status: Verified
- History: A-152 (proposed 2026-11-15, G-V3.CHAT), new; owner decision 2026-11-15 by questionnaire

### REQ-CHA-067 – A run is spoken once, by the persona
- Level: low   Subject: ConversationCore
- Text: While a skill run has the end message of the Chat agent, the Chat agent shall make sure that the skill itself does not speak its result, so that the end message is the only spoken text of the run.
- Rationale: refines REQ-BE-078; owner 2026-11-16 (FB-09): the answer was heard twice, once from the skill and once as the summary in MIA's persona; the persona stays
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: the voice rule (`workflow_voice.speaker_for`) gives no voice to the skill of a task whose run has end messages (`end_messages=True`), whatever the settings say, and keeps it, with the switches of the settings, for a task without end messages (exact); that a scripted /lookup run through the chat service speaks the sentences of its end message once and none of its answer is a unit test of the task
- Verified by: TC-CHA-072
- Status: Verified
- History: A-156 (approved 2026-11-16, FB-09), new

### REQ-CHA-068 – Live status line of a run
- Level: low   Subject: ConversationCore
- Text: While a skill run works, the Chat agent shall send the web frontend one status line with the current phase name of the manifest, or `working` for a run without declared phases.
- Rationale: refines REQ-BE-078; owner 2026-11-17 (A-158): the chat shows what currently happens like a chatbot, and the status card is superseded by the Skill run view (FB-09, A-156)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted run with phases `collect`, `rank`, `report` sends the lines `collect`, `rank`, `report` in order, a repeated phase once, and a lookup run sends `working` (exact)
- Verified by: TC-CHA-073
- Status: Verified
- History: A-158 (owner decisions 2026-11-17: generic line, fixed wording), new

### REQ-CHA-069 – Live line ends with the run
- Level: low   Subject: ConversationCore
- Text: When a skill run ends done, failed or stopped, the Chat agent shall send the clearing of the status line of the run when the text of the end message is ready and before it adds the end message, whether or not a line was shown; until then the line shows the phase the run was in.
- Rationale: refines REQ-BE-078; owner 2026-11-17 (A-158): the end message is the last thing in the chat, as in common chatbots
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: for each of the three ends, and for a run that never showed a line, the clearing is sent before the end message and no line follows it; with a digest that takes a scripted time the line is not cleared before the digest has returned: line, digest call, clearing, message (exact)
- Verified by: TC-CHA-074, TC-CHA-080
- Status: Verified
- History: A-158 (owner 2026-11-17), new; clarified by the Verify finding F-06 (the clearing is also sent without a line, so that a lost line cannot stay); A-160 (owner 2026-11-18, plan gate): the line stays until the text of the end message is ready (first real /review: the chat was blank for 16 minutes)

### REQ-CHA-070 – Live line while a question waits
- Level: low   Subject: ConversationCore
- Text: While a skill run waits for the answer to a question, the Chat agent shall send the status line `waiting for your answer`.
- Rationale: refines REQ-BE-078; owner 2026-11-17 (A-158): the chat tells what to answer and that the run waits for it
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted review that asks one question sends the line `waiting for your answer` after the question message and the line of the phase again after the answer (exact)
- Verified by: TC-CHA-075
- Status: Verified
- History: A-158 (owner 2026-11-17), new

### REQ-CHA-071 – Live line is transient
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall keep the status line of a run out of the chat log, the history of the chat model and speech.
- Rationale: refines REQ-BE-078; owner 2026-11-17 (A-158): transient, so no clutter stays and the persona speaks once (A-156, REQ-CHA-067)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: after a scripted run with three phases the chat log, the model history and the speech route hold none of the lines (exact)
- Verified by: TC-CHA-073
- Status: Verified
- History: A-158 (owner decision 2026-11-17: transient), new, split from REQ-CHA-068

### REQ-CHA-072 – Phase line again after a question
- Level: low   Subject: ConversationCore
- Text: When a question of a skill run ends by an answer or a timeout, the Chat agent shall send the status line of the current phase again, or `working` for a run without phases.
- Rationale: refines REQ-BE-078; owner 2026-11-17 (A-158) and Verify findings F-03, F-06: the line `waiting for your answer` must not stay while the skill goes on
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: after an answer, and after a timeout without an answer, the line of the phase is sent again; a run without a phase gets `working` (exact); after a stop of the run no line is sent again
- Verified by: TC-CHA-076
- Status: Verified
- History: A-158 amended (owner 2026-11-17), new, from the Verify findings F-03 and F-06

### REQ-CHA-073 – Output of a digest call
- Level: low   Subject: ConversationCore
- Text: The Chat agent shall ask the model server for at most 1024 tokens in each model call of SkillDigestStep.
- Rationale: refines REQ-BE-078 and REQ-CHA-050; owner 2026-11-18 (A-160): with an input of at most 4096 tokens a call stays inside num_ctx 8192, so the server never ends a text at the context limit; first real /review: a digest piece wrote about 1400 tokens and the end message was cut in the middle
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: with a fake model that records the options of each call, a summary of a long result makes only calls with `num_predict` 1024 (exact)
- Verified by: TC-CHA-077
- Status: Verified
- History: A-160 (owner 2026-11-18, plan gate), new

### REQ-CHA-074 – A too long summary is asked again once
- Level: low   Subject: ConversationCore
- Text: When the text of the last call of SkillDigestStep is longer than 1200 characters, the Chat agent shall ask the step once more to shorten that text to at most 1200 characters and pass on the text of the second call.
- Rationale: refines REQ-BE-078 and REQ-WFM-036; owner 2026-11-18 (A-160): REQ-CHA-052 only asks for 1200 characters and a 12B model does not always comply; the second call gets the short text and costs seconds; the code never cuts (REQ-CHA-063 unchanged)
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: with scripted replies a first reply of 800 characters makes one call; a first reply of 3000 and a second of 900 characters makes two calls and the chat gets the 900 characters; a first reply of 3000 and a second of 2500 characters makes two calls (no third) and the chat gets the 2500 characters unchanged (exact)
- Verified by: TC-CHA-078
- Status: Verified
- History: A-160 (owner 2026-11-18, plan gate), new

### REQ-CHA-075 – Stop ends the end message
- Level: low   Subject: ConversationCore
- Text: When the user stops while the end message of a run is made, the Chat agent shall make no further model call for it and end the run with the plain sentence of its outcome and the link to the run.
- Rationale: refines REQ-BE-078 and REQ-CHA-004; owner 2026-11-18 (A-160, decision A): Stop must work at every point of a run, also in the minutes after its skill returned; the result is stored, the user has the report in the Skill run view
- Parent: REQ-BE-078
- Group: ST
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: with a long result of ten pieces and a stop during the first piece call, no further model call is made, the end message is the plain sentence `The run is done.` with the link and the chat model history holds no digest text (exact)
- Verified by: TC-CHA-079
- Status: Verified
- History: A-160 (owner 2026-11-18, plan gate), new
