# Goal G-V4 – Graph rework, graph app and the leftovers of G-V2 and G-V3 (DRAFT)

Opened 2026-11-20 on the owner's request: "G-V4 starts a bigger rework". The owner chose (questionnaire 2026-11-20) to **take the leftovers of G-V2 and G-V3 as the scope**. The sources are `G-V2/remainder-for-next-goal.md`, the open items of `G-V3/verification-report.md` and `deferred.md` (TD-82 to TD-90). **Nothing here is decided by the owner beyond that choice**: statement, outcome criteria and scope rows are a proposal for the Explore phase; the rework may be bigger than this list.

- Kind: iteration
- Parent: –
- Statement: The converted skills run with the live trust, lifecycle, budgets and stop of the owner, the skills improved by the rework are measured on holdout suites, the draft requirements and deferrals of G-V2 and G-V3 are settled, and the validation of G-V2 and G-V3 is done on this version.
- Exit criterion: OC-1 to OC-5 below (proposal), checked in Plan; the validation criteria are those collected in G-V4.VALIDATE
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4
- Subgoals: G-V4.GRAPHSTORE, then G-V4.GRAPHAPI, then G-V4.VIEW, G-V4.EDIT, G-V4.REPLAY, with G-V4.LEFTOVER alongside, and G-V4.VALIDATE last
- Status: Proposed

## Owner's scope of 2026-11-20 (D-360)
1. Review how graphs are stored: files and database interchangeable, graphs transferable (files fit tests). Subgoal **G-V4.GRAPHSTORE** (taken from the earlier proposal of 2026-11-19 on `plan/graph-rework`; the file and PostgreSQL backends and `storage_copy.py` already exist).
2. Review how the runner works on graphs, favouring networkx. Subgoal **G-V4.GRAPHAPI** (same source; closes FB-02 on the Python side). Decision: a graph is a networkx graph, and **code may be stored in the graph**: a code snippet is a data node attached to a transform node, and the toolbox reference (for example a `python-exec` tool) does the calling. The runner never executes code by itself.
3. Graph viewer (N-5) done properly, each stage its own subgoal: **G-V4.VIEW** (pull from the data source, minimal prototype drawing it in the web app), **G-V4.EDIT** (editing in the web app), **G-V4.REPLAY** (store the edits as an edit log and replay it on a graph).
4. Start the validation runs of G-V2 and G-V3 and use the editor to improve the workflow graphs: **G-V4.VALIDATE** (existing draft; the improvement of graphs becomes one of its stages, to confirm).
5. The leftovers of the draft (OC-1 to OC-4 below) stay together as **G-V4.LEFTOVER**.

New outcome criteria OC-6 to OC-9 are in the table; OC-1 to OC-5 stay as proposed.

## Outcome criteria (proposal, to confirm in Explore)
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a skill that runs on the graph path, when the owner changes its trust or lifecycle, or asks it to stop, or it reaches its budget, then the run follows the owner's current setting and ends as the old runner would | FR-6, FR-7, FR-34 (TD-86, TD-87) |
| OC-2 | Given the skills of the rework, when they are measured against their suites, then the decision rests on holdout cases labelled by the owner, not on the dev split alone | FR-6 (TD-88, TD-89, TD-90) |
| OC-3 | Given an imported skill step that would do harm, when it is offered to MIA, then it is refused and a red-team case shows that | NFR-3 (V2-6, THR-011) |
| OC-4 | Given the requirements, tests and records of G-V2 and G-V3, when they are checked, then no draft, stale scope wording or missing table entry from the lists of both goals remains | FR-6, FR-34 (V2-1 to V2-3, V2-8, TD-82 to TD-85), FR-35 |
| OC-6 | Given a graph kept in the live store or in a portable set of files, when the owner moves it between the live store and a portable set of files (used for tests and transfer), then it is there with all its versions and reads back exactly as before | FR-40, owner 2026-11-20 (item 1), FR-30, NFR-8 |
| OC-7 | Given a skill with a stored graph, when the owner runs it, then the run follows exactly that graph, the same one the owner sees and edits, and a piece of code inside the graph runs only with the trust the owner has given it | FR-6, FR-40 (FB-02, owner 2026-11-20, item 2), FR-36, FR-37, FR-38, FR-45 |
| OC-8 | Given a stored graph, when the owner opens it in the web app, then it is drawn as it is stored, the owner can change it, a change that breaks a graph rule is refused with the rule named, and every change can be played back on the graph | FR-22, owner 2026-11-20 (item 3), FR-16, FR-21, NFR-6, NFR-9 |
| OC-9 | Given the validation runs, when a workflow graph turns out to be weak, then the owner improves it in the web app and can later see what was changed, when and why | FR-6, FR-22 (owner 2026-11-20, item 4) |
| OC-10 | Given a snapshot of the skill set taken before the rework and one after, when the owner restores either, then every graph is as it was at that snapshot, and the state before a restore is kept | FR-47 |
| OC-5 | Given the finished rework, when the owner uses the version, then G-V2 and G-V3 are validated on it (G-V4.VALIDATE) | FR-6, FR-34, FR-46 (VAL-006, 007, 009, 012, 013) |

## Measure ideas for Plan step 1a (technology dependent second layer, not outcomes)
Written here so they are not lost; Plan turns them into `Kind: measure` items (Method, Metric, Reference, Detail in).
| Outcome | Measure idea |
|---|---|
| OC-6 | round trip of the 15 converted skill graphs, both directions, files and PostgreSQL 16: identical content and version lists (the spike of GRAPHSTORE is the first run) |
| OC-7 | the run record names the stored graph and its version; a run of each converted skill on the stored graph gives the same results as the converted-in-memory run on its suite (decided by `eval_decide.py`, pins of `eval-spec.md`); a code step without trust is refused in a red-team case |
| OC-8 | demonstration TC-GA-016 plus contract suite of the graph interface; replay of the edit log on the first version gives the stored last version for every edit sequence of a seeded generator |
| OC-10 | take a snapshot, run the migration, take a second snapshot, restore each and compare every graph version (the snapshot tests of G-V2.SNAPSHOT on the new stored form) |
| OC-9 | at least one workflow graph improved in a validation session, with its edit log shown to the owner |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| model server and pins of `eval-spec.md` (MP-light `gemma4:12b-it-qat`) | real | a changed pin or quantization needs the owner |
| holdout suites for research, plans, verdicts, computable, extraction | to be written and labelled by the owner | TD-88; agents never label or run holdout |
| release v0.2.1 and the old-runner baselines of D-355 | real | the starting point |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| validation of G-V2 and G-V3 as its own subgoal | split: G-V4.VALIDATE | owner 2026-11-20: validate after the rework, since its changes may affect the validation runs | 2026-11-20 |
| improving the skills (TD-86 to TD-89 name it as the trigger) | open | scope not set; decide in Explore | |
| the four leftovers (OC-1 to OC-4) | split: G-V4.LEFTOVER | owner 2026-11-20 (D-360) | 2026-11-20 |
| graph storage, runner on networkx | split: G-V4.GRAPHSTORE, G-V4.GRAPHAPI | owner 2026-11-19 and 2026-11-20 (D-360) | 2026-11-20 |
| viewer stages | split: G-V4.VIEW, G-V4.EDIT, G-V4.REPLAY, each with all seven phases | owner 2026-11-20 (D-360) | 2026-11-20 |

## Scope
Marked in Explore by the owner's direction of 2026-11-20 (D-360 to D-362) for the top-level items of `requirements.md`. "partly" counts as in; the subgoals take the parts (their own scope tables come in Plan).

| Item | In/Out | Reason |
|---|---|---|
| FR-6 | in | skills run on the stored graph with the owner's trust, lifecycle, budgets and stop (OC-1, OC-7; TD-86, TD-87), G-V4.GRAPHAPI, G-V4.LEFTOVER |
| FR-7 | in | the graph rules become one set and apply to the stored graph (G-V4.GRAPHAPI) |
| FR-22 | in | the graph app: view, edit, edit log (G-V4.VIEW, G-V4.EDIT, G-V4.REPLAY); the old text of the requirement stays as legacy (D-362) |
| FR-30 | partly | context graphs follow the same stored form (G-V4.GRAPHSTORE); their content and the context-graph builder stay as they are |
| FR-34, FR-35, FR-46 | partly | open items of G-V3 only (V3-6, F-04, TD-82 to TD-85) in G-V4.LEFTOVER |
| FR-36 | partly | the skill record points at its stored graph (G-V4.GRAPHSTORE); the skill definition itself is unchanged |
| FR-37 | in | the graph model: one rule set and one stored truth (G-V4.GRAPHSTORE, G-V4.GRAPHAPI) |
| FR-38 | partly | code in a graph is called only through the toolbox with its trust (D-360, THR-013); exchange of transforms is unchanged |
| FR-40 | in | files and database interchangeable, one stored truth, migration of the existing record (G-V4.GRAPHSTORE); legacy text stays (D-362) |
| FR-45 | partly | the converted pipelines become an import path into stored graphs (G-V4.GRAPHSTORE); no new skill is converted |
| FR-47 | in | snapshots read and restore stored graph versions (OC-3 of G-V4.GRAPHSTORE) |
| FR-16 | partly | the run record names the stored graph and its version, the edit log shows who changed what (G-V4.GRAPHAPI, G-V4.REPLAY); the event schema is otherwise unchanged |
| FR-21 | partly | the graph app needs login and attributes every edit to the account (G-V4.EDIT); no change to accounts |
| NFR-3 | in | stored code and imported steps stay data until the toolbox runs them (OC-3, THR-011, THR-013) |
| NFR-6 | partly | the graph app is reached only through the same authenticated access (G-V4.VIEW); no change to the access rules |
| NFR-8 | in | files and database behave the same behind the storage interface (G-V4.GRAPHSTORE) |
| NFR-9 | partly | the graph app runs as its own container (G-V4.VIEW); the other containers are unchanged |
| FR-17 | out | the evaluation harness is used to decide OC-7 and OC-2, not changed |
| FR-1, FR-2, FR-3, FR-4, FR-5, FR-23, FR-24, FR-25, FR-31, FR-32 | out | conversation, character, voice, transparency and persona are not touched by the graph rework |
| FR-8, FR-14, FR-15, FR-18, FR-19, FR-27, FR-28, FR-29, FR-33 | out | model management, memory, rules, learning, operation, feedback, tasks and schedule are not touched |
| FR-9, FR-10, FR-11, FR-12, FR-13 | out | the verification, lookup, literature, source and method skills only run on the new path; their behaviour is checked as equivalence under OC-7, not changed |
| FR-20, FR-26 | out | the path to promotion and the specification and benchmark of a workflow stay as they are; improving graphs in the editor (OC-9) does not change them |
| FR-41, FR-42 | out | goal C (categories as schemas, proposals of items) overlaps with context graphs and waits (open question of G-V4.GRAPHSTORE) |
| FR-43 | out | the skills window is goal B; the graph app is the editor of this goal |
| FR-39, FR-44 | out | goal D (debates, benchmarks, review of exchanged transforms) |
| NFR-1, NFR-2, NFR-4, NFR-5, NFR-7 | out | device range, small-model strategies, honest confidence, privacy and efficiency are not changed by the rework (the loader is measured inside OC-7) |

## Parts
To be written in Plan.

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|

None yet: the subgoals share the stored graph form (G-V4.GRAPHSTORE); Plan freezes the requirements they share.

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHSTORE | [ ] Stefan Reiterer (owner) | |
| G-V4.GRAPHAPI | [ ] Stefan Reiterer (owner) | |
| G-V4.VIEW | [ ] Stefan Reiterer (owner) | |
| G-V4.EDIT | [ ] Stefan Reiterer (owner) | |
| G-V4.REPLAY | [ ] Stefan Reiterer (owner) | |
| G-V4.LEFTOVER | [ ] Stefan Reiterer (owner) | |
| G-V4.VALIDATE | [ ] Stefan Reiterer (owner) | |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | open | scope of the rework (owner), `top-level-spec.md` update |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | G-V4.VALIDATE |
