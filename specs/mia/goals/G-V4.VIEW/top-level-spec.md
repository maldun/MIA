# Top-Level Specification: Graph viewer (G-V4.VIEW)

**Status:** Approved by the owner (maldun, 2026-11-20, D-389), with the phone aspects moved out of scope; amended by the owner 2026-11-21 (D-403 to D-405): FR-48 and FR-50 reworded for the kind of the graph
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, subgoal VIEW of G-V4 (item 3a of the owner's list). Refines FR-22 (graph app, legacy text stays, D-362); the later subgoals EDIT and REPLAY build on it.

## 1. Context and goal
The owner wants to look at the workflows and context graphs MIA works with, as they are stored, instead of reading them as text. Today a graph can only be seen by picking a file from disk; the app does not read what MIA has stored. This subgoal lets the owner open any stored graph from the live store or from a set of files and see it drawn clearly. Editing and the history of changes follow in later subgoals; the place for them is kept free.

## 2. Scope
### In scope
Opening and looking at stored graphs: the list, the drawing, the content of a selected item, the arrangement the earlier versions and their history, and the view settings. Requirements FR-48 to FR-55 and FR-96 (search by description, new number) below (new numbers after FR-47 and NFR-9; assigned for real when Plan writes them into `requirements.md`).
### Out of scope (non-goals)
Use on a phone-sized screen (the owner moved it out of scope for now, 2026-11-20, D-389; the stacked layout of the picture and the side panel follows in a later iteration); Changing a graph, saving, keeping where the owner placed the steps between visits (G-V4.EDIT); the playback of the individual changes and what a change did within a session (G-V4.REPLAY); running a workflow from the viewer; the skills window (goal B); building context graphs (goal C).
### Known shortcuts (prototype)
The prototype `prototype/graphview` shows the data path and the look; it has no login, shows no graph with a loop-controlling step, and keeps no settings between visits.
### Candidate goals (increments) and proposed first split
| Candidate goal | What users get (outcome) | Likely in scope | Why this cut |
|---|---|---|---|
| VIEW (this) | the owner sees any stored graph drawn clearly and can inspect every item | FR-48 to FR-55, FR-96 | can be judged by looking, before any editing exists |
| EDIT | the owner changes a graph, with the rules applied | FR-22 editing | needs the view first |
| REPLAY | every change made in the editor can be played back and explained step by step | FR-22 history of changes, FR-16 | needs the edits first |

## 3. Top-level requirements

### 3.1 Functional requirements
- FR-48: The system shall let the owner open any stored workflow graph or context graph and find it by name.
  - Outcome: Given graphs stored in the live store, when the owner opens the viewer, then a list of all stored graphs is offered, each marked with its kind (workflow graph or context graph), the list narrows as the owner types part of a name, and choosing one shows that graph; given the same graphs kept as a set of files, then the list and the picture are the same; given a graph of a kind the viewer does not know, then it is listed with its kind named and shown as plain steps and connections, read-only.
- FR-96: The system shall, when a language model is available, let the owner describe in words which graph is wanted and propose matching graphs.
  - Outcome: Given the owner types a description such as "the graph that checks claims against sources", when the model is available, then the viewer proposes up to a few matching graphs, best first, each with a short reason, and choosing one opens it; when the model is not available, then the owner is told that the search by description is not available and the name filter of FR-48 still works; a proposal only selects a graph to open and changes nothing.
- FR-49: The system shall draw every step and connection of a stored graph, and say what it cannot draw.
  - Outcome: Given a stored graph with N steps and M connections, when it is opened, then N steps and M connections are shown, each connection with its direction; if something is wrong (for example a connection to a step that does not exist) it is named beside the picture and marked on the drawing, for instance as a broken line to a marked missing step, and nothing is dropped silently.
- FR-50: The system shall show the type of each node, and the trust and lifecycle state of each node that uses a tool, at a glance.
  - Outcome: Given a workflow graph with data, processing and loop-controlling steps, when it is shown, then the owner can tell the three types apart without opening any of them and without relying on colour alone, and each processing step shows whether it is trusted, whether it changed since it was trusted, and whether it is draft, tested or retired; the types of a graph of another kind are shown by the same rule, taken from the description of that kind.
- FR-51: The system shall show the full content of a selected step or connection.
  - Outcome: Given a drawn graph, when the owner selects a step or a connection, then its known values appear beside the picture as labelled read-only fields and the full stored text is available next to them as plain text, and selecting nothing clears it.
- FR-52: The system shall arrange the graph so that it reads naturally and keeps what the owner arranged.
  - Outcome: Given a graph of about fifty steps, when it is opened, then it appears with the arrangement the owner saved in the editor if there is one, otherwise it settles by itself into a picture where steps do not lie on each other and connections are followable; when the owner moves a step it stays where it was put while the graph is open; the owner can return to a clear layered arrangement in which every connection points forward.
- FR-53: The system shall let the owner choose how connections and the arrangement look, in one place.
  - Outcome: Given a drawn graph, when the owner changes the connection style (rounded or straight) or the automatic arrangement, then the picture follows at once, the moved steps stay in place, all such choices are found in one settings place, and they are remembered on that device for the next visit; if they cannot be remembered the viewer works with its defaults.
- FR-54: The system shall always show the graph as it is stored and never run or follow what it contains.
  - Outcome: Given a stored graph whose names or contents contain text that looks like an instruction, markup or code, when it is shown or selected, then it appears as text only and nothing is executed or opened; a step that holds code is marked as such together with its trust state.

- FR-55: The system shall show the history of a graph as a list the owner can scroll through and let the owner look at any earlier stored version.
  - Outcome: Given a graph with several stored versions, when the owner opens its history, then the versions are listed newest first with who stored each and when and the current one is marked; choosing an entry shows that version as it was stored, read-only, and the picture says which version it is and when it was stored; the owner can step to the previous and the next version. *(FR-56 of the first draft is merged into this item; the number is not reused.)*

### 3.2 Non-functional requirements
- NFR-10 (Usability): The owner can find, open and read a graph without help.
  - Outcome: Given a first-time use, when the owner wants to look at one named graph, then the owner opens it and reads the content of one step within a minute and without instructions.
- NFR-11 (Performance, as experienced): Opening a graph is not a wait.
  - Outcome: Given a graph of about fifty steps, when it is chosen, then the picture is usable at the moment the owner starts looking at it, and moving or selecting stays smooth; what happens if it is slower is decided with the hard bound in Plan.
- NFR-12 (Access): Only logged-in users see stored graphs.
  - Outcome: Given someone who is not logged in, when they try to open the viewer or a graph, then nothing is shown and they are asked to log in; given any logged-in account, then it can look at graphs but not change them (G-V4.EDIT, NFR-19); given the owner logged in once, then the viewer needs no second login.
- NFR-13 (Privacy): The viewer works inside the home network only.
  - Outcome: Given the viewer in use, when the owner opens graphs for an hour, then nothing is requested from or sent to any outside address.
- NFR-14 (Looks and accessibility): The viewer follows the system's light or dark setting and works by keyboard.
  - Outcome: Given either the light or the dark setting, when a graph is shown, then labels, steps and connections can be read and the three kinds of step stay distinguishable; given only a keyboard, then the owner can pick a graph, move between steps, select one and open the settings.

### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Access only through the existing accounts and login | FR-21, NFR-6 (approved requirements) | the viewer must not open a second way in |
| Existing wording of FR-22 stays as legacy | D-362 (owner, 2026-11-20) | locked requirements are not amended for this goal |

### 3.4 Target environment and lifetime
The owner's host at home, used from the owner's own devices over the home network or the tailnet. The viewer is part of the maintained product. A running deployment of the current version exists (v0.2.1), and the viewer is added to it.

### 3.5 Quality, security and sharing (Explore decisions)
- Quality model: ISO/IEC 25010:2023; usability, security and performance efficiency are the characteristics that matter here (`quality.md` to be extended in Plan).
- Security: the content of a stored graph may come from outside (imported steps, text from the web); it is untrusted and shown as text only (FR-54, THR-011, candidate THR-013). No credentials or external effects. Approval by the owner.
- Sharing: team (owner) only; AI use disclosed.
- Maintained or frozen: maintained.
- Path to product: undecided; shortcuts register unchanged.
- Scale and first split: a leaf inside the existing decomposition (node N-5); the cut from EDIT and REPLAY is in section 2.

## 4. Context view (technology independent)
### 4.1 Overview
The owner looks at stored graphs through the viewer. The viewer asks MIA's store for the list of graphs and for one graph, with the owner's login. It gets nothing else and sends nothing out.
### 4.2 SysML context model
Not yet written; the context model of G-V4 (`architecture.sysml`) gets the viewer, the owner and the store with the flows below in Plan.
```sysml
// actor Owner -> part GraphViewer : requests graph, selection, settings
// part GraphViewer <- store : list of graphs, a stored graph and its versions
// no internal parts
```
### 4.3 Integration with the existing system
Findings with references are in `research.md` of this folder: the page opens a file only (F1), the existing routes serve one stored form (F2, F3), the page and the backend run in separate places (F4). The prototype `prototype/graphview` shows 15 of 15 stored graphs drawn completely from files and from the database.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner logs in once and opens the viewer. A list of the stored graphs appears. The owner picks the research workflow of about fifty steps. It settles into a readable picture with data, processing and controlling steps apart. The owner clicks one step and its stored content appears on the left. The owner drags the step aside, switches the connections to straight lines and back to rounded ones, and then returns to the layered arrangement. The owner repeats the first part with the graphs kept as files and sees the same list and the same picture.
- AC-2: A stored graph has a connection to a step that is not there. The viewer draws everything else and names the broken connection beside the picture.
- AC-3: A step in a stored graph has a name containing markup and a text that reads like an instruction. The viewer shows both as plain text and does nothing else.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| Loop-controlling steps (none in today's 15 converted graphs) may not be drawable the same way | FR-49, FR-50 incomplete for such graphs | **decided (D-378):** the cases include a graph with a loop-controlling step and a context graph |
| Context graphs differ from workflow graphs (Q-5 of N-5) | FR-48 may need a second look | **decided (D-378):** viewed in VIEW; the stored form is GRAPHSTORE's; editing is G-V4.CONTEXT |
| Natural arrangement is not reproducible | a graph never arranged settles differently on each opening | decided: the viewer opens with the arrangement saved in EDIT if there is one (D-377); the layered arrangement is the reproducible reset |
| A history shows who stored a version but not what changed between two; the comparison of two versions stays in REPLAY (owner, D-366) | FR-55 shows a list, not a difference | decided |
| Search by description uses a language model: graph content is untrusted text for the model, the model is local, the result only selects a graph | FR-96 adds an agent feature to the viewer (agent profile, evaluation cases, injection check) | decide in Plan with the agent-app rules; owner |
| Use on a phone-sized screen is out of scope for now | the viewer may be hard to use on the phones in use (NFR-1 of the product) | owner decision D-389; revisit in a later iteration |
| Very large graphs (more than about fifty steps) | readability and speed unknown | **decided (D-378):** no bound for now; only about fifty steps are promised (NFR-11) |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| G-V4.VIEW as a whole | accepted | `prototype/graphview`, `specs/mia/goals/G-V4.VIEW/prototypes/graphview/prototype-report.md` (commit `e263f361`); carry-over for the owner to decide |

## 7. References
- Research notes: `specs/mia/goals/G-V4.VIEW/research.md`
- Goal record: `specs/mia/goals/G-V4.VIEW/goal.md`; parent `specs/mia/goals/G-V4/goal.md` (OC-8)
- Decisions: D-360 to D-363, D-376 in `specs/mia/review-log.md`
