# Top-Level Specification: Graph storage (G-V4.GRAPHSTORE)

**Status:** Draft, for the owner's review
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal GRAPHSTORE of G-V4. Reviews how graphs are stored (item 1 of the owner's list). Requirement IDs are provisional (continuing after FR-56 and NFR-14 of the VIEW spec); Plan assigns them in `requirements.md`.

## 1. Context and goal
The owner wants every workflow graph and every context graph to have one stored truth that can live in the live store or in a portable set of files (files serve tests and transfer), with the same behaviour in both and no loss when a graph moves between them. A skill's workflow should be a stored graph the owner can see and change, not something rebuilt from its definition at every run.

## 2. Scope
### In scope
One stored truth per graph, the two places, moving graphs between them, graphs that belong to one graph alone, migration of what exists, skills running from stored graphs, snapshots of graphs. Requirements FR-57 to FR-62, NFR-15, NFR-16.
### Out of scope (non-goals)
Drawing and editing (G-V4.VIEW, EDIT, REPLAY); how a run executes a graph (G-V4.GRAPHAPI); the contents of context graphs and their builder (goal C).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-57: The system shall keep exactly one stored truth for every workflow graph and every context graph, with every change a new version and no version deleted.
  - Outcome: Given a graph that is saved, changed twice, read and listed, when the owner asks for it, then the newest state is returned, all three versions are listed with who stored each and when, and no version has disappeared.
- FR-58: The system shall keep graphs in the live store or in a portable set of files with the same behaviour in both.
  - Outcome: Given the same sequence of saving, changing, reading and listing graphs carried out once in the live store and once in a set of files, then every answer is the same in both, including versions, authors and refusals.
- FR-59: The system shall move graphs between the live store and a set of files in both directions without loss.
  - Outcome: Given graphs with several versions each, when the owner moves them from either place to the other, then every graph arrives with all its versions, authors and times unchanged and numbered as before; moving the same graphs again changes nothing; if one graph cannot be moved, nothing is moved and that graph is named.
- FR-60: The system shall let every step and connection belong to exactly one graph.
  - Outcome: Given two graphs that both contain a step of the same local name but different content, when the owner changes that step in one graph, then the other graph and its history are untouched, and the step's history lists only the changes made in its own graph.
- FR-61: The system shall move the graphs that exist today to the new stored form and let the owner check the result before anything old is removed.
  - Outcome: Given the graphs stored today, when the owner runs the move, then a report compares each old graph with its new one (steps, connections, versions) and shows no difference except the new names; the old graphs remain until the owner confirms.
- FR-62: The system shall run each skill from its stored workflow graph.
  - Outcome: Given a skill that has a stored workflow graph, when the owner runs the skill, then the run follows that stored graph and says which graph and version it used; given a skill that has only a pipeline definition, when the owner imports it, then a stored graph is created from it once, and importing it again does not create a second copy.
### 3.2 Non-functional requirements
- NFR-15 (Portability): A set of files made on one machine works on another.
  - Outcome: Given a set of files moved from the owner's host to a test machine, when MIA is started there on those files, then every graph is listed with the same versions and content as at the source.
- NFR-16 (Reliability of storage): A refused or interrupted save never leaves a half-stored graph.
  - Outcome: Given a save of a graph that is refused for breaking a rule or interrupted halfway, when the owner lists and reads graphs afterwards, then the graph is either entirely as before or entirely new; a refused save is not counted as a version.
### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Locked requirement texts (FR-40, NFR-8) name technology | D-362 | legacy; not amended for this goal |

### 3.4 Target environment and lifetime
The owner's host (live store) and test machines (files). Maintained product. The migration runs once, on a copy of the real data first.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; the characteristics that matter are named in the requirements above.
- Security: Stored graphs and their parts may contain text from outside; they are data and are shown or moved, never run, by this subgoal.
- Sharing: owner only; AI use disclosed. Maintained, not frozen. Path to product undecided.
- Scale and first split: a leaf inside the existing decomposition; cut from the other G-V4 subgoals as in `../G-V4/goal.md`.

## 4. Context view (technology independent)
The owner and MIA's store, as in `../G-V4.VIEW/top-level-spec.md` section 4; the flows specific to this subgoal are in the requirements. No internal parts are named here.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner moves all graphs from the live store to files, starts MIA on a test machine with those files, and sees the same graphs with the same versions; then moves them back and sees no change.
- AC-2: The owner changes a step named `write` in the research graph; the review graph's step of the same name and its history are unchanged.
- AC-3: The owner runs the migration, reads the comparison report, finds no difference, and only then confirms removal of the old graphs.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Context graphs may differ from workflow graphs (goal C overlap) | FR-57 may need a separate look | open question of the old record; decide in Plan; owner |
| A graph with a step that controls loops (none today) may not move as a plain document | FR-59, FR-62 incomplete for it | include one in the cases; owner |
| Importing a skill creates the graph once; a later change of its definition | the two may drift apart | the stored graph is the truth after import (D-361); owner confirms the rule for re-import |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| FR-57 to FR-62 | not needed | proposed by the agent, the owner confirms: the capability spike of 2026-11-20 (`spikes.md`) answered the open question; the owner confirms |

## 7. References
- Research and spike: `research.md`, `spikes.md`
- Goal record: `goal.md`; parent `../G-V4/goal.md` (OC-6, OC-7, OC-10)
- Decisions: D-361, D-368
