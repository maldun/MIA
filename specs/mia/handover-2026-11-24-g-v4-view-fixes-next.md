# Handover: G-V4.VIEW Verify done (not yet verified); next Implement fixes V-1 … V-13 (2026-11-24)

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v4-view`, branch `goal/v4.view` (pushed, tracks `origin/goal/v4.view`); the Verify work ends at `43605cd2`. Start in a **fresh session**: read `CLAUDE.md`, this file, `specs/mia/goals/G-V4.VIEW/verification-report.md` (the findings V-1 to V-15 and the owner's decisions), `goal.md` and `plan.md`. Then load `dev-workflow`, `implement-phase`, `agent-app` and `agent-app-implement`. VIEW has no model step, so the agent additions do not apply. This file supersedes `handover-2026-11-23-g-v4-view-verify-findings.md`.

## State
| Item | State | Where |
|---|---|---|
| Implement | T-01 to T-12 done; F-1 closed by A-175, F-2 kept by D-500 | `specs/mia/goals/G-V4.VIEW/implementation-log.md` |
| Verify | report drafted by an independent reviewer. Proposal: not yet verified. Verdict box empty | `specs/mia/goals/G-V4.VIEW/verification-report.md` (`750b3034`, `9de81f4e`) |
| Owner's decisions on the findings | D-501 (all as recommended) | `specs/mia/review-log.md` |
| Phases table | Verify `in progress` | `goal.md` |
| V-15 (offline image build) | closed 2026-11-24. The owner built `mia-view-check`; `tests/test_delivery_on_stack.py` is OK (5 tests). **Keep the tag until the merge**: without it the cached pip layer can go, and the offline build fails again | report, D-501 (4) |
| Reproduction scripts | `specs/mia/goals/G-V4.VIEW/verify-repro/repro_f1.py` (V-1), `repro_f2.py` (V-9), `repro_f3.py` (V-2). Run: `<venv python> <script> <checkout root>`; each starts the browser checks' server helper and prints what it sees | – |

## What to do (Implement, D-501)
Reopen each task named below. For every finding:
1. Write a failing test first and log the finding in `implementation-log.md` (a new section "Fixes after Verify").
2. Fix the code.
3. Commit once per reopened task, naming the V-number(s), e.g. `fix: T-08 V-1, V-8 …`.

The protected checks stay unchanged (D-501 (1)). New tests go into `tests/js/` or `tests/test_graph_api_v2.py`. They are not protected.

| Finding | Task | What is wrong, and the fix | Test first |
|---|---|---|---|
| V-1 | T-08 | `graph_app/viewer.js:86`: `list.children.filter` throws in Firefox (an `HTMLCollection` has no `filter`), so ArrowUp and ArrowDown in the graph list do nothing. Fix: `Array.from(list.children)` | a unit test whose fake `children` is not an Array. The fake DOM (`tests/js/fake-dom.mjs:45`) returns an Array, which hid this. Afterwards `repro_f1.py` must show the focus move and no page error |
| V-8 | T-08 | `viewer.js:107-114`: a 401 while a graph is open clears only the list, canvas and status. Fix: also clear the problem list, step list, left column and history; Previous and Next must not send `GET /graphs/null?...` | a unit test: open cp2.multi, select a step, open the history, then the mock answers 401 |
| V-10 | T-07 | `viewer.js:204`: the store entry is written once in `start()`. Fix: after a 503 it says the store does not answer; after a later success, reachable again | a unit test with the mock's `unreachable` switched during a session |
| V-2 | T-10 | `graph_app/drawing.js:117`: on a light/dark change the listener calls `drawing.show(drawing.data, …)` and the graph settles again, so dropped places are lost. Fix: re-colour the shown nodes and edges (`nodes.update` / `setOptions`) without a new `show` | a unit test with a recording vis stand-in: after a drop and a scheme change, no new `setData`, and the dropped place is kept. Afterwards `repro_f3.py` must show x unchanged after the switch |
| V-9 | T-10 | `graph_app/app.js:10`: `localStorage` is read outside any try. With cookies and site data blocked it throws `SecurityError` and the page stays blank. Fix: read it in a try and hand in `null` on failure; the viewer works with its defaults (REQ-GA-035) | a unit test of the entry, or of a small `pageStorage()` helper with a throwing getter. Afterwards `repro_f2.py` must draw the 8 areas |
| V-5 | T-04 | `graph_api_v2.py:240`: only "`nodes` and `edges` are lists" is checked, so a step or connection that is not an object with a text `id` crashes `derive` (`:133`) with a 500. Fix: 422 `invalid` with detail `graph` for the save and the check route, and nothing written (REQ-API-048) | `tests/test_graph_api_v2.py`: a connection without `id`, an `id` that is an object, a step that is a string |
| V-4 | T-06 | `graph_api_v2.py:172-183`: the play-back of editor entries checks only `after`; `before` is stored as sent. Fix: compare each entry's `before` with the value in the version it is played on; a mismatch is 422 `changes_do_not_match`, nothing written (REQ-API-038) | `tests/test_graph_api_v2.py`: a `change_step` with a false `before` and the right `after` gives 422 and still the same number of versions |
| V-13 | T-12 | `specs/mia/architecture.sysml`, `part def GraphApp` (line 350 ff.): `pageFrame`, `graphList`, `detailsColumn` and `historyList` are still `proposed`; `graphView` is `partly` and names `graph-view.js`. Fix: set the statuses to `built` and name the modules (`viewer.js`, `drawing.js`, `api.js`, `adapter.js`, `step-marks.js`, `problems.js`, `panel.js`, `history.js`, `arrangement.js`, `settings.js`, `list-filter.js`, `store-note.js`, `app.js`, `index.html`, `graph.css`, `tokens.css`, `vendor`) | `bash tools/check_sysml.sh` 0/0 and `python3 -I tools/check_sysml_model.py .` OK |

**Not in Implement:**
- V-3 (a PostgreSQL connection is never reopened; MIA does not start while the database is down) goes to G-V4.GRAPHSTORE.TRANSFER. Add one line about it to TRANSFER's next handover or its goal record, in the session that works on TRANSFER (another line of work: do not edit it from here).
- V-6, V-7, V-11, V-12 and V-14 are accepted. V-7, V-11 and the V-14 items are written into the specification at Commit.

**Stop and report (CLAUDE.md)** if a fix needs a change of a protected test, a new interface field, or a file outside these tasks, apart from `architecture.sysml` for V-13.

## Checks after the fixes (the implementer's runs: feedback, not verification)
- The VIEW checks:
  - `tests/acceptance/test_view_backend.py`
  - `tests/acceptance/contract/test_if_104_v2_graph_api.py` (33, PostgreSQL under podman)
  - `tests/acceptance/test_graph_view_files.py`
  - `node --test tests/acceptance/graph_view_page.test.mjs`
  - `tests/acceptance/test_graph_view_browser.py`, three runs in a row
- `node --test "tests/js/*.test.mjs"` (225 before the fixes).
- The unit suite `<venv python> -m unittest discover -s tests`. Before the fixes: 2588 tests, 4 skipped, 2 expected failures, and green since V-15. `test_delivery_on_stack` now runs here; it skips only without a model server.
- Every acceptance script, one by one (not in parallel: `mia.log`). Known reds outside VIEW: `test_decide_guard.py` and `test_judge_calibration.py` (G-V3.REPORT F-3).
- The three reproduction scripts.
- Traceability: the same 549 ERROR lines as at the plan gate, none new. Goal check: the same 82 errors. Model check OK.

## Next
1. Implement the fixes above (this session), log them, and update the Phases row of Implement ("fixes after Verify, D-501").
2. Verify again in a **fresh, independent session**:
   - the automated checks in full;
   - the protected diff (still only A-175 since `b961c573`);
   - the three reproduction scripts;
   - a review of the fix commits only;
   - a short section "Re-verify" appended to `verification-report.md`;
   - the owner ticks the verdict box. The close look at the page (the owner's rule) follows the list in the report's notes.
3. Then Commit (merge into `goal/v4`; move requirements, checks and TR-VIEW into the node files; Witnesses of AC-009 to AC-016 and AC-035; V-7, V-11 and V-14 into the specification), Deploy (SMOKE-VIEW-001 and 002; the owner's look with `store: database`), and Validate as the goal record says.

Shared Ollama: VIEW's checks call no model. `test_delivery_on_stack` asks the model server only whether it answers.

Next free numbers: D-502 (VIEW's block D-500 to D-519), A-176, TC-API-026, TR-VIEW-022, TC-GA-040, TC-OPR-012, SMOKE-VIEW-003. REQ-API for VIEW stays at or below 059.
