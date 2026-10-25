# Glossary: MIA

Used by the requirements linter (L1) and as context for the LLM assessor (L3). Terms of the decomposition and of the verification gate; more are added when the nodes are cut. "Avoid" lists synonyms that must not be used in requirements.

| Term | Definition | Model element | Unit | Avoid |
|---|---|---|---|---|
| Web Frontend | Node N-1: the static files of the chat page, the character view, login views and voice playback; served by the backend container | WebFrontEnd | – | GUI, UI |
| Backend | Node N-2: the server and accounts, the chat agent, workflow management and execution, voice synthesis | WebApplication | – | server side, middleware |
| Database | Node N-3: the PostgreSQL database and its storage layer | Persistence | – | data layer |
| Evaluation and operation node | Node N-4: harness, suites, baselines, compose stack, backup, shutdown | Evaluation | – | tooling node |
| Graph app | Node N-5: the independent add-on tool that shows and edits workflow and context graphs | GraphApp | – | graph editor, graph UI |
| storage interface | The interface IF-102 of the Database used by the Backend and the Graph app | StorageLayer | – | database API, DB access |
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
