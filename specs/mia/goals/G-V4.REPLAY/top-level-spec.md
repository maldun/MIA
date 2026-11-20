# Top-Level Specification: Edit log and playback (G-V4.REPLAY)

**Status:** Draft, for the owner's review
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal REPLAY of G-V4. Records and plays back the changes made in the editor (item 3c of the owner's list). Requirement IDs are provisional (continuing after FR-56 and NFR-14 of the VIEW spec); Plan assigns them in `requirements.md`.

## 1. Context and goal
The owner wants to see what was changed in a graph, step by step, who changed it, when and why, to play the changes back on the starting version, and to compare two versions. This also lets the owner follow how a workflow graph was improved after the validation runs.

## 2. Scope
### In scope
The record of single changes, playback, the history of changes with a reason, comparison of two versions, the record's protection and its transfer. Requirements FR-76 to FR-81, NFR-20.
### Out of scope (non-goals)
Showing versions and their history list (G-V4.VIEW); making changes (G-V4.EDIT); the arrangement of steps and its moves (G-V4.EDIT, FR-74).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-76: The system shall record every change made in the editor as a separate entry with who made it, when, what it did and what version it started from.
  - Outcome: Given an editing session with five changes that keeps one version, when the owner looks at that version, then five entries are listed, each with account, time, what it changed with the value before and after, and the version it started from. Moving a step is not among these entries (it has a record of its own, FR-74 of G-V4.EDIT).
- FR-77: The system shall let the owner give a reason for a change and show it.
  - Outcome: Given a change with a reason, when the owner looks at its entry, then the reason is shown with it; a change without a reason is shown as such.
- FR-78: The system shall play recorded changes back on a version and give the saved version again.
  - Outcome: Given a saved version and its recorded changes, when the owner plays them back on the starting version, then the result is identical to the saved version; the owner steps forward and back one change at a time, the picture follows and the changed step is marked.
- FR-79: The system shall show what differs between two versions of a graph.
  - Outcome: Given two versions of a graph, when the owner compares them, then the steps and connections added, removed and changed are listed with their old and new content, and the drawing marks each of them differently.
- FR-80: The system shall not allow recorded changes to be altered or deleted.
  - Outcome: Given recorded changes, when anyone tries to change or delete one, then it is refused and the record is unchanged.
- FR-81: The system shall keep the recorded changes with the graph when graphs move between places.
  - Outcome: Given a graph with recorded changes moved between the live store and a set of files, when the owner looks at it at the destination, then every entry arrives unchanged and playback gives the same result.
### 3.2 Non-functional requirements
- NFR-20 (Traceability): Every kept version can be explained.
  - Outcome: Given any version of a graph that was changed in the editor, when the owner asks how it came about, then the entries that made it are shown from the starting version to the saved one without a gap; a version made before the record existed is listed as made before the record, and the comparison of FR-79 still shows what differs.
### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| The record of changes belongs to the graph and moves with it | FR-59 (GRAPHSTORE) | the owner expects transfers without loss |

### 3.4 Target environment and lifetime
The owner's host; the log grows with use and lives as long as the graph.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; the characteristics that matter are named in the requirements above.
- Security: The record of changes is evidence: it is append-only and names the account. Its content may include text typed by the owner; it is shown as text only.
- Sharing: owner only; AI use disclosed. Maintained, not frozen. Path to product undecided.
- Scale and first split: a leaf inside the existing decomposition; cut from the other G-V4 subgoals as in `../G-V4/goal.md`.

## 4. Context view (technology independent)
The owner and MIA's store, as in `../G-V4.VIEW/top-level-spec.md` section 4; the flows specific to this subgoal are in the requirements. No internal parts are named here.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner improves a workflow graph after a validation run in three changes with reasons, then opens its history and sees the three entries in order with reasons, plays them back, and ends at the saved version.
- AC-2: The owner compares version 3 and 6 and sees the added step, the removed connection and the changed field.
- AC-3: The owner tries to delete an entry and is refused.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Whether undone changes (FR-91 of EDIT) appear in the edit log | log readability | **decided (D-371):** no; only changes that are part of a kept version |
| How long entries are kept | storage growth | **decided (D-371):** everything is kept for as long as the graph exists; the owner revisits if it grows |
| Moves of steps | log readability | **decided (D-371):** moves are kept in a record of their own, not among the changes of a version; replay of moves is not offered |
| Relation of the record to the list of versions of VIEW | duplicated facts | VIEW lists versions, REPLAY explains how each came about (D-366) |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| G-V4.REPLAY as a whole | not needed | proposed by the agent, the owner confirms: the owner may ask for a small prototype of the record and playback |

## 7. References
- Research: `../G-V4.VIEW/research.md`
- Goal record: `goal.md`; parent `../G-V4/goal.md` (OC-8, OC-9)
- Decisions: D-363, D-365, D-366, D-371
