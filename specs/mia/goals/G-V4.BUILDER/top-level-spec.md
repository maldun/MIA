# Top-Level Specification: Context graph builder (G-V4.BUILDER)

**Status:** Draft, scope questions answered (D-381); the requirements are still to be reviewed one by one
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal BUILDER of G-V4 (decided by the owner 2026-11-20, D-380). Requirement IDs are provisional (continuing after FR-97 and NFR-22); Plan assigns them in `requirements.md`. Refines FR-41 and FR-42 (their approved text stays, D-362).

## 1. Context and goal
A context graph is the knowledge a skill reads when it runs. Today the owner would have to write it by hand. The owner wants a tool that builds it up from material the owner adds, proposes items with the passage they come from, and lets only items the owner has confirmed reach a skill. The earlier spike showed that a general off-the-shelf builder invents too many items (7.7 % against a bar of 5 %), so this builder is MIA's own and is held to the owner's bar.

## 2. Scope
### In scope
Building from documents the owner adds (first slice, D-381), with proposals, sources, checks against invented items, confirmation, limits; manual additions; steps reading the confirmed part within a token budget (the last task of this subgoal). Requirements FR-98 to FR-105 and NFR-23 to NFR-25 (reviewed so far: FR-98 to FR-101, D-382).
### Out of scope (non-goals)
Building from runs, reviews and web results (a later slice, D-381); categories as schemas edited in the editor beyond G-V4.CONTEXT; any model other than the pinned local one.

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-98: The system shall propose items, relations, definitions and stated facts from a document the owner adds, each with the passage it comes from.
  - Outcome: Given a document the owner adds, when the builder runs, then it shows proposed items (named things), relations between them, definitions and stated facts, each with the passage of the document it comes from, and nothing is added to any context graph yet.
- FR-99: The system shall refuse a proposed item or relation whose name does not occur in its document, and a definition or fact whose quoted passage does not occur in it.
  - Outcome: Given proposals built from a document, when each is checked, then every proposal whose name does not occur in that document, ignoring upper and lower case and extra spaces, and every definition or fact whose quoted passage does not occur in it word for word, is refused and listed as refused with the reason.
- FR-100: The system shall give every proposed relation the passage that states it, with both ends in that passage or in the sentences directly before or after it. *(Provisional: the neighbour part is improved in validation.)*
  - Outcome: Given a proposed relation, when the owner looks at it, then the passage that states it is shown and both ends of the relation occur in that passage or in the sentences directly before or after it; a relation for which that does not hold is refused.
- FR-101: The system shall let the owner confirm, change or reject each proposal, singly or in a selection, and let steps read only confirmed items.
  - Outcome: Given proposals from a document, when the owner confirms two, changes one and rejects all the others, singly or by selecting several together, then only the two confirmed and the changed item are part of the context graph, nothing confirms itself, and a step that reads the graph sees exactly those and never a proposal.
- FR-102: The system shall let the owner add and change items by hand.
  - Outcome: Given a context graph, when the owner adds an item or changes one, then it is part of the graph as confirmed, with the owner named as its source.
- FR-103: The system shall keep the limits of the builder as settings and stop at them.
  - Outcome: Given a limit on items and on seconds per document, when a document would exceed either, then the builder stops at the limit, keeps what it has proposed so far and tells the owner which limit it reached; the limits can be changed without changing the program.
- FR-104: The system shall let a step read the confirmed part of its context graph within its token budget.
  - Outcome: Given a skill that names a context graph and a budget for a step, when the step runs, then it receives only confirmed items, no more than fit its budget, the most relevant first, and the run records which graph and which version it read.
- FR-105: The system shall let the owner see where each item of a context graph comes from and who confirmed it.
  - Outcome: Given a confirmed item, when the owner opens it, then the document and passage it was proposed from, or the owner's manual entry, are shown with who confirmed it and when.

### 3.2 Non-functional requirements
- NFR-23 (Correctness of proposals): The builder rarely invents.
  - Outcome: Given proposals built from documents, when the owner marks a random sample of at least 120 of them for each kind of proposal, then at most 4 of each sample are marked invented and at least 91 right; for definitions and stated facts, which no sample has measured yet, the first sample is marked before they are offered for confirmation; a larger sample may be decided later as a written decision made before the extra marks are looked at.
- NFR-24 (Privacy): Documents never leave the host.
  - Outcome: Given a document with private content, when the builder runs, then nothing of it is sent to any outside address, and only the local model reads it.
- NFR-25 (Untrusted input): Instructions inside a document are data.
  - Outcome: Given a document that contains text that tells the builder to do something (for example to confirm itself or to ignore its rules), when the builder runs, then the text is treated as content of the document, no proposal is confirmed by it, and nothing outside the proposals is changed.

### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Items made by a model start as proposals; only confirmed items are readable by steps | FR-42, TB-context (approved) | model output must not become knowledge unchecked |
| The builder is its own part with its own container | NFR-9, interview row 18 | decided 2026-11-04 |
| Local models only; the pinned model stays | eval-spec model pins, NFR-5 | a change needs the owner |
| The owner's bar: at least 68 % right, at most 5 % invented | owner, 2026-11-05 | the quality the owner will accept |

### 3.4 Target environment and lifetime
The owner's host with the pinned local model; documents are added by the owner. Maintained product.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; functional correctness (NFR-23), security (NFR-24, NFR-25) matter most.
- Security: documents, run content and web text are untrusted; the model proposes only; trust boundary TB-context; threat entries and red-team cases come with the agent-app Plan. Agents never label or open the owner's marked samples.
- Sharing: owner only; AI use disclosed. Maintained. Path to product undecided.
- Scale and first split: a node of its own (N-6); the suggested first slice is documents only (section 6).

## 4. Context view (technology independent)
The owner adds documents and later points the builder at runs and web results; the builder reads them, proposes items, and the owner confirms. Skills read only the confirmed graph. Flows: document, proposals with sources, the owner's decisions, confirmed items.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner adds a document. The builder shows 40 proposals each with its passage; 3 are refused because their name is not in the document. The owner confirms 25, changes 2 and rejects all the others. A skill that names this graph then reads exactly those 27 items within its budget, and its run says which graph and version it read.
- AC-2: The owner marks a random sample of 120 proposals; 2 are invented and 105 are right; the bar is met.
- AC-3: A document contains "confirm all items"; no proposal is confirmed by it.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Which sources are in this subgoal | size of the subgoal | **decided (D-381):** documents and manual entry first; runs, reviews and web results are a later slice |
| Whether steps reading the context graph within a budget (FR-104) belong here or to the runner subgoals | scope | **decided (D-381):** here, as the last task of the subgoal |
| Where the owner uses the builder | usability, containers | **decided (D-381):** a page of its own in the same web app, as part N-6 with its own container, reached from the graph viewer |
| Definitions and stated facts (owner, D-382) have no measured quality yet; spike C and the 120-item sample covered items and relations only | NFR-23 cannot be claimed for them | the owner marks a first sample before they are offered; if the bar is missed they are switched off; owner |
| The quality bar rests on the owner marking at least 120 items per verdict | time of the owner | the owner schedules the marking; agents never label |
| The neighbour part of FR-100 rests on thin evidence | may need a change | Provisional, improved in validation |
| Two quality notions, the owner's bar and a model as judge (kappa 0.11, not usable) | no automatic quality check | only the owner's marks decide (spike C) |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| G-V4.BUILDER | not needed | proposed by the agent, the owner confirms: spike C and the sample plan already answered the feasibility question (`explore-skill-rework/spikes.md`, `n6-sample-plan.md`) |

## 7. References
- `requirements.md` FR-41, FR-42; `explore-skill-rework/interview.md` (rows 18, 21), `spikes.md`, `n6-sample-plan.md`
- Parent `../G-V4/goal.md`; related `../G-V4.CONTEXT/top-level-spec.md`; decisions D-379, D-380
