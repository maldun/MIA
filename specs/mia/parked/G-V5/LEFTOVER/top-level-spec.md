# Top-Level Specification: Leftovers of G-V2, G-V3 and G-V4 (G-V5.LEFTOVER)

**Status:** Draft, for the owner's review
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal LEFTOVER of G-V5. Settles what the earlier goals (G-V2, G-V3 and G-V4) left open; moved from G-V4 to G-V5 by the owner (D-385). Requirement IDs are provisional (continuing after the other G-V4 specs); Plan assigns them in `requirements.md`.

## 1. Context and goal
G-V2 and G-V3 were closed with accepted deviations (D-358, D-359). The owner wants the converted skills to follow the live settings (trust, lifecycle, budgets, stop), improved skills to be decided on cases the owner labelled, harmful imported steps to be refused with proof, and the records to be consistent.

## 2. Scope
### In scope
The live settings on the graph path (TD-86, TD-87), decisions on labelled holdout cases (TD-88, TD-89, TD-90), the refusal of harmful imported steps (V2-6, THR-011), consistency of the records (V2-1 to V2-3, V2-8, TD-82 to TD-85), the open items V3-6 and F-04. Requirements FR-82 to FR-85, NFR-21.
### Out of scope (non-goals)
New skills or new conversions; the graph rework itself (GRAPHSTORE, GRAPHAPI); validation sessions (G-V5.VALIDATE).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-82: The system shall run a skill with the owner's current trust and lifecycle settings and end the run when the owner stops it or a budget is reached.
  - Outcome: Given a skill that is running, when the owner marks a step as not trusted before it starts, then that step does not run and the run says so; when the owner presses stop, then the run ends and says it was stopped; when a budget is reached, then the run ends as the old runner ended and says which budget.
- FR-83: The system shall decide whether a changed skill is better only on cases the owner has labelled and the change has never seen.
  - Outcome: Given a changed skill and a set of cases labelled by the owner and never used for the change, when the skill is measured, then the verdict rests on those cases alone and the cases, labels and the rule for deciding are unchanged by anyone but the owner.
- FR-84: The system shall refuse an imported step that would do harm and show a recorded case that proves it.
  - Outcome: Given an imported step that tries to read outside its allowed space or send data out, when it is offered to MIA, then it is refused, and a recorded case shows the refusal and can be repeated.
- FR-85: The system shall show the conversion and run checks of the converted skills on the pinned model in the same way for the old and the new runner.
  - Outcome: Given a converted skill, when the owner compares the old and the new runner on the same cases, then both results and their time are shown side by side, and the difference in time is stated.
### 3.2 Non-functional requirements
- NFR-21 (Consistency of records): Requirements, tests and records of G-V2 and G-V3 agree.
  - Outcome: Given the requirements, tests and records of G-V2, G-V3 and G-V4, when the owner runs the consistency checks, then no requirement is left as a draft without a decision, no scope wording is stale and no check is missing from its table; every open deferral has a decision or a new date, including those that G-V4 leaves open.
### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Holdout suites are labelled only by the owner; agents never label or run them | CLAUDE.md, agent-app rules | the decision must not be influenced by the agent |
| Pinned model and quantization stay as they are | eval-spec model pins | a change needs the owner |

### 3.4 Target environment and lifetime
The owner's host with the pinned local models.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; the characteristics that matter are named in the requirements above.
- Security: Imported steps are untrusted (THR-011); the refusal case is a red-team case written with the owner. Agents never label or open holdout cases.
- Sharing: owner only; AI use disclosed. Maintained, not frozen. Path to product undecided.
- Scale and first split: a leaf inside the existing decomposition; cut from the other G-V4 subgoals as in `../goal.md`.

## 4. Context view (technology independent)
The owner and MIA's store, as in `../../../goals/G-V4.VIEW/top-level-spec.md` section 4; the flows specific to this subgoal are in the requirements. No internal parts are named here.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner stops a running lookup; it ends as stopped. The owner marks a step untrusted before a run; the step does not run and is named.
- AC-2: An improved skill is measured on the owner's labelled cases and the verdict is shown with the rule.
- AC-3: An imported step that tries to send data out is refused; the red-team case shows it.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Holdout suites need the owner's labelling time | FR-83 cannot be decided without them | owner schedules the labelling |
| FR-85 may duplicate G-V5.VALIDATE (V2-4) | scope | the owner decides whether the timing comparison stays here |
| Several items (TD-82 to TD-85, F-04) are small and technical | readability of the goal | list them as tasks, not requirements |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| FR-82 to FR-85 | not needed | proposed by the agent, the owner confirms: the items are known from the verification reports; no feasibility doubt |

## 7. References
- Sources: `../../../goals/G-V2/remainder-for-next-goal.md`, `../../../goals/G-V3/verification-report.md`, `deferred.md`
- Goal record: `goal.md`; parent `../goal.md` (OC-1 to OC-4)
