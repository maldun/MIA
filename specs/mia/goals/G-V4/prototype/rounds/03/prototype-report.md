# Prototype report: G-V4, round 03 (G-V4.GRAPHSTORE.CORE, MVP)

Status: Prototype (reviewable draft, no product guarantees until parts are `real`) · Location: `specs/mia/goals/G-V4/prototype/rounds/03/` · Code: worktree `../MIA-prototype-g-v4`, branch `prototype/g-v4`
Scope: the outcomes of G-V4.GRAPHSTORE.CORE (run.md) · Budget: 4 checkpoints of about an hour · Status table: `specs/mia/goals/G-V4/prototype/status.md`

## Question
Are the requirements of the CORE high-level spec (HR-001 to HR-005) sound: does one stored truth hold for **context graphs** as well as workflow graphs (FR-57), does a step belong to one graph also across the two kinds (FR-60), and is a graph never half-stored whatever the write at which a save is interrupted (NFR-16)?

## Hard requirements (top-level only)
FR-57, FR-60, NFR-16 of `specs/mia/goals/G-V4.GRAPHSTORE/top-level-spec.md`.

## What was built
- **CP13: context graphs in the graph model.** `GraphModel.save_graph` and `read_graph` now follow the `kind` of the graph (`workflow`, the default, or `context`): the member tables are chosen by the kind (`graph_nodes` and `graph_edges`, or `context_nodes` and `context_edges`), a context graph has only the rules of identity and ends (`context_problems`: a step or connection ID used twice, a connection to a missing step; no order, no kinds of steps, no stop limits), and a read context graph carries `"kind": "context"`. `step_history` follows the kind of the header. The record tables already existed (A-98); the model did not use them.
- **CP14: the same cases on PostgreSQL 16** (throw-away container): `proto_checks/cp13_check.py postgres` gives the same ten results as the files backend.
- **CP15: fault injection at every write position,** `proto_checks/cp15_check.py [files|postgres]`: a save of a workflow graph (10 writes for the first save, 4 for a change), of a context graph (6 and 2), a one-graph move (14 writes for three versions, 8 for two) and a sync that must set a differing graph aside (22 writes) are each interrupted after every write k = 1..n; nothing is sampled.

## Findings
- **FR-57 for both kinds holds** on files and on PostgreSQL: a context graph saved and changed twice gives three versions with account and time, each readable as saved, and an identical save makes no version (cp13, 10 of 10 on both backends).
- **FR-60 holds across the two kinds:** a step `step.write` in a workflow graph and in a context graph have separate histories; changing one touches no record of the other.
- **NFR-16 holds for saves, moves and syncs, with one precision.** After an interruption at any of the writes of a save, the graph is entirely as before or entirely new (10 of 10, 4 of 4, 6 of 6, 2 of 2) and a repeated save finishes it, on both backends; a refused save (cycle, two writers, unknown kind of step, context connection to a missing step) writes no record and counts no version. **A move or sync that catches a multi-version graph up writes the header versions one after the other, so an interruption between two of them leaves the copy at an earlier complete version of the live history** (all members stored, readable, not the old copy and not the final state): one of 22 positions in the sync case. The run again finishes it. The wording of NFR-16 ("entirely as before or entirely new") does not cover this; see "Proposed TLS changes".
- **The editor check route applies the workflow rules to any graph** (the eight rules include the kind of step), so a context graph cannot be edited or kept in the prototype's editor: it is read-only there. Editing context graphs is G-V4.CONTEXT; the viewer list shows a context graph with its kind, but it was not looked at in a browser in this round.
- **Orphan step versions** after an interrupted save are as expected and harmless (the owner accepted no clean-up, D-402): the repeated save pins them again when the content is equal.
- The number of writes of a save is small (10 for a graph of five steps and four connections), so trying every position is cheap; HR-005 can keep its "all k" metric.

## Assumptions and choices the prototype made
| ID | Assumption or choice | Alternatives | Evidence |
|---|---|---|---|
| ASM-4 | a context graph has the rules of identity and ends only; the workflow rules (order, kinds, writers, stop limits) do not apply to it | the same eight rules | context steps are categories (any text type), there is no run order of a context graph; D-378 leaves its content to G-V4.CONTEXT |
| ASM-5 | a save without a `kind` is a workflow graph | the kind is required | all callers so far are workflow graphs; the stored header always names the kind |
| ASM-6 | a header version written during a move or sync is one append per version | one atomic write of all versions | the files backend has no multi-record write; the interrupted state is a complete earlier version |

## Proposed TLS changes
- **NFR-16, outcome:** "…every graph is entirely as before or entirely new in both places…" does not hold for the catch-up of a graph with several new versions in a move or sync. Proposal: "…every graph is entirely as before, entirely new, or at an earlier complete version of the live store's history, never with a missing step or connection…". The owner decides; the TLS is not edited.

## Effect on the TLS
NFR-16 needs the sentence above or the move and sync must write all versions of a graph at once (not possible on files without a new mechanism). FR-57 and FR-60 stand as written for both kinds.

## Carry-over (the developer decides)
| Item (requirement, spec text, decision, code, scenario) | Where | Decision: adopt / adapt / drop / stand-in | Reason |
|---|---|---|---|
| Context graphs saved, read, listed and changed through the model, by kind (R1 update) | `graph_model.py` | adopt | Proposed by the agent, for the owner to confirm or change: closes the gap of FR-57 for both kinds; checked by `cp13_check.py` on files and PostgreSQL |
| Fault-injection checks at every write position | `proto_checks/cp15_check.py` | adapt | Proposed by the agent, for the owner to confirm or change: becomes the scenario and test requirement of HR-005; the code is reworked into the acceptance test |
| Precision of NFR-16 for move and sync | this report | adapt | Proposed by the agent, for the owner to confirm or change: TLS proposal above, then the requirement of the TRANSFER subgoal |

Decided by: –

## Prototype tests (run once here; the developer's carry-over decision above decides what happens)
| Question (requirement or top-level item) | Command (repeatable) | Result (value, unit, uncertainty, hardware, date; pass / fail / not_run) |
|---|---|---|
| FR-57, FR-60: context graphs and workflow graphs, versions, shared local names, refusals | `python proto_checks/cp13_check.py files` and `... postgres` | 10 pass on each, 2026-11-21, Fedora host, PostgreSQL 16 under podman |
| NFR-16: every write position of a save, a one-graph move and a sync, refused saves | `python proto_checks/cp15_check.py files` and `... postgres` | 9 pass on each, 2026-11-21, Fedora host, PostgreSQL 16 under podman |
