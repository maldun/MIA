# Prototype validation: G-V4, round 02 (graph path slice)

<!-- Written for the owner at each breakpoint (★), filled during and after the session. The owner, not the agent, judges. One row per item of the scope. -->

Validated by: –
Date: – · Prototype state: branch prototype/g-v4 · Where it ran: –

## Outcomes
| Item | What the user tried (Given / When from the outcome) | What was observed | Result (met / partly / not met / not tried) | Finding |
|---|---|---|---|---|
| FR-48 | Given the sample store, start the viewer (`graph_proto_app.py --store files:/tmp/gs/v`), log in, type part of a name into the filter, pick a graph; then start it on the database store and compare | – | not tried | – |
| FR-49 | Given the graph `sample.broken`, open it: a dashed connection to a marked missing step and the problem named above the picture | – | not tried | – |
| FR-50 | Given the sample store with --code, open `sample.code`: three shapes for data, processing and loop-controlling steps; an UNTRUSTED code step; trusted marks on the others; the legend above the picture | – | not tried | – |
| FR-51 | Given a graph, click a step: labelled fields on the left, `Full stored text` opens the complete content; click a connection; click empty space: it clears | – | not tried | – |
| FR-52 | Given the sample store, open `cp2.multi`: it settles by itself; drag steps, open the settings menu, `Save this arrangement`; reload and open it again: the places are where you left them; `Reset to layers`: the layered picture, then `Use the saved arrangement` | – | not tried | – |
| FR-53 | Given the settings menu, switch the connections to straight and physics off, reload the page: the choices are still there | – | not tried | – |
| FR-54 | Given `sample.code` with a step named like an HTML tag and a value that tells the viewer what to do: both appear as plain text, nothing happens | – | not tried | – |
| FR-55 | Given `cp2.multi` with four versions: the History list on the left (newest first, who, when), click an entry or press `Previous version`; the status line says which version and that it is read-only | – | not tried | – |
| FR-57 | Given graphs stored, run `python proto_checks/cp1_demo.py`; look at the versions of `lookup` after a change and after saving the same graph again | – | not tried | – |
| FR-58 | Given the same operations on files and on the database, run `python proto_checks/cp2_check.py` (check 1 and 2) and compare | – | not tried | – |
| FR-59 | Given a store, move it with `python graph_store_move.py files:<folder> postgres:<url>` and back, repeat it, and try a store with a missing step (checks 3 to 9 of `cp2_check.py`) | – | not tried | – |
| FR-60 | Given two graphs with a step named `step.write`, change it in `lookup` and look at the histories of both graphs (`cp1_demo.py`) | – | not tried | – |
| FR-63 | Given the sample store, in the editor of `cp2.multi` make two mistakes (connect `var.out` back to `step.write`, and add a second connection into one data step): both rules are named under the status line in the same order; then `Keep the change` is refused with the same rules; add a loop-controlling step without a limit and a data step with `{"stop": {"max_repetitions": 2}}` in the other-fields text: the session-setting rule names them | – | not tried | – |
| FR-64 | Given the sample store made with `--broken`: open `sample.broken`, press "Try a run (stand-in steps)": "Run refused: no step ran" and the broken connection named; open `chat@1` and try again: the missing input `input.text` is named; type `{"input.text": "hello"}` into the start values and try again: the checks pass and the stand-in step runs | – | not tried | – |
| FR-68 | Given the sample store, log in as owner, open `cp2.multi`, `Edit this graph`: add a step, add a connection, remove a connection, remove a step; the picture follows each change | – | not tried | – |
| FR-69 | Given the working copy, connect `var.out` to `step.write`: the broken rule (a cycle) is named under the status line at once and `Keep the change` is disabled; remove the connection: the rule goes | – | not tried | – |
| FR-70 | Given a change that keeps every rule, `Keep the change`: a new version appears in the history, by you; a change that breaks a rule cannot be kept | – | not tried | – |
| FR-71 | Given the kept change: the History list has version 5; version 4 is still there as it was | – | not tried | – |
| FR-72 | Given two browser windows on the same graph: keep a change in one, then try to keep another in the other: it says the graph changed and writes nothing | – | not tried | – |
| FR-73 | Given `cp2.multi` with several versions: open an earlier one in the History, `Restore this version`: a new version appears with that content, the versions before it are unchanged | – | not tried | – |
| FR-74 | Given a graph, log in as owner, `Edit this graph`, drag two steps, `Save the arrangement`; log out, log in again (or open a second browser as another account) and open the graph: the steps are where you left them and the History list has no new version; move one step again and save: the last move counts | – | not tried | – |
| FR-76 | Given `cp2.multi`, `Edit this graph`: make five changes (add a step, add a connection, change a tool, remove a step, change a value), undo one of them; the list "Changes to keep" shows the four that count; `Keep the change`; under History, "How this version came about" lists the entries with account, time, the value before and after, and the version it started from; drag a step and save the arrangement: no new entry | steps 1 to 9 tried by the owner 2026-11-20: worked | met | – |
| FR-77 | Given the same session: type a reason into two of the changes before keeping; the entries show "reason: ..." and the others "no reason given" | steps 1 to 9 tried by the owner 2026-11-20: worked | met | – |
| FR-78 | Given a version you kept in CP11 (for example version 5 of `cp2.multi`): choose it in the History and press "Play back this version": the picture shows the starting version; "Forward one change" step by step, each change is described under the bar and its step or connection is marked; "Back one change" returns; at the last change the bar says the result is identical to the saved version | tried by the owner 2026-11-20 (one change and a longer playback, forward and back to the end): worked | met | – |
| FR-79 | Given a graph with several versions: open the newest, choose an older one in "Compare with version" and press "Compare": the steps and connections added, removed and changed are listed with old and new content, and the drawing marks them in different colours and with [added], [removed], [changed]; "Leave playback or comparison" returns | tried by the owner 2026-11-20: worked | met | – |
| FR-80 | Given a recorded change: there is no button or address in the page that alters or deletes it; `python proto_checks/cp11_check.py` (checks "cannot be altered", "cannot be deleted") shows the refusals at the storage layer | steps 1 to 9 tried by the owner 2026-11-20: worked | met | – |
| FR-81 | Given a graph with recorded changes: move the store with `python graph_store_move.py files:<a> files:<b>` and open `<b>` in the viewer: the same entries; or sync a live store to a copy (CP3) and look at the copy | steps 1 to 9 tried by the owner 2026-11-20: worked | met | – |
| FR-91 | Given the editor: make three changes, `Undo` twice, `Redo` once (or Ctrl+Z / Ctrl+Y): the picture follows; nothing is kept until `Keep the change` | – | not tried | – |
| FR-92 | Given a processing step selected while editing: a form with the tool; a data step: value and parameters; a loop-controlling step: stop limits; type something wrong and read the reason; other stored fields as JSON text | – | not tried | – |
| FR-93 | Given a live and a copy folder (`python graph_store_sync.py files:<live> files:<copy> --lag` shows the lag per graph): change a graph in the live store through the viewer started on the live folder only, look at the lag, `python graph_store_sync.py ...` or `Sync the copy now`: the copy equals it. Then write a version on the copy and another on the live store for the same graph: the header names the graph as differing, the sync names the version it set aside and the file in `data/proto_aside` (or `--aside`); the file holds the copy's version. Start the viewer with `--auto-sync` and stop it with Ctrl+C: both syncs are printed | steps 1 to 4 tried by the owner 2026-11-20: worked (the optional step 6, unreachable live store, was not tried) | met | – |
| FR-94 | Given a step selected while not editing (owner): under its fields "Copy ... into another graph": search a graph, choose it, `Copy the step`; open that graph: the step is there with the same content and a new version; change either step and keep: the other is unchanged; a name that is used there is refused with the reason | – | not tried | – |
| FR-95 | Given the viewer started with `--store <copy> --live <live>`: keep a change (the live store gets it, the header says the copy is behind), `Sync the copy now`; then remove the live folder: the header says NOT REACHABLE, the edit button is disabled, looking still works | – | not tried | – |
| NFR-10 | Given you have never used the viewer: from the login find `research.escalate@1`, open it and read the content of one step without instructions; note the time | – | not tried | – |
| NFR-11 | Given `research.escalate@1` (54 steps): how long until the picture is usable, and do moving and selecting stay smooth? | – | not tried | – |
| NFR-12 | Given you are not logged in, open `/api/v2/graphs` and a graph: nothing is shown; log in once, log out | – | not tried | – |
| NFR-13 | Given the browser's network tab while you use the viewer for a while: only requests to 127.0.0.1 | – | not tried | – |
| NFR-14 | Given only the keyboard: Tab to the graph list and the step list, Enter selects; the settings button opens with Enter and closes with Escape; switch the system between light and dark | – | not tried | – |
| NFR-15 | Given a copy folder: copy it to another folder (or another machine) and start the viewer there with `--store files:<that folder>`: every graph is listed with the same versions and content (`cp3_check.py` checks the same and that no path of the source is stored) | step 5 tried by the owner 2026-11-20: worked | met | – |
| NFR-16 | Given a graph with a cycle and an interrupted save, look at the demo output and at the checks 8 to 10 of `python proto_checks/cp1_check.py files` | – | not tried | – |
| NFR-18 | Given you have not used the editor (or someone else tries it): change the tool of one step and keep it, without any instructions; note the time (the aim is under three minutes) and where you hesitated | – | not tried | – |
| NFR-19 | Given a second account (not the owner): no `Edit this graph` button; the routes refuse it | – | not tried | – |
| NFR-20 | Given the sample graphs: versions made before the record say "made before the record of changes existed"; a version you kept shows its entries from the version it started from. Then "Play back" on such a version says there is nothing to play, and "Compare" still shows what differs from another version (CP12) | listing and "before the record" worked (CP11), playback and comparison worked (CP12), 2026-11-20 | met | – |

## Beyond the outcomes
- **FB-1 (owner, 2026-11-20, after CP6):** for the editor the panel for the contents of a step is the place where edits happen; the current narrow column of read-only fields does not look good for editing, so its place and form may change. To decide at CP8 (EDIT).
- **Owner, 2026-11-20:** the review of the UI (the editing panel and the rest) moves to the planning stage.
- The status line was easy to overlook (owner); it is now a highlighted bar (CP6).

## What this changes
| Finding | Goes to | Change |
|---|---|---|
| – | – | – |

Hand-over to Plan: the prototype's specs are taken over as drafts and changed by the table above, then go through the normal Plan pipeline.
