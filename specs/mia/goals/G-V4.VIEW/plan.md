# Plan: G-V4.VIEW (graph viewer: pull from the data source and draw)

**Goal:** `specs/mia/goals/G-V4.VIEW/goal.md`   **Requirements:** `requirements.md` of this folder (70 approved, D-437, D-438; Track A 37, Track B 33)   **Test spec:** `test-spec.md`, `test-requirements.md` of this folder (approved, D-441, D-442)   **Interfaces:** IF-104 v2 (A-171, `contracts/IF-104-graph-api.md`), IF-302 v15 (A-172), page interface note (D-443)   **Status:** Draft for the owner's plan gate (2026-11-23; questionnaire D-446)

Line of work `goal/v4.view` (worktree `../MIA-goal-v4-view`), merges into `goal/v4`; supervised. Two tracks inside one goal (D-430 (2), D-432): Track A (interface and backend, T-01 to T-06) first, Track B (page, T-07 to T-12) after it or beside it in its own session. No model step, no prompt, no eval suite. New dev dependency: Playwright 1.64.1 with Firefox (approved D-430, installed in `mia312`, `requirements-browser.txt`, not in the image). New module: `graph_api_v2.py` (the v2 blueprint in N-2.1, D-430 (8)).

## Deployment and feedback (M51)
- Environment: the owner's host, the compose stack with Caddy (`/graph/` to the graph app). Deploy runs SMOKE-VIEW-001 (`tests/smoke/smoke_view_image.py`, writes nothing, TR-VIEW-016) and SMOKE-VIEW-002 (`tests/smoke/smoke_view_open_time.py`, measured, no bound, TR-VIEW-017).
- Feedback slices: after T-06 the owner can call the v2 routes on the branch (files and database); after T-09 the page shows the list and the picture against the JS mock (`node`-served stand-in is not provided; the owner looks at it after T-12 in Firefox against the real backend).
- Living prototype (M46): `prototype/graphview` and `prototype/g-v4`; reuse map: R6 (page helpers, keep with tests), R11 (fixtures, done in `tests/fixtures/graph_view/`).
- Source of each fact (P26): `requirements.md` of this folder → the generated block of `specs/mia/architecture.sysml` (D-439).

## Before the first task
1. (done, D-446 (1)) RULES brought into this branch: `goal/v4` merged into `goal/v4.view` (`b961c573`); the conflict in `specs/mia/architecture.sysml` resolved by keeping both sides, the model regenerated unchanged, `check_sysml.sh` 0/0, `check_sysml_model.py` OK.
2. (done) Red state on the merged branch, 2026-11-23: the same counts as at the red commit (section below); TC-API-025 now fails on the missing provider, no longer on RULES.
3. Tick the plan gate.

## Interface fixed by the red tests
- `graph_api_v2.create_app(backend, accounts_store, store, allowed_origins)` returns a Flask app holding the v2 blueprint under `/api/v2` beside v1 (REQ-API-030); `web_app.py` registers the same blueprint on its own app with its session.
- Store setting: config key `store`, `files` (default) or `database` with `MIA_DATABASE_URL`; any other value stops the start naming `store` and the value (REQ-API-019, 020, D-440 (4)).
- Record tables (IF-302 v15): `arrangements`, `graph_changes` in `record_tables.py` (A-172).
- Page: `graph_app/viewer.js` `createViewer(...)`, `api.js` `httpApi(...)`, `drawing.js` `visDrawing(...)`, hooks and test hook as in `page-interface-note.md`; the stand-ins `tests/helpers/graph_view_page.mjs`, `graph_view_server.py`, `graph_view_data.py`.

## State at the red commit (`82327296`, tag `plan-baseline-g-v4-view`)
Red: `tests/acceptance/test_view_backend.py` (12), `test_graph_view_files.py` (2), `test_graph_view_browser.py` (7), `graph_view_page.test.mjs` (14), the real side of the IF-104 v2 suite (22: files and postgres) and of TC-IF-302-13, 14. Green and to be kept green: the mock side of both suites (11 + 11 JS), the IF-104 v1 suites. TC-API-025 stays red until RULES is in this branch (TR-VIEW-014).

Regression set after every task: the unit suite (`<venv> -m unittest discover -s tests`), every acceptance script one by one (not in parallel: `mia.log`), `node --test "tests/js/*.test.mjs"` and `node --test tests/acceptance/graph_view_page.test.mjs`; green except the VIEW checks of later tasks (the unit suite had no known red on the merged branch, 2026-11-23). In particular the IF-104 v1 suites, the IF-302 v1 to v14 cases, the CORE and RULES checks, `tests/test_graph_api.py`.

Each task's "Done when" lists the defect of TR-VIEW-021 that must make each of its new checks fail once (run, seen red, reverted, logged in `implementation-log.md`).

## Tasks
| Task | Track | Implements | Green when | Depends on |
|---|---|---|---|---|
| T-01 Record tables | A | REQ-RTB-010, 011 | TC-IF-302-13, 14 (real side) | step 1 |
| T-02 Store setting, provider, access, image | A | REQ-API-018 to 022, 030, 045, 047, 050; REQ-OPR-011 | TC-API-018, 019, 020, 024; TC-OPR-011; TC-IF-104-26, 27 | step 1 |
| T-03 Read routes | A | REQ-API-023 to 029, 043, 049 (read side) | TC-IF-104-17, 18, 19 | T-02 |
| T-04 Save as a new version, refusals | A | REQ-API-032 to 037, 046, 048 | TC-IF-104-20, 22; TC-API-021 | T-01, T-03 |
| T-05 Check, restore, arrangement save | A | REQ-API-031, 041, 044 | TC-IF-104-23, 24, 25; TC-API-025 | T-04 |
| T-06 Record of changes | A | REQ-API-038, 051, 039, 040, 042 | TC-IF-104-21; TC-API-022, 023 | T-04 |
| T-07 Tokens, frame, status | B | REQ-GA-012 to 018 (node and file side) | TC-GA-021, 031, 032 | – (JS mock) |
| T-08 List and opening | B | REQ-GA-019 to 023 | TC-GA-017 to 020 | T-07 |
| T-09 The picture | B | REQ-GA-024 to 029 (node side) | TC-GA-022 to 025 | T-08 |
| T-10 Arrangement and settings | B | REQ-GA-030 to 035 (node side) | TC-GA-026 to 028 | T-09 |
| T-11 Left column and history | B | REQ-GA-036, 044, 037 to 040 | TC-GA-029, 030 | T-09 |
| T-12 The page in Firefox | B | REQ-GA-041 to 043; browser side of REQ-GA-012, 013, 016, 029, 031, 032 | TC-GA-033 to 039 | T-03, T-10, T-11 |

Twelve tasks are above the size signal of about eight; the owner kept one goal and cut it into the two tracks instead (D-432), six tasks each. Implement runs Track A, then Track B, in one session line on `goal/v4.view` (D-446 (3)).

### T-01: Record tables
- Implements: REQ-RTB-010, REQ-RTB-011
- Tests to turn green: the real side of TC-IF-302-13, 14 (`tests/acceptance/contract/test_if_302_record_tables.py`)
- Touches: `record_tables.py` (tables `arrangements`, `graph_changes` as IF-302 v15 says; `graph_changes` written once, D-435); unit tests `tests/test_record_tables_view.py`
- Must not touch: protected material (incl. `tests/fixtures/graph_view/`, deny rule D-446 (2)); `storage.py` and the backends (no IF-102 change, D-435); `graph_tables.py`
- Done when: both cases green on files and PostgreSQL; the IF-302 v1 to v14 cases unchanged and green. (The installed contract cases are not in TR-VIEW-021; the defect "a second write of the same graph version replaces the record" is still run once against TC-IF-302-14 and logged.)

### T-02: Store setting, provider, access, image
- Implements: REQ-API-018 to 022, REQ-API-030, REQ-API-045, REQ-API-047, REQ-API-050, REQ-OPR-011
- Tests to turn green: TC-API-018, 019, 020, 024, TC-OPR-011 (`tests/acceptance/test_view_backend.py`); the real side of TC-IF-104-26, 27
- Touches: new `graph_api_v2.py` (blueprint, `create_app`, routes `me` and `store`, the session and origin checks for every v2 route, 503 `store_unreachable`; the other routes answer 501 until their task); `web_app.py` (the store setting, the backend it chooses, the blueprint registered under the existing session); `config.py` if the setting is read there; `deploy/Containerfile` (install `requirements-db.txt` in the release stage); `deploy/README.md` (the `store` key)
- Must not touch: protected material; `graph_api.py` (v1 unchanged, REQ-API-030); `deploy/.env`
- Done when: the listed tests green; each new check fails once on its defect: TC-API-018 the default changed to `database`; TC-API-019 an unknown value falling back to `files`; TC-API-020 the v2 blueprint on an app of its own (no shared session); TC-API-024 the origin check removed; TC-OPR-011 the `requirements-db.txt` line moved to the builder stage
- Notes: the live/copy fields of the store route are fixed values until TRANSFER (REQ-API-022, D-460).

### T-03: Read routes
- Implements: REQ-API-023 to REQ-API-029, REQ-API-043, REQ-API-049 (read side)
- Tests to turn green: the real side of TC-IF-104-17, 18, 19; the read part of TC-IF-104-24, 25 (their write parts in T-05)
- Touches: `graph_api_v2.py` (list, graph by version, versions, arrangement read, the problems that cannot be drawn, kind and marks per step, text as stored; `changed_since_trusted` fixed `false` until CODE, REQ-API-028); unit tests
- Reuses: `graph_model.py` and `graph_tables.py` of CORE for reading; prototype R6 `adapter.js` logic only as a reference for the problem list
- Must not touch: protected material; `graph_model.py` save path (T-04)
- Done when: the listed cases green on mock, files and postgres (TR-VIEW-001: each listed three times in the report)

### T-04: Save as a new version, refusals
- Implements: REQ-API-032 to REQ-API-037, REQ-API-046, REQ-API-048
- Tests to turn green: the real side of TC-IF-104-20, 22; TC-API-021
- Touches: `graph_api_v2.py` (save route: new version, unchanged writes nothing, `conflict` on a stale version, `rules_broken` with the IF-301 v4 report, `refused` on a record check with `schema_break`, owner only, malformed input; the derived record of changes written with the version)
- Must not touch: protected material; `graph_rule_set.py` (RULES); `graph_model.py` beyond calling its save
- Depends on: T-01, T-03; RULES in this branch (step 1)
- Done when: the listed tests green; TC-API-021 fails once with the record check skipped (the graph with `colour` stored)

### T-05: Check, restore, arrangement save
- Implements: REQ-API-031, REQ-API-041, REQ-API-044
- Tests to turn green: the real side of TC-IF-104-23, 24, 25; TC-API-025
- Touches: `graph_api_v2.py` (check route for the owner, restore as a new version with a `restore` record, arrangement save into `arrangements`)
- Must not touch: protected material; `graph_rule_set.py`
- Depends on: T-04
- Done when: the listed tests green; TC-API-025 fails once with the check route on CORE's `check_graph` instead of `rule_report`

### T-06: Record of changes
- Implements: REQ-API-038, REQ-API-051, REQ-API-039, REQ-API-040, REQ-API-042
- Tests to turn green: the real side of TC-IF-104-21; TC-API-022, 023
- Touches: `graph_api_v2.py` (editor entries checked against the graph, `changes_do_not_match`, written once, a version kept with `logged` false when its record is lost, the changes route with `before_the_record`)
- Depends on: T-04
- Done when: every Track A check green (TC-API-025 included); TC-API-022 fails once with the record written twice; TC-API-023 fails once with the save refused when the record write fails

### T-07: Tokens, frame, status
- Implements: REQ-GA-012 to REQ-GA-018 (node and file side)
- Tests to turn green: TC-GA-021 (`tests/acceptance/graph_view_page.test.mjs`), TC-GA-031, 032 (`test_graph_view_files.py`)
- Touches: `graph_app/tokens.css` (byte copy of `templates/static/chat/tokens.css`), `graph_app/graph.css` (only `var(--…)`), `graph_app/index.html`, `graph_app/viewer.js` (frame, areas, empty areas of later subgoals, status bar, store entry); helpers from R6 (`store-note.js`) with unit tests in `tests/js/`
- Must not touch: protected material; `templates/static/chat/tokens.css`
- Done when: the listed tests green; TC-GA-021 fails once with the store entry hard-coded `database`; TC-GA-031 with one byte changed in the copy; TC-GA-032 with a planted `color: #fff` in `graph.css`

### T-08: List and opening
- Implements: REQ-GA-019 to REQ-GA-023
- Tests to turn green: TC-GA-017 to 020
- Touches: `graph_app/viewer.js`, `graph_app/api.js`; R6 `list-filter.js` with its unit tests
- Done when: the listed tests green; defects: TC-GA-017 opening draws version 1 instead of the current; TC-GA-018 a filter that ignores the description; TC-GA-019 the empty list drawn on 401 without the login link; TC-GA-020 the picture cleared on 503

### T-09: The picture
- Implements: REQ-GA-024 to REQ-GA-029 (node side)
- Tests to turn green: TC-GA-022 to 025
- Touches: `graph_app/viewer.js`; R6 `adapter.js`, `step-marks.js`, `problems.js` with their unit tests
- Done when: the listed tests green; defects: TC-GA-022 arrows left out; TC-GA-023 the connection to a missing step dropped; TC-GA-024 a mark on every step; TC-GA-025 a graph of another kind drawn with workflow shapes

### T-10: Arrangement and settings
- Implements: REQ-GA-030 to REQ-GA-035 (node side)
- Tests to turn green: TC-GA-026 to 028
- Touches: `graph_app/viewer.js`; R6 `arrangement.js`, `settings.js` with their unit tests
- Done when: the listed tests green; defects: TC-GA-026 the saved arrangement ignored; TC-GA-027 every step on one level; TC-GA-028 settings not written to storage

### T-11: Left column and history
- Implements: REQ-GA-036, REQ-GA-044, REQ-GA-037 to REQ-GA-040
- Tests to turn green: TC-GA-029, 030
- Touches: `graph_app/viewer.js`; R6 `panel.js`, `history.js` with their unit tests
- Done when: the listed tests green; defects: TC-GA-029 `changed_since_trusted` left out of the fields; TC-GA-030 history oldest first

### T-12: The page in Firefox
- Implements: REQ-GA-041 to REQ-GA-043; the browser side of REQ-GA-012, 013, 016, 029, 031, 032
- Tests to turn green: TC-GA-033 to 039 (`tests/acceptance/test_graph_view_browser.py`), so every VIEW check is green
- Touches: `graph_app/drawing.js` (vis-network, fixed seed and solver, `onStabilized`, the test hook), `graph_app/app.js` (entry as the note says), `graph_app/index.html`; removes the old `graph_app/graph-view.js` and its test `tests/js/graph-view.test.mjs` (not protected; its "physics off" line is D-436's stray text)
- Depends on: T-03 (the server helper runs the real backend), T-10, T-11
- Done when: every VIEW check green and the regression set holds; defects: TC-GA-033 a button in an empty area; TC-GA-034 a fixed light background in dark; TC-GA-035 a link around the stored name; TC-GA-036 a random seed; TC-GA-037 a page that saves the arrangement on drop; TC-GA-038 step list entries without keyboard focus; TC-GA-039 a planted request to `https://example.invalid/x.css`
- Demonstrator: the owner opens `/graph/` on the branch in Firefox (files, then `store: database`), the end of Implement

## Binding map (accepted cases of G-V4, filled into the Witnesses column at the merge)
| Case | Outcome | Witnessed by | Task |
|---|---|---|---|
| AC-009 | FR-48 | TC-GA-017, TC-GA-018; TC-IF-104-17 on files and postgres | T-03, T-08 |
| AC-010 | FR-49 | TC-GA-023; TC-IF-104-18 | T-03, T-09 |
| AC-011 | FR-50 | TC-GA-024; TC-IF-104-19 | T-03, T-09 |
| AC-012 | FR-54 | TC-GA-035; TC-IF-104-19 | T-03, T-12 |
| AC-013 | FR-51 | TC-GA-029 | T-11 |
| AC-014 | FR-52 | TC-GA-026, TC-GA-027, TC-GA-037; TC-IF-104-25 (save step: backend only; the page's save is EDIT's, D-425 B) | T-05, T-10, T-12 |
| AC-015 | FR-53 | TC-GA-028, TC-GA-037 | T-10, T-12 |
| AC-016 | FR-55 | TC-GA-030 | T-11 |
| AC-035 | NFR-12 | TC-GA-019; TC-IF-104-27 | T-02, T-08 |

## At the merge (Commit phase, not a task)
- Move the 70 requirements into the node files (REQ-API into N-2.1, REQ-RTB into N-3.3, REQ-OPR-011 into N-4.2, REQ-GA into N-5), the checks, scenarios and smoke rows into the node test specs, TR-VIEW-001 to 021 into `specs/mia/test-requirements.md` through an owner-run script; regenerate the model.
- Fill the Witnesses column of the cases above in `specs/mia/goals/G-V4/accepted-cases.md`.
- Notes for other subgoals: TRANSFER (carries `arrangements` and `graph_changes`; makes the store route's live/copy fields real), EDIT (the page side of the write routes, the arrangement save button), CODE (`changed_since_trusted` real).

## Plan gate
- [ ] Plan package approved by the owner: goal, high-level spec, requirements, checks and test code (red tests `82327296`, tag `plan-baseline-g-v4-view`), this plan. Date:
