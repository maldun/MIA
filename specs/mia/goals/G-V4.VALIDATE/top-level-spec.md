# Top-Level Specification: Validation of G-V2 and G-V3 and improvement of the graphs (G-V4.VALIDATE)

**Status:** Draft, for the owner's review
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal VALIDATE of G-V4. Validates the earlier goals on the reworked version and improves workflow graphs with the editor. Requirement IDs are provisional (continuing after FR-56 and NFR-14 of the VIEW spec); Plan assigns them in `requirements.md`.

## 1. Context and goal
The validation of G-V2 and G-V3 was deferred until the rework is done (D-359). The owner wants to judge the reworked version in real use, with every finding triaged, and to use the graph editor to improve workflow graphs that the validation runs show to be weak.

## 2. Scope
### In scope
The owner's judgements VAL-006, VAL-007, VAL-009, VAL-012 and VAL-013 on the reworked version, the strip height of REQ-CLV-041, the open items (V2-4, V3-6, F-04), and the editor-driven improvement of graphs. Requirements FR-86 to FR-90.
### Out of scope (non-goals)
The rework itself and its checks (the other subgoals); new validation of G-V1 material (VAL-001, 003, 004, 005) unless the owner adds it.

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-86: The system shall let the owner judge in real use whether the converted skills and the snapshots are as good as before.
  - Outcome: Given a week of use of the converted skills and a snapshot taken, changed and restored, when the owner reviews it, then each skill that seemed worse is a feedback item, and the restored snapshot shows the former state (VAL-007).
- FR-87: The system shall let the owner tell what a skill is made of from its record and understand why a rule-breaking description is refused.
  - Outcome: Given a skill record with its workflow and context graph, when the owner describes it in their own words and is shown three rule-breaking descriptions, then the owner names the command, the steps and the knowledge, and states the reason for each refusal (VAL-009).
- FR-88: The system shall let the owner follow a skill run in the Skill run view without reading the chat.
  - Outcome: Given real runs of lookup, search and review, when the owner uses the Skill run view, then the owner can say at any time what the run is doing, and the compact strip is judged readable and small enough (VAL-012; settles the strip height of REQ-CLV-041).
- FR-89: The system shall let the owner check that summaries and status messages are faithful and in persona in daily use.
  - Outcome: Given 20 sampled summaries and status messages from a week of real runs, when the owner marks each as faithful or not and in persona or not, then the rates are known and compared with the claim of the evaluation (VAL-013).
- FR-90: The system shall let the owner improve a weak workflow graph in the graph editor and show what was changed and why.
  - Outcome: Given a workflow that a validation run showed to be weak, when the owner changes its graph in the editor, then the change, its reason and its effect on the next validation run are shown together.
### 3.2 Non-functional requirements
- NFR-22 (Efficiency in daily use): MIA is fast and light enough in daily use.
  - Outcome: Given a week of daily use, when the owner looks at the measured first-text time, frame rate on the phones in use, model calls and the estimate against measured time, then the owner judges them acceptable or names what is too slow (VAL-006).
### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Run logs stay on the host | CLAUDE.md (confidential data never leaves the host) | privacy of run content |
| The validation runs on the frozen post-rework version | D-359 | results must refer to one version |

### 3.4 Target environment and lifetime
The owner's host and the owner's phones, one week of use; a deployment of the reworked version is the starting point.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; the characteristics that matter are named in the requirements above.
- Security: The sessions read run logs; they stay local. Consent of any user besides the owner is open (validation plan).
- Sharing: owner only; AI use disclosed. Maintained, not frozen. Path to product undecided.
- Scale and first split: a leaf inside the existing decomposition; cut from the other G-V4 subgoals as in `../G-V4/goal.md`.

## 4. Context view (technology independent)
The owner and MIA's store, as in `../G-V4.VIEW/top-level-spec.md` section 4; the flows specific to this subgoal are in the requirements. No internal parts are named here.

## 5. Acceptance scenarios (end to end)
- AC-1: After a week the owner has a validation report with a rating for each of VAL-006, 007, 009, 012 and 013 and a triage of every finding.
- AC-2: The owner finds a weak lookup graph, improves it in the editor with reasons, runs the next validation and sees the effect.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| The rework may change what the validation criteria observe | the plan of validation | the first task of G-V4.VALIDATE reviews each criterion (keep, change, drop, add) |
| Retention of run logs and consent of other users | privacy | owner decides |
| Whether VAL-001, 003, 004, 005 join | scope | owner decides |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| G-V4.VALIDATE as a whole | not needed | validation by use is itself the test; no feasibility doubt |

## 7. References
- Sources: `test-spec.md` (VAL rows), `validation-plan-v0.2.1.md`, `goals/G-V4.VALIDATE/goal.md`
- Parent `../G-V4/goal.md` (OC-5, OC-9)
