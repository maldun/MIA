# Goal G-V4 – Graph rework, graph app and the leftovers of G-V2 and G-V3 (DRAFT)

Opened 2026-11-20 on the owner's request: "G-V4 starts a bigger rework". The owner chose (questionnaire 2026-11-20) to **take the leftovers of G-V2 and G-V3 as the scope**. The sources are `G-V2/remainder-for-next-goal.md`, the open items of `G-V3/verification-report.md` and `deferred.md` (TD-82 to TD-90). **Nothing here is decided by the owner beyond that choice**: statement, outcome criteria and scope rows are a proposal for the Explore phase; the rework may be bigger than this list.

- Kind: iteration
- Parent: –
- Statement: The converted skills run with the live trust, lifecycle, budgets and stop of the owner, the skills improved by the rework are measured on holdout suites, the draft requirements and deferrals of G-V2 and G-V3 are settled, and the validation of G-V2 and G-V3 is done on this version.
- Exit criterion: OC-1 to OC-5 below (proposal), checked in Plan; the validation criteria are those collected in G-V4.VALIDATE
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v4
- Subgoals (proposed, owner 2026-11-20, D-360): G-V4.GRAPHSTORE, then G-V4.GRAPHAPI, then G-V4.VIEW, G-V4.EDIT, G-V4.REPLAY, with G-V4.LEFTOVER alongside, and G-V4.VALIDATE last
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
| OC-4 | Given the requirements, tests and records of G-V2 and G-V3, when they are checked, then no draft, stale scope wording or missing table entry from the lists of both goals remains | (V2-1 to V2-3, V2-8, TD-82 to TD-85) |
| OC-6 | Given a graph in the files or in the database, when it is moved to the other, then it reads back identical with all versions | FR-40, owner 2026-11-20 (item 1) |
| OC-7 | Given a stored graph, when a workflow is run or checked, then it reaches the runner as one directed graph, and the call of a code snippet in a graph goes through the toolbox with its trust, never directly | FB-02, owner 2026-11-20 (item 2) |
| OC-8 | Given a stored graph, when the owner opens it in the web app, then it is drawn from the data source, can be edited with the graph rules applied, and every edit is stored and can be played back on the graph | FR-22, owner 2026-11-20 (item 3) |
| OC-9 | Given the validation runs, when a workflow graph is found weak, then the owner improves it in the editor and the change is traceable in the edit log | owner 2026-11-20 (item 4) |
| OC-5 | Given the finished rework, when the owner uses the version, then G-V2 and G-V3 are validated on it (G-V4.VALIDATE) | VAL-006, 007, 009, 012, 013 |

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
To be written in Explore. Every FR and NFR of the top-level spec needs a row (in or out, with a reason) before Plan. Proposed from the leftovers:

| Item | In/Out | Reason |
|---|---|---|
| FR-6, FR-7 (graph path: trust, lifecycle, budgets, stop) | proposed in | TD-86, TD-87 |
| FR-34, FR-35, FR-46 (Skill run view, chat) | proposed in, partly | open items V3-6, F-04, TD-82 to TD-85 |
| NFR-3 (trust boundaries) | proposed in | V2-6, THR-011, `TB-exchange` |
| everything else | open | decide in Explore |

## Parts
To be written in Plan.

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | none yet |

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
