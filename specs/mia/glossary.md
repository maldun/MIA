# Glossary: MIA

Used by the requirements linter (L1) and as context for the LLM assessor (L3). Terms of the decomposition and of the verification gate; more are added when the nodes are cut. "Avoid" lists synonyms that must not be used in requirements.

| Term | Definition | Model element | Unit | Avoid |
|---|---|---|---|---|
| Web Frontend | Node N-1: the static files of the chat page, the character view, login views and voice playback; served by the backend container | WebFrontEnd | – | GUI, UI |
| Backend | Node N-2: the server and accounts, the chat agent, workflow management and execution, voice synthesis | WebApplication | – | server side, middleware |
| Database | Node N-3: the PostgreSQL database and its storage layer | Persistence | – | data layer |
| Evaluation and operation node | Node N-4: harness, suites, baselines, compose stack, backup, shutdown | Evaluation | – | tooling node |
| Graph app | Node N-5: the independent add-on tool that shows and edits workflow and context graphs | GraphApp | – | graph editor, graph UI |
| storage interface | The interface IF-102 of the Database, used by the Backend only | StorageLayer | – | database API, DB access |
| workflow | A pipeline or agent workflow stored as a graph of process nodes and data nodes | – | – | flow, pipeline graph |
| process node | A node of a workflow graph that does work (a task, a model step or a session) | – | – | step node, task node |
| data node | A node of a workflow graph that holds an artifact (a claim, a page, a result) | – | – | material node, artifact node |
| session node | A process node that holds a multi-agent task with its stopping criteria | – | – | debate node |
| context graph | The concepts, entities and relations a workflow or the chat works with, with the views of its steps | – | – | knowledge graph |
| mood map | The editable table that assigns an expression and a gesture to a mood | – | – | emotion table |
| voice line | A short text with an audio file spoken for a mood or an event | – | – | sound clip |
| claim | A statement whose truth the verification checks | – | – | assertion |
| verdict | The result of verifying a claim: supported, refuted or unclear | – | – | judgement result |
| judgement style | The way model judgement is organised for open claims: single voice, repeated samples, jury, cops, trial | – | – | verdict style |
| model pin | The model name, tag and digest an evaluation was run with (MP-light, MP-full) | – | – | model version |
| holdout | The part of a suite used only for decisions in Verify | – | – | test split |
| API and accounts | Node N-2.1: the Socket.IO and REST surface of the Backend, accounts and sessions, delivery of the frontend files | WebApplication | – | gateway |
| Chat agent | Node N-2.2: the shared conversation, queue, persona, mood, memory, behaviour rules, votes, adaptation, tasks and memos | ConversationCore | – | chat bot, dialogue manager |
| Workflow management | Node N-2.3: the library of workflows and skills, graph rules, specifications, context graphs, schedule | TaskRuntime | – | workflow editor |
| Workflow execution | Node N-2.4: running a workflow under budgets with verification, research, sandbox and run log | TaskRuntime | – | task engine |
| Voice synthesis | Node N-2.5: text-to-speech on the host with the anime effect and the voice lines | VoiceSubsystem | – | speech engine |
| Chat and login views | Node N-1.1: the chat page, login and user views, voting, tasks and memos views, accessibility; owns the socket to the Backend | WebFrontEnd | – | chat UI |
| Character view | Node N-1.2: the 3D character in an iframe, expressions, gestures, mouth, mood map, editors, model selection | WebFrontEnd | – | avatar view |
| Voice playback | Node N-1.3: playing the audio of the answers and the voice lines in this browser | WebFrontEnd | – | audio player |
| Storage layer | Node N-3.1: the PostgreSQL database and the one door to it (IF-102) | Persistence | – | DB layer |
| Graph tables | Node N-3.2: the tables of workflows and context graphs and the graph rules of every write | Persistence | – | graph store |
| Record tables | Node N-3.3: the tables of history, memory, votes, tasks, memos, presets, gestures and run results | Persistence | – | record store |
| Pipeline runner | Node N-2.4.1: runs a workflow step by step under budgets, with model calls and model management; knows no particular workflow | TaskRuntime | – | executor |
| Tools and sandbox | Node N-2.4.2: the tools any workflow can call (code checks, web, scholarly sources, source records) and the sandbox, counted against the budgets of a run | VerificationSuite | – | tool box |
| Run log | Node N-2.4.3: typed events of runs, replay, comparison, the account of an answer | Observability | – | trace store |
| example workflow | A workflow delivered as library data to prove the platform and to serve as a blueprint: lookup, verify, review, method transfer; its criteria are decided by the benchmark | – | – | built-in skill |
