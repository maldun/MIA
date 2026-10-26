# Test specification: MIA, top level (node N-0)

**Requirements:** specs/mia/requirements.md (FR-1..33, NFR-1..9, CON-1..7)   **Acceptance criteria:** HLS section 6 (AC-1..AC-29)   **Status:** Draft (Plan step 3 for the root node, 2026-10-25)

One test case per acceptance criterion of the HLS, at the level where the criterion can be seen: the system as a whole. The nodes have their own test specifications (refined requirements, unit and component tests); the interfaces between the nodes are tested by the contract suites below. Requirements that depend on the model are decided by eval suites with the pinned model, never by a mock (agent-app rule); their criteria, repeats and seeds are fixed in the eval spec of the example workflow (for verification: `specs/number-gate/eval-spec.md`) and are not changed here. The example workflows lookup and review are the proof of concept: lookup is the thinnest end-to-end scenario (step 0 of the integration tests). Open numbers are listed at the end as OPEN-n and fixed by the owner before the check is written.

## Test cases

| Test ID | Verifies | Level | Stage | Setup / inputs | Expected result | Limit / tolerance |
| --- | --- | --- | --- | --- | --- | --- |
| TC-MIA-001 (AC-1) | FR-1, FR-2, NFR-1 | System (browser) | 3 | Two accounts log in, one on a desktop viewport and one on a phone viewport (360, 768, 1440 px, both themes); the backend runs with the fake model server; a second run with the character iframe blocked | messages show their sender; answers stream; stop, queue position, reload and the shared history work; regenerate and speak again work; with the character blocked the chat still answers; keyboard and screen reader checks pass; touch targets measure 44 px or more | exact; phone part by the checklist `ui/CHECKLIST_CHAT_PHONE.md` (Demonstration) |
| TC-MIA-002 (AC-2) | FR-9, FR-10, FR-17 | Eval (holdout) | 4 | The suites of the example workflow verify (VitaminC and Wikidata, holdout, MP-light), single voice as baseline, 3 repeats | the chosen gate passes fewer wrong claims than the single voice and loses no more true claims among those with evidence; a number claim without evidence answers unclear | decided by `eval_decide.py` against the baseline; criteria, repeats and seeds are in `specs/number-gate/eval-spec.md` (fixed there, not changed here) |
| TC-MIA-003 (AC-3) | FR-11, FR-12, NFR-4 | Eval (benchmark) | 4 | The review benchmark per tier against its recorded baseline (example workflow review, when promoted) | source recall and precision per tier; violations of the cut-off = 0; invented references = 0; quotes anchored = 100 %; retracted works dropped and listed | exact for the three zero/100 % criteria; recall and precision against the baseline by the rule of `eval-spec.md` (set when the review is planned) |
| TC-MIA-004 (AC-4) | FR-16 | Integration | 3 | A recorded lookup run (fake model, recorded pages); a log with two events swapped; two runs of the same question; a secret fed to the writer | the replay offline gives an identical result; the broken order is reported; the two runs compare; the secret does not appear in the log | exact |
| TC-MIA-005 (AC-5) | NFR-5 | System (browser) | 3 | A browser run of a chat session and of the graph app that records every request; the web log of a lookup | no request leaves the host; the web log lists every query that left the machine | exact |
| TC-MIA-006 (AC-6) | NFR-3 | Integration + red team | 3 | The sandbox removed; pages and papers with injected instructions (the red-team cases of `threat-model.md`) | script checks report unavailable and nothing runs; no verdict changes and no tool starts | exact (0 failures over all red-team cases) |
| TC-MIA-007 (AC-7) | FR-19 | Smoke (target) | 3 | A fresh checkout, one configuration file, one command (compose stack with the database); the owner creates the first account; a second start with two options removed | MIA comes up and answers a chat message; the first account exists; the second start reports both missing options | exact |
| TC-MIA-008 (AC-8) | FR-25 | Eval (statistical) | 4 | Check dialogues made from `calibration.txt` (a) and the personality dialogues (b), MP-light, against a recorded baseline of today's MIA | the pass rate is not lower than the baseline's and reaches the rate fixed below; every user is addressed as master unless the file says otherwise | at least 84 of 100 dialogues pass (OPEN-1, decided); the baseline run of today's MIA on the same 100 dialogues is measured first (T-04); if it is clearly below about 0.90 the owner is asked again |
| TC-MIA-009 (AC-9) | FR-20, FR-10, FR-11 | Inspection + measurement | 4 | The record of the skill path: lookup as the documented example; the review added by the same path; the time stamps idea and promotion | both workflows have specification, context graph and benchmark with holdout and baseline; the review is promoted within one month after the lookup | exact (inspection); the one-month limit is read from the recorded time stamps |
| TC-MIA-010 (AC-10) | FR-26, FR-30, FR-7 | Integration | 3 | The library with the seed entries; a workflow without specification, one without context graph, one without benchmark; a harness run | the library refuses to promote each incomplete workflow; every shipped workflow has specification, context graph and benchmark with baseline; every harness run records workflow version, model pin and benchmark version | exact |
| TC-MIA-011 (AC-11) | FR-29 | Statistical | 4 | A behaviour with 5 net negative votes; 1000 opportunities with fixed seeds; then a positive vote and 1000 more; a vote on a fact | at most 10 appearances in 1000 after the negative votes; a higher rate after the positive vote; MIA asks before a behaviour is nearly stopped; the fact is unchanged | see the statistical table: the implemented rate is 0.5 %, not 1 % (finding F-1) |
| TC-MIA-012 (AC-12) | FR-28 | Integration | 2 | 50 stored tasks and memos with odd characters, due now | all 50 are recited word for word on request and at their due time | exact (0 deviations) |
| TC-MIA-013 (AC-13) | FR-3, FR-31 | System + demonstration | 3 | Answers with markup and stage directions; every mood of the mood map; a missing audio file; mute and stop | each answer is spoken in the browser with the TTS voice and the effect, without markup; every mood has a line or is declared silent; the defaults are generated by the TTS; a missing file does not interrupt the conversation and is logged; mute and stop work | exact; the sound is judged in a demonstration |
| TC-MIA-014 (AC-14) | FR-21, NFR-6, CON-4, CON-5 | System | 3 | A non-owner creates an account; requests without login; six failed logins within a minute; passwords in database and logs; plain HTTP from a LAN address and to localhost; a foreign origin; a port scan from outside | only the owner creates accounts; every request needs a login; the sixth failed login is refused even with the right password; only salted slow hashes are stored and no password is logged; plain HTTP to a LAN address is refused; origins are checked; no public port | exact |
| TC-MIA-015 (AC-15) | NFR-8, CON-7, FR-5, CON-6 | Integration | 3 | The stack with the database; files to database and back; backup, wipe and restore; a change by one user watched on a second connection | the state is in the PostgreSQL database; the round trip gives identical files; backup and restore return the same records; the change is visible on the second connection within 5 s and carries its author | exact; "within seconds" is 5 s (OPEN-5, decided) |
| TC-MIA-016 (AC-16) | FR-22 | System + demonstration | 3 | The graph app against the backend: edit a node as JSON, save, an invalid edit, restore a former version, export then seed | a new version with author and time; the invalid edit is refused with the rule named; the restore creates a new version equal to the former; export then seed gives identical entries | exact |
| TC-MIA-017 (AC-17) | FR-24, FR-32, FR-2, FR-23, FR-5 | System + demonstration | 3 | The contact sheet of the presets; a second .vrm model; a saved expression watched on a second device; a workflow with and without a variant; the seven moods | the sheet looks right (reviewer); the unmappable presets and gestures are listed; the saved expression appears without reload; the variant changes the outfit, none keeps the chat's; each mood shows its mapped expression | exact except the sheet (reviewer) |
| TC-MIA-018 (AC-18) | FR-27 | Integration | 3 | Scripted votes in the four categories, a minus on a factual answer, a change of the interval | votes are stored with user, time and subject; scores per category and overall over time; the overall score shifts the mood; the interval is a setting; the minus opens a benchmark case and leaves the fact unchanged | exact |
| TC-MIA-019 (AC-19) | NFR-7, CON-2 | Benchmark | 4 | BM-MIA-001 (first text, with and without a review slice running) and BM-MIA-002 (frame rate) on the reference hardware | first text within 10 s on MP-light, also while a review slice runs; 30 fps or more on any phone inside the network and on desktop | median of repeated runs, see the benchmark table |
| TC-MIA-020 (AC-20) | CON-1, CON-3, CON-6 | Inspection | 2 | The repository and a web log of a session | the licence file is present; no paid API host in the web log; Python versions, Godot 4.6.1 and the plain stack hold; the login page says everything is visible to all | exact |
| TC-MIA-021 (AC-21) | FR-4 | Integration | 3 | An answer produced by a task; the status line over a chat | the account equals a rendering of the logged events and contains no model-written part; the status line shows mood and activity | exact |
| TC-MIA-022 (AC-22) | NFR-2, FR-17, FR-18 | Eval (measurement) | 4 | The lookup suites on MP-light; a learned choice switched on and off | the cheap first try needs fewer than 15 model calls per question; every model input is at most 50 % of the context window; a learned choice is logged next to the default and can be switched off and reversed; variants are compared on the same cases with repeats | maximum over the suite < 15 (exact); the rest exact |
| TC-MIA-023 (AC-23) | FR-8, FR-6, FR-10 | System + demonstration | 3 | The commands /light!, /full!, /search; the model server stopped; a chat message that would need the internet | the model switches after a confirmation and GPU memory is freed; the unreachable server gives a plain message; a task that reaches the internet starts only by a command; /search lists findings and composes no answer | exact |
| TC-MIA-024 (AC-24) | FR-14 | Eval (measurement) | 4 | The memory test set (store, update, contradict, recall, unknown) against today's summary-based dreaming | passed at least as well at equal or lower token cost; every record shows its source and can be corrected and deleted | later, not in the first version (Should); set when FR-14 is planned |
| TC-MIA-025 (AC-25) | FR-15 | Eval (measurement) | 4 | The behaviour suite with the speech-rule detectors | precision and recall are not lower than the recorded ones; a violation is repaired silently and never enters the memory as a scolding | against the recorded values, rule of `eval-spec.md` |
| TC-MIA-026 (AC-26) | FR-13 | Eval (measurement) | 4 | The retro-discovery cases of the owner | the known method is in the top 3; a candidate is marked verified only when an executable test passed | later, optional (Could) |
| TC-MIA-027 (AC-27) | FR-7 | Property | 2 | Generated graphs (seeds 1 to 1000) with and without cycles, adjacent data nodes, shared inputs; session nodes with and without a stopping criterion | a cycle is refused with the cycle named; two adjacent data nodes are refused; a shared data node appears once and both processes see the same value; every accepted graph has a topological order; a session node without a stopping criterion is refused | 0 failures over 1000 seeds |
| TC-MIA-028 (AC-28) | FR-33 | Measurement | 4 | The recorded lookup runs; the estimate computed from the graph and the measured costs | the estimate of time, calls and tokens is shown before a run; it lies within the factor below of the measured time; a run whose estimate exceeds its budget is refused | the estimate is within a factor of 3 of the measured time, either way (OPEN-3, decided: generous; what matters is that an estimate is shown, the run works and the first text comes within about 10 s) |
| TC-MIA-029 (AC-29) | NFR-9 | Smoke (target) | 3 | From a fresh checkout the compose stack; each node container alone against the mocks of its neighbours | the containers of N-2 (serving the frontend), N-3, N-4 and N-5 start with one configuration file; each starts alone and passes its contract suites; the chat page loads from the backend container | exact |

## Contract suites (the interfaces between the nodes)

One suite per interface, protected, with a provider fixture over the mock (stage 1, green from the start) and the real provider (stage 2, skipped until the node is integrated). Drafts are in `specs/mia/contract-drafts/` and installed by `tools/install_contract_drafts.sh`; specs in `contracts/`.

| Interface | Name | Provider to consumers | Decided by | Mock complexity | Suite |
| --- | --- | --- | --- | --- | --- |
| IF-101 | Chat, expression and REST API (browser to server) | N-2 to N-1 | N-0 | 3 | tests/acceptance/contract/test_if_101_chat_api.py |
| IF-102 | Storage interface (state of all apps) | N-3 to N-2 | N-0 | 2 | tests/acceptance/contract/test_if_102_storage.py |
| IF-103 | Model server (chat completion with structured output) | ext:ollama to N-2 | N-0 | 3 | tests/acceptance/contract/test_if_103_model_server.py |
| IF-104 | Workflow and graph API (REST with the backend's session) | N-2 to N-5 | N-0 | 2 | tests/acceptance/contract/test_if_104_graph_api.py |
| IF-105 | Evaluation access (run a case with a pinned model, seed and temperature) | N-2 to N-4 | N-0 | 2 | tests/acceptance/contract/test_if_105_evaluation_access.py |
| IF-201 | Chat turn service (API and accounts to chat agent) | N-2.2 to N-2.1 | N-2 | 3 | tests/acceptance/contract/test_if_201_chat_turn.py |
| IF-202 | Run a workflow | N-2.4 to N-2.2, N-2.3 | N-2 | 3 | tests/acceptance/contract/test_if_202_run_workflow.py |
| IF-203 | Workflow library | N-2.3 to N-2.1, N-2.2, N-2.4 | N-2 | 2 | tests/acceptance/contract/test_if_203_workflow_library.py |
| IF-204 | Speech synthesis | N-2.5 to N-2.2 | N-2 | 2 | tests/acceptance/contract/test_if_204_speech.py |
| IF-111 | Character bridge (page to the character iframe) | N-1.2 to N-1.1 | N-1 | 2 | tests/acceptance/contract/test_if_111_character_bridge.test.mjs |
| IF-112 | Voice player (page to the audio playback) | N-1.3 to N-1.1 | N-1 | 3 | tests/acceptance/contract/test_if_112_voice_player.test.mjs |
| IF-301 | Graph table definitions and validation | N-3.2 to N-3.1 | N-3 | 1 | tests/acceptance/contract/test_if_301_graph_tables.py |
| IF-302 | Record table definitions and validation | N-3.3 to N-3.1 | N-3 | 1 | tests/acceptance/contract/test_if_302_record_tables.py |
| IF-401 | Run event log | N-2.4.3 to N-2.4.1, N-2.4.2 | N-2.4 | 2 | tests/acceptance/contract/test_if_401_run_events.py |
| IF-402 | Tool calls | N-2.4.2 to N-2.4.1 | N-2.4 | 3 | tests/acceptance/contract/test_if_402_tool_calls.py |
| IF-404 | Web search and fetch (external) | ext:web to N-2.4.2 | N-2.4 | 3 | tests/acceptance/contract/test_if_404_web.py |
| IF-405 | Scholarly sources (external) | ext:scholar to N-2.4.2 | N-2.4 | 3 | tests/acceptance/contract/test_if_405_scholarly_sources.py |

### Contract test cases

Setup and expected result are in the docstring of each test (the golden examples of the spec in `contracts/`).

| Test ID | Verifies | Level | Stage | What it checks | Limit / tolerance |
| --- | --- | --- | --- | --- | --- |
| TC-IF-101-01 | IF-101 | Contract | 1 (mock) and 2 (real) | the right password opens a session, a wrong one is 401 bad_credentials. | exact |
| TC-IF-101-02 | IF-101 | Contract | 1 (mock) and 2 (real) | golden 2: five failures, then 429 even with the right password; after 61 s the right password works. | exact |
| TC-IF-101-03 | IF-101 | Contract | 1 (mock) and 2 (real) | send, stop, history and connect without a session are 401 unauthenticated and queue nothing. | exact |
| TC-IF-101-04 | IF-101 | Contract | 1 (mock) and 2 (real) | golden 1: ben | exact |
| TC-IF-101-05 | IF-101 | Contract | 1 (mock) and 2 (real) | golden 3: positions 1, 2, 3 (two users); a fourth message is 503 queue_full and queues nothing; after settle the queue is empty. | exact |
| TC-IF-101-09 | IF-101 | Contract | 1 (mock) and 2 (real) | with the defaults (5 in all, 2 per user) a third waiting message of one user is 503 queue_full while another user can still send. | exact |
| TC-IF-101-06 | IF-101 | Contract | 1 (mock) and 2 (real) | golden 3: stop right after send gives chat_done with status stopped and no chat_delta. | exact |
| TC-IF-101-07 | IF-101 | Contract | 1 (mock) and 2 (real) | empty or blank text is 422 empty_text and nothing is queued. | exact |
| TC-IF-101-08 | IF-101 | Contract | 1 (mock) and 2 (real) | a user who connects later gets the same ordered history with senders, the assistant | exact |
| TC-IF-102-01 | IF-102 | Contract | 1 (mock) and 2 (real) | golden 1: version 1, version 2, and version 1 reads back unchanged. | exact |
| TC-IF-102-02 | IF-102 | Contract | 1 (mock) and 2 (real) | golden 2: each broken rule is refused with its name and nothing is stored. | exact |
| TC-IF-102-03 | IF-102 | Contract | 1 (mock) and 2 (real) | golden 3: a cycle p->d->p is refused as a cycle and named by its ids, first id repeated at the end. | exact |
| TC-IF-102-04 | IF-102 | Contract | 1 (mock) and 2 (real) | conflict names the current version; unknown id, version and table are refused; a new record accepts expected_version 0. | exact |
| TC-IF-102-05 | IF-102 | Contract | 1 (mock) and 2 (real) | versioned tables refuse delete; a memory record can be deleted and is gone. | exact |
| TC-IF-102-06 | IF-102 | Contract | 1 (mock) and 2 (real) | a subscriber gets one notice per write; after unsubscribe none. | exact |
| TC-IF-102-07 | IF-102 | Contract | 1 (mock) and 2 (real) | text with odd characters comes back byte for byte (the word-for-word recital of FR-28). | exact |
| TC-IF-103-01 | IF-103 | Contract | 1 (mock) and 2 (real) | golden 1: message, model and token counts. | exact |
| TC-IF-103-02 | IF-103 | Contract | 1 (mock) and 2 (real) | a JSON text or a dict that has the required keys is returned as a dict. | exact |
| TC-IF-103-03 | IF-103 | Contract | 1 (mock) and 2 (real) | golden 2: text that is not JSON and JSON that lacks a required key are bad_output with the raw reply in detail. | exact |
| TC-IF-103-04 | IF-103 | Contract | 1 (mock) and 2 (real) | golden 2: a server that is not running is  | exact |
| TC-IF-103-05 | IF-103 | Contract | 1 (mock) and 2 (real) | no answer in time is  | exact |
| TC-IF-103-06 | IF-103 | Contract | 1 (mock) and 2 (real) | golden 3: no messages is a ValueError of the caller, not a model error. | exact |
| TC-IF-104-01 | IF-104 | Contract | 1 (mock) and 2 (real) | golden 1: version 1, an edit as version 2, the diff names the changed node, restore gives version 3 equal to version 1. | exact |
| TC-IF-104-02 | IF-104 | Contract | 1 (mock) and 2 (real) | the graph app has no login of its own; the version records the account of the backend session. | exact |
| TC-IF-104-03 | IF-104 | Contract | 1 (mock) and 2 (real) | golden 3: wrong credentials and a made-up token are 401 and change nothing. | exact |
| TC-IF-104-04 | IF-104 | Contract | 1 (mock) and 2 (real) | golden 2: a cycle is 422 with the rule; no id and no version appear. | exact |
| TC-IF-104-05 | IF-104 | Contract | 1 (mock) and 2 (real) | golden 3: unknown id and kind are 404; a stale expected_version is 409 with the current version. | exact |
| TC-IF-105-01 | IF-105 | Contract | 1 (mock) and 2 (real) | golden 1: done; the run_start event carries model pin, seed and temperature; the run belongs to the user harness; the cost is returned. | exact |
| TC-IF-105-02 | IF-105 | Contract | 1 (mock) and 2 (real) | golden 2: no seed is bad_options, the pin MP-huge is pin_unavailable, an unknown workflow is unknown_workflow; nothing runs. | exact |
| TC-IF-105-03 | IF-105 | Contract | 1 (mock) and 2 (real) | golden 3: with a fake model two runs with the same inputs and options have equal outputs and equal event types and payloads. | exact |
| TC-IF-105-04 | IF-105 | Contract | 1 (mock) and 2 (real) | a budget below the estimate is refused with the budget named; cost 0; run_start and run_end exist. | exact |
| TC-IF-111-01 | IF-111 | Contract | 1 (mock) and 2 (real) | golden 1: after ready, an expression and the mouth follow the messages | exact |
| TC-IF-111-02 | IF-111 | Contract | 1 (mock) and 2 (real) | golden 3: an unknown expression shows neutral | exact |
| TC-IF-111-03 | IF-111 | Contract | 1 (mock) and 2 (real) | golden 3: a foreign origin, malformed JSON and an unknown type change nothing and raise nothing | exact |
| TC-IF-111-04 | IF-111 | Contract | 1 (mock) and 2 (real) | golden 3: the covered area counts negative or missing values as 0 | exact |
| TC-IF-111-05 | IF-111 | Contract | 1 (mock) and 2 (real) | golden 2: a character that cannot load says failed once | exact |
| TC-IF-111-06 | IF-111 | Contract | 1 (mock) and 2 (real) | a model that cannot map everything reports what is missing; a variant and null | exact |
| TC-IF-112-01 | IF-112 | Contract | 1 (mock) and 2 (real) | golden 1: lines play in arrival order and the speaking signal is true once and false once | exact |
| TC-IF-112-02 | IF-112 | Contract | 1 (mock) and 2 (real) | a line that arrives early never cuts the playing one | exact |
| TC-IF-112-03 | IF-112 | Contract | 1 (mock) and 2 (real) | golden 2: a muted device plays nothing and a second device still plays | exact |
| TC-IF-112-04 | IF-112 | Contract | 1 (mock) and 2 (real) | stop clears the queue and ends speaking; a page that is not the owner stays silent | exact |
| TC-IF-112-05 | IF-112 | Contract | 1 (mock) and 2 (real) | golden 3: blocked autoplay holds the lines and nothing is lost; a line that cannot load is skipped | exact |
| TC-IF-201-01 | IF-201 | Contract | 1 (mock) and 2 (real) | golden 1: message with sender, start, growing deltas, one audio chunk per sentence, done. | exact |
| TC-IF-201-02 | IF-201 | Contract | 1 (mock) and 2 (real) | golden 2: blank text is empty_text and nothing is queued. | exact |
| TC-IF-201-03 | IF-201 | Contract | 1 (mock) and 2 (real) | golden 2: positions 1, 2; the third message is queue_full; the queued ones are still answered. | exact |
| TC-IF-201-04 | IF-201 | Contract | 1 (mock) and 2 (real) | golden 3: stop right after send ends the answer without a delta; with nothing running it is stopped false. | exact |
| TC-IF-202-01 | IF-202 | Contract | 1 (mock) and 2 (real) | golden 1: done with outputs; run_start first, run_end last, every event has the run id and the starting user. | exact |
| TC-IF-202-02 | IF-202 | Contract | 1 (mock) and 2 (real) | golden 2: estimated at 2 calls, needs 4, budget 3: budget_exhausted, missing names the budget, partial outputs, run_end written. | exact |
| TC-IF-202-03 | IF-202 | Contract | 1 (mock) and 2 (real) | golden 3: a budget below the estimate is refused before any work; unknown workflow is unknown_workflow. | exact |
| TC-IF-202-04 | IF-202 | Contract | 1 (mock) and 2 (real) | costs of a node that was run are numbers; of an unknown node None (the schedule then marks the estimate incomplete). | exact |
| TC-IF-202-05 | IF-202 | Contract | 1 (mock) and 2 (real) | the options of a run (model pin, seed, temperature) are in the run_start event; the cost is returned and is 0 for a refused run. | exact |
| TC-IF-203-01 | IF-203 | Contract | 1 (mock) and 2 (real) | golden 1: version 1, an edit as version 2, the diff names the node, restore gives version 3 equal to version 1; status stays draft. | exact |
| TC-IF-203-02 | IF-203 | Contract | 1 (mock) and 2 (real) | cycle, adjacent data nodes and a session node without stopping criterion are invalid with the rule; nothing is stored. | exact |
| TC-IF-203-03 | IF-203 | Contract | 1 (mock) and 2 (real) | golden 2: tested before specification and benchmark are attached is not_promotable and names both; after attaching it works. | exact |
| TC-IF-203-04 | IF-203 | Contract | 1 (mock) and 2 (real) | golden 3: topological order, critical path, sums from the node costs; a session node counts its maximum cycles. | exact |
| TC-IF-204-01 | IF-204 | Contract | 1 (mock) and 2 (real) | golden 1: wav bytes, the spoken text equals the sentence. | exact |
| TC-IF-204-02 | IF-204 | Contract | 1 (mock) and 2 (real) | golden 3:  | exact |
| TC-IF-204-03 | IF-204 | Contract | 1 (mock) and 2 (real) | golden 2: engine down is unavailable; a voice line that does not exist is no_line and nothing else is affected. | exact |
| TC-IF-301-01 | IF-301 | Contract | 1 (mock) and 2 (real) | workflows and context_graphs are defined, versioned, not deletable. | exact |
| TC-IF-301-02 | IF-301 | Contract | 1 (mock) and 2 (real) | golden 1 and 2: a valid graph gives None; each broken rule is named. | exact |
| TC-IF-301-03 | IF-301 | Contract | 1 (mock) and 2 (real) | golden 3: p->d->p is a cycle named as [p, d, p]; a table that is not a graph table is a ValueError. | exact |
| TC-IF-302-01 | IF-302 | Contract | 1 (mock) and 2 (real) | golden 3: memory, tasks and memos are deletable, votes and runs are not; every table is versioned. | exact |
| TC-IF-302-02 | IF-302 | Contract | 1 (mock) and 2 (real) | golden 1 and 2: the four categories are valid; another category is rule category; a value other than 1 or -1 is rule schema. | exact |
| TC-IF-302-03 | IF-302 | Contract | 1 (mock) and 2 (real) | a memory record needs a source (rule schema, detail source); text with newlines, quotes and non-ASCII characters is valid; a foreign table is a ValueError. | exact |
| TC-IF-401-01 | IF-401 | Contract | 1 (mock) and 2 (real) | golden 1: three events give seq 1, 2, 3, each with the run id and the starting user; the account lists the events with a plain text. | exact |
| TC-IF-401-02 | IF-401 | Contract | 1 (mock) and 2 (real) | golden 2: an unknown type is refused and nothing is written; secrets in the payload are stored as [removed]. | exact |
| TC-IF-401-03 | IF-401 | Contract | 1 (mock) and 2 (real) | a log whose first event is not run_start, or whose seq has a gap, is reported. | exact |
| TC-IF-401-04 | IF-401 | Contract | 1 (mock) and 2 (real) | golden 3: the same steps differ only in time and run id (same); one extra check_run is a difference. | exact |
| TC-IF-402-01 | IF-402 | Contract | 1 (mock) and 2 (real) | golden 1: 1,200 m against 1,020 m fails, 1,200 against 1,200 passes, no number in the evidence is inconclusive; all with trust code. | exact |
| TC-IF-402-02 | IF-402 | Contract | 1 (mock) and 2 (real) | golden 3: a quote that is not verbatim fails; fetched passages carry the source reference and the web trust label. | exact |
| TC-IF-402-03 | IF-402 | Contract | 1 (mock) and 2 (real) | golden 2: with a limit of 1 the second web_search of the run is  | exact |
| TC-IF-402-04 | IF-402 | Contract | 1 (mock) and 2 (real) | golden 2: without a sandbox run_script is  | exact |
| TC-IF-402-05 | IF-402 | Contract | 1 (mock) and 2 (real) | checks are  | exact |
| TC-IF-404-01 | IF-404 | Contract | 1 (mock) and 2 (real) | golden 1: search returns findings with url, title and content; fetch returns text, a hash and the size. | exact |
| TC-IF-404-02 | IF-404 | Contract | 1 (mock) and 2 (real) | golden 2 and 3: a private address, localhost, port 8080 and a file scheme are unsafe_url and nothing is fetched. | exact |
| TC-IF-404-03 | IF-404 | Contract | 1 (mock) and 2 (real) | golden 2: a 404 is http_status with 404; an image is unsupported_content. | exact |
| TC-IF-404-04 | IF-404 | Contract | 1 (mock) and 2 (real) | golden 2: a search service that fails is search_error, with no partial list. | exact |
| TC-IF-404-05 | IF-404 | Contract | 1 (mock) and 2 (real) | golden 3: a page over the limit comes back truncated with exactly the limit in bytes. | exact |
| TC-IF-405-01 | IF-405 | Contract | 1 (mock) and 2 (real) | golden 1: the same DOI from two sources appears once with both sources listed. | exact |
| TC-IF-405-02 | IF-405 | Contract | 1 (mock) and 2 (real) | golden 3: until 2001-11-22 keeps the exact day, drops  | exact |
| TC-IF-405-03 | IF-405 | Contract | 1 (mock) and 2 (real) | golden 2: openalex fails: its error is listed, the works of the other sources are returned. | exact |
| TC-IF-405-04 | IF-405 | Contract | 1 (mock) and 2 (real) | if every source fails, works is empty and every failure is listed; nothing is raised. | exact |

## Statistical checks (M19: fixed before any data; run nightly and before gates)

| Test ID | Verifies | Statistic | n | Seeds | Criterion | Method | False alarm / miss (exact) | Paired fixed-seed test |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC-MIA-011 | FR-29 | appearances of the behaviour in 1000 opportunities after 5 net negative votes | 1000 | 1 to 1000 (one per opportunity); the fixed-seed regression uses seed 7 | at most 10 of 1000 (k <= 10) | exact binomial pass rule, implemented rate 0.5 % | false alarm 0.0135 at the true rate 0.005 (0.0002 with one re-run); miss 0.0102 at the true rate 0.02 (0.0204 with the re-run) | TC-MIA-011 regression: seed 7, 1000 opportunities, the count is recorded as the expected value after the first green run |
| TC-MIA-002 | FR-9, FR-10 | wrong claims passed and true claims lost on the holdout, gate against single voice | holdout size of the suites (about 110 wrong claims) | pins of `eval-spec.md` | the decision rule of `eval_decide.py` (agent-app) | paired comparison against the baseline | fixed in `specs/number-gate/eval-spec.md`; a failing check is re-run once with fresh seeds, never changed | the dev-split baseline runs of T-06 and T-10 of `specs/number-gate` |
| TC-MIA-008 | FR-25 | pass rate of the persona dialogues | 100 dialogues | dialogue set fixed once; the model run uses the pin of `eval-spec.md` (seed 7, temperature 0) | at least 84 of 100 pass (k >= 84) | exact binomial pass rule; the true rate of today's MIA is taken as 0.90 (about 1 hiccup in 10, owner) | false alarm 0.0206 at the true rate 0.90 (0.0004 with one re-run); miss 0.0211 at the true rate 0.75 (0.0418 with the re-run) | the same 100 dialogues once with seed 7 |

Error rates from `plan-phase/scripts/false_alarm.py` (`--n 1000 --max-rate 0.01 --good 0.005 --bad 0.02`, with and without `--rerun`). **Finding F-1:** the criterion of AC-11 "at most 10 appearances in 1000" fails 41.7 % of the time if the true rate is exactly 1 % (FR-29 says "at most 1 %"). A test written that way would be flaky. The implemented rate for a nearly stopped behaviour is therefore 0.5 %, which keeps FR-29 true and gives the error rates above (OPEN-2).

## Benchmarks and baselines

| Benchmark | Verifies | Reference hardware | Repetitions (warm-up) | Baseline median (measured <date>) | Budget / regression rule |
| --- | --- | --- | --- | --- | --- |
| BM-MIA-001 | NFR-7 | workstation: Ryzen 9 5900X, RX 7800 XT 16 GB, MP-light (`gemma4:12b-it-qat`), `num_ctx` 8192 | 20 runs after 3 warm-up runs, with and without a review slice running | not yet measured (task T-13: measure on today's MIA first) | median <= 10 s; a regression of more than 20 % against the baseline fails |
| BM-MIA-002 | NFR-7 | desktop browser and any phone inside the network (no particular device; the owner names none) | 10 runs of 30 s after 2 warm-up runs | not yet measured (task T-13) | median >= 30 fps on the desktop and on the phone |

## Smoke tests (run in Phase 6, target environment)

| Test ID | Verifies | Target | Conditions | Expected result |
| --- | --- | --- | --- | --- |
| SMOKE-MIA-001 | FR-19, NFR-9 | the owner's workstation (Fedora 43, podman) | fresh checkout, one configuration file, one command | compose stack up with all containers; the first account can be created; a chat message is answered |
| SMOKE-MIA-002 | NFR-6, CON-5 | a phone outside the home network | Tailscale (tailnet) and HTTPS | the chat page loads and a message is answered; no public port is open (the owner runs this; SC-03) |
| SMOKE-MIA-003 | NFR-9 | the owner's workstation | each container started alone against the mocks of its neighbours | each container passes the contract suites of its interfaces (stage 2) |

## Validation criteria (checked in Phase 7)

| ID | Criterion | How we check | Who | Agreement (if numeric): margin, mean or single values, method |
| --- | --- | --- | --- | --- |
| VAL-001 | The owner can trust the facts in a lookup answer | the owner confirms or rejects the verdict of 20 sampled answers against the sources; rejected ones become eval cases | owner | descriptive; a rate is reported with its interval, no margin |
| VAL-002 | The path works: the second workflow (review) is added within one month after the lookup is promoted | the recorded time stamps of the skill path (AC-9) | owner | date check; no numeric agreement |
| VAL-003 | The character feels in character and pleasant to the users | the weekly overall score (AC-8c), a short rating by each user after one week, the check dialogues (AC-8a, b) | users and owner | descriptive; the score trend over the week, no margin |
| VAL-004 | MIA is usable on a phone inside the tailnet | each user uses the chat on their phone for one week and reports problems (SMOKE-MIA-002, FB items) | users | descriptive |
| VAL-005 | The platform is a blueprint: a person adds a new example workflow by the documented path without changing platform code | a dry run of the path with a new small workflow, time recorded | owner | descriptive |

## Open numbers and the owner decisions on them (2026-10-25)

| ID | Where | What | Who |
| --- | --- | --- | --- |
| OPEN-1 | AC-8 / TC-MIA-008 | Decided (owner, 2026-10-25): 100 dialogues, at least 84 pass; today's MIA has a hiccup in about 1 of 10 dialogues, so the true rate is taken as 0.90; the baseline run on the same dialogues is measured first (T-04) | owner |
| OPEN-2 | AC-11 / FR-29 | Decided (owner): the implemented rate for a nearly stopped behaviour is 0.5 %; FR-29 keeps "at most 1 %"; the check is "at most 10 of 1000" | owner |
| OPEN-3 | AC-28 / TC-MIA-028 | Decided (owner): generous, a factor of 3 either way; what matters is that an estimate is shown, the run works and the first text comes within about 10 s (the current implementation answers 1 or 2 sentences within that) | owner |
| OPEN-4 | AC-19 / BM-MIA-002 | Decided (owner): no particular phone, any phone inside the network; 30 fps is the target on the phone and on the desktop (NFR-7 and AC-19 amended: the desktop figure was 60 fps) | owner |
| OPEN-5 | AC-15 / TC-MIA-015 | Decided (owner): "within seconds" is 5 s (the Database promises 2 s per subscriber) | owner |
| OPEN-6 | NFR-7 / REQ-BE-003 | Decided (owner, 2026-10-25, on the recommendation): a queue of 5 waiting messages and at most 2 waiting messages per user | owner |
