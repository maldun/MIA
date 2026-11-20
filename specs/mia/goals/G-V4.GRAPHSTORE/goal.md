# Goal G-V4.GRAPHSTORE – One stored form for workflow and context graphs

Proposed 2026-11-19 by the owner (maldun) in the design review of the graph storage: "unify it; especially context graphs should move into the database in the long run".

- Kind: subgoal
- Parent: G-V4
- Statement: Every workflow graph and every context graph has one stored truth, in the files or in the database, and the library, the runner and the snapshots all use it (the record form is the chosen means, a decision for the high-level spec).
- Exit criterion: OC-1 to OC-3 below, checked by tests still to be written in Plan (no ids yet)
- Supervision: supervised
- Accepted by: pending (the owner records the agreement in the table below)
- Line of work: goal/v4.graphstore
- Subgoals: –
- Status: Agreed

## Where we are (checked in the code on 2026-11-19)
- **Two forms of a graph exist in the same Storage backend (files or PostgreSQL, one generic `records` table there).** Document form: tables `workflows` and `context_graphs`, one `{"nodes", "edges"}` document per version; `WorkflowLibrary` (IF-203) reads and writes it. Record form (IF-301 v2, FR-40): tables `graph_nodes`, `graph_edges`, `graphs` and, since A-98, `context_nodes` and `context_edges`; a `graphs` header pins the version of every node and edge; `graph_model.py` and `graph_run.py` (converted skills) use it.
- `to_document` / `from_document` convert between the forms; a graph with a master node is `not_representable` in the document form.
- No migration and no synchronisation between the two forms was found; the two code paths look separate (not yet traced end to end).
- The snapshots (G-V2.SNAPSHOT) store the current version of items of the kinds `workflows` and `context_graphs` through the library, so they depend on what a graph version means.

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a workflow graph or a context graph, when it is saved, read, changed and listed, then there is one stored truth for it, with every edit a new version and no version deleted | FR-40, owner 2026-11-19 |
| OC-2 | Given the graphs stored today, when they are moved to the new form, then each reads back as before (same nodes, edges and versions as far as the old form could hold them) and the owner can compare old and new before anything old is removed | OC-6 of G-V4 (FR-40) |
| OC-3 | Given a snapshot taken before and one after the change, when the owner restores either, then the graphs are as they were at that snapshot | OC-10 of G-V4 (FR-47) |
| OC-4 | Given a live store and a copy used for daily running, when the owner syncs them (on command, at start and at an orderly stop), then the copy equals the live store, and nothing that exists only on the copy is lost | OC-6 of G-V4 (FR-40, NFR-8) |

## Added 2026-11-20 (D-360)
Files and database must be interchangeable and graphs transferable (files serve tests): the file backend, the PostgreSQL backend and `storage_copy.py` exist, so the review checks the round trip in both directions.

## Explore result (2026-11-20, D-361)
`research.md` (facts), `spikes.md` (15 converted graphs through both backends). Decisions: the stored graph is the truth and the pipeline JSON becomes an import path; target form is the record form with the document as export; one-time migration of the existing record with a comparison report. Open for Plan: graph-scoped record IDs (spike finding S1), the effect on IF-203, the toolbox and snapshots, how run_workflow's derived document (D-112) is replaced.

## Decisions of 2026-11-20 (D-368)
Node and edge records are scoped by graph (`<graph id>/<local id>`) and the storage layer refuses an unscoped ID (amendment of A-92 / REQ-GTB-021 and its test). The converted graphs and `review` are migrated once with the new IDs. IF-104 v2 is written at G-V4 level; v1 stays until the migration is confirmed.

## Decisions of the owner (2026-11-19)
| Question | Answer |
|---|---|
| Target form | the record form; the document form `{nodes, edges}` stays at most as a view or export |
| Existing graphs | one-time migration with a round-trip check; old rows are kept until the owner confirms |
| networkx | not here; its own subgoal after this one (G-V4.GRAPHAPI) |

## Dependencies and bounds
| Item | Real or stand-in | Note |
|---|---|---|
| PostgreSQL and the file backend (IF-102) | real | both stay; the unification is above the backend |
| IF-301 v2 (record tables), IF-203 (library), IF-102 | real | a change of a contract is an amendment for the owner (CLAUDE.md: stop and report) |
| G-V2.SNAPSHOT | real | the snapshot store reads versions of graph kinds; G-V2 is closed before this starts |
| Graph app N-5 | stand-in (mock of IF-104) | it works only through the backend API; keep IF-104 stable or amend it |


## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-3.2 Graph tables, N-3.1 Storage layer | real | table definitions, copy and migration |
| N-2.3 Workflow management (library, graph model, snapshots) | real | |
| N-2.4.1 Pipeline runner (`graph_run`) | real | reads the record form already |

## Open questions (for the owner, before Plan)
1. (answered 2026-11-19: parent is the new iteration goal G-V4; G-V2 is closed separately.)
2. Goal C (FR-41, FR-42, N-6: context graph with node categories as JSON schemas, one per skill) overlaps with "context graphs into the database". Is this goal the storage half of Goal C, or does Goal C wait for it?
3. Does IF-203 (the library) keep its operations and only change what is behind them, or is it amended? Consumers: toolbox, run_workflow, graph_api, snapshot store.
4. What happens to graphs with a master node when a document view is asked for (`not_representable`)?
5. Which graphs exist in both forms today? (to be traced in Explore; the migration needs it)

## Candidate tasks (not a plan)
1. Trace and list: who reads and writes which form; which stored graphs exist in which table (read-only Explore).
2. Requirements and red tests: library on the record form, round-trip, snapshots over both.
3. Library on the record form for workflows; then for context graphs; the document form as a view.
4. Migration tool with the comparison report; run on a copy of the real data first.
5. Remove the old tables only after the owner's confirmation (own task, owner gate).

## Scope
Inside the scope of G-V4 (`../G-V4/goal.md`). Items are the existing top-level items and requirements; the new items of this subgoal's top-level spec (FR-48 and later) are listed here when Plan step 1b writes them into `requirements.md`.

| Item | In/Out | Reason |
|---|---|---|
| FR-40 | in | files and database interchangeable, one stored truth, migration (FR-57 to FR-62, FR-93 of its spec); legacy text stays (D-362) |
| FR-47 | in | snapshots read and restore stored graph versions (OC-10 of G-V4) |
| NFR-8 | in | files and database behave the same behind the storage interface (FR-58, FR-93) |
| FR-36 | partly | a skill record points at its stored graph (FR-62); the skill definition itself is unchanged |
| FR-45 | partly | the converted pipelines become an import path into stored graphs (FR-62); no new skill is converted |
| FR-30 | partly | context graphs follow the same stored form (FR-57); their content, rules and editing are G-V4.CONTEXT |
| REQ-GA-008 | in | export and seed of the library moved here from the graph app (D-367); the transfer is FR-59 and FR-93 |
| REQ-GA-006 | out | editing context graphs is G-V4.CONTEXT (D-369); only the stored form is here |
| FR-6, FR-7, FR-16, FR-37, FR-38, NFR-3 | out | the run, the rules, the run record and trust of steps are G-V4.GRAPHAPI |
| FR-21, FR-22, FR-41, FR-42, NFR-6, NFR-9 | out | the graph app, access, the builder and containers are other subgoals |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V4.GRAPHSTORE | [x] Stefan Reiterer (owner) | 2026-11-20 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | research and spikes in this folder, `top-level-spec.md` approved 2026-11-20 (D-389 to D-391) |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | the first test run, G-V5 (parked, D-386) |
