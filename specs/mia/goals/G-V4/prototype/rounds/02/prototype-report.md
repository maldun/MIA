# Prototype report: G-V4, round 02 (graph path slice, MVP)

Status: Prototype (reviewable draft, no product guarantees until parts are `real`) · Location: `specs/mia/goals/G-V4/prototype/rounds/02/` · Mock-up code: worktree `../MIA-prototype-g-v4`, branch `prototype/g-v4` · Date: started 2026-11-20
Scope: the graph path slice (run.md) · Budget: 12 checkpoints of about an hour, a stop at each subgoal breakpoint · Status table: `specs/mia/goals/G-V4/prototype/status.md`

## Question
Can the graph path (scoped storage in two places, one rule set, viewer, editor, edit log with playback) be built as one thin working slice that the owner can try, and what does it teach about the requirements?

## Hard requirements (top-level only)
The items of `../../top-level-spec.md` (the aggregate of the subgoal specs in scope).

## What was built
**CP1 (GRAPHSTORE.CORE, breakpoint ★), 2026-11-20, commit 2f9312f8.**
- Every step and connection of a graph is a record `<graph id>/<local id>`; the graph a caller sees has local IDs. The storage layer (`graph_tables.py`) refuses an unscoped ID and a header that pins a step of another graph (rule `unscoped_id`).
- `GraphModel.save_graph` checks everything the storage would refuse before the first write, writes a step only when it differs from its newest version, and writes no new graph version when nothing changed. `step_history` lists the versions of one step as the headers of that graph pinned them.
- Demonstration: `python proto_checks/cp1_demo.py` (a short story) and `python proto_checks/cp1_check.py files|postgres` (10 checks, all pass on both backends).
- Plan checkpoints CP2 to CP12 follow in `run.md`.

**CP2 (GRAPHSTORE.TRANSFER, first part), 2026-11-20, commit 70e9c2cb.**
- `graph_store_move.py` moves the whole store (steps, connections, headers) between any two backends: every graph is checked first (headers, pinned step versions, scoped IDs) and compared with the target; one graph that cannot be moved, or that has a different history in the target, refuses the whole move with the graphs named and writes nothing. Steps are written before headers, so a graph appears only when complete; nothing is renumbered; authors and times are kept; a second move changes nothing.
- Demonstration: `python proto_checks/cp2_check.py` (9 checks, all pass, PostgreSQL 16 under podman) and the command line `python graph_store_move.py files:<folder> postgres:<url>`.


**CP5 (VIEW, first part), 2026-11-20, commit 85efcc21.** (Built before CP3 and CP4, D-399.)
- `graph_proto_app.py`: a Flask backend over any store (`files:<dir>` or `postgres:<url>`) using the existing accounts and session cookie (`accounts_api`); only the login and the page are open, every graph route needs a session (NFR-12). Routes: `GET /api/v2/graphs` (the list), `GET /api/v2/graphs/<id>[?version=n]` (a graph with local IDs, version, author, time and what cannot be drawn), `GET /api/v2/graphs/<id>/versions`.
- `graph_app_v2/`: the page: login, the list of graphs with a name filter (id, description, kind), the drawing (round 01 look), problems named beside the picture and a connection to a missing step drawn dashed to a marked "missing step".
- Demonstration: `python graph_proto_app.py --store files:/tmp/gs/v --user owner:secret --port 8801` and open http://127.0.0.1:8801/ (sample store: `python proto_checks/make_sample_store.py /tmp/gs/v --broken`); checks: `python proto_checks/cp5_check.py` (19 pass, files and database) and `node --test proto_checks/cp5.test.mjs` (4 pass).

## Findings
- The 15 converted graphs give 154 step records for 107 distinct local names: with scoped IDs the 13 shared names (4 with different content) no longer share a history.
- The new rule breaks existing tests that use plain IDs: `tests/test_graph_record_checks.py` (34 failures), `tests/acceptance/contract/test_if_301_v2_graph_tables.py` (28) and `tests/acceptance/test_graph_records.py` (14 errors), all with `unscoped_id`; `test_graph_model.py`, `test_graph_run.py`, `test_graph_tables.py` still pass. The amendment of A-92 / REQ-GTB-021 therefore has to rewrite those protected tests.
- A crash between the writes of the steps and of the header can still leave unused step versions; they are not part of any graph and `step_history` ignores them; a second save pins them again if the content is the same.
- The move reuses `copy_records` of the existing copy operation and adds the graph-level check; 16 graphs make 341 records.
- The page itself was not looked at in a browser by the agent (none in the session); the HTTP side was run for real with curl (login, 401 without it, list, the broken graph's problem).
- Context graphs are not stored anywhere yet (the context tables exist, no data, no `GraphModel` for them), so the list shows workflow graphs only; FR-48 asks for both kinds.
- Not examined: context graphs, a graph with a loop-controlling step (none among the 15), the `review` workflow (document form, migration is out of this run).

## Assumptions and choices the prototype made
| ID | Assumption or choice | Alternatives | Evidence |
|---|---|---|---|
| ASM-1 | the separator is the first `/`; a local ID may contain further slashes, a graph ID must not | a different separator such as `#` | storage already quotes IDs with a slash (`storage_files.py`) |
| ASM-2 | a step is written as a new version only when its content differs | write every member at every save | `cp1_check.py`: unchanged save = no version |

## Prototype tests (run once here)
| Question (requirement or top-level item) | Command (repeatable) | Result (value, unit, uncertainty, hardware, date; pass / fail / not_run) |
|---|---|---|
| FR-48, FR-49, NFR-12: login, list from files and database, graph and versions, problems named | `python proto_checks/cp5_check.py`, `node --test proto_checks/cp5.test.mjs` | 19 and 4 pass, 2026-11-20, Fedora host, PostgreSQL 16 under podman |
| FR-58, FR-59: the same answers in files and database; the whole store moves both ways, repeatably, all or nothing | `python proto_checks/cp2_check.py` | 9 of 9 pass, 2026-11-20, Fedora host, PostgreSQL 16 under podman |
| FR-57, FR-60, NFR-16: scoped storage, versions, refused and interrupted saves | `python proto_checks/cp1_check.py files` and `postgres` | 10 of 10 pass on each backend, 2026-11-20, Fedora host, PostgreSQL 16 under podman |

## Carry-over (the developer decides)
| Item (requirement, spec text, decision, code, scenario) | Where | Decision: adopt / adapt / drop / stand-in | Reason |
|---|---|---|---|

Decided by: –

## Proposed TLS changes
- –

## Effect on the TLS
–
