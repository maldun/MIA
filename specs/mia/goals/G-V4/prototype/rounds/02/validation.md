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
| FR-63 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-64 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-68 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-69 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-70 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-71 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-72 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-73 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-74 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-76 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-77 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-78 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-79 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-80 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-81 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-91 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-92 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-93 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-94 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| FR-95 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| NFR-10 | Given you have never used the viewer: from the login find `research.escalate@1`, open it and read the content of one step without instructions; note the time | – | not tried | – |
| NFR-11 | Given `research.escalate@1` (54 steps): how long until the picture is usable, and do moving and selecting stay smooth? | – | not tried | – |
| NFR-12 | Given you are not logged in, open `/api/v2/graphs` and a graph: nothing is shown; log in once, log out | – | not tried | – |
| NFR-13 | Given the browser's network tab while you use the viewer for a while: only requests to 127.0.0.1 | – | not tried | – |
| NFR-14 | Given only the keyboard: Tab to the graph list and the step list, Enter selects; the settings button opens with Enter and closes with Escape; switch the system between light and dark | – | not tried | – |
| NFR-15 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| NFR-16 | Given a graph with a cycle and an interrupted save, look at the demo output and at the checks 8 to 10 of `python proto_checks/cp1_check.py files` | – | not tried | – |
| NFR-18 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| NFR-19 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |
| NFR-20 | the outcome's Given and When, as steps (written when its subgoal's breakpoint is reached) | – | not tried | – |

## Beyond the outcomes
- **FB-1 (owner, 2026-11-20, after CP6):** for the editor the panel for the contents of a step is the place where edits happen; the current narrow column of read-only fields does not look good for editing, so its place and form may change. To decide at CP8 (EDIT).
- The status line was easy to overlook (owner); it is now a highlighted bar (CP6).

## What this changes
| Finding | Goes to | Change |
|---|---|---|
| – | – | – |

Hand-over to Plan: the prototype's specs are taken over as drafts and changed by the table above, then go through the normal Plan pipeline.
