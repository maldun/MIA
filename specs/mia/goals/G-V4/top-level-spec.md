# Top-Level Specification: G-V4 run 1 scope (aggregate of the subgoal specs)

<!-- Generated on 2026-11-20 from the approved top-level specs of G-V4.GRAPHSTORE, GRAPHAPI, VIEW, EDIT and REPLAY (the items in scope of prototype run 1).
     The subgoal specs are the source; this file only makes the run's protected part checkable (spec_check.py PT9 fingerprint, PT11 validation rows).
     Do not edit. When a subgoal spec changes, regenerate this file and add a fingerprint row to rounds/02/run.md (a person's decision).
     Amended 2026-11-21 (D-405): FR-48, FR-50, FR-63, FR-64, FR-72, FR-73, FR-92, FR-94 as in the subgoal specs of VIEW, GRAPHAPI and EDIT (the kind of the graph selects rule set, description and copy rule). -->

**Status:** Approved (the items are approved in their subgoal specs, D-389 to D-391)
**Owner:** Stefan Reiterer   **Date:** 2026-11-20
**Project / deliverable:** MIA, G-V4 graph rework, living prototype run 1 (the graph path slice)

## 1. Context and goal
The owner wants to store, view, change and replay graphs; run 1 builds the thin end-to-end slice (storage in two places, one rule set, viewer, editor, edit log with playback).

## 2. Scope
### In scope
The items below. Out of this run: migration (FR-61, FR-62), the run and code in graphs (FR-65 to FR-67), context graphs and the builder, the search by description (FR-96).

## 3. Top-level requirements
### 3.1 Functional requirements
- FR-48: The system shall let the owner open any stored workflow graph or context graph and find it by name.
  - Outcome: Given graphs stored in the live store, when the owner opens the viewer, then a list of all stored graphs is offered, each marked with its kind (workflow graph or context graph), the list narrows as the owner types part of a name, and choosing one shows that graph; given the same graphs kept as a set of files, then the list and the picture are the same; given a graph of a kind the viewer does not know, then it is listed with its kind named and shown as plain steps and connections, read-only.
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
- FR-57: The system shall keep exactly one stored truth for every workflow graph and every context graph, with every change a new version and no version deleted.
  - Outcome: Given a graph that is saved, changed twice, read and listed, when the owner asks for it, then the newest state is returned, all three versions are listed with who stored each and when, and no version has disappeared; the same holds for graphs with steps of every kind, including a step that controls loops.
- FR-58: The system shall keep graphs in the live store, which holds everything, and in a copy as a portable set of files, with the same behaviour in both, so that MIA can run daily on the copy.
  - Outcome: Given the same sequence of saving, changing, reading and listing graphs carried out once in the live store and once in a copy, then every answer is the same in both, including versions, authors and refusals.
- FR-59: The system shall move the whole store between the live store and a set of files in both directions without loss.
  - Outcome: Given graphs with several versions each, when the owner moves the whole store from either place to the other, then every graph arrives with all its versions, authors and times unchanged and numbered as before; moving again changes nothing; if one graph cannot be moved, nothing is moved and that graph is named.
- FR-60: The system shall let every step and connection belong to exactly one graph.
  - Outcome: Given two graphs that both contain a step of the same local name but different content, when the owner changes that step in one graph, then the other graph and its history are untouched, and the step's history lists only the changes made in its own graph.
- FR-63: The system shall apply one set of graph rules for the kind of the graph wherever it is checked, in the same fixed order, and name every broken rule.
  - Outcome: Given a workflow graph that breaks two rules, when it is checked while saving, while editing and before a run, then the same broken rules are listed in the same order every time, each with its steps or connections; the eight rules of workflow graphs and their order are written in one place: ids, kind of step, connections to missing steps and duplicate connections, no two data steps adjacent, one writer per piece of data, session setting and stop limit, no cycle; the rule set of a context graph, and of any further kind of graph, is written in the same place and chosen by the kind of the graph.
- FR-64: The system shall refuse to run a graph that breaks the rules, has a step input that nobody supplies or is of a kind that cannot run, and name the broken part before any step has run.
  - Outcome: Given a stored graph with a cycle, two writers of one piece of data, a connection to a missing step, two identical connections, or a step input that has no writer, no start value in the graph and no value given with the run, when the owner runs it, then no step runs, the run ends as refused and names each broken step, connection or input; given a graph of a kind that cannot run, or of a kind the program does not know, then no step runs and the run ends as refused naming the kind.
- FR-68: The system shall let the owner change a graph in the web app by adding, removing and changing steps and connections and their fields.
  - Outcome: Given a drawn graph, when the owner adds a step, connects it, changes a field of another step and removes a connection, then the drawn graph shows all four changes before anything is kept.
- FR-69: The system shall tell the owner at once when a change breaks a graph rule and name the rule.
  - Outcome: Given a change that would create a cycle or give a piece of data two writers, when the owner makes it, then the problem and the broken rule are shown beside the picture before the owner tries to keep the change.
- FR-70: The system shall keep a change only when the graph rules hold, and refuse it otherwise with the rule named.
  - Outcome: Given a change that breaks a rule, when the owner tries to keep it, then it is refused with the rule named and the stored graph is unchanged; a change that keeps all rules is kept.
- FR-71: The system shall keep every kept change as a new version and leave earlier versions reachable.
  - Outcome: Given a graph at version 3, when the owner keeps a change, then version 4 exists with the change, version 3 is still there as it was, and version 4 names the owner and the time.
- FR-72: The system shall not overwrite a graph that changed while the owner was editing it.
  - Outcome: Given a graph opened at version 3 that another session changes to version 4, when the owner tries to keep a change made on version 3, then nothing is overwritten and the owner is told that the graph has changed; given a graph of a kind the program does not know, when the owner tries to keep a change, then it is refused with the reason unknown kind and nothing is written.
- FR-73: The system shall let the owner make an earlier version the current one again.
  - Outcome: Given a graph at version 5, when the owner restores version 2, then version 6 exists with the content of version 2, and versions 1 to 5 are unchanged; given a graph of a kind the program does not know, then the restore is refused with the reason unknown kind and nothing is written.
- FR-74: The system shall keep where the owner placed the steps of a graph between visits, the same for everyone who opens it, without making a new version.
  - Outcome: Given a graph in which the owner has moved steps, when anyone opens it again, then the steps are where they were last left and the graph's version list is unchanged; if two accounts move the same step, the last move counts.
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
- FR-91: The system shall let the owner undo and redo the changes of the open editing session one by one before they are kept.
  - Outcome: Given an editing session with three changes that are not yet kept, when the owner undoes the last two and redoes one, then the drawn graph shows the first and second change only, and nothing has been kept or recorded as a version.
- FR-92: The system shall offer the known fields of each type of node of the graph's kind as a form with checks, and any other field as editable text.
  - Outcome: Given a node of each type of a workflow graph (data, processing, loop-controlling), when the owner opens it for change, then its known fields appear as labelled form fields, any further field appears as text the owner can edit, and a value that does not fit a form field is refused with the reason before it is kept; a further kind of graph brings the types and fields of its own.
- FR-93: The system shall keep the copy in sync with the live store, which is the master, and never lose a version that exists only on the copy.
  - Outcome: Given a live store with new versions and a copy that lags behind, when the owner runs the sync or MIA starts or stops in an orderly way, then the copy receives the missing versions and equals the live store; MIA shows how far the copy lags before a sync; given graphs that got different new versions on the copy since the last sync, then the live store's history counts, and the copy's differing versions are saved aside and named to the owner, not discarded. Graphs are changed only in the live store (FR-95 of G-V4.EDIT), so the copy never holds versions of its own in normal use.
- FR-94: The system shall let the owner copy a step into another graph of the same kind as an independent copy.
  - Outcome: Given a step in one graph, when the owner copies it into another graph of the same kind, then the other graph has a step with the same content and its own history from that moment, and a later change to either step does not change the other; given a graph of another kind or of a kind the program does not know, then the copy is refused naming both kinds and nothing is written.
- FR-95: The system shall write every kept change to the live store, and make the editor read-only when the live store cannot be reached.
  - Outcome: Given MIA running on a copy of the graphs, when the owner keeps a change, then it is stored in the live store and reaches the copy at the next sync; given the live store cannot be reached, when the owner opens a graph, then it can be looked at, the editor says that changing is not possible now and why, and nothing is kept.

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
- NFR-15 (Portability): A set of files made on one machine works on another.
  - Outcome: Given a set of files moved from the owner's host to a test machine, when MIA is started there on those files, then every graph is listed with the same versions and content as at the source; given a set of files made by an older version of MIA, when a newer version opens it, then it is read completely or converted by a stated step that reports what it did.
- NFR-16 (Reliability of storage): A refused or interrupted save, move or sync never leaves a half-stored graph.
  - Outcome: Given a save, a move of the whole store or a sync that is refused or interrupted halfway, when the owner lists and reads graphs afterwards, then every graph is entirely as before, entirely new, or (after a move or sync that brings several new versions) at an earlier complete version of the live store's history, never with a missing step or connection, in both places, a refused save is not counted as a version, and an interrupted move or sync can be run again to finish.
- NFR-18 (Usability): A first change is possible without instructions.
  - Outcome: Given the owner has not used the editor before, when the owner wants to change one field of one step and keep it, then it is done in under three minutes without instructions.
- NFR-19 (Security): Only the owner changes graphs, and a step changed since it was trusted is marked.
  - Outcome: Given any account other than the owner's, when it opens a graph, then it can look but not change or keep anything; given a trusted step that the owner changes, then it stays trusted and is marked as changed since it was trusted (FR-67 of G-V4.GRAPHAPI).
- NFR-20 (Traceability): Every kept version can be explained.
  - Outcome: Given any version of a graph that was changed in the editor, when the owner asks how it came about, then the entries that made it are shown from the starting version to the saved one without a gap; a version made before the record existed is listed as made before the record, and the comparison of FR-79 still shows what differs.

### 3.3 Given constraints
| Constraint | Source | Why it cannot be changed |
|---|---|---|
| Locked requirement texts (FR-40, NFR-8) name technology | D-362 | legacy; not amended for this goal |
| Locked texts of FR-7, FR-37 name technology | D-362 | legacy |
| Trust is set only by the owner | FR-38 (approved) | an imported or changed step must not run on its own authority |
| Access only through the existing accounts and login | FR-21, NFR-6 (approved requirements) | the viewer must not open a second way in |
| Existing wording of FR-22 stays as legacy | D-362 (owner, 2026-11-20) | locked requirements are not amended for this goal |
| Access only through the existing accounts | FR-21, NFR-6 | no second way in |
| Locked FR-22 text stays as legacy | D-362 | locked requirements are not amended |
| The record of changes belongs to the graph and moves with it | FR-59 (GRAPHSTORE) | the owner expects transfers without loss |

## 4. Context view
As in the subgoal specs.

## 5. Acceptance scenarios (end to end)
- AC-1: The owner opens the viewer, picks a stored graph, selects a step, changes a field with a rule problem shown, keeps a valid change as a new version, looks at the history and plays the changes back, in the live store and on a copy.

## 6. Risks and open questions
| Risk / question | Impact | Mitigation / owner |
|---|---|---|
| none beyond those in the subgoal specs | – | – |

### Prototype decisions
| Item | Decision | Report or reason |
|---|---|---|
| G-V4 viewer, look and data path (round 01, the earlier `graphview` prototype) | accepted | `prototype/rounds/01/prototype-report.md` |
| G-V4 graph path slice, run 1 (round 02): storage, transfer and sync, rules and refusal before a run, viewer, editor, edit log, playback and comparison; MVP level | accepted | `prototype/rounds/02/prototype-report.md`, authorized by the owner in `prototype/rounds/02/run.md` (2026-11-20); built in 12 checkpoints on `prototype/g-v4`; the owner's validation is `prototype/rounds/02/validation.md`; what is carried into Plan is decided in the carry-over table of the report (the owner decides) |
| G-V4.GRAPHSTORE.CORE, prototype expansion (round 03): context graphs stored, the same cases on PostgreSQL, fault injection at every write position; MVP level | accepted | `prototype/rounds/03/prototype-report.md`, authorized by the owner in `prototype/rounds/03/run.md` (2026-11-21); the owner's validation is `prototype/rounds/03/validation.md` |

## 7. References
- Subgoal specs: `../G-V4.GRAPHSTORE/`, `../G-V4.GRAPHAPI/`, `../G-V4.VIEW/`, `../G-V4.EDIT/`, `../G-V4.REPLAY/` (`top-level-spec.md`)
