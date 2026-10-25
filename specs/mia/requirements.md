# Requirements: MIA, top level (Plan, node N-0)

**HLS:** specs/mia/high-level-spec.md   **Decomposition:** specs/mia/decomposition.yaml   **Status:** Draft (Plan step 1 for the root node, 2026-10-25)

Scope: the requirements of the whole system. They are the HLS requirements FR-1..FR-33 and NFR-1..NFR-9 in EARS form, keeping their ids; the long HLS texts are cut to the one statement that is checked at the top, and the details are refined in the child nodes (the line `Refined in`). The acceptance criterion points to the HLS criteria AC-1..AC-28, whose numbers *Plan* fixes (repeats, thresholds, seeds) are set in the node that owns the measurement (agent-app rule: not here). The constraints CON-1..CON-7 of HLS section 3.3 are at the end. Interfaces between the top-level nodes are in the section at the end.

Status of this file: first draft by the coding agent. Not yet done: lint run, plausibility record, glossary, `test-spec.md`, the refinement into the nodes, the interface contracts with mocks and suites.

## Requirements

### FR-1 – Conversation
- Level: top   Subject: MiaSystem
- Text: The MIA system shall let several logged-in users hold one shared conversation with her in a web browser, with answers appearing while they are written, a history that survives a reload and appears live on every connected device, and every message attributed to the user who sent it.
- Rationale: HLS section 3.1, FR-1
- Parent: HLS FR-1
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: two users on a desktop and a phone viewport; messages show the sender; answers stream; stop, queue position, reload and shared history work; the chat works when the character cannot load
- Refined in: N-1.1, N-2.1, N-2.2, N-3.3
- Verified by: –
- Status: Draft
- History: –

### FR-2 – Embodied character
- Level: top   Subject: MiaSystem
- Text: The MIA system shall show her emotional state and speech through a 3D character driven by one central expression API; if the character cannot load, the chat shall still work.
- Rationale: HLS section 3.1, FR-2
- Parent: HLS FR-2
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1, AC-17: expressions blend, gestures play, the mouth moves while speaking; with the character unloaded the chat still answers
- Refined in: N-1.2
- Verified by: –
- Status: Draft
- History: –

### FR-3 – Voice
- Level: top   Subject: MiaSystem
- Text: When an answer is written, the MIA system shall synthesise it on the host with an open text-to-speech engine behind one interface, apply the anime voice effect and deliver it sentence by sentence to the user's browser for playback.
- Rationale: HLS section 3.1, FR-3
- Parent: HLS FR-3
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-13: every answer is synthesised on the host with the anime effect and played sentence by sentence in the browser, without markup or stage directions; a user can mute or stop it for themselves
- Refined in: N-2.5, N-1.3
- Verified by: –
- Status: Draft
- History: –

### FR-4 – Transparency
- Level: top   Subject: MiaSystem
- Text: The MIA system shall show every user in one short line how she feels and what she is doing, and let a user open for any answer produced by a task an account of how it came about whose accurate part comes from event data.
- Rationale: HLS section 3.1, FR-4
- Parent: HLS FR-4
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-21: the status line shows mood and activity; for an answer produced by a task the step-by-step account is built from event data and contains no model-written part
- Refined in: N-1.1, N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-5 – User-shaped appearance and persona
- Level: top   Subject: MiaSystem
- Text: The MIA system shall let every user change expressions, gestures, backgrounds, mood phrases, emotions and the persona as data without changing code, apply a saved change to all users at once and record its author.
- Rationale: HLS section 3.1, FR-5
- Parent: HLS FR-5
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-15, AC-17: a saved change of expression, gesture, background, mood phrase, emotion or persona appears on a second device within seconds without a reload and is recorded with its author
- Refined in: N-1.2, N-2.1, N-3.3
- Verified by: –
- Status: Draft
- History: –

### FR-6 – Tasks as skills
- Level: top   Subject: MiaSystem
- Text: The MIA system shall perform each kind of work as a task defined by a human-readable skill file and a pipeline selectable by every user, and start a task that reaches the internet only by a command of a user.
- Rationale: HLS section 3.1, FR-6
- Parent: HLS FR-6
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-23: a task that reaches the internet is started only by a command of a user
- Refined in: N-2.3, N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-7 – Workflows as data
- Level: top   Subject: MiaSystem
- Text: The MIA system shall define every pipeline and agent workflow as validated, versioned data in a library, store every edit as a new immutable version with author and time, and refuse a workflow whose graph of process nodes and data nodes has a cycle.
- Rationale: HLS section 3.1, FR-7
- Parent: HLS FR-7
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-27: a cycle is refused with the cycle named; two adjacent data nodes are refused; a session node without a stopping criterion is refused; every accepted graph has a topological order (property test on generated graphs)
- Refined in: N-2.3, N-3.2
- Verified by: –
- Status: Draft
- History: –

### FR-8 – Model management
- Level: top   Subject: MiaSystem
- Text: The MIA system shall run on a local model server, let any user switch between the light and the full model after a confirmation, free GPU memory on request and say plainly when the model server is unreachable.
- Rationale: HLS section 3.1, FR-8
- Parent: HLS FR-8
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-23: `/light!` and `/full!` switch the model after a confirmation and free GPU memory; an unreachable model server gives a plain message
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-9 – Verify before asserting
- Level: top   Subject: MiaSystem
- Text: The MIA system shall check a claim by code where a code check exists, use model judgement only for the claims the hard checks leave open, accept "unknown" as an answer, and let a failed hard check inform the judge; a claim with a number and no evidence shall get the verdict unclear without a model call (amendment 4).
- Rationale: HLS section 3.1, FR-9
- Parent: HLS FR-9
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-2: on the holdout the chosen gate passes fewer wrong claims than the single voice and loses no more true claims among those with evidence (agent-app decision rule); repeated runs give the same verdicts (REQ-VER-005, REQ-VER-006)
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-10 – Lookup
- Level: top   Subject: MiaSystem
- Text: When a user asks a factual question, the MIA system shall answer with the sources and verbatim quotes that back it, or with "unknown" when nothing backs an answer.
- Rationale: HLS section 3.1, FR-10
- Parent: HLS FR-10
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-2, AC-23: every answer carries sources and verbatim quotes or the answer unknown; `/search` lists findings without composing an answer; a repeated lookup on the same sources gives the same facts
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-11 – Literature review
- Level: top   Subject: MiaSystem
- Text: When a user gives a research question with a cut-off date and a budget, the MIA system shall produce a structured report of kept and dropped sources, findings per sub-question with verbatim anchors, conflicts and open gaps, and continue past an intermediate report only when the requesting user agrees.
- Rationale: HLS section 3.1, FR-11
- Parent: HLS FR-11
- Priority: Should
- Verification method: Measurement, Test
- Acceptance criterion: AC-3: per tier source recall and precision against a baseline; 0 violations of the cut-off; 0 invented references; 100 % of quotes anchored
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-12 – Knowledge of sources
- Level: top   Subject: MiaSystem
- Text: The MIA system shall record for every source where it comes from and how far she trusts it, keep the users' edits of that trust and honour a time cut-off strictly.
- Rationale: HLS section 3.1, FR-12
- Parent: HLS FR-12
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-3: retracted works are dropped and listed; the cut-off is honoured strictly; a user's edit of a trust value is kept
- Refined in: N-2.4, N-3.3
- Verified by: –
- Status: Draft
- History: –

### FR-13 – Method transfer
- Level: top   Subject: MiaSystem
- Text: Where method transfer is switched on, the MIA system shall offer few ranked candidate methods from other fields, marked as hypotheses unless an executable test on a toy instance passed.
- Rationale: HLS section 3.1, FR-13
- Parent: HLS FR-13
- Priority: Could
- Verification method: Measurement
- Acceptance criterion: AC-26 (later, optional): the scout proposes the known method in its top 3 on the retro-discovery cases and marks a candidate verified only when an executable test passed
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-14 – Memory
- Level: top   Subject: MiaSystem
- Text: The MIA system shall keep structured facts, preferences and commitments linked to their source, retrieve what is relevant within the token budget, let every user inspect, correct and delete any record, and never store a fact about a user that came from web or file text.
- Rationale: HLS section 3.1, FR-14
- Parent: HLS FR-14
- Priority: Should
- Verification method: Measurement, Test
- Acceptance criterion: AC-24 (later): the memory test set is passed at least as well as today's summary-based dreaming at equal or lower token cost; every record shows its source and can be corrected and deleted by a user
- Refined in: N-2.2, N-3.3
- Verified by: –
- Status: Draft
- History: –

### FR-15 – Behaviour rules and feedback
- Level: top   Subject: MiaSystem
- Text: If a behaviour rule is violated, then the MIA system shall repair the answer silently, record the violation as a signal and keep the correction out of the conversation memory.
- Rationale: HLS section 3.1, FR-15
- Parent: HLS FR-15
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-25: the speech-rule detectors keep their recorded precision and recall on the behaviour suite; a violation is repaired silently and never enters the memory as a scolding
- Refined in: N-2.2
- Verified by: –
- Status: Draft
- History: –

### FR-16 – Traceability
- Level: top   Subject: MiaSystem
- Text: The MIA system shall write every run as typed, schema-checked events with one run id and the starting user, with secrets removed, such that a recorded run is replayable offline and two runs are comparable.
- Rationale: HLS section 3.1, FR-16
- Parent: HLS FR-16
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-4: a recorded run replays offline with an identical result; a log with a broken order is reported; two runs compare; a secret fed to the writer does not appear in the log
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-17 – Measurable quality
- Level: top   Subject: MiaSystem
- Text: The MIA system shall be evaluated by a harness that runs pipeline variants on fixed suites with repeats, intervals and cost counting, and decide improvement claims on held-out cases.
- Rationale: HLS section 3.1, FR-17
- Parent: HLS FR-17
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-22: variants are compared on the same cases with repeats and intervals; a judge model counts only after calibration against the users' ratings
- Refined in: N-4
- Verified by: –
- Status: Draft
- History: –

### FR-18 – Optional learning
- Level: top   Subject: MiaSystem
- Text: Where learning is switched on, the MIA system shall learn only from logged signals and only in discrete choices of configuration and graph weights, and log every learned choice next to the default.
- Rationale: HLS section 3.1, FR-18
- Parent: HLS FR-18
- Priority: Could
- Verification method: Test
- Acceptance criterion: AC-22: a learned choice is logged next to the default, can be switched off and reversed
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### FR-19 – Operable
- Level: top   Subject: MiaSystem
- Text: The MIA system shall be installable and runnable from one configuration file and one command, shut down in an orderly way that saves her memory, back up and restore her data including the database, and report missing options after an update.
- Rationale: HLS section 3.1, FR-19
- Parent: HLS FR-19
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-7: a fresh checkout, one configuration file and one command bring MIA up in the compose stack including the database; the owner creates the first account; the next start reports missing options
- Refined in: N-4
- Verified by: –
- Status: Draft
- History: –

### FR-20 – Skill development path
- Level: top   Subject: MiaSystem
- Text: The MIA system shall provide one documented path from an idea to a promoted skill, open to every user, that keeps a skill in draft status until a user promotes it and records the time from idea to promotion.
- Rationale: HLS section 3.1, FR-20
- Parent: HLS FR-20
- Priority: Must
- Verification method: Inspection, Measurement
- Acceptance criterion: AC-9: the lookup passes the path first as the documented example; the literature review is added within one month after its promotion; the time from idea to promotion is recorded
- Refined in: N-2.3, N-4
- Verified by: –
- Status: Draft
- History: –

### FR-21 – Accounts and login
- Level: top   Subject: MiaSystem
- Text: The MIA system shall let only the owner create accounts, let every user log in with a local account and password, and attribute every action that changes shared data to the account.
- Rationale: HLS section 3.1, FR-21
- Parent: HLS FR-21
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-14: only the owner creates accounts; at most 5 failed logins per minute per account are accepted; passwords are stored only as salted slow hashes and never logged; a user changes their own password
- Refined in: N-1.1, N-2.1, N-3.1
- Verified by: –
- Status: Draft
- History: –

### FR-22 – Graph app
- Level: top   Subject: MiaSystem
- Text: The MIA system shall provide a graph app that shows workflow graphs as nodes and edges, lets a logged-in user edit each node and edge as a JSON dictionary, checks the graph rules before saving and saves every edit as a new version.
- Rationale: HLS section 3.1, FR-22
- Parent: HLS FR-22
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-16: a user edits a node as JSON and saves a new version; an invalid edit is refused with the broken rule named; a former version can be restored; the export to files and the seed from files give identical entries
- Refined in: N-5, N-3.2
- Verified by: –
- Status: Draft
- History: –

### FR-23 – Mood in every situation
- Level: top   Subject: MiaSystem
- Text: The MIA system shall hold a mood at all times and show the expression and gesture that an editable mood map assigns to that mood, falling back to neutral for an unknown mood.
- Rationale: HLS section 3.1, FR-23
- Parent: HLS FR-23
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-17: in each listed situation (idle, thinking, speaking, queue, login, error, offline) the character shows the expression of the mood map; an unknown mood falls back to neutral
- Refined in: N-1.2, N-2.2
- Verified by: –
- Status: Draft
- History: –

### FR-24 – Character exchange
- Level: top   Subject: MiaSystem
- Text: When a user selects another VRoid model, the MIA system shall map the expressions and gestures defined for one model to the shape keys of the other or report them as missing.
- Rationale: HLS section 3.1, FR-24
- Parent: HLS FR-24
- Priority: Should
- Verification method: Demonstration, Test
- Acceptance criterion: AC-17: a second `.vrm` model loads and reports which presets and gestures it cannot map
- Refined in: N-1.2
- Verified by: –
- Status: Draft
- History: –

### FR-25 – Persona from a file
- Level: top   Subject: MiaSystem
- Text: The MIA system shall behave as the persona file specifies, using its names, pronouns and form of address, and use one shared persona file as the baseline for all users.
- Rationale: HLS section 3.1, FR-25
- Parent: HLS FR-25
- Priority: Should
- Verification method: Measurement
- Acceptance criterion: AC-8: check dialogues made from `calibration.txt` pass at a rate fixed in Plan against the recorded baseline, decided statistically; every user is addressed as master unless the file says otherwise
- Refined in: N-2.2
- Verified by: –
- Status: Draft
- History: –

### FR-26 – Workflow specification and benchmark
- Level: top   Subject: MiaSystem
- Text: The MIA system shall keep with every workflow a written specification of its inputs, outputs and measurable acceptance criteria, a context graph and a benchmark with a recorded baseline, and keep a workflow without them in draft status.
- Rationale: HLS section 3.1, FR-26
- Parent: HLS FR-26
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-10: every shipped workflow has a specification, a context graph and a benchmark with a baseline; the library refuses to promote one without them; every harness run records workflow version, model pin and benchmark version
- Refined in: N-2.3, N-4
- Verified by: –
- Status: Draft
- History: –

### FR-27 – Feedback and points
- Level: top   Subject: MiaSystem
- Text: When a user votes plus or minus on an answer, a reaction or a behaviour, the MIA system shall store the vote with user, time and subject in one of four categories and keep a score per category and overall.
- Rationale: HLS section 3.1, FR-27
- Parent: HLS FR-27
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-18: votes in the four categories are stored with user, time and subject; scores show per category and overall over time; the overall score shifts the mood; a minus on a factual answer opens a benchmark case and changes no fact
- Refined in: N-1.1, N-2.2, N-3.3
- Verified by: –
- Status: Draft
- History: –

### FR-28 – Tasks and memos
- Level: top   Subject: MiaSystem
- Text: When a task falls due or a user asks for it, the MIA system shall read the text of a task or memo back from its record, word for word, and never regenerate it by a model.
- Rationale: HLS section 3.1, FR-28
- Parent: HLS FR-28
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-12: of 50 stored tasks and memos all are recited word for word on request and at their due time
- Refined in: N-2.2, N-3.3
- Verified by: –
- Status: Draft
- History: –

### FR-29 – Adaptation to negative feedback
- Level: top   Subject: MiaSystem
- Text: When a behaviour has received at least 5 net negative votes, the MIA system shall show it with a chance of at most 1 % per opportunity, and never apply this rule to facts or safety checks.
- Rationale: HLS section 3.1, FR-29
- Parent: HLS FR-29
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-11: after 5 net negative votes a test of 1000 opportunities shows the behaviour at most 10 times; a positive vote raises the rate again; votes on facts never change a fact
- Refined in: N-2.2
- Verified by: –
- Status: Draft
- History: –

### FR-30 – Workflow context graph
- Level: top   Subject: MiaSystem
- Text: The MIA system shall keep one context graph per workflow and one for the chat as a whole in the shared database, with the views that say which part each step sees within its token budget.
- Rationale: HLS section 3.1, FR-30
- Parent: HLS FR-30
- Priority: Should
- Verification method: Inspection, Test
- Acceptance criterion: AC-10: every shipped workflow and the chat have a stored context graph that any user can adapt in the graph app as a new version
- Refined in: N-2.3, N-3.2, N-5
- Verified by: –
- Status: Draft
- History: –

### FR-31 – Voice lines
- Level: top   Subject: MiaSystem
- Text: When a mood or event occurs, the MIA system shall speak a voice line chosen at random among those assigned to it, stay silent if there is none, and skip a missing audio file with a log entry.
- Rationale: HLS section 3.1, FR-31
- Parent: HLS FR-31
- Priority: Should
- Verification method: Test, Demonstration
- Acceptance criterion: AC-13: every mood of the mood map has at least one voice line or is declared silent; the default lines are generated by the TTS; a missing audio file does not interrupt a conversation and is logged
- Refined in: N-2.5, N-1.3
- Verified by: –
- Status: Draft
- History: –

### FR-32 – Character variant per workflow
- Level: top   Subject: MiaSystem
- Text: While a workflow with a character variant runs, the MIA system shall show the character in that variant and a small label in the chat.
- Rationale: HLS section 3.1, FR-32
- Parent: HLS FR-32
- Priority: Could
- Verification method: Demonstration, Test
- Acceptance criterion: AC-17: a workflow with a variant changes the outfit and one without keeps the chat's
- Refined in: N-1.2, N-2.3
- Verified by: –
- Status: Draft
- History: –

### FR-33 – Workflow schedule
- Level: top   Subject: MiaSystem
- Text: When a workflow is about to run, the MIA system shall compute from its graph and the measured costs of its process nodes the order, the critical path and an estimate of time, calls and tokens, and refuse to start a run whose estimate exceeds its budget.
- Rationale: HLS section 3.1, FR-33
- Parent: HLS FR-33
- Priority: Should
- Verification method: Test, Measurement
- Acceptance criterion: AC-28: the estimate of time, calls and tokens is shown before a run; on the recorded lookup runs it is within the factor fixed in Plan of the measured time; a run whose estimate exceeds its budget is refused
- Refined in: N-2.3
- Verified by: –
- Status: Draft
- History: –

### NFR-1 – Accessibility and device range
- Level: top   Subject: MiaSystem
- Text: The MIA system shall be usable by keyboard and screen reader, in a dark and a light theme and with reduced motion, at widths from 320 to 2560 px in current Chrome, Firefox and Safari (iOS 16 and later), with touch targets of at least 44 px.
- Rationale: HLS section 3.2, NFR-1
- Parent: HLS NFR-1
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-1: browser checks at 360, 768 and 1440 px in both themes; keyboard and screen reader pass; touch targets of at least 44 px
- Refined in: N-1.1, N-1.2
- Verified by: –
- Status: Draft
- History: –

### NFR-2 – Small-model strategies
- Level: top   Subject: MiaSystem
- Text: The MIA system shall keep every model input inside 50 % of the context window and use fewer than 15 model calls for the first try of a question on the light model.
- Rationale: HLS section 3.2, NFR-2
- Parent: HLS NFR-2
- Priority: Must
- Verification method: Measurement, Inspection
- Acceptance criterion: AC-22: on the lookup suites the cheap first try needs fewer than 15 model calls per question on the light model; every model input stays inside 50 % of the context window
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### NFR-3 – Untrusted input stays data
- Level: top   Subject: MiaSystem
- Text: The MIA system shall treat text from the web, papers, PDFs and users as data and never as instruction, and run model-written scripts and hostile documents only in an isolating sandbox, refusing the operation when no sandbox is present.
- Rationale: HLS section 3.2, NFR-3
- Parent: HLS NFR-3
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-6: with the sandbox removed script checks report unavailable and nothing runs; injected instructions in pages and papers change no verdict and start no tool
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### NFR-4 – Honest confidence
- Level: top   Subject: MiaSystem
- Text: The MIA system shall compute confidence figures by code from anchored evidence, show no source she did not retrieve, and report the limits with every result.
- Rationale: HLS section 3.2, NFR-4
- Parent: HLS NFR-4
- Priority: Must
- Verification method: Test, Measurement
- Acceptance criterion: AC-3: 0 invented references and 100 % of cited quotes found in their source; confidence figures computed by code
- Refined in: N-2.4
- Verified by: –
- Status: Draft
- History: –

### NFR-5 – Local-first privacy
- Level: top   Subject: MiaSystem
- Text: The MIA system shall keep conversations, memory, logs, accounts and models on the host, send only the text of a web or scholarly query and, if configured, an e-mail address off it, and load nothing from the internet into the page.
- Rationale: HLS section 3.2, NFR-5
- Parent: HLS NFR-5
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-5: a browser test records every request the page makes and finds none outside the host; the web log lists every query that left the machine; the login page says that nothing is private between users
- Refined in: N-1, N-2, N-3
- Verified by: –
- Status: Draft
- History: –

### NFR-6 – Secure access
- Level: top   Subject: MiaSystem
- Text: The MIA system shall be reachable from other devices only over HTTPS inside the home network or the tailnet, authenticate every request by an account, check origins and limit message rates per user.
- Rationale: HLS section 3.2, NFR-6
- Parent: HLS NFR-6
- Priority: Must
- Verification method: Test, Inspection
- Acceptance criterion: AC-14: other devices reach MIA only over HTTPS inside the home network or the tailnet; every request needs a login; origins are checked; message rates are limited per user; passwords go over plain HTTP only to `localhost`
- Refined in: N-2.1, N-4
- Verified by: –
- Status: Draft
- History: –

### NFR-7 – Efficient on the given hardware
- Level: top   Subject: MiaSystem
- Text: The MIA system shall show the first text of a chat answer within 10 s on the light model, run every task under explicit budgets of steps, seconds, calls and tokens, and give a waiting chat message priority over a background task.
- Rationale: HLS section 3.2, NFR-7
- Parent: HLS NFR-7
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-19: first text of a chat answer within 10 s on the light model, also while a review slice runs; 30 fps or more on a mid-range phone and 60 fps on desktop
- Refined in: N-1.2, N-2.1, N-2.4
- Verified by: –
- Status: Draft
- History: –

### NFR-8 – Shared state in a database
- Level: top   Subject: MiaSystem
- Text: The MIA system shall keep her shared state in a PostgreSQL database in a container behind storage interfaces, such that MIA and the graph app share it and the move from files to the database is one reversible command.
- Rationale: HLS section 3.2, NFR-8
- Parent: HLS NFR-8
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-15: the state is in the PostgreSQL database; files to database and back gives identical files; backup and restore round-trip including the database; a change by one user is visible to another within seconds with its author
- Refined in: N-3, N-2.1
- Verified by: –
- Status: Draft
- History: –

### NFR-9 – A container per node
- Level: top   Subject: MiaSystem
- Text: The MIA system shall run each of the nodes N-2 to N-5 as its own container under podman, serve the web frontend N-1 as static files from the backend container, and start every container alone and all together by the compose stack with the same configuration file.
- Rationale: HLS section 3.2, NFR-9
- Parent: HLS NFR-9
- Priority: Must
- Verification method: Test, Demonstration
- Acceptance criterion: AC-29: from a fresh checkout the compose stack starts the containers of N-2 (serving the frontend files of N-1), N-3, N-4 and N-5 with one configuration file; each container also starts alone against the mocks of its neighbours and passes its contract suites
- Refined in: N-4, N-2, N-3, N-5
- Verified by: –
- Status: Draft
- History: –

### CON-1 – Free and open
- Level: top   Subject: MiaSystem
- Text: The MIA system shall use only local models through Ollama and self-hosted search, no paid API, under the licence GPL-3.0-or-later.
- Rationale: HLS section 3.3, CON-1
- Parent: HLS CON-1
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: licence file present; no paid API in the web log
- Refined in: N-4
- Verified by: –
- Status: Draft
- History: –

### CON-2 – Hardware
- Level: top   Subject: MiaSystem
- Text: The MIA system shall run on the Ryzen 9 5900X host with 16 GB VRAM and 62 GB RAM with one language model loaded at a time, queueing the requests of several users.
- Rationale: HLS section 3.3, CON-2
- Parent: HLS CON-2
- Priority: Must
- Verification method: Measurement
- Acceptance criterion: AC-19: measured on the Ryzen 9 5900X with the RX 7800 XT (16 GB VRAM, 62 GB RAM); one language model loaded at a time
- Refined in: N-2.4, N-4
- Verified by: –
- Status: Draft
- History: –

### CON-3 – Technology
- Level: top   Subject: MiaSystem
- Text: The MIA system shall use Python 3.11 to 3.13, Godot 4.6.1 with GDScript only and the Compatibility renderer, and a chat page in plain HTML, CSS and ES modules without build step or UI framework.
- Rationale: HLS section 3.3, CON-3
- Parent: HLS CON-3
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-20: Python 3.11 to 3.13; Godot 4.6.1 with GDScript and the Compatibility renderer; chat page in plain HTML, CSS and ES modules without build step
- Refined in: N-1, N-2
- Verified by: –
- Status: Draft
- History: –

### CON-4 – Secure context for the character
- Level: top   Subject: MiaSystem
- Text: The MIA system shall run the 3D character only on `localhost` or over HTTPS and accept passwords only over HTTPS or on `localhost`.
- Rationale: HLS section 3.3, CON-4
- Parent: HLS CON-4
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-14: the character loads only on `localhost` or over HTTPS; passwords are sent only over HTTPS or to `localhost`
- Refined in: N-1, N-2.1
- Verified by: –
- Status: Draft
- History: –

### CON-5 – Private network only
- Level: top   Subject: MiaSystem
- Text: The MIA system shall be reachable from outside the host only inside a private network (Tailscale) and shall expose no public port.
- Rationale: HLS section 3.3, CON-5
- Parent: HLS CON-5
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-14: no public port; `tailscale funnel` is not used
- Refined in: N-4
- Verified by: –
- Status: Draft
- History: –

### CON-6 – Trusted users only
- Level: top   Subject: MiaSystem
- Text: The MIA system shall let every logged-in user see and change everything, without roles or per-user permissions, and apply a change to all users at once.
- Rationale: HLS section 3.3, CON-6
- Parent: HLS CON-6
- Priority: Must
- Verification method: Inspection, Test
- Acceptance criterion: AC-20: the login page says that everything is visible to all; a change by one user applies to all
- Refined in: N-1.1, N-2.1
- Verified by: –
- Status: Draft
- History: –

### CON-7 – One shared database
- Level: top   Subject: MiaSystem
- Text: The MIA system shall keep its shared state in one PostgreSQL database in a container behind storage interfaces.
- Rationale: HLS section 3.3, CON-7
- Parent: HLS CON-7
- Priority: Must
- Verification method: Inspection
- Acceptance criterion: AC-15: one PostgreSQL database in a container reachable by MIA and the graph app; MIA's state is behind storage interfaces
- Refined in: N-3
- Verified by: –
- Status: Draft
- History: –
