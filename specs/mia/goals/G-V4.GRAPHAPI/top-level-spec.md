# Top-Level Specification: Graph rules and the run of a stored graph (G-V4.GRAPHAPI)

**Status:** Draft, for the owner's review
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal GRAPHAPI of G-V4. Reviews how a graph is checked and run (item 2 of the owner's list). Requirement IDs are provisional (continuing after FR-56 and NFR-14 of the VIEW spec); Plan assigns them in `requirements.md`.

## 1. Context and goal
The owner wants a stored graph to be checked and run as the same graph they see and edit: one set of graph rules everywhere, one way a graph reaches the run, and the code that may sit in a graph run only with the trust the owner gave it. Skills must give the same results as before the rework.

## 2. Scope
### In scope
The rules, the order of steps, the run of a stored graph, code inside a graph, equivalence with today's skills. Requirements FR-63 to FR-67, NFR-17.
### Out of scope (non-goals)
Storing graphs (G-V4.GRAPHSTORE); drawing and editing (VIEW, EDIT); live trust, lifecycle, budgets and stop of a running skill (G-V4.LEFTOVER, planned together with this subgoal).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-63: The system shall apply one set of eight graph rules to a graph wherever it is checked, in the same fixed order, and name every broken rule.
  - Outcome: Given a graph that breaks two rules, when it is checked while saving, while editing and before a run, then the same broken rules are listed in the same order every time, each with its steps or connections; the eight rules and their order are written in one place: ids, kind of step, connections to missing steps and duplicate connections, no two data steps adjacent, one writer per piece of data, session setting and stop limit, no cycle.
- FR-64: The system shall refuse to run a graph that breaks the rules or has a step input that nobody supplies, and name the broken part before any step has run.
  - Outcome: Given a stored graph with a cycle, two writers of one piece of data, a connection to a missing step, two identical connections, or a step input that has no writer, no start value in the graph and no value given with the run, when the owner runs it, then no step runs, the run ends as refused and names each broken step, connection or input.
- FR-65: The system shall run the steps of a stored graph one after the other in a fixed order in which every step runs after the steps it reads from.
  - Outcome: Given a stored graph, when it runs, then every step starts only after all the steps that supply its inputs have finished, no two steps run at the same time, and the same graph with the same inputs runs the same steps in the same order.
- FR-66: The system shall run a piece of code that is stored in a graph only through a tool the owner has trusted for that step, never by itself.
  - Outcome: Given a graph with a code step, when the owner has not trusted that step with its current code, then the run is refused before any step runs and names the step; when the owner has trusted the tool and that step with its current code, then it runs in the contained space of its tool and its output is treated as data like any other.
- FR-67: The system shall drop a step back to untrusted when its content changes.
  - Outcome: Given a trusted step whose code, tool or settings are changed, when the owner next runs the graph, then the step is untrusted until the owner trusts it again, and the run record names the version of the step that ran; a change of the step's position or of a reason text does not drop its trust.
### 3.2 Non-functional requirements
- NFR-17 (Compatibility): Skills give the same results after the rework as before.
  - Outcome: Given every skill that was converted at the end of G-V2 and its cases, when it is run on its stored graph, then it gives the same results on those cases as before the rework, decided on the dev suites against the old-runner baselines with the agreed statistical rule and the pinned model; the same check is repeated on holdout cases as soon as the owner has labelled them (G-V4.LEFTOVER).
### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Locked texts of FR-7, FR-37 name technology | D-362 | legacy |
| Trust is set only by the owner | FR-38 (approved) | an imported or changed step must not run on its own authority |

### 3.4 Target environment and lifetime
The owner's host with the pinned local models; graphs have tens of steps (largest today 54).

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; the characteristics that matter are named in the requirements above.
- Security: Code text in a graph may come from outside (imports) or a model: it is untrusted data until the owner trusts the tool and step; candidate threat THR-013 (see `research.md`). Approval by the owner. No new external effects.
- Sharing: owner only; AI use disclosed. Maintained, not frozen. Path to product undecided.
- Scale and first split: a leaf inside the existing decomposition; cut from the other G-V4 subgoals as in `../G-V4/goal.md`.

## 4. Context view (technology independent)
The owner and MIA's store, as in `../G-V4.VIEW/top-level-spec.md` section 4; the flows specific to this subgoal are in the requirements. No internal parts are named here.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner runs a converted skill; the run record names the stored graph and version; its result on the skill's cases equals the result before the rework.
- AC-2: A graph with two writers of one piece of data is run; nothing runs and the two writers are named.
- AC-3: The owner edits the code of a trusted code step and runs the graph; it is refused as untrusted until the owner trusts it again.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Two sets of graph rules exist today with different names and orders | FR-63 needs one merged set | **decided (D-375):** eight rules, local facts first and the cycle last, all broken rules listed; names and tests in Plan |
| Whether the run applies the rules itself (it does not today) | FR-64 | **decided (D-375):** yes, before any step runs, plus the missing-input check |
| Code steps need a threat entry and red-team cases | FR-66, FR-67 | write THR-013 in Plan with the owner; trust per step and its current content (D-375) |
| Equivalence of every skill needs the model and the suites | NFR-17 | **decided (D-375):** dev suites now, holdout when labelled; the statistical rule is fixed in Plan |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| FR-63 to FR-67, NFR-17 | not needed | proposed by the agent, the owner confirms: the capability spike of 2026-11-20 (`spikes.md`) covered the data side; the owner confirms |

## 7. References
- Research and spike: `research.md`, `spikes.md`
- Goal record: `goal.md`; parent `../G-V4/goal.md` (OC-7)
- Decisions: D-360, D-362, D-375
