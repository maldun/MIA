# Requirements: Backend (N-2, high level)

**Parent:** `specs/mia/requirements.md` (top level N-0)   **Decomposition:** `specs/mia/decomposition.yaml`   **Status:** Draft (Plan, 2026-10-25)

The server and accounts, the chat agent, workflow management, workflow execution with verification and research, voice synthesis. Provides IF-101, consumes IF-102 and IF-103. Refines the top-level requirements named in each `Parent`; the details of low-level nodes follow when this node is cut. Numbers marked *Plan* are fixed in the node that owns the measurement.

## Requirements

### REQ-BE-001 – Chat events and streaming
- Level: high   Subject: WebApplication
- Text: When a logged-in user sends a message, the Backend shall answer it as a stream of sentences with expression events (IF-101).
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: with the fake model each scripted answer arrives as ordered sentences
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-002 – One shared MIA
- Level: high   Subject: WebApplication
- Text: The Backend shall answer all users in one conversation with one memory and one persona, and attribute each message to its sender.
- Rationale: refines FR-1, CON-6
- Parent: FR-1, CON-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: two users' messages appear with their names in the same history
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-003 – Queue with positions
- Level: high   Subject: WebApplication
- Text: While the model server is busy, the Backend shall queue incoming chat messages, report each position and refuse a message only when the queue is full (at most 5 waiting messages in all and at most 2 per user).
- Rationale: refines FR-1, NFR-7
- Parent: FR-1, NFR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: with 5 waiting messages the sixth is refused with a plain message; a third waiting message of one user is refused while another user can still send; positions are reported
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-004 – Stop an answer
- Level: high   Subject: WebApplication
- Text: When a user asks to stop, the Backend shall end the running generation.
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: after a stop request no further sentence is sent (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-005 – Bounded history
- Level: high   Subject: WebApplication
- Text: The Backend shall keep the visible history apart from the memory, bounded in size, and delete it after a confirmation by a user.
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1: the bound is held; deletion without confirmation is refused
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-006 – Regenerate and speak again
- Level: high   Subject: WebApplication
- Text: When a user requests it, the Backend shall regenerate the last answer or speak any answer again.
- Rationale: refines FR-1
- Parent: FR-1
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-1: two requests give a new answer and a new audio stream
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-007 – Changes reach all devices
- Level: high   Subject: WebApplication
- Text: When a user changes shared data, the Backend shall push the change to every connected device.
- Rationale: refines FR-1, FR-5, NFR-8
- Parent: FR-1, FR-5, NFR-8
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: a change by one user is visible on a second connection within 5 s with its author
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-008 – Login and session
- Level: high   Subject: WebApplication
- Text: When a user gives the correct account and password, the Backend shall open a session for that device.
- Rationale: refines FR-21
- Parent: FR-21
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: correct credentials open a session; wrong ones do not (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-009 – Throttled failed logins
- Level: high   Subject: WebApplication
- Text: If more than 5 logins fail within one minute for an account, then the Backend shall refuse further logins for that account until the minute has passed.
- Rationale: refines FR-21
- Parent: FR-21
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: the sixth failed attempt within a minute is refused even with the right password (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-010 – Password handling
- Level: high   Subject: WebApplication
- Text: The Backend shall store only salted slow hashes of passwords and write no password to any log.
- Rationale: refines FR-21
- Parent: FR-21
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-14: a search of the database and all logs after 10 logins finds no password (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-011 – Own password and owner-only accounts
- Level: high   Subject: WebApplication
- Text: The Backend shall let a user change their own password and let only the owner create an account.
- Rationale: refines FR-21
- Parent: FR-21
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: a non-owner's create request is refused (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-012 – Every request authenticated
- Level: high   Subject: WebApplication
- Text: The Backend shall authenticate every request by an account, check the origin and limit message rates per user.
- Rationale: refines NFR-6
- Parent: NFR-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: a request without a session is refused; a foreign origin is refused; the rate limit value is set in Plan
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-013 – Passwords only over a secure channel
- Level: high   Subject: WebApplication
- Text: If a password arrives over plain HTTP from an address other than localhost, then the Backend shall refuse it.
- Rationale: refines CON-4, NFR-6
- Parent: CON-4, NFR-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: plain HTTP from a LAN address is refused (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-014 – Attribution of changes
- Level: high   Subject: WebApplication
- Text: When shared data changes, the Backend shall record the account that made the change.
- Rationale: refines FR-21, FR-5, FR-16
- Parent: FR-21, FR-5, FR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: 100 % of changes in a scripted session carry the account
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-015 – Everything visible to all users
- Level: high   Subject: WebApplication
- Text: The Backend shall give every logged-in user the same access to all data and apply a change to all users at once, without roles.
- Rationale: refines CON-6, FR-5
- Parent: CON-6, FR-5
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-20: a second user sees and changes a first user's workflow, preset and persona
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-016 – Voice synthesis
- Level: high   Subject: WebApplication
- Text: When an answer is written, the Backend shall synthesise it sentence by sentence with an open text-to-speech engine behind one interface on the host and apply the anime voice effect.
- Rationale: refines FR-3
- Parent: FR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: each sentence of a 5-sentence answer yields one audio chunk
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-017 – Speak only what is meant to be heard
- Level: high   Subject: WebApplication
- Text: The Backend shall remove markup and stage directions from the text before synthesis.
- Rationale: refines FR-3
- Parent: FR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-13: on 10 answers with markup the synthesis input contains none (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-018 – Voice lines
- Level: high   Subject: WebApplication
- Text: When a mood or event occurs, the Backend shall choose at random one of the voice lines assigned to it, stay silent if there is none and skip a missing audio file with a log entry.
- Rationale: refines FR-31
- Parent: FR-31
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-13: every mood of the map has a line or is declared silent; a missing file is logged and skipped
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-019 – Default voice lines generated
- Level: high   Subject: WebApplication
- Text: The Backend shall generate the default voice lines with its own text-to-speech engine and voice effect.
- Rationale: refines FR-31
- Parent: FR-31
- Priority: Should
- Verification method: Inspection
- Acceptance criterion: AC-13: no default line is a third-party recording
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-020 – Step-by-step account
- Level: high   Subject: WebApplication
- Text: When a user opens the account of an answer produced by a task, the Backend shall deliver it from event data and without a model-written part.
- Rationale: refines FR-4
- Parent: FR-4
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-21: the account equals a rendering of the logged events (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-021 – Persona from the file
- Level: high   Subject: WebApplication
- Text: The Backend shall behave as the shared persona file specifies, with its names, pronouns and form of address, and address every user as master unless the file says otherwise.
- Rationale: refines FR-25
- Parent: FR-25
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-8: check dialogues pass at a rate fixed in Plan against the recorded baseline, decided statistically
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-022 – Mood at all times
- Level: high   Subject: WebApplication
- Text: While MIA is idle, thinking, speaking, waiting, greeting a user, reporting an error or offline, the Backend shall hold the corresponding mood, change it with events and settle it back over time.
- Rationale: refines FR-23
- Parent: FR-23
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-17: for each of the 7 situations the held mood equals the mood map
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-023 – Score shifts the mood
- Level: high   Subject: WebApplication
- Text: The Backend shall shift the general mood by the overall feedback score.
- Rationale: refines FR-23, FR-27
- Parent: FR-23, FR-27
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-18: a scripted score change moves the mood offset in the right direction
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-024 – Structured memory
- Level: high   Subject: WebApplication
- Text: The Backend shall keep structured facts, preferences and commitments linked to their source and retrieve what is relevant within the token budget.
- Rationale: refines FR-14
- Parent: FR-14
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-24: the memory test set is passed at least as well as today's dreaming at equal or lower token cost
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-025 – No memory from untrusted text
- Level: high   Subject: WebApplication
- Text: The Backend shall not store a fact about a user that came from web or file text.
- Rationale: refines FR-14, NFR-3
- Parent: FR-14, NFR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: a page that states a fact about a user leaves the memory unchanged (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-026 – Memory open to users
- Level: high   Subject: WebApplication
- Text: When a user inspects, corrects or deletes a memory record, the Backend shall apply it and show the source of the record.
- Rationale: refines FR-14
- Parent: FR-14
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-24: the three actions work on a sample record
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-027 – Silent repair of behaviour violations
- Level: high   Subject: WebApplication
- Text: If a defined behaviour rule is violated, then the Backend shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory.
- Rationale: refines FR-15
- Parent: FR-15
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-25: the detectors keep their recorded precision and recall on the behaviour suite
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-028 – Votes stored
- Level: high   Subject: WebApplication
- Text: When a user votes, the Backend shall store the vote with user, time, subject and one of four categories (answer quality, reactions, character behaviour, service) and keep a score per category and overall.
- Rationale: refines FR-27
- Parent: FR-27
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-18: 100 % of scripted votes are stored complete and the scores equal their sums
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-029 – A minus on a fact opens a case
- Level: high   Subject: WebApplication
- Text: When a user gives a minus to a factual answer, the Backend shall open a benchmark case and leave the stated fact unchanged.
- Rationale: refines FR-27, FR-29
- Parent: FR-27, FR-29
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-18, AC-11: after the minus the answer text is unchanged (exact) and one case is proposed
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-030 – Adaptation to negative feedback
- Level: high   Subject: WebApplication
- Text: When a behaviour has received at least 5 net negative votes, the Backend shall show it with a chance of at most 1 % per opportunity and raise the chance again after positive votes.
- Rationale: refines FR-29
- Parent: FR-29
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-11: in 1000 opportunities after 5 net negative votes the behaviour appears at most 10 times
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-031 – Counters visible and resettable
- Level: high   Subject: WebApplication
- Text: The Backend shall let every user see and reset the adaptation counters, and never apply the rule to facts or safety checks.
- Rationale: refines FR-29, CON-6
- Parent: FR-29, CON-6
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-11: a reset restores the default rate; a vote on a fact leaves counters of facts unchanged
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-032 – Tasks and memos recited from records
- Level: high   Subject: WebApplication
- Text: When a task falls due or a user asks, the Backend shall read the text of the task or memo from its record word for word.
- Rationale: refines FR-28
- Parent: FR-28
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12: 50 of 50 stored items are recited word for word on request and at their due time (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-033 – Skills as tasks
- Level: high   Subject: WebApplication
- Text: The Backend shall perform each kind of work as a task defined by a skill file and a pipeline selectable by every user.
- Rationale: refines FR-6
- Parent: FR-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: the selectable list shows each skill; a selected skill runs its pipeline
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-034 – Internet tasks only on command
- Level: high   Subject: WebApplication
- Text: The Backend shall start a task that reaches the internet only by a command of a user.
- Rationale: refines FR-6
- Parent: FR-6
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: a chat message alone starts no internet task (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-035 – Versioned workflow library
- Level: high   Subject: WebApplication
- Text: The Backend shall keep every pipeline and workflow as validated data in a library with the lifecycle draft, tested, trusted and retired and store every edit as a new immutable version with author and time.
- Rationale: refines FR-7
- Parent: FR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10, AC-16: an edit creates version n+1 and leaves version n unchanged (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-036 – No cycles
- Level: high   Subject: WebApplication
- Text: When a workflow is saved and before it runs, the Backend shall check by an algorithm that its graph has no cycle and name a cycle that it finds.
- Rationale: refines FR-7
- Parent: FR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: a workflow with a cycle is refused with the cycle named; property test on generated graphs: every accepted graph has a topological order
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-037 – Graph rules
- Level: high   Subject: WebApplication
- Text: The Backend shall refuse a workflow with two adjacent data nodes or a session node without a maximum number of cycles or a maximum time.
- Rationale: refines FR-7
- Parent: FR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: each of the three violations is refused with the rule named (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-038 – Model proposals stay drafts
- Level: high   Subject: WebApplication
- Text: When a model proposes a library entry, the Backend shall keep it as a draft until a user approves it, shown as a diff and tried on the test set.
- Rationale: refines FR-7, FR-20
- Parent: FR-7, FR-20
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: a proposed entry has status draft and cannot be run as trusted
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-039 – Specification before trust
- Level: high   Subject: WebApplication
- Text: The Backend shall keep a workflow without specification, context graph and benchmark with a baseline in draft status and refuse to promote it.
- Rationale: refines FR-26, FR-20
- Parent: FR-26, FR-20
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-10: promotion of a workflow lacking any of the three is refused (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-040 – Time from idea to promotion
- Level: high   Subject: WebApplication
- Text: The Backend shall record the time from the idea of a skill to its promotion.
- Rationale: refines FR-20
- Parent: FR-20
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-9: the record has two time stamps for each promoted skill
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-041 – Context graphs
- Level: high   Subject: WebApplication
- Text: The Backend shall keep one context graph per workflow and one for the chat and give each step the view that fits its token budget.
- Rationale: refines FR-30
- Parent: FR-30
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-10: the view of a step stays within its budget in tokens (exact on the recorded lookup run)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-042 – Workflow schedule and estimate
- Level: high   Subject: WebApplication
- Text: When a workflow is about to run, the Backend shall compute its order, critical path and an estimate of time, calls and tokens from its graph and the measured costs, and refuse a run whose estimate exceeds its budget.
- Rationale: refines FR-33
- Parent: FR-33
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-28: on the recorded lookup runs the estimate is within the factor set in Plan of the measured time
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-043 – Character variant per workflow
- Level: high   Subject: WebApplication
- Text: The Backend shall let a workflow name a character variant and send it to the frontend while the workflow runs.
- Rationale: refines FR-32
- Parent: FR-32
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-17: a run with a variant sends the variant name; a run without sends none
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-044 – Switch the model
- Level: high   Subject: WebApplication
- Text: When a user asks for the light or the full model and confirms, the Backend shall switch the model for all users and free GPU memory on request.
- Rationale: refines FR-8
- Parent: FR-8
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-23: /light! and /full! switch after confirmation; memory is freed on request
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-045 – Model server unreachable
- Level: high   Subject: WebApplication
- Text: If the model server is unreachable, then the Backend shall say so in plain words.
- Rationale: refines FR-8
- Parent: FR-8
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: with the fake server down the user gets the plain message (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-046 – Code checks first
- Level: high   Subject: WebApplication
- Text: The Backend shall check a claim by code where a code check exists and use model judgement only for the claims that the code checks leave open.
- Rationale: refines FR-9
- Parent: FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: in the run log the code checks precede the first model call of each claim
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-047 – Unclear without evidence
- Level: high   Subject: WebApplication
- Text: If a claim contains a number and has no evidence, then the Backend shall give the verdict unclear without a model call.
- Rationale: refines FR-9
- Parent: FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: for 10 claims with a number and no evidence there are 0 model calls and the verdict is unclear (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-048 – A failed check informs the judge
- Level: high   Subject: WebApplication
- Text: If a code check fails, then the Backend shall pass the failed check to the judgement style as a contradiction found by code.
- Rationale: refines FR-9
- Parent: FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-2: the judge input contains the check line (exact); the verdict is the judge's
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-049 – Judgement quality
- Level: high   Subject: WebApplication
- Text: The Backend shall run the chosen judgement style so that on the holdout it passes fewer wrong claims than the single voice and loses no more true claims among those with evidence.
- Rationale: refines FR-9
- Parent: FR-9
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-2: decided with the rule of the agent-app workflow against the baseline
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-050 – Stable verdicts
- Level: high   Subject: WebApplication
- Text: When a verification is repeated on the same input and the same sources, the Backend shall give the same verdicts and the same set of facts.
- Rationale: refines FR-9, FR-10
- Parent: FR-9, FR-10
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-2: stability limit 0.90 (lower bound of the 95 % interval, at least) on the dev suites (REQ-VER-005, REQ-VER-006)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-051 – Lookup with sources
- Level: high   Subject: WebApplication
- Text: When a user asks a factual question, the Backend shall answer with the sources and verbatim quotes that back it, or with unknown when nothing backs an answer.
- Rationale: refines FR-10
- Parent: FR-10
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-2: every answer of the lookup suite carries a source and a quote or the verdict unknown
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-052 – Search command
- Level: high   Subject: WebApplication
- Text: When a user gives the search command, the Backend shall list the findings of the metasearch (title, address, short text) without composing or verifying an answer.
- Rationale: refines FR-10
- Parent: FR-10
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-23: /search returns the list and starts no pipeline
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-053 – Review report
- Level: high   Subject: WebApplication
- Text: When a user gives a research question, a cut-off date and a budget, the Backend shall produce a report of kept and dropped sources with reasons, findings per sub-question with verbatim anchors, conflicts and open gaps.
- Rationale: refines FR-11
- Parent: FR-11
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-3: per tier source recall and precision against the baseline
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-054 – Review in time slices
- Level: high   Subject: WebApplication
- Text: The Backend shall work a review in time slices, give an intermediate report with a recommendation at the end of each slice and continue only when the requesting user agrees.
- Rationale: refines FR-11
- Parent: FR-11
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: after the first slice (60 s) the run waits for agreement (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-055 – Review stops by a code check
- Level: high   Subject: WebApplication
- Text: The Backend shall end a review when a code check finds every sub-question answered or a budget used up.
- Rationale: refines FR-11
- Parent: FR-11
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-3: with a fake model that always says done, the run still continues until the code check holds
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-056 – Source records and cut-off
- Level: high   Subject: WebApplication
- Text: The Backend shall record where a source comes from and how far it is trusted, keep the users' edits of that trust and honour a time cut-off strictly.
- Rationale: refines FR-12
- Parent: FR-12
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: 0 violations of the cut-off; retracted works are dropped and listed (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-057 – Method transfer
- Level: high   Subject: WebApplication
- Text: Where method transfer is switched on, the Backend shall offer few ranked candidate methods marked as hypotheses unless an executable test on a toy instance passed.
- Rationale: refines FR-13
- Parent: FR-13
- Priority: Could
- Verification method: Measurement
- Acceptance criterion: AC-26: the known method is in the top 3 on the retro-discovery cases
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-058 – Typed run events
- Level: high   Subject: WebApplication
- Text: The Backend shall write every run as typed, schema-checked events with one run id and the starting user, with secrets removed.
- Rationale: refines FR-16
- Parent: FR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4: a secret fed to the writer does not appear in the log (exact); a log with a broken order is reported
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-059 – Replay and comparison
- Level: high   Subject: WebApplication
- Text: The Backend shall replay a recorded run offline with an identical result and compare two runs.
- Rationale: refines FR-16
- Parent: FR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4: replay equals the original (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-060 – Statements traceable to a query
- Level: high   Subject: WebApplication
- Text: The Backend shall make every statement of an answer traceable to the query that found its source.
- Rationale: refines FR-16
- Parent: FR-16
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-4: on the recorded lookup run 100 % of statements link to a query
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-061 – Optional learning
- Level: high   Subject: WebApplication
- Text: Where learning is switched on, the Backend shall learn only from logged signals in discrete choices of configuration and graph weights and log every learned choice next to the default.
- Rationale: refines FR-18
- Parent: FR-18
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-22: a learned choice is logged with the default and can be switched off and reversed
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-062 – Context window share
- Level: high   Subject: WebApplication
- Text: The Backend shall keep every model input inside 50 % of the context window.
- Rationale: refines NFR-2
- Parent: NFR-2
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: over the lookup suites 100 % of inputs are at most 4096 tokens at num_ctx 8192
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-063 – Model calls of the first try
- Level: high   Subject: WebApplication
- Text: The Backend shall use fewer than 15 model calls for the first try of a question on the light model.
- Rationale: refines NFR-2
- Parent: NFR-2
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-22: on the lookup suites the maximum is below 15
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-064 – Untrusted text is data
- Level: high   Subject: WebApplication
- Text: The Backend shall treat text from the web, papers, PDFs and users as data and never as instruction.
- Rationale: refines NFR-3
- Parent: NFR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: injected instructions change no verdict and start no tool (red-team cases)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-065 – Sandbox or refuse
- Level: high   Subject: WebApplication
- Text: If no isolating sandbox is present, then the Backend shall refuse to run a model-written script or a hostile document.
- Rationale: refines NFR-3
- Parent: NFR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: with the sandbox removed script checks report unavailable and nothing runs (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-066 – Confidence by code
- Level: high   Subject: WebApplication
- Text: The Backend shall compute confidence figures by code from anchored evidence and report the limits with every result.
- Rationale: refines NFR-4
- Parent: NFR-4
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: each result shows its limits
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-067 – No invented source
- Level: high   Subject: WebApplication
- Text: The Backend shall show no source it did not retrieve.
- Rationale: refines NFR-4
- Parent: NFR-4
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-3: 0 invented references and 100 % of cited quotes found in their source
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-068 – Only queries leave the host
- Level: high   Subject: WebApplication
- Text: The Backend shall send off the host only the text of a web or scholarly query and, if configured, an e-mail address.
- Rationale: refines NFR-5
- Parent: NFR-5
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-5: the web log lists every query that left the machine
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-069 – First text in 10 seconds
- Level: high   Subject: WebApplication
- Text: When a chat message is answered on the light model, the Backend shall send the first text within 10 s.
- Rationale: refines NFR-7
- Parent: NFR-7
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-19: median over 20 runs is within 10 s, also while a review slice runs
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-070 – Budgets and what is missing
- Level: high   Subject: WebApplication
- Text: If a task exceeds a budget of steps, seconds, calls or tokens, then the Backend shall end it with what it has and say what is missing.
- Rationale: refines NFR-7
- Parent: NFR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: each of the four budgets ends a scripted run with a message naming it
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-071 – Chat before background
- Level: high   Subject: WebApplication
- Text: While a chat message waits, the Backend shall let a long background task yield the model server.
- Rationale: refines NFR-7
- Parent: NFR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: with a review slice running a chat message gets its first text within 10 s
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-072 – One model at a time
- Level: high   Subject: WebApplication
- Text: The Backend shall use one language model at a time on the 16 GB GPU and serve several users by the queue.
- Rationale: refines CON-2, NFR-7
- Parent: CON-2, NFR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-19: two simultaneous messages are answered one after the other
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-073 – Python versions
- Level: high   Subject: WebApplication
- Text: The Backend shall run on Python 3.11 to 3.13.
- Rationale: refines CON-3, NFR-9
- Parent: CON-3, NFR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-20: the unit tests pass on 3.12 and the import works on 3.11 and 3.13 (exact)
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-074 – State only through the storage interface
- Level: high   Subject: WebApplication
- Text: The Backend shall keep and read shared state only through the storage interface IF-102.
- Rationale: refines NFR-8, CON-7
- Parent: NFR-8, CON-7
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-15: no database driver is imported outside the storage client
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-075 – Serve the frontend
- Level: high   Subject: WebApplication
- Text: The Backend shall serve the files of the Web Frontend and run as its own container.
- Rationale: refines NFR-9
- Parent: NFR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-29: the container starts alone against the mocks and serves the chat page
- Verified by: –
- Status: Draft
- History: –

### REQ-BE-076 – Workflow and graph API
- Level: high   Subject: WebApplication
- Text: The Backend shall offer the Graph app, under the Backend's session, the listing, reading, saving as a new version, history, diff and restore of workflows and context graphs, and refuse an invalid graph with the broken rule named (IF-104).
- Rationale: refines FR-22, FR-30, FR-7
- Parent: FR-22, FR-30, FR-7
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-16: with the fake storage each of the six operations works; an invalid graph is refused with the rule named (exact)
- Verified by: –
- Status: Draft
- History: –

## Interface requirements

Owned by this node as provider (or, for an external provider, as the consumer that depends on it). The details are in `contracts/`; the mock and the contract suite are in `tests/helpers/mocks/` and `tests/acceptance/contract/`.

### IF-101 – Chat, expression, audio and REST API
- Level: high   Subject: WebApplication
- Text: The Backend shall provide the Web Frontend with the chat, expression, audio and REST interface IF-101 as specified in contracts/IF-101-chat-api.md (login with throttling, send with queue position, stop, history with senders, and the events chat_message, chat_start, chat_delta, audio_chunk, expression, chat_done and chat_error).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: FR-1, FR-3, FR-21
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-1, AC-14: the contract suite test_if_101_chat_api.py passes against the mock (stage 1) and the Backend (stage 2)
- Verified by: TC-IF-101-01..08
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)

### IF-103 – Model server (chat completion with structured output)
- Level: high   Subject: WebApplication
- Text: The Backend shall use the model server only through the interface IF-103 as specified in contracts/IF-103-model-server.md, handling the errors unreachable, timeout and bad_output.
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: FR-8, FR-9, NFR-2
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-23: the contract suite test_if_103_model_server.py passes against the mock (stage 1) and the pinned Ollama (stage 2)
- Verified by: TC-IF-103-01..06
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)

### IF-104 – Workflow and graph API for the Graph app
- Level: high   Subject: WebApplication
- Text: The Backend shall provide the Graph app with the workflow and graph interface IF-104 as specified in contracts/IF-104-graph-api.md (login with the Backend's session, list, read, save as a new version, history, diff and restore, and refusal of an invalid graph with the broken rule named).
- Rationale: interface between sibling nodes, decided by N-0 (decomposition.yaml)
- Parent: FR-22, FR-30, FR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-16, AC-27: the contract suite test_if_104_graph_api.py passes against the mock (stage 1) and the Backend (stage 2)
- Verified by: TC-IF-104-01..05
- Status: Draft
- History: v0, amendment 5/7 (2026-10-25)
