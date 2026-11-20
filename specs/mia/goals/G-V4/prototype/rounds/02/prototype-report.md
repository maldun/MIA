# Prototype report: G-V4, round 02 (graph path slice, MVP)

Status: Prototype (reviewable draft, no product guarantees until parts are `real`) · Location: `specs/mia/goals/G-V4/prototype/rounds/02/` · Mock-up code: worktree `../MIA-prototype-g-v4`, branch `prototype/g-v4` · Date: started 2026-11-20
Scope: the graph path slice (run.md) · Budget: 12 checkpoints of about an hour, a stop at each subgoal breakpoint · Status table: `specs/mia/goals/G-V4/prototype/status.md`

## Question
Can the graph path (scoped storage in two places, one rule set, viewer, editor, edit log with playback) be built as one thin working slice that the owner can try, and what does it teach about the requirements?

## Hard requirements (top-level only)
The items of `../../top-level-spec.md` (the aggregate of the subgoal specs in scope).

## What was built
**CP1 (GRAPHSTORE.CORE, breakpoint ★), 2026-11-20, commit 2f9312f8.**
- Every step and connection of a graph is a record `<graph id>/<local id>`; the graph a caller sees has local IDs. The storage layer (`graph_tables.py`) refuses an unscoped ID and a header that pins a step of another graph (rule `unscoped_id`).
- `GraphModel.save_graph` checks everything the storage would refuse before the first write, writes a step only when it differs from its newest version, and writes no new graph version when nothing changed. `step_history` lists the versions of one step as the headers of that graph pinned them.
- Demonstration: `python proto_checks/cp1_demo.py` (a short story) and `python proto_checks/cp1_check.py files|postgres` (10 checks, all pass on both backends).
- Plan checkpoints CP2 to CP12 follow in `run.md`.

**CP2 (GRAPHSTORE.TRANSFER, first part), 2026-11-20, commit 70e9c2cb.**
- `graph_store_move.py` moves the whole store (steps, connections, headers) between any two backends: every graph is checked first (headers, pinned step versions, scoped IDs) and compared with the target; one graph that cannot be moved, or that has a different history in the target, refuses the whole move with the graphs named and writes nothing. Steps are written before headers, so a graph appears only when complete; nothing is renumbered; authors and times are kept; a second move changes nothing.
- Demonstration: `python proto_checks/cp2_check.py` (9 checks, all pass, PostgreSQL 16 under podman) and the command line `python graph_store_move.py files:<folder> postgres:<url>`.


**CP5 (VIEW, first part), 2026-11-20, commit 85efcc21.** (Built before CP3 and CP4, D-399.)
- `graph_proto_app.py`: a Flask backend over any store (`files:<dir>` or `postgres:<url>`) using the existing accounts and session cookie (`accounts_api`); only the login and the page are open, every graph route needs a session (NFR-12). Routes: `GET /api/v2/graphs` (the list), `GET /api/v2/graphs/<id>[?version=n]` (a graph with local IDs, version, author, time and what cannot be drawn), `GET /api/v2/graphs/<id>/versions`.
- `graph_app_v2/`: the page: login, the list of graphs with a name filter (id, description, kind), the drawing (round 01 look), problems named beside the picture and a connection to a missing step drawn dashed to a marked "missing step".
- Demonstration: `python graph_proto_app.py --store files:/tmp/gs/v --user owner:secret --port 8801` and open http://127.0.0.1:8801/ (sample store: `python proto_checks/make_sample_store.py /tmp/gs/v --broken`); checks: `python proto_checks/cp5_check.py` (19 pass, files and database) and `node --test proto_checks/cp5.test.mjs` (4 pass).


**CP6 (VIEW, second part), 2026-11-20, commit 80bd08df.**
- Kinds at a glance: data = ellipse, processing = box, loop-controlling = hexagon, missing = dashed box; the kind is also in words on the panel and in a legend. A processing or loop-controlling step carries its marks under its name: trusted or UNTRUSTED (dashed border), lifecycle, and `code`.
- The backend (`steps_info`) takes the trust and lifecycle of a step from the toolbox (the shipped transforms and controllers, seeded in memory; a step not in the toolbox is untrusted and says why); a step holds code when a connection of the role `code` leads into it.
- The left panel shows the known values as labelled read-only fields and the full stored text below, built only with `createElement` and `textContent` (no `innerHTML` anywhere in the page); a step list below the graph list is reached with Tab and selected with Enter or Space.
- Settings menu (physics on/off, rounded or straight connections, reset to layers): opens under its button, closes with Escape or a click outside, applies at once and is remembered in this browser; defaults when it cannot be kept.
- Demonstration: `python proto_checks/make_sample_store.py /tmp/gs/v --broken --code`, then the viewer as in CP5; open `sample.code` (an untrusted code step with a name that looks like markup, a loop-controlling step, an instruction in a value) and `sample.broken`; checks: `python proto_checks/cp6_check.py` (7 pass), `node --test proto_checks/cp6.test.mjs` (8 pass).


**CP7 (VIEW, third part), 2026-11-20, commit 20574749.**
- Arrangement: one arrangement per graph, the same for everyone, kept apart from the graph versions (table `arrangements`, a record table of IF-302 added in the prototype). The viewer opens a graph with it when there is one (no physics when every step has a place), otherwise the graph settles by itself; "Reset to layers" shows the layered picture without changing the saved one; "Save this arrangement" (settings menu) saves the places for everyone; only the owner (the account made first) may, others are refused. A place for a step the graph does not have is ignored.
- History: the versions as a list, newest first, with who and when, the current one marked; click or Enter shows that version (read-only, the status line says so), and Previous and Next step through them; every version uses the saved arrangement.
- First look at speed: the backend answers the 54-step graph in about 9 ms (test client, files); the layout of 54 steps takes under 0.1 ms; the drawing and the physics in the browser are for the owner to judge.
- Demonstration: the viewer as before with `--broken --code` sample store; open `cp2.multi` (four versions by four authors), step back, drag steps, save the arrangement, reload; checks: `python proto_checks/cp7_check.py` (14 pass), `node --test proto_checks/cp7.test.mjs` (7 pass).


**CP8 (EDIT, first part), 2026-11-20, commit 897dc5b8.**
- `graph_rules_proto.py` (the core of GRAPHAPI.RULES, pulled forward): eight rules in one fixed order (step names, step kinds, connection ends, duplicate connections, adjacency, one writer, stop limit, cycle); every broken rule is named with its steps. `POST /api/v2/graphs/<id>/check` returns them for a graph that is not kept yet; `PUT /api/v2/graphs/<id>` keeps a change as a new version only when no rule is broken (otherwise 422 with the rules, nothing written), refuses a change made on an old version (409), and is for the owner only (403); the version names the account that kept it; keeping an unchanged graph makes no version.
- The editor (owner only; button "Edit this graph" on the current version): a working copy that is drawn at once with the steps staying where they are; add a step (name and kind), add a connection (from, to, role), remove a step with its connections, remove a connection; click a step: a form with its known fields (tool; value and parameters as JSON; stop after repetitions or seconds) and the other stored fields as JSON text, with the reason shown next to a value that does not fit; click a connection: role and name. After every change the rules are asked and named under the status line; "Keep the change" is disabled while one is broken. The side panel can be widened by dragging its corner (FB-1: the final layout is still open).
- Demonstration: open `cp2.multi`, "Edit this graph", add a step, connect `var.out` to `step.write` (a cycle): the rule is named and keeping is disabled; click that connection and remove it; change the tool of `step.write` and keep: version 5 by `owner`. Checks: `python proto_checks/cp8_check.py` (22 pass), `node --test proto_checks/cp8.test.mjs` (8 pass), and the whole flow run against the real backend with a stand-in browser.


**CP9 (EDIT, second part), 2026-11-20, commit 77a01ba3.**
- Live store and copy: `graph_proto_app.py --store <copy> --live <live store>` reads the copy and writes every change (keep, restore) to the live store; `GET /api/v2/status` tells whether the live store is reached and how many versions the copy is behind; `POST /api/v2/sync` (owner) brings the copy up to date with the whole move (all or nothing). Without `--live` the one store is both.
- Restore (FR-73): "Restore this version" (shown when an earlier version is open, owner only) saves its content as a new version; nothing is deleted; restoring what is current changes nothing.
- Undo and redo (FR-91): buttons and Ctrl+Z / Ctrl+Y in the editor over the working copies of the session; nothing is kept or recorded.
- Live store not reachable (FR-95): the status says so, "Edit this graph", "Restore" are disabled, and every change route answers 503 `store_unreachable` and writes nothing; looking at the copy still works; a store that cannot be reached is an answer, not a crash. Conflicts are checked against the live store (FR-72): a change made on a copy that is behind is refused.
- Demonstration: `python graph_store_move.py` a live folder into a copy folder, start the viewer with `--store <copy> --live <live>`; edit and keep (the copy stays behind), "Sync the copy now", restore an earlier version, stop the live store (remove its folder) and see the editor refused. Checks: `python proto_checks/cp9_check.py` (19 pass), `node --test proto_checks/cp9.test.mjs` (5 pass), the whole flow against the real backend with a stand-in browser.

## Findings
- The 15 converted graphs give 154 step records for 107 distinct local names: with scoped IDs the 13 shared names (4 with different content) no longer share a history.
- The new rule breaks existing tests that use plain IDs: `tests/test_graph_record_checks.py` (34 failures), `tests/acceptance/contract/test_if_301_v2_graph_tables.py` (28) and `tests/acceptance/test_graph_records.py` (14 errors), all with `unscoped_id`; `test_graph_model.py`, `test_graph_run.py`, `test_graph_tables.py` still pass. The amendment of A-92 / REQ-GTB-021 therefore has to rewrite those protected tests.
- A crash between the writes of the steps and of the header can still leave unused step versions; they are not part of any graph and `step_history` ignores them; a second save pins them again if the content is the same.
- The move reuses `copy_records` of the existing copy operation and adds the graph-level check; 16 graphs make 341 records.
- The page itself was not looked at in a browser by the agent (none in the session); the HTTP side was run for real with curl (login, 401 without it, list, the broken graph's problem).
- Context graphs are not stored anywhere yet (the context tables exist, no data, no `GraphModel` for them), so the list shows workflow graphs only; FR-48 asks for both kinds.
- A graph that stores code as text cannot be saved as a processing step with a field: the transform schema refuses extra fields (`additionalProperties: false`), so code lives in a connected data step with the role `code` on the connection (as decided in D-360); the VIEW requirements do not say how a code step is recognised, and the mark "changed since trusted" has no data yet (GRAPHAPI.CODE). Proposed for Plan: name the role `code` in IF-301 and record the trusted content with the trust.
- **Owner's remark after CP6 (2026-11-20):** for the editor the side panel will have to change, because the contents of steps are edited there and the current panel (a narrow column of read-only fields) does not look good for editing; the place, width and form of the editing panel are to be decided at CP8 (FB-1 in `rounds/02/validation.md`).
- A processing step added without a tool passes the eight rules and can be kept with an empty tool; only the form refuses an empty tool. Candidate for the rule set in Plan (a processing step needs a tool).
- The changes are drawn from the working copy only in the picture; the step list and the panel follow. The editing panel is the existing left column made resizable; FB-1 asks for something better for editing step contents and is still open.
- **Owner, after CP9:** "restoring version 4 brings me back to version 5": with a separate live store the restore lands in the live store while the viewer shows the copy, which looked like nothing had happened. The page now says where the new version is and that the copy shows it after the sync, the sync button is highlighted, the header names the graphs the copy is behind on, and a restore of content that is already current says so. **Decided by the owner (2026-11-20): a restore reaches the copy at once; the prototype does the same for a kept change.** `move_graph` copies the one graph (steps, connections and all versions, all or nothing, repeatable) right after the write; if the copy cannot take it (a different history) the change stays in the live store and the answer says the copy was not updated, naming the graph. The sync on command stays for changes made elsewhere.
- The arrangement record is not part of the move tables, so it stays on the store that is read; with a separate live store it is not synced. To decide in Plan where the arrangement lives (FR-74).
- The owner moved the review of the editing panel layout (FB-1) to the planning stage (2026-11-20).
- **CP4:** the rules and the refusal are one module (`graph_rules_proto.py`), used by the check route (editing), by keeping and by the run route, so the same broken rules come in the same order. Rule 7 ("session setting and stop limit") is defined here as: a data step that carries a session setting (`stop` or `session`), a step with more than one settings connection, a loop-controlling step without a valid stop limit; this is an assumption for Plan (ASM-3). A step input nobody supplies is an input of a processing or loop-controlling step from a data step that has no writer, no start value (`value`) and no value given with the run; settings and order connections are not inputs. **Finding:** all 14 converted skill graphs with inputs (for example `chat@1`: `input.text`) are refused without start values, which is correct (the question or text comes with the run), so the run must be started with its inputs; the page has a field for them. The run itself is the existing `GraphRunner` with stand-in steps that only note that they ran: the networkx-based runner, the order of steps and the equivalence are G-V4.GRAPHAPI.RUN, not in this run. The trust check of the runner is a stand-in here (everything trusted), because the code and trust handling is G-V4.GRAPHAPI.CODE.
- **Owner, after CP4:** a cycle added in the editor did not stop "Try a run": the run used the stored version, while the cycle was only in the working copy (a cycle cannot be kept). Fixed: from the editor the run uses the working copy, and the status line says so.
- **CP3:** the live store wins. What only the copy has (a version on top of the live history, a different history, a graph that exists only on the copy) is written to a JSON file in an aside folder first (fsync, then rename), named in the answer with the version numbers, and only then replaced; a header leaves the copy first and arrives last, so no graph is ever listed with missing steps, and a sync interrupted after 1, 3 or 6 writes finishes on the next run (leftover steps without a header are dropped, their content is in the aside file). The arrangement table is not synced (it lives on the store that is read). A live store that is unreachable at start or stop is a report, never a block. "Set aside" is a file, not a database table: Plan decides whether the owner needs a way to look at or restore from it. The older-version case of NFR-15 (conversion by a stated step) is not built: the prototype has one format. The check `cp3_check.py` uses files only; the database backend goes through the same `move_graph` calls (tested in `cp2_check.py`).
- **CP10:** the arrangement can be saved from the editor (positions of steps that are only in the working copy are ignored by the server until the change is kept); a copy of a step is a new step in the other graph with the same content, its own history from that version on, and no connections; today's eight rules cannot be broken by adding one isolated step, so the refusal "the copy would break a rule" is only shown with a stand-in rule in the check (candidate rules for Plan: a processing step needs a tool). Copying is offered in the viewing mode only (a working copy in progress is not copied); copying from an older version takes that version. The first-change check (NFR-18) needs a person: the editor has no help text on purpose.
- **Skills update (owner, 2026-11-20 evening):** the new rules of the workflow (a binding map of fixed and open requirements decided in Plan from the validated outcomes and accepted cases, `STAB-n` stability criteria in the TLS, a workflow configuration) change nothing in the code of the prototype; the cases the owner accepts in `validation.md` become the `accepted-cases.md` of Plan, so the Results the owner enters there are the input for the binding pass.
- Not examined: context graphs, a graph with a loop-controlling step (none among the 15), the `review` workflow (document form, migration is out of this run).

## Assumptions and choices the prototype made
| ID | Assumption or choice | Alternatives | Evidence |
|---|---|---|---|
| ASM-1 | the separator is the first `/`; a local ID may contain further slashes, a graph ID must not | a different separator such as `#` | storage already quotes IDs with a slash (`storage_files.py`) |
| ASM-3 | rule 7 covers a session setting on a data step, two settings connections into one step and a loop-controlling step without a stop limit | only the stop limit (as before CP4) | D-375 names "session setting and stop limit" without defining the setting in the new form |
| ASM-2 | a step is written as a new version only when its content differs | write every member at every save | `cp1_check.py`: unchanged save = no version |

## Prototype tests (run once here)
| Question (requirement or top-level item) | Command (repeatable) | Result (value, unit, uncertainty, hardware, date; pass / fail / not_run) |
|---|---|---|
| FR-63, FR-64: rules in one order, the session-setting rule, refusal before a run, missing inputs, the run route | `python proto_checks/cp4_check.py` | 25 pass, 2026-11-20, Fedora host |
| FR-64: what the owner is told when a run is tried | `node --test proto_checks/cp4.test.mjs` | 3 pass, 2026-11-20 |
| FR-93, NFR-15, NFR-16: lag per graph, sync with set-aside, interrupted syncs, start and stop, a set of files in another folder | `python proto_checks/cp3_check.py` | 20 pass, 2026-11-20, Fedora host |
| FR-93: what the owner is told | `node --test proto_checks/cp3.test.mjs` | 2 pass, 2026-11-20 |
| FR-74, FR-94, FR-95: the arrangement without a new version, copy of a step as an independent copy, refusals | `python proto_checks/cp10_check.py` | 20 pass, 2026-11-20, Fedora host |
| FR-94, FR-74: the copy form as text and inputs only, the messages | `node --test proto_checks/cp10.test.mjs` | 5 pass, 2026-11-20 |
| FR-73, FR-95, FR-93 (first form), FR-72 against the live store: restore, writes to the live store, the editor refused when it cannot be reached, a first sync | `python proto_checks/cp9_check.py` | 19 pass, 2026-11-20, Fedora host |
| FR-91, FR-95: undo and redo, what the owner is told | `node --test proto_checks/cp9.test.mjs` | 5 pass, 2026-11-20 |
| FR-63, FR-69, FR-70, FR-71, FR-72, NFR-19: the eight rules, the check route, keeping, conflict, owner only | `python proto_checks/cp8_check.py` | 22 pass, 2026-11-20, Fedora host |
| FR-68, FR-92: the working copy and the form | `node --test proto_checks/cp8.test.mjs` | 8 pass, 2026-11-20 |
| FR-52, FR-55, NFR-11: the arrangement, the history list, a first look at speed | `python proto_checks/cp7_check.py`, `node --test proto_checks/cp7.test.mjs` | 14 and 7 pass, 2026-11-20, Fedora host |
| FR-50, FR-54: kinds, trust and lifecycle, code mark, text-only display; FR-51, FR-53, NFR-13, NFR-14: fields, remembered settings, nothing from outside, keyboard | `python proto_checks/cp6_check.py`, `node --test proto_checks/cp6.test.mjs` | 7 and 8 pass, 2026-11-20, Fedora host |
| FR-48, FR-49, NFR-12: login, list from files and database, graph and versions, problems named | `python proto_checks/cp5_check.py`, `node --test proto_checks/cp5.test.mjs` | 19 and 4 pass, 2026-11-20, Fedora host, PostgreSQL 16 under podman |
| FR-58, FR-59: the same answers in files and database; the whole store moves both ways, repeatably, all or nothing | `python proto_checks/cp2_check.py` | 9 of 9 pass, 2026-11-20, Fedora host, PostgreSQL 16 under podman |
| FR-57, FR-60, NFR-16: scoped storage, versions, refused and interrupted saves | `python proto_checks/cp1_check.py files` and `postgres` | 10 of 10 pass on each backend, 2026-11-20, Fedora host, PostgreSQL 16 under podman |

## Carry-over (the developer decides)
| Item (requirement, spec text, decision, code, scenario) | Where | Decision: adopt / adapt / drop / stand-in | Reason |
|---|---|---|---|

Decided by: –

## Proposed TLS changes
- –

## Effect on the TLS
–
