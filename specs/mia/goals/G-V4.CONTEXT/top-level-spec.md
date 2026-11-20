# Top-Level Specification: Context graph editing (G-V4.CONTEXT)

**Status:** Reviewed by the owner (D-379); approval box open
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal CONTEXT of G-V4 (decided by the owner 2026-11-20, D-369). Requirement IDs provisional (FR-75 moved from G-V4.EDIT, FR-97 new); Plan assigns it in `requirements.md`.

## 1. Context and goal
A context graph is the knowledge a skill reads when it runs. The owner wants to change it in the web app like a workflow graph. It follows the viewer, the editor and the stored form of graphs.

## 2. Scope
### In scope
Changing stored context graphs with the editor's checks, versions and restore (FR-75), and showing the context graph of a finished run read-only (FR-97, new number).
### Out of scope (non-goals)
Building context graphs from documents and runs, categories as schemas, proposals of items (goal C, FR-41, FR-42, N-6); everything the editor does for workflow graphs (G-V4.EDIT).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-75: The system shall let the owner change a stored context graph, with the structural rules of workflow graphs and the rules for categories and budgets. *(Priority: Should.)*
  - Outcome: Given a stored context graph, when the owner changes and keeps it, then the same versions and restore as for a workflow graph apply; a change that breaks a structural rule, gives a step an unknown category or a budget that is not a positive number is refused with the rule named, and the problem is shown while editing; the list of these rules is written in one place together with the workflow rules.
- FR-97: The system shall show the context graph of a finished run, read-only, in the viewer.
  - Outcome: Given a finished run, when the owner chooses to see its context graph, then the graph rebuilt from the events of that run is drawn with the viewer's picture and settings, each item can be traced to the event that made it, a problem in the log is named instead of being turned into a wrong graph, nothing is stored and nothing can be changed.

### 3.2 Non-functional requirements
None of its own: usability and security follow NFR-18 and NFR-19 of G-V4.EDIT, and access follows NFR-12 of G-V4.VIEW.
### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Access only through the existing accounts | FR-21, NFR-6 | no second way in |

### 3.4 Target environment and lifetime
The owner's devices over the home network; maintained product.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; usability and security as in G-V4.EDIT.
- Security: the content of a context graph may come from documents and web text; it is untrusted data, shown as text and never run.
- Sharing: owner only; AI use disclosed. Maintained. Path to product undecided.
- Scale and first split: a small leaf after EDIT; cut from EDIT by the owner on 2026-11-20.

## 4. Context view (technology independent)
As in `../G-V4.VIEW/top-level-spec.md` section 4.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner opens the context graph of the lookup skill, changes one entry, sees a rule problem named when it breaks a rule, keeps a valid change as a new version and restores the earlier version.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Context graphs are not yet in the stored form of workflow graphs | FR-75 cannot be built first | depends on G-V4.GRAPHSTORE; owner |
| Whether goal C (builder, schemas) joins this subgoal | scope | **decided (D-379):** no; the builder, schema categories and proposals wait for their own goal |
| Whether viewing and storing context graphs stay in VIEW (FR-48) and GRAPHSTORE (FR-57) | cuts | **decided (D-374, D-378):** yes; this subgoal edits stored context graphs and shows a run's graph |
| A run's context graph is rebuilt from its events and never stored | FR-97 needs a read route and the log must be readable | **decided (D-379):** shown read-only here (answers Q-5 of N-5) |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| FR-75 | not needed | proposed by the agent, the owner confirms: the editor of G-V4.EDIT is reused |

## 7. References
- `../G-V4.EDIT/top-level-spec.md`, `../G-V4.VIEW/research.md`; decisions D-367, D-369
