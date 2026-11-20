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

## Findings
- The 15 converted graphs give 154 step records for 107 distinct local names: with scoped IDs the 13 shared names (4 with different content) no longer share a history.
- The new rule breaks existing tests that use plain IDs: `tests/test_graph_record_checks.py` (34 failures), `tests/acceptance/contract/test_if_301_v2_graph_tables.py` (28) and `tests/acceptance/test_graph_records.py` (14 errors), all with `unscoped_id`; `test_graph_model.py`, `test_graph_run.py`, `test_graph_tables.py` still pass. The amendment of A-92 / REQ-GTB-021 therefore has to rewrite those protected tests.
- A crash between the writes of the steps and of the header can still leave unused step versions; they are not part of any graph and `step_history` ignores them; a second save pins them again if the content is the same.
- Not examined: context graphs, a graph with a loop-controlling step (none among the 15), the `review` workflow (document form, migration is out of this run).

## Assumptions and choices the prototype made
| ID | Assumption or choice | Alternatives | Evidence |
|---|---|---|---|
| ASM-1 | the separator is the first `/`; a local ID may contain further slashes, a graph ID must not | a different separator such as `#` | storage already quotes IDs with a slash (`storage_files.py`) |
| ASM-2 | a step is written as a new version only when its content differs | write every member at every save | `cp1_check.py`: unchanged save = no version |

## Prototype tests (run once here)
| Question (requirement or top-level item) | Command (repeatable) | Result (value, unit, uncertainty, hardware, date; pass / fail / not_run) |
|---|---|---|
| FR-57, FR-60, NFR-16: scoped storage, versions, refused and interrupted saves | `python proto_checks/cp1_check.py files` and `postgres` | 10 of 10 pass on each backend, 2026-11-20, Fedora host, PostgreSQL 16 under podman |

## Carry-over (the developer decides)
| Item (requirement, spec text, decision, code, scenario) | Where | Decision: adopt / adapt / drop / stand-in | Reason |
|---|---|---|---|

Decided by: –

## Proposed TLS changes
- –

## Effect on the TLS
–
