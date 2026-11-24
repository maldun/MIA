# Goal G-V4 – Graph rework, graph app and context-graph builder (DRAFT)

Opened 2026-11-20 on the owner's request ("G-V4 starts a bigger rework"). Scope as the owner set it on 2026-11-20 (D-360 to D-385): the graph rework (storage, runner), the graph app in three stages, context graphs and their builder. The leftovers of G-V2 and G-V3 and the validation moved to a new goal **G-V5, the first test run**, whose definition is parked until G-V4 closes (D-385, D-386; drafts in `../../parked/G-V5/`). **State:** Explore artifacts and reviewed top-level specs exist per subgoal; the owner's Explore gate and the agreements below are open; scope rows, Parts and frozen requirements are Plan step 0.

- Kind: iteration
- Parent: –
- Statement: Every workflow and context graph has one stored truth in the live store or in a copy, runs as the graph the owner sees and edits, can be viewed, edited and replayed in the web app, and context graphs can be built from documents with items the owner confirms.
- Exit criterion: OC-6 to OC-11 below (to confirm in Plan), checked by the exit criteria of the subgoals; the leftovers and the validation moved to G-V5 (D-385)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4
- Subgoals: G-V4.GRAPHSTORE, then G-V4.GRAPHAPI, then G-V4.VIEW, G-V4.EDIT, G-V4.REPLAY, G-V4.CONTEXT (after EDIT), G-V4.BUILDER (after CONTEXT)
- Status: Proposed

## Owner's scope of 2026-11-20 (D-360)
1. Review how graphs are stored: files and database interchangeable, graphs transferable (files fit tests). Subgoal **G-V4.GRAPHSTORE** (taken from the earlier proposal of 2026-11-19 on `plan/graph-rework`; the file and PostgreSQL backends and `storage_copy.py` already exist).
2. Review how the runner works on graphs, favouring networkx. Subgoal **G-V4.GRAPHAPI** (same source; closes FB-02 on the Python side). Decision: a graph is a networkx graph, and **code may be stored in the graph**: a code snippet is a data node attached to a transform node, and the toolbox reference (for example a `python-exec` tool) does the calling. The runner never executes code by itself.
3. Graph viewer (N-5) done properly, each stage its own subgoal: **G-V4.VIEW** (pull from the data source, minimal prototype drawing it in the web app), **G-V4.EDIT** (editing in the web app), **G-V4.REPLAY** (store the edits as an edit log and replay it on a graph).
4. Validation runs and the editor-driven improvement of graphs: moved to **G-V5** (D-385), where the owner judges what G-V2 to G-V4 built.
5. The leftovers of G-V2 and G-V3 (the old OC-1 to OC-4): moved to **G-V5.LEFTOVER** (D-385).


## Outcome criteria (Explore state 2026-11-20, to confirm in Plan)
OC-1 to OC-5 of the earlier draft (live settings, holdout decisions, harmful imports, consistent records, validation of G-V2 and G-V3) moved to G-V5 (D-385); the numbers are not reused.

| ID | Expected outcome | Derived from |
|---|---|---|
| OC-6 | Given a graph kept in the live store or in a portable set of files, when the owner moves it between the live store and a portable set of files (used for tests and transfer), then it is there with all its versions and reads back exactly as before | FR-40, owner 2026-11-20 (item 1), FR-30, NFR-8 |
| OC-7 | Given a skill with a stored graph, when the owner runs it, then the run follows exactly that graph, the same one the owner sees and edits, and a piece of code inside the graph runs only with the trust the owner has given it | FR-6, FR-7, FR-40, NFR-3 (FB-02, owner 2026-11-20, item 2), FR-36, FR-37, FR-38, FR-45 |
| OC-8 | Given a stored graph, when the owner opens it in the web app, then it is drawn as it is stored, the owner can change it, a change that breaks a graph rule is refused with the rule named, and every change can be played back on the graph | FR-22, owner 2026-11-20 (item 3), FR-16, FR-21, NFR-6, NFR-9 |
| OC-9 | Given a workflow graph that the owner has changed in the web app, when the owner looks at it later, then the changes, their reasons, who made them and when are shown, so the owner can follow how a graph was improved | FR-6, FR-22 (owner 2026-11-20, item 4; the improvement during the validation runs is in G-V5) |
| OC-10 | Given a snapshot of the skill set taken before the rework and one after, when the owner restores either, then every graph is as it was at that snapshot, and the state before a restore is kept | FR-47 |
| OC-11 | Given a document the owner adds, when the owner builds a context graph from it, then items are proposed with their source, only confirmed items are read by skills, and the proposals meet the owner's quality bar | FR-41, FR-42 (owner 2026-11-20, D-380) |

## Measure ideas for Plan step 1a (technology dependent second layer, not outcomes)
Written here so they are not lost; Plan turns them into `Kind: measure` items (Method, Metric, Reference, Detail in).
| Outcome | Measure idea |
|---|---|
| OC-6 | round trip of the 15 converted skill graphs, both directions, files and PostgreSQL 16: identical content and version lists (the spike of GRAPHSTORE is the first run) |
| OC-7 | the run record names the stored graph and its version; a run of each converted skill on the stored graph gives the same results as the converted-in-memory run on its suite (decided by `eval_decide.py`, pins of `eval-spec.md`); a code step without trust is refused in a red-team case |
| OC-8 | demonstration TC-GA-016 plus contract suite of the graph interface; replay of the edit log on the first version gives the stored last version for every edit sequence of a seeded generator |
| OC-9 | a graph is changed in the editor, then its history shows the entries with their reasons and the playback gives the saved version |
| OC-10 | take a snapshot, run the migration, take a second snapshot, restore each and compare every graph version (the snapshot tests of G-V2.SNAPSHOT on the new stored form) |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| model server and pins of `eval-spec.md` (MP-light `gemma4:12b-it-qat`) | real | a changed pin or quantization needs the owner |
| holdout suites for research, plans, verdicts, computable, extraction | to be written and labelled by the owner | TD-88; agents never label or run holdout |
| release v0.2.1 and the old-runner baselines of D-355 | real | the starting point |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| validation of G-V2 and G-V3 as its own subgoal | moved out of G-V4 to G-V5.VALIDATE | owner 2026-11-20 (D-385) | 2026-11-20 |
| improving the skills (TD-86 to TD-89 name it as the trigger) | open | scope not set; decide in Explore | |
| the four leftovers (old OC-1 to OC-4) | moved out of G-V4 to G-V5.LEFTOVER | owner 2026-11-20 (D-385) | 2026-11-20 |
| graph storage, runner on networkx | split: G-V4.GRAPHSTORE, G-V4.GRAPHAPI | owner 2026-11-19 and 2026-11-20 (D-360) | 2026-11-20 |
| viewer stages | split: G-V4.VIEW, G-V4.EDIT, G-V4.REPLAY, each with all seven phases | owner 2026-11-20 (D-360) | 2026-11-20 |
| size of GRAPHSTORE and GRAPHAPI by descendants (about 90 and 96 requirements, most of them verified in G-V1 and G-V2) | split by the owner on 2026-11-20 (D-392) into three parts each: GRAPHSTORE.CORE, .TRANSFER, .MIGRATION and GRAPHAPI.RULES, .RUN, .CODE (26 to 42 requirements each by descendants; the cut into tasks follows in step 5) | the number comes from the descendants of 5 and 6 top-level items, not from new work | 2026-11-20 |
| editing context graphs | split: G-V4.CONTEXT | owner 2026-11-20 (D-369) | 2026-11-20 |
| the context-graph builder (goal C) | split: G-V4.BUILDER, the largest and last graph subgoal; first slice documents only (proposed) | owner 2026-11-20 (D-380) | 2026-11-20 |

## Scope
Marked in Explore by the owner's direction of 2026-11-20 (D-360 to D-362) for the top-level items of `requirements.md`. "partly" counts as in; the subgoals take the parts (their own scope tables come in Plan).

| Item | In/Out | Reason |
|---|---|---|
| FR-6 | partly | skills run from their stored graph (G-V4.GRAPHSTORE, G-V4.GRAPHAPI); the live trust, lifecycle, budgets and stop (TD-86, TD-87) are in G-V5.LEFTOVER |
| FR-7 | in | the graph rules become one set and apply to the stored graph (G-V4.GRAPHAPI) |
| FR-22 | in | the graph app: view, edit, edit log (G-V4.VIEW, G-V4.EDIT, G-V4.REPLAY); the old text of the requirement stays as legacy (D-362) |
| FR-30 | partly | context graphs follow the same stored form (G-V4.GRAPHSTORE) and are edited in G-V4.CONTEXT; their content and the context-graph builder stay as they are |
| FR-34, FR-35, FR-46 | out | the open items of G-V3 moved to G-V5.LEFTOVER (D-385) |
| FR-36 | partly | the skill record points at its stored graph (G-V4.GRAPHSTORE); the skill definition itself is unchanged |
| FR-37 | in | the graph model: one rule set and one stored truth (G-V4.GRAPHSTORE, G-V4.GRAPHAPI) |
| FR-38 | partly | code in a graph is called only through the toolbox with its trust (D-360, THR-013); exchange of transforms is unchanged |
| FR-40 | in | files and database interchangeable, one stored truth, migration of the existing record (G-V4.GRAPHSTORE); legacy text stays (D-362) |
| FR-45 | partly | the converted pipelines become an import path into stored graphs (G-V4.GRAPHSTORE); no new skill is converted |
| FR-47 | in | snapshots read and restore stored graph versions (OC-3 of G-V4.GRAPHSTORE) |
| FR-16 | partly | the run record names the stored graph and its version, the edit log shows who changed what (G-V4.GRAPHAPI, G-V4.REPLAY); the event schema is otherwise unchanged |
| FR-21 | partly | the graph app needs login and attributes every edit to the account (G-V4.EDIT); no change to accounts |
| NFR-3 | in | stored code and imported steps stay data until the toolbox runs them (G-V4.GRAPHAPI, THR-013); the refusal of harmful imports with a recorded case is in G-V5.LEFTOVER |
| REQ-GA-010 | in | the viewer works inside the home network and loads nothing from outside (NFR-13 of G-V4.VIEW); the rest of NFR-5 is not changed |
| NFR-6 | partly | the graph app is reached only through the same authenticated access (G-V4.VIEW); no change to the access rules |
| NFR-8 | in | files and database behave the same behind the storage interface (G-V4.GRAPHSTORE) |
| NFR-9 | partly | the graph app runs as its own container (G-V4.VIEW); the other containers are unchanged |
| FR-17 | out | the evaluation harness is used to decide OC-7 and OC-2, not changed |
| FR-1, FR-2, FR-3, FR-4, FR-5, FR-23, FR-24, FR-25, FR-31, FR-32 | out | conversation, character, voice, transparency and persona are not touched by the graph rework |
| FR-8, FR-14, FR-15, FR-18, FR-19, FR-27, FR-28, FR-29, FR-33 | out | model management, memory, rules, learning, operation, feedback, tasks and schedule are not touched |
| FR-9, FR-10, FR-11, FR-12, FR-13 | out | the verification, lookup, literature, source and method skills only run on the new path; their behaviour is checked as equivalence under OC-7, not changed |
| FR-20, FR-26 | out | the path to promotion and the specification and benchmark of a workflow stay as they are; improving graphs in the editor (OC-9) does not change them |
| FR-41, FR-42 | in | the context-graph builder and the reading of the confirmed part (G-V4.BUILDER, D-380); was out as goal C |
| FR-43 | out | the skills window is goal B; the graph app is the editor of this goal |
| FR-39, FR-44 | out | goal D (debates, benchmarks, review of exchanged transforms) |
| NFR-1, NFR-2, NFR-4, NFR-5, NFR-7 | out | device range, small-model strategies, honest confidence, privacy and efficiency are not changed by the rework (the loader is measured inside OC-7) |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.1 API and accounts | real |  |
| N-2.3 Workflow management (library, graph model, snapshots, toolbox) | real | library, snapshots, toolbox |
| N-2.4.1 Pipeline runner (graph run, converter) | real | the runner and the converter |
| N-2.4.2 Tools and sandbox | real | contained space for code steps |
| N-2.4.3 Run log | real | run record, a run's context graph |
| N-3.1 Storage layer (files and PostgreSQL backends, copy) | real | both backends |
| N-3.2 Workflows and context graphs (graph tables, rules) | real |  |
| N-3.3 Memories, history, feedback (record tables) | real | new tables for the edit log and the arrangement |
| N-4.1 Evaluation (suites, harness) | real | the equivalence suites |
| N-5 Graph app (page, vendored vis-network) | real |  |
| N-6 Context-graph builder (new; a workflow on the runner, no container of its own, D-520) | real | new part |
| local model server with the pinned models (Ollama) | real | the pinned models; scripted replies in the unit tests |
| compose stack and web routing (Caddy) | real | one origin for page and backend |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| IF-102 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the storage layer interface, read by both groups; changes only by a joint amendment (scoped record IDs, sync) |
| IF-104 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the graph interface for the app; IF-104 v2 is written at G-V4 level (D-368) and shared with VIEW, EDIT, REPLAY and CONTEXT |
| IF-203 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the workflow library interface, used by storage and by the run |
| IF-301 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the graph tables; scoped record IDs and the rules refusal live here (D-368) |
| REQ-API-014 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the workflow and graph routes of the backend |
| REQ-API-016 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | graph routes under the session, author of a version |
| REQ-BE-076 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the backend reads graphs through the library |
| REQ-SLY-012 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the storage notices after a write |
| REQ-WFM-026 | G-V4.GRAPHSTORE, G-V4.GRAPHAPI | the library keeps the versions of workflows and context graphs |

The new shared items are frozen when Plan step 1b writes them: IF-104 v2, the scoped record IDs and their refusal (IF-301), the one rule set of eight rules, and the arrangement record. Until then they are named in `consistency-review.md` section 4.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHSTORE | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.GRAPHAPI | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.VIEW | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.EDIT | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.REPLAY | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.CONTEXT | [x] Stefan Reiterer (owner) | 2026-11-20 |
| G-V4.BUILDER | [x] Stefan Reiterer (owner) | 2026-11-20 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | gate passed 2026-11-20: the seven top-level specs approved (D-389 to D-391), the agreements to the split ticked, `consistency-review.md`, the carry-over of the prototype graphview decided (D-387, D-388) |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5, to be defined when G-V4 closes (D-386) |
