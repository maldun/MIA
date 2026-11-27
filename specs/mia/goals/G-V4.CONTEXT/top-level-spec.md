# Top-Level Specification: Context graph editing (G-V4.CONTEXT)

**Status:** Approved by the owner (maldun, 2026-11-20, D-390); scope note by the owner 2026-11-21 (D-403 to D-405): the editor's functions are EDIT's, this subgoal brings the description of the context kind, its rule set and the run view; the text of FR-75 and FR-97 is unchanged; amendment by the owner 2026-11-28 (D-638, applying D-429 and D-632 to D-635): FR-97 moved to a later slice of G-V4.VIEW, the categories are per graph, the rule set is decided; the text of FR-75 is unchanged
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal CONTEXT of G-V4 (decided by the owner 2026-11-20, D-369). Requirement IDs provisional (FR-75 moved from G-V4.EDIT; FR-97, new here, moved to G-V4.VIEW by D-635); Plan assigns it in `requirements.md`.

## 1. Context and goal
A context graph is the knowledge a skill reads when it runs. The owner wants to change it in the web app like a workflow graph. It follows the viewer, the editor and the stored form of graphs.

## 2. Scope
### In scope
Changing stored context graphs (FR-75), the first slice of the builder (D-429 (2)): the description of the context kind for the general editor of G-V4.EDIT; each context graph's own categories (types of nodes with their fields), relations and budget, kept with the graph and re-used by copying from another graph (D-632); its rule set (D-634); manual entry of items with a source note; with the editor's versions and restore.
### Out of scope (non-goals)
Building context graphs from documents and runs, proposals of categories and items (goal C, FR-41, FR-42, N-6: the later slices of G-V4.BUILDER); a shared catalogue of categories (D-632); showing the context graph of a finished run (FR-97, a later slice of G-V4.VIEW, D-635); everything the editor does for workflow graphs (G-V4.EDIT).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-75: The system shall let the owner change a stored context graph, with the structural rules of workflow graphs and the rules for categories and budgets. *(Priority: Should.)*
  - Outcome: Given a stored context graph, when the owner changes and keeps it, then the same versions and restore as for a workflow graph apply; a change that breaks a structural rule, gives a step an unknown category or a budget that is not a positive number is refused with the rule named, and the problem is shown while editing; the list of these rules is written in one place together with the workflow rules.
FR-97 (a finished run's context graph) moved to `../G-V4.VIEW/top-level-spec.md` as a later slice, text unchanged (D-429 (2), D-635).

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
| Which of the workflow rules are structural for a context graph (FR-75: "the structural rules of workflow graphs"): identity, ends and duplicates are, order and the data/processing alternation probably are not | the rule set of the context kind | **decided (D-634):** identity, ends and duplicates of the workflow rules; plus category and fields, budget, source note and typed relations; no order, adjacency, single writer, stop limit or cycle |
| A run's context graph is rebuilt from its events and never stored | FR-97 needs a read route and the log must be readable | **decided (D-379), moved (D-635):** shown read-only in a later slice of G-V4.VIEW |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| FR-75 | not needed | proposed by the agent, the owner confirms: the editor of G-V4.EDIT is reused |

## 7. References
- `../G-V4.EDIT/top-level-spec.md`, `../G-V4.VIEW/research.md`; decisions D-367, D-369
