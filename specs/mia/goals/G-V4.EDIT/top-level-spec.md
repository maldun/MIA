# Top-Level Specification: Graph editor (G-V4.EDIT)

**Status:** Approved by the owner (maldun, 2026-11-20, D-389)
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal EDIT of G-V4. Adds editing to the graph viewer (item 3b of the owner's list). Requirement IDs are provisional (continuing after FR-56 and NFR-14 of the VIEW spec); Plan assigns them in `requirements.md`.

## 1. Context and goal
The owner wants to change a graph in the web app instead of in files: change a step or connection, be told at once when a change breaks a rule, keep the change as a new version and keep the picture as arranged. The viewer (G-V4.VIEW) is the base.

## 2. Scope
### In scope
Changing steps, connections and their fields; rule check before keeping; new versions and restoring; conflicts; keeping the arrangement of a graph; trust of changed steps. Requirements FR-68 to FR-74, FR-91, FR-92, FR-94, FR-95 (new numbers for undo, the field form, copying a step and the live store), NFR-18, NFR-19.
### Out of scope (non-goals)
Drawing and history (G-V4.VIEW); playback and comparison (G-V4.REPLAY); editing context graphs (G-V4.CONTEXT, owner 2026-11-20); the skills window and who may promote a skill (goal B).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-68: The system shall let the owner change a graph in the web app by adding, removing and changing steps and connections and their fields.
  - Outcome: Given a drawn graph, when the owner adds a step, connects it, changes a field of another step and removes a connection, then the drawn graph shows all four changes before anything is kept.
- FR-69: The system shall tell the owner at once when a change breaks a graph rule and name the rule.
  - Outcome: Given a change that would create a cycle or give a piece of data two writers, when the owner makes it, then the problem and the broken rule are shown beside the picture before the owner tries to keep the change.
- FR-70: The system shall keep a change only when the graph rules hold, and refuse it otherwise with the rule named.
  - Outcome: Given a change that breaks a rule, when the owner tries to keep it, then it is refused with the rule named and the stored graph is unchanged; a change that keeps all rules is kept.
- FR-71: The system shall keep every kept change as a new version and leave earlier versions reachable.
  - Outcome: Given a graph at version 3, when the owner keeps a change, then version 4 exists with the change, version 3 is still there as it was, and version 4 names the owner and the time.
- FR-72: The system shall not overwrite a graph that changed while the owner was editing it.
  - Outcome: Given a graph opened at version 3 that another session changes to version 4, when the owner tries to keep a change made on version 3, then nothing is overwritten and the owner is told that the graph has changed.
- FR-73: The system shall let the owner make an earlier version the current one again.
  - Outcome: Given a graph at version 5, when the owner restores version 2, then version 6 exists with the content of version 2, and versions 1 to 5 are unchanged.
- FR-74: The system shall keep where the owner placed the steps of a graph between visits, the same for everyone who opens it, without making a new version.
  - Outcome: Given a graph in which the owner has moved steps, when anyone opens it again, then the steps are where they were last left and the graph's version list is unchanged; if two accounts move the same step, the last move counts.
- FR-91: The system shall let the owner undo and redo the changes of the open editing session one by one before they are kept.
  - Outcome: Given an editing session with three changes that are not yet kept, when the owner undoes the last two and redoes one, then the drawn graph shows the first and second change only, and nothing has been kept or recorded as a version.
- FR-92: The system shall offer the known fields of each kind of step as a form with checks, and any other field as editable text.
  - Outcome: Given a step of each kind (data, processing, loop-controlling), when the owner opens it for change, then its known fields appear as labelled form fields, any further field appears as text the owner can edit, and a value that does not fit a form field is refused with the reason before it is kept.

- FR-94: The system shall let the owner copy a step into another graph as an independent copy.
  - Outcome: Given a step in one graph, when the owner copies it into another graph, then the other graph has a step with the same content and its own history from that moment, and a later change to either step does not change the other.

- FR-95: The system shall write every kept change to the live store, and make the editor read-only when the live store cannot be reached.
  - Outcome: Given MIA running on a copy of the graphs, when the owner keeps a change, then it is stored in the live store and reaches the copy at the next sync; given the live store cannot be reached, when the owner opens a graph, then it can be looked at, the editor says that changing is not possible now and why, and nothing is kept.

### 3.2 Non-functional requirements
- NFR-18 (Usability): A first change is possible without instructions.
  - Outcome: Given the owner has not used the editor before, when the owner wants to change one field of one step and keep it, then it is done in under three minutes without instructions.
- NFR-19 (Security): Only the owner changes graphs, and changed code steps lose their trust.
  - Outcome: Given any account other than the owner's, when it opens a graph, then it can look but not change or keep anything; given a trusted step whose code is changed, then it is untrusted afterwards (FR-67).
### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Access only through the existing accounts | FR-21, NFR-6 | no second way in |
| Locked FR-22 text stays as legacy | D-362 | locked requirements are not amended |

### 3.4 Target environment and lifetime
The owner's devices over the home network; the editor extends the viewer in the same app.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; the characteristics that matter are named in the requirements above.
- Security: The content of a graph may come from outside and may contain code text; the editor shows it as text (FR-54 of VIEW) and never runs it. Who may edit is an open question below. Approval by the owner.
- Sharing: owner only; AI use disclosed. Maintained, not frozen. Path to product undecided.
- Scale and first split: a leaf inside the existing decomposition; cut from the other G-V4 subgoals as in `../G-V4/goal.md`.

## 4. Context view (technology independent)
The owner and MIA's store, as in `../G-V4.VIEW/top-level-spec.md` section 4; the flows specific to this subgoal are in the requirements. No internal parts are named here.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner opens the review graph, adds a step and a connection, sees the picture update, tries a connection that would make a cycle and sees the rule named, then keeps the valid change and sees version 4.
- AC-2: Two sessions edit the same graph; the second to keep is told that the graph changed and loses nothing.
- AC-3: The owner moves steps, closes the page, opens it later and finds them where they were left.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Who may edit | NFR-19 | **decided (D-370):** only the owner; others read; CON-6 stays legacy |
| One shared arrangement per graph (owner, 2026-11-20): a move by one account changes the picture of all | surprise for other accounts | accepted by the owner; moves are kept in a record of their own (D-371), not in the edit log |
| Undo within a session | an edit mistake needs a restore | **decided (D-370):** undo and redo before keeping (FR-91); whether undone changes appear in the edit log is open for REPLAY |
| Editing by form or as text (REQ-GA-002) | FR-68, FR-92 | **decided (D-370):** a form per kind of step for known fields, text for the rest |
| The check route and the edit log need IF-104 v2 | FR-69, FR-70 | D-368, joint amendment |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| G-V4.EDIT as a whole | not needed | proposed by the agent, the owner confirms: the viewer prototype shows the look; editing is built on it; the owner may ask for a prototype of the editor |

## 7. References
- Research: `../G-V4.VIEW/research.md`
- Goal record: `goal.md`; parent `../G-V4/goal.md` (OC-8, OC-9)
- Decisions: D-363, D-366, D-367, D-368, D-369
