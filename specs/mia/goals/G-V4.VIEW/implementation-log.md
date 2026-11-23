# Implementation log: G-V4.VIEW

Goal: G-V4.VIEW   Line of work: goal/v4.view   Supervision: supervised (plan gate ticked by the owner, D-447)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Record tables | done | see `git log` ("feat: T-01 record tables arrangements and graph_changes") | TC-IF-302-13, 14 (mock and real); `tests/test_record_tables_view.py` (6 unit tests) | `tests/test_record_tables.py`: the expected table set gets the two new tables (A-172) |
| T-02 Store setting, provider, access, image | done | see `git log` ("feat: T-02 store setting, v2 provider, access and image") | TC-API-019, 024, TC-OPR-011; TC-IF-104-26 (mock, files, postgres); `tests/test_graph_api_v2.py` (7 unit tests) | TC-API-018, 020 and TC-IF-104-27 wait for T-03 (they need the list, read and versions routes) |
| T-03 Read routes | done | see `git log` ("feat: T-03 read routes") | TC-IF-104-17, 18, 19, 26, 27 (mock, files, postgres); read parts of TC-IF-104-24, 25; TC-API-018, 020; `tests/test_graph_api_v2.py` (10 unit tests) | the write parts of TC-IF-104-24, 25 stop at 501 `not_built` (T-05) |
| T-04 Save as a new version, refusals | done | see `git log` ("feat: T-04 save as a new version, refusals") | TC-IF-104-22 (mock, files, postgres); the save parts of TC-IF-104-20 and TC-API-021; `tests/test_graph_api_v2.py` (18 unit tests) | TC-IF-104-20 stops at the changes route (T-06), TC-API-021 at the restore (T-05) |
| T-05 Check, restore, arrangement save | done | see `git log` ("feat: T-05 check, restore, arrangement save") | TC-IF-104-23, 25 (mock, files, postgres); the restore part of TC-IF-104-24; TC-API-021 (T-04's), TC-API-025; `tests/test_graph_api_v2.py` (23 unit tests) | TC-IF-104-24 stops at the changes route (T-06) |
| T-06 Record of changes | done | see `git log` ("feat: T-06 record of changes") | every Track A check: IF-104 v2 suite 33/33 (mock, files, postgres), `test_view_backend.py` 9/9 (TC-API-018 to 025, TC-OPR-011); `tests/test_graph_api_v2.py` (28 unit tests) | Track A complete |
| T-07 Tokens, frame, status | done | see `git log` ("feat: T-07 tokens, frame, status") | TC-GA-021, TC-GA-031, 032; `tests/js/store-note.test.mjs` (2), `tests/js/graph-viewer-frame.test.mjs` (3) | Track B started; the list is text only until T-08, the picture empty until T-09 |
| T-08 List and opening | done | see `git log` ("feat: T-08 list and opening") | TC-GA-018, 019, 020 (TC-GA-021 stays green); `tests/js/list-filter.test.mjs` (3), `tests/js/graph-viewer-list.test.mjs` (5) | TC-GA-017 stops at `selectStep` (the left column, T-11) |
| T-09 The picture | done | see `git log` ("feat: T-09 the picture") | TC-GA-022, 023, 024, 025; `tests/js/graph-picture.test.mjs` (8) | finding F-1: TC-GA-025 cannot see its planned defect (owner decision) |
| T-10 Arrangement and settings | done | see `git log` ("feat: T-10 arrangement and settings") | TC-GA-026, 027, 028; `tests/js/graph-settings.test.mjs` (3), `graph-arrangement.test.mjs` (4), `graph-viewer-arrange.test.mjs` (3) | the drawing applies seed, solver and drag in T-12 |
| T-11 Left column and history | done | see `git log` ("feat: T-11 left column and history") | TC-GA-029, 030, and TC-GA-017 (waiting since T-08): all 15 page node checks green; `tests/js/graph-panel.test.mjs` (5), `graph-viewer-history.test.mjs` (3) | the browser side follows in T-12 |
| T-12 The page in Firefox | done | see `git log` ("feat: T-12 the page in Firefox") | TC-GA-033 to 039 (`test_graph_view_browser.py` 7/7, three runs); every VIEW check green | `graph-view.js` kept (finding F-2, protected smoke check); A-175 still staged |

## T-01: Record tables

**What was done**
- `record_tables.py`: tables `arrangements` and `graph_changes` (versioned, not deletable), their required fields, and the checks IF-302 v15 states: `graph` a text that is not empty; `positions` a mapping from a text step ID to exactly `{x, y}`, both integers (no bool, no float); `version` and `from_version` integers of at least 1; `kind` one of `editor`, `derived`, `restore`; `entries` a list, kept as given. Written once is the graph API's check (D-435, T-06), not the table's.
- `tests/test_record_tables_view.py` written first and seen red (6 errors): zero and negative places, a place with a third key, a step ID that is not text, both tables versioned and kept, entries kept as given, a restore from an older version.
- `tests/test_record_tables.py` (not protected): the exact set of tables in TC-RTB-001 gets `arrangements` and `graph_changes`, the change A-172 approved.
- No change to `architecture.sysml`: `record_tables.py` is already a module of `persistence.graphRecords` (D-439).

**Tests green (my runs, feedback only):** `tests/acceptance/contract/test_if_302_record_tables.py` 28/28; `tests/test_record_tables_view.py` 6/6; `tests/test_record_tables.py` OK.

**Regression set (2026-11-23, sequential):** unit suite `discover -s tests` exit 0 (2560 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 186 pass. Acceptance scripts: all OK except the VIEW checks of later tasks (`test_view_backend.py` 12, `test_graph_view_files.py` 2, `test_graph_view_browser.py` 7, `graph_view_page.test.mjs` 14, the real side of `test_if_104_v2_graph_api.py` 22) and the known reds `test_decide_guard.py`, `test_judge_calibration.py` (G-V3.REPORT F-3: `behaviour.FUNCTIONS` missing; also red on `goal/v4`).

**Deliberate defects (not required by TR-VIEW-021 for contract cases; run once, then restored):**

| Defect in `record_tables.py` | Check | Result |
|---|---|---|
| `before_the_record` accepted as a stored kind | TC-IF-302-14 | fails |
| a place's coordinates accepted as any number (float, bool) | TC-IF-302-13 | fails |

**Deviation:** `plan.md` T-01 names the defect "a second write of the same graph version replaces the record" against TC-IF-302-14. That case checks the table definition and validation only; written once is checked by the graph API before the write (D-435) and shown by TC-API-022 in T-06. So that defect belongs to T-06 (where the plan already lists "the record written twice"), and the kind defect above was run instead. No plan change needed; for Verify to note.

**Open questions for Verify:** none.

## T-02: Store setting, provider, access, image

**What was done**
- New `graph_api_v2.py` (N-2.1): `store_setting(cfg)` (files without a setting; anything but `files` or `database` raises, naming `"store"` and the value, REQ-API-019, 020); `reachable(backend)`; `create_graph_v2_blueprint(backend, store, is_owner, allowed_origins)` with one guard for every v2 route in this order: a change needs an allowed `Origin` (403 `bad_origin`, before the session, also without one), a session (401 `unauthenticated`, also when the accounts switch is off), the owner for a change (403 `not_owner`), a store that answers (503 `store_unreachable`, except `me` and `store`); routes `me` and `store` (fixed live/copy fields, REQ-API-022); the other nine routes answer 501 `not_built` until T-03 to T-06. `create_app(backend, accounts_store, store, allowed_origins)`: a Flask app with the IF-101 account routes, the existing guard (`accounts_api.install_guard`) and the blueprint; the owner is the first account.
- `web_app.py`: the store setting is read right after the configuration is loaded, so a wrong value stops the start before anything else; the graph backend is the data folder's `FileBackend` (shared with the votes store) or `PostgresBackend(MIA_DATABASE_URL)`; the v2 blueprint is registered beside v1 under the same session.
- `deploy/Containerfile`: `requirements-db.txt` copied and installed in the (only) release stage. `deploy/compose.yaml`: the comment on `MIA_DATABASE_URL` says who reads it now.
- `setup_cfg.example.json`, `deploy/setup_cfg.compose.json`: `"store": "files"`; `README.md`: the option described (needed by `test_config.py` and `test_deploy.py`; the plan named `deploy/README.md`, the options are described in the top-level `README.md`).
- Unit tests `tests/test_graph_api_v2.py` (7), written after the first draft of the module, not before it (a deviation from test-first in this task): setting values, `create_app` with a wrong name, a change without Origin, a change by ben, a store that is down, the blueprint without the guard.

**Tests green (my runs, feedback only):** `test_view_backend.py` TC-API-019, TC-API-024, TC-OPR-011; IF-104 v2 suite TC-IF-104-26 on mock, files and postgres; `tests/test_graph_api_v2.py` 7/7; `test_config.py`, `test_deploy.py` OK. `architecture.sysml`: `graph_api_v2.py` named as the module of `webApp.graphApiV2` (status stays proposed until T-06); SysML checks 0/0, OK.

**Not green yet, and why (plan deviation):** `plan.md` puts TC-API-018, TC-API-020 and TC-IF-104-27 into T-02, but each needs a route of T-03: TC-API-018 lists and reads (501 now), TC-API-020 lists (its `me` assertion already passes), TC-IF-104-27 counts versions after the 401 calls (all eleven 401 answers already pass). They turn green with T-03, and their defects (TR-VIEW-021) are run there: TC-API-018 the default changed to `database`, TC-API-020 the v2 blueprint on an app of its own.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2566 tests); `node --test "tests/js/*.test.mjs"` 186 pass; acceptance scripts all OK except the VIEW checks of later tasks (`test_view_backend.py` 7, the real side of the IF-104 v2 suite 20, `test_graph_view_files.py` 2, `test_graph_view_browser.py` 7, `graph_view_page.test.mjs` 14) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`. The browser checks now end in 7 errors instead of 7 failures: the server helper starts on the real provider, and each check stops at its first page hook (`Page.wait_for_selector` timeout) on the stub page, as the page interface note says; T-07 to T-12.

**Deliberate defects (TR-VIEW-021), run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| an unknown store value falls back to `files` | TC-API-019 | fails (3 sub-cases) |
| every origin allowed (the origin check removed in the guard and the blueprint) | TC-API-024 | fails |
| `-r MIA/requirements-db.txt` dropped from the release stage | TC-OPR-011 | fails |

The plan's defect for TC-OPR-011 ("the line moved to the builder stage") does not apply: the Containerfile has one stage; dropping the install was run instead.

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. `store: database` without `MIA_DATABASE_URL` stops the start with a message naming the setting and the variable. No requirement says this; REQ-API-020 covers only an unknown value. Proposal: keep it, and add it to REQ-API-020 at the merge (or a small amendment).
2. With `store: database` and the database down when MIA starts, `PostgresBackend` cannot connect and the start fails. REQ-API-050 covers a store that stops answering while MIA runs. Proposal: decide in Deploy (preflight checks the database) or by an amendment; SMOKE-VIEW-001 starts with the database up.
3. A foreign `Origin` on a GET is refused too, as everywhere in MIA (the existing guard); IF-104 v2 names the origin only for routes 8 to 11. Kept as the existing guard does.

## T-03: Read routes

**What was done**
- `graph_api_v2.py`: `GraphReader` on the `Storage` layer of the backend, with `GraphModel` of CORE for reading a graph and the toolbox's `look_up` for the marks; routes `GET /graphs` (id, kind, version, author, time, description, step and connection counts), `GET /graphs/<id>` (current or `?version=n`; graph, version, current, author, time, `problems`, `steps`), `GET /graphs/<id>/versions`, `GET /graphs/<id>/arrangement` (`{"positions": null}` when never arranged). The remaining five routes still answer 501 `not_built` (T-04 to T-06).
- `problems_of(graph)`: what cannot be drawn (REQ-API-026): a connection to a step the graph does not have (`missing_step` with the connection, the step and the end), a step ID used twice (`duplicate_step`, named once); never a rule report (D-425 A).
- `steps_of(graph, toolbox)`: the kind per step; for a processing or loop-controlling step (`transform`, `master`) trust, lifecycle and reason of its toolbox entry, or `untrusted` with "it is not in the toolbox"; `code` when a code connection leads to it; `changed_since_trusted` fixed `false` until G-V4.GRAPHAPI.CODE (REQ-API-028). A context graph's steps carry the kind only.
- Not found (REQ-API-049): an unknown graph is 404 `not_found` on every read; a version that is not stored, or is not a whole number of at least 1, is 404 `not_found` with `detail: "version"`.
- Unit tests `tests/test_graph_api_v2.py` +4 (`Reading`): versions 0, 2, -1, `abc`; an unknown graph on the three reads; a step ID used three times plus a missing end; a context graph. Written after the code (the code was drafted in the session before), so a deviation from test-first as in T-02.

**Tests green (my runs, feedback only):** IF-104 v2 suite TC-IF-104-17, 18, 19, 26, 27 on mock, files and postgres (33 cases: 21 OK); TC-IF-104-24, 25 pass their read parts and stop at the first write (501 `not_built`, T-05); `test_view_backend.py` TC-API-018, 019, 020, 024, TC-OPR-011 OK, the `Writes` checks (TC-API-021, 022, 023, 025) wait for T-04 to T-06; `tests/test_graph_api_v2.py` 10/10.

**Regression set (2026-11-23, sequential):** unit suite `discover -s tests` exit 0 (2570 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 186 pass; acceptance scripts all OK except the VIEW checks of later tasks (`test_view_backend.py` 5, the IF-104 v2 suite 12 on the real side, `test_graph_view_files.py` 2, `test_graph_view_browser.py` 7 errors, `graph_view_page.test.mjs` 14) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`.

**Deliberate defects (TR-VIEW-021), the two carried over from T-02; run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| the store default changed to `database` (`store_setting`) | TC-API-018 | fails (the start stops: `MIA_DATABASE_URL` not set) |
| the v2 blueprint registered on a Flask app of its own in `web_app.py` (no shared session) | TC-API-020 | fails (`/api/v2/me` 404 instead of anna, owner) |

The contract cases TC-IF-104-17 to 19 got no defect run, as in T-01 (TR-VIEW-021 does not ask for one on contract cases).

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. A step without stored data or type is given the kind `unknown`; REQ-API-027 names no value for that case. Proposal: keep, and name it at the merge.
2. A version that is not a whole number (`?version=abc`) is 404 `not_found` with `detail: "version"`, the same as a version that is not stored (REQ-API-049 names only the second). Proposal: keep.

## T-04: Save as a new version, refusals

**What was done**
- `graph_api_v2.py`: `PUT /graphs/<id>` (route 9) through `GraphWriter.save`, in this order: unknown graph 404 `not_found`; a body without a `graph` object or with `nodes`/`edges` not lists 422 `invalid`, detail `graph` (REQ-API-048); `expected_version` not the current one 409 `conflict` with `current` (REQ-API-034); the rule report of IF-301 v4 (`graph_rule_set.rule_report`) not empty 422 `rules_broken` with `rules` (REQ-API-035); equal in content to the current version (any order of steps, connections and keys) the current version with `changed: false`, `logged: null`, nothing written (REQ-API-033); else CORE's `GraphModel.save_graph` with the owner as author (REQ-API-032), whose record-check refusal is 422 `refused` with `rule` and `detail` (REQ-API-036); then the record of changes `graph_changes/<id>/<version>` of kind `derived`, from the current version, with the derived entries numbered from 1 (REQ-API-037).
- The sent graph keeps the stored header (`id`, `kind`, `context_graph_id`, `testbench_id`); `description` is taken when sent (IF-104 v2 save body).
- `derive(before, after)`: the entries in the order of the IF-104 v2 mock (connections removed, steps removed, steps added, steps changed, connections added and changed); a removed step carries the connections that go with it in `connections`, and those are not listed again as `remove_connection`.
- Unit tests `tests/test_graph_api_v2.py` +8 (`Saving`), written first and seen red (7 failures, 1 error): a changed step with its derived record read from the store, an unchanged graph in another order, a new description only, the order of entries, a stale version, a cycle and a step that is a text, the extra field `colour`, malformed bodies and an unknown graph. Two findings on the way, each caught by these tests: the comparison depended on the order of keys (the test client sends sorted keys; now `json.dumps(sort_keys=True)`), and a step that is not an object broke the comparison before the rules ran (the rule report now comes first).

**Tests green (my runs, feedback only):** IF-104 v2 suite TC-IF-104-22 on mock, files and postgres; TC-IF-104-20 passes its save answers and the author, then stops at `changes` (501, T-06); TC-API-021 passes its refused save on files and postgres, then stops at the restore (501, T-05). The derived record of TC-IF-104-20 is shown by the unit test reading `graph_changes` directly. `tests/test_graph_api_v2.py` 18/18.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2578 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 186 pass; acceptance scripts all OK except the VIEW checks of later tasks (`test_view_backend.py` 5, the IF-104 v2 suite 10 on the real side, `test_graph_view_files.py` 2, `test_graph_view_browser.py` 7 errors, `graph_view_page.test.mjs` 14) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`.

**Plan deviation (as in T-02):** `plan.md` puts TC-IF-104-20 and TC-API-021 into T-04, but each needs a route of a later task: TC-IF-104-20 reads the record through the changes route (T-06), TC-API-021 restores (T-05). They turn green with those tasks.

**Deliberate defect (TR-VIEW-021), run once, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| the record check skipped: a `schema_break` refusal of CORE's save written around the checks as raw records (with the test's own `append_raw_version`, since the Storage layer refuses the record a second time) | TC-API-021 | fails on files and postgres (200 instead of 422 `refused`) |

A first try that only bypassed CORE's `_first_refusal` still ended refused, by the Storage layer's own check (`StorageError invalid`, a 500): the record check holds in two places.

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. A `remove_step` entry carries a field `connections` (the connections removed with the step) that IF-104 v2's entry fields do not list; the mock does the same, and the connections are not repeated as `remove_connection` entries. Proposal: name the field in IF-104 v2 at the merge (needed to play a record back).
2. An `expected_version` that is not a number (`"4"`) is a 409 `conflict`, as in the mock; the contract lists no `invalid` for it. Proposal: keep.
3. A graph equal in content to the current version that breaks a rule (a stored broken graph saved again) is `rules_broken`, not unchanged: the rules come first, as in the mock.

## T-05: Check, restore, arrangement save

**What was done**
- `graph_api_v2.py`: `POST /graphs/<id>/check` (route 8): the IF-301 v4 rule report of the sent steps and connections under the stored header, nothing stored (REQ-API-031); `POST /graphs/<id>/restore` (route 10): the content of an earlier version as a new version with a record of kind `restore` holding one entry (`target` the restored version, `reason` trimmed or null), nothing deleted (REQ-API-041); `PUT /graphs/<id>/arrangement` (route 11): the places of the graph's steps rounded to whole numbers as the one `arrangements` record of the graph, places of unknown steps ignored, `positions` not an object 422 `invalid` detail `positions`, a place that is not two finite numbers (a boolean is none) 422 `invalid` with the step ID (REQ-API-044, 048). Only the changes route still answers 501 (T-06).
- Save and restore share `GraphWriter._keep`: the rules first (`rules_broken`), then unchanged content (nothing written), then CORE's save (`refused` on a record check), then the record of changes. A restore of the current content answers `changed: false`.
- Unit tests `tests/test_graph_api_v2.py` +5 (`CheckRestoreArrange`), written first and seen red on the T-04 code (4 failures, 1 error): the check with a cycle and a malformed body; a restore with its record and trimmed reason; a restore of the current content and of versions 0, 9, `"1"` and none; an arrangement kept rounded and replaced by the next save; malformed arrangements. One finding on the way, caught by T-04's unit test: the first draft derived the entries before the rule check, so a step that is a text broke the save again; the entries are now derived only after the rules and the comparison (`entries_of`).

**Tests green (my runs, feedback only):** IF-104 v2 suite TC-IF-104-23, 25 on mock, files and postgres; TC-IF-104-24 passes its restore answer and versions, then stops at `changes` (501, T-06); `test_view_backend.py` TC-API-021 (left by T-04) and TC-API-025 on files and postgres; `tests/test_graph_api_v2.py` 23/23. Left for T-06: TC-IF-104-20, 21, 24 (the changes route and editor entries), TC-API-022, 023.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2583 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 186 pass; acceptance scripts all OK except the VIEW checks of later tasks (`test_view_backend.py` 2, the IF-104 v2 suite 6 on the real side, `test_graph_view_files.py` 2, `test_graph_view_browser.py` 7 errors, `graph_view_page.test.mjs` 14) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`.

**Deliberate defect (TR-VIEW-021), run once, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| the check route on CORE's `check_graph` instead of `rule_report` | TC-API-025 | fails (a flat list of parts instead of the items) |

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. Each arrangement save replaces the whole arrangement (places not sent are dropped), as the mock does; REQ-API-044 says "the one arrangement record", not whether a save merges. Proposal: keep (the page always sends every place).
2. Python's `round` rounds a half to the even number (10.5 gives 10, 11.5 gives 12), as the mock does; REQ-API-044 says "rounded to whole numbers". Proposal: keep, and name it in IF-104 v2 at the merge if it matters to EDIT.
3. A restore body without a whole-number `version` (missing, `"1"`, `true`) is 404 `not_found` with `detail: "version"`; the contract lists no `invalid` for route 10. Proposal: keep.

## T-06: Record of changes

**What was done**
- `graph_api_v2.py`: a save with `changes` (the editor's entries) plays them back on the current version (`apply_change`, the six editor operations; `restore` is the restore route's) and keeps them as kind `editor` only when the result equals the sent graph in content; otherwise, or when the list is not a list of entries with a known operation, 422 `changes_do_not_match` and nothing written (REQ-API-038, 051). A kept entry is `{n, op, target, before, after, reason}` with the reason trimmed (empty is null); other keys are dropped.
- The record is written once (REQ-API-039): `Storage.put(..., expected_version=0)`, so it is written only while no record has its ID, in the same lock as the version check. When it cannot be written (a record already there, a lost connection, a failing disk), the version is kept and the save answers `logged: false` (REQ-API-040).
- `GET /graphs/<id>/changes` (route 7, REQ-API-042): one item per version, oldest first, `{version, kind, from_version, author, time, entries}` from its record, or `before_the_record` (no `from_version`, `entries` empty) for a version without one; `author` and `time` are the version's.
- Order of a save or restore (`_keep`): rules, then the entries (which may refuse), then unchanged content, then CORE's save, then the record.
- No 501 route is left; `architecture.sysml`: `webApp.graphApiV2` status `built` (all eleven routes); model checks OK, SysML 0/0.
- Unit tests `tests/test_graph_api_v2.py` +5 (`RecordOfChanges`), written first and seen red on the T-05 code (4 failures, 1 error): matching editor entries, five entry lists that do not give the graph, a record already there, a lost record with the changes route, the changes route after a save and a restore.

**Tests green (my runs, feedback only):** every Track A check: the IF-104 v2 suite 33/33 (TC-IF-104-17 to 27 on mock, files and postgres), `test_view_backend.py` 9/9 (TC-API-018 to 025, TC-OPR-011, files and postgres where the case asks); `tests/test_graph_api_v2.py` 28/28.

**Regression set (2026-11-23, sequential, while G-V4.GRAPHSTORE.TRANSFER ran its own unit suite on the same machine from 20:25):** unit suite 2588 tests, 2 failures, both not of T-06: (1) `test_checkout_untouched` named `specs/mia/handover-...md` and `review-log.md`, which I edited during the run (D-451); its re-run then named a stale `mia.log` (ignored, left in the checkout root by earlier manual runs); with that file moved to the scratchpad the check is OK. (2) `test_sandbox` `test_runs_in_parallel_do_not_collide` gave `None` for two of four podman runs, twice, both while TRANSFER's suite ran; run alone the four runs give 0, 2, 4, 6 (T-06 does not touch the sandbox). `node --test "tests/js/*.test.mjs"` 186 pass; acceptance scripts all OK, `test_view_backend.py` and the IF-104 v2 suite included, except the page checks of Track B (`test_graph_view_files.py` 2, `test_graph_view_browser.py` 7 errors, `graph_view_page.test.mjs` 14) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`; traceability check: warnings only (TR-PANEL credibility aspects, not of this goal).

**Deliberate defects (TR-VIEW-021), run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| the record written twice (`expected_version=0` dropped) | TC-API-022 | fails (2 record versions instead of 1) |
| the save refused when the record write fails (only a `StorageError` gives `logged: false`, any other error is raised) | TC-API-023 | fails (500 instead of 200) |

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. When a record with the new version's ID is already there (TC-API-022), the save answers `logged: false`: this save did not write the record. REQ-API-039 and REQ-API-040 do not say what `logged` is then. Proposal: keep.
2. Keys of an editor entry other than `op`, `target`, `before`, `after`, `reason` are dropped from the record (the mock does the same). Proposal: keep.
3. The changes route gives `author` and `time` of the graph version, not of the record (the record has its own, written a moment later by the same account). Proposal: keep.

## T-07: Tokens, frame, status

**What was done**
- `graph_app/tokens.css`: a byte copy of `templates/static/chat/tokens.css` (REQ-GA-014); `index.html` loads it before `graph.css`, sets `data-theme="auto"` on `<html>` so the tokens follow the system's light or dark setting (REQ-GA-016), and holds only `<div id="app">`.
- `graph_app/graph.css` written again: every colour, font, spacing, radius and shadow from `var(--…)` (REQ-GA-015); the layout of the owner's sketch (D-425) as a grid: top band (graph list, search and chat, other things), the left column beside the picture with the actions under it, the history and replay row, the status bar.
- `graph_app/viewer.js`: `createViewer({document, root, api})` builds the frame with the eight areas of the interface note (`data-area`, `aria-label` and the label as heading, REQ-GA-012) and the four later areas (`data-later` SEARCH, EDIT, REPLAY, RUN: one line naming the subgoal, no control, REQ-GA-013); `start()` asks `me`, `store` and the list, fills the store entry `[data-store]` ("store: files, reachable", text only, REQ-GA-018) and the list entries (text only until T-08); `open(id)` reads the current version and puts graph ID, kind, version, author, time and `read-only` into the status bar (REQ-GA-017). `storage` and `makeDrawing` are taken in with T-10 and T-09.
- `graph_app/store-note.js` (R6, written again for the v2 store route: the prototype's helper read the older `/api/v2/status` shape): `storeEntry(answer)` and `graphStatus(shown)`, pure.
- `graph_app/api.js`: `httpApi(fetchFn, base)` with the six GETs of the interface note (rejecting with `{status, code, detail}`); written now because `start()` needs `me` and `store` (the plan names `api.js` in T-08).
- `graph_app/app.js` replaced by the page entry of the interface note (the old file-open page of N-5 T-01 is gone; `graph-view.js` and its tests stay until T-09 decides). Not in T-07's "Touches", but `index.html` cannot load the new frame without it.
- `tests/js/graph-app-files.test.mjs` (not protected): the expected file list gets `store-note.js` and `tokens.css`, the expected links of `index.html` start with `tokens.css`.
- Unit tests written first and seen red (4 failures: the modules were missing): `tests/js/store-note.test.mjs` (2), `tests/js/graph-viewer-frame.test.mjs` (3: every area once with label and heading; the later areas in their areas, one line, no control; the store entry from the store route).
- A look in Firefox (Playwright, 1280 × 800, light and dark, the browser checks' server helper): the frame renders without page errors, the areas sit as in the sketch, the background and text follow the theme. Screenshots: `/tmp/claude-1000/-home-maldun-prog-Python-MIA-goal-v4-view/0ca32470-a536-4706-9a76-e2b655730929/scratchpad/frame-light.png`, `.../frame-dark.png` (scratchpad, not kept).

**Tests green (my runs, feedback only):** TC-GA-021 (`graph_view_page.test.mjs`; the other 12 node checks wait for T-08 to T-11); TC-GA-031, 032 (`test_graph_view_files.py`); `node --test "tests/js/*.test.mjs"` 191 pass.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2588 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 191 pass; acceptance scripts all OK, `test_graph_view_files.py` now included, except the page checks of later tasks (`graph_view_page.test.mjs` 13, `test_graph_view_browser.py` 6 errors and 1 failure) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`. The browser checks now load the frame: six stop at the `window.graphViewTest.settled` hook (the picture, T-09), TC-GA-038 at the keyboard reach of the list (`ul` takes the focus, the entries do not; T-08 and T-12).

**Deliberate defects (TR-VIEW-021), run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| the store entry hard-coded `database` | TC-GA-021 | fails |
| one byte of the copy of `tokens.css` changed (`/*` to `/ *` in line 1) | TC-GA-031 | fails |
| `color: #fff` planted in `graph.css` | TC-GA-032 | fails (`graph.css: colour literal in color: #fff`) |

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. The words of the later areas, the area labels ("Graphs", "Search and chat", "Other things", "Selection", "Picture", "Actions", "History and replay", "Graph status") and the status line form (`cp2.multi · workflow · version 4 · stored by ben · <time> · read-only`, `version 2 of 4` for an older one) are mine; no requirement fixes them. Proposal: the owner looks at the screenshots and changes words as he likes.
2. The list says `1 connections` for one connection (the interface note fixes `<n> connections`). Proposal: decide at T-08 (singular for one would need the note's form widened).

## T-08: List and opening

**What was done**
- `graph_app/list-filter.js` (R6, written again): `filterGraphs(graphs, text)` keeps the graphs whose ID or description holds every typed word, case ignored (REQ-GA-020; the prototype also searched the kind, which the requirement does not name, so the kind is left out); `entryLabel(g)` in the words of the interface note.
- `graph_app/viewer.js`: the filter field `#graph-filter` above the list; each `li[data-graph-id]` a tab stop of its own (`tabindex=0`), Enter or a click opens the graph, ArrowDown and ArrowUp move to the next or previous shown entry, the open entry carries `aria-current="true"` (REQ-GA-019, 021); `filter(text)` hides the entries that do not match; `open(id)` reads the current version (no version asked), names it in the status bar and hands the drawing every step and every directed connection (`{id, label}`, `{id, from, to, arrows: 'to'}`; T-09 adds shapes, kinds and marks); the drawing is made on the first opening.
- Refusals (REQ-GA-022, 023): 401 on any read empties the list, hides the picture, resets the status bar and puts `[data-login]` with a link to `/` into the list area; 503 keeps the list, the picture and the status bar and adds the one line `[data-notice=store_unreachable]` to the status bar, removed again at the next answer; any other failure is passed on to the caller.
- `tests/js/graph-app-files.test.mjs`: the expected file list gets `list-filter.js`.
- Unit tests written first and seen red (5 of 6; the sixth, "other failures are not swallowed", already held): `tests/js/list-filter.test.mjs` (3) and `tests/js/graph-viewer-list.test.mjs` (5: click and Enter open and mark the entry; tab stops and arrow keys; a session that ends after opening; the store notice once and gone again; a 500 passed on). Finding on the way: the fake DOM does not match a class in a descendant selector, so the drawing container got the hook `data-drawing` (the test reads that).

**Tests green (my runs, feedback only):** TC-GA-018, 019, 020 (and TC-GA-021) of `graph_view_page.test.mjs`; `node --test "tests/js/*.test.mjs"` 199 pass. TC-GA-017 passes the list, the opening and `version 4`, then stops at `viewer.selectStep` (the left column, REQ-GA-036, T-11), as T-02 left checks for later tasks.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2588 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 199 pass; acceptance scripts all OK except the page checks of later tasks (`graph_view_page.test.mjs` 10, `test_graph_view_browser.py` 7 errors) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`.

**Known gap until T-09:** `drawing.js` is still the stub, so in the browser the first opening throws `not written` (the node checks use the recording drawing). The browser checks wait for T-09 to T-12 anyway.

**Deliberate defects (TR-VIEW-021), run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| opening asks for version 1 instead of the current | TC-GA-017 | fails at line 30 (`version 4` in the status bar), before the `selectStep` it waits for |
| the filter ignores the description | TC-GA-018 | fails |
| 401 empties the list without the login link | TC-GA-019 | fails |
| the picture cleared on 503 | TC-GA-020 | fails |

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. The filter does not search the kind (the prototype did; REQ-GA-020 names ID and description only). Proposal: keep as the requirement says.
2. The words of the login note ("Not logged in. Log in through the main app.") and of the store notice ("The store does not answer now; what is shown stays as it was.") are mine. Proposal: keep; the owner may change them.

## T-09: The picture

**What was done**
- `graph_app/step-marks.js` (R6, written again for D-426): `kindOf(step, workflow)` gives shape and word (data ellipse "data", transform box "processing", master hexagon "loop-controlling"; any other type, and every step of a graph of another kind, a box with its stored type, `unknown` when none); `marksOf(info)` gives at most `untrusted`, `changed`, `code`, one word each, only for a processing or loop-controlling step (the prototype marked trusted steps too and used several words: D-426 says trusted steps stay plain); `isWorkflow(graph)`.
- `graph_app/problems.js` (R6, written again for IF-104 v2 `problems`): `missingSteps(problems)`, `problemText(p)`.
- `graph_app/adapter.js` (R6, written again): `pictureOf(shown)` gives the drawing `{nodes, edges}` of the interface note: every stored step once (a step ID used twice is drawn as stored first; the problem names it), a node `{missing: true, kind: 'missing step'}` for each missing end, every connection with `arrows: 'to'`, `dashes` true for a connection to or from a missing step; labels are the ID, then the kind and the marks, plain text (REQ-GA-024 to 029).
- `graph_app/viewer.js`: the opening draws `pictureOf(shown)`; the left column lists what cannot be drawn, `li[data-problem]` per problem in words (REQ-GA-025). `graph.css`: the problem list in `var(--danger)`, hidden when empty. `tests/js/graph-app-files.test.mjs`: the expected file list gets the three modules.
- Unit tests `tests/js/graph-picture.test.mjs` (8), written first and seen red (the modules were missing): kinds and shapes, marks, another kind, a context step with workflow types, the missing step and dashes, a step ID used twice, the problem words, a hostile label kept as text.

**Tests green (my runs, feedback only):** TC-GA-022 to 025 of `graph_view_page.test.mjs` (with TC-GA-018 to 021; TC-GA-017 still waits for `selectStep`, T-11); `node --test "tests/js/*.test.mjs"` 207 pass; TC-GA-031, 032 OK.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2588 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 207 pass; acceptance scripts all OK except the page checks of later tasks (`graph_view_page.test.mjs` 6, `test_graph_view_browser.py` 7 errors) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`.

**Deliberate defects (TR-VIEW-021), run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| the arrows left out | TC-GA-022 | fails |
| the connection to a missing step dropped | TC-GA-023 | fails |
| a mark on every step (`checked`) | TC-GA-024 | fails |
| a graph of another kind drawn with the workflow shapes (`isWorkflow` always true) | TC-GA-025 | **passes**: the check does not see it (F-1); my unit tests `graph-picture.test.mjs` fail twice on it |

**Finding F-1 (for the owner; protected test and fixture, so not changed):** TC-GA-025 cannot fail on its planned defect. Its graphs of another kind, `ctx.small` (types `concept`, `source`) and `swarm.one` (type `agent`), use no workflow type, so the workflow shapes give the same boxes; and the backend (and the JS mock) never send trust marks for a graph of another kind, so the page cannot add any. A defect that drew such a graph with the workflow shapes would show only on a step whose type is `data`, `transform` or `master`. Covered meanwhile by my unit test "a step of another kind whose type is a workflow type is still a neutral box". Owner's decision (D-454): amend the fixture, amendment A-175. The proposal was an amendment that gives `ctx.small` (fixture `tests/fixtures/graph_view/graphs.json`, protected) a step of type `data`, and TC-GA-025 the assertion that it is a box; or accept the unit test as the witness and record that the check cannot see the defect.

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. A step ID used twice is drawn once, as stored first (vis-network refuses two nodes with one ID); REQ-GA-025 names only missing steps. Proposal: keep; the problem list names it.
2. The label of a step is two lines, its ID and then its kind and marks (`step.write` / `processing · untrusted · code`). Proposal: keep; the owner sees it in the browser at T-12.

## T-10: Arrangement and settings

**What was done**
- `graph_app/settings.js` (R6, written again for the interface note's names): `KEY`, `DEFAULTS` (`edges: rounded`, `arrangement: on`), `loadSettings(storage)` (the defaults where nothing is saved, the text is damaged, a value is unknown or the storage throws, REQ-GA-035), `saveSettings` (false on a blocked storage, never a throw), `validSettings`, `drawingOptions(settings, layout)` with the fixed `SEED` 7 and `SOLVER` `barnesHut` (the prototype's validated solver, REQ-GA-031).
- `graph_app/arrangement.js` (R6, written again): `placed(nodes, saved, moved)` (a moved place wins over the saved one, either is held with `fixed`, a step without one is left to the solver, places of unknown steps ignored, REQ-GA-030, 032); `layered(nodes, edges)` (longest-path levels in a depth-first order; a connection that closes a cycle is left out of the layering so a stored cyclic graph still gets whole-number levels; no place held, REQ-GA-033).
- `graph_app/viewer.js`: opening reads the graph and its arrangement together and draws the steps at their places with the drawing options of the settings; the drawing's drag end keeps the dropped place (rounded to whole pixels) while the same graph stays open, also when it is read again; another graph starts without moved places. The settings place in "other things": the button `#settings-open` (with `aria-expanded`), the group `[data-settings]` with `[data-setting=edges]`, `[data-setting=arrangement]` and the button `#layered-reset`; a change reaches the drawing through `setOptions` at once without reading the graph again and is saved on the device; `setSettings`, `layered()` on the controller.
- `graph_app/graph.css`: the settings place as a small popover under its button (opening it first pushed the rows below out of the frame); the filter field and the controls styled from the tokens; the picture may shrink, so the actions row stays inside the frame at 1280 × 800 (seen in Firefox, light and dark).
- `tests/js/graph-app-files.test.mjs`: the expected file list gets `arrangement.js` and `settings.js` (and is kept sorted).
- Unit tests written first and seen red (5 files failing to load): `graph-settings.test.mjs` (3), `graph-arrangement.test.mjs` (4, with a branch and join and a cycle), `graph-viewer-arrange.test.mjs` (3: a moved place kept, the settings place and its writes, the layered reset by call and by button).

**Tests green (my runs, feedback only):** TC-GA-026, 027, 028 (with TC-GA-018 to 025); `node --test "tests/js/*.test.mjs"` 217 pass; TC-GA-031, 032 OK.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2588 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 217 pass; acceptance scripts all OK except the page checks of later tasks (`graph_view_page.test.mjs` 3, `test_graph_view_browser.py` 7 errors) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`.

**Deliberate defects (TR-VIEW-021), run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| the saved arrangement ignored (`saved = null`) | TC-GA-026 | fails |
| every step on one level (`level: 0`) | TC-GA-027 | fails |
| the settings not written to the storage | TC-GA-028 | fails |

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. The fixed seed is 7 and the solver `barnesHut` (the prototype's); REQ-GA-031 fixes only that there is one of each. Proposal: keep; TC-GA-036 checks the sameness in Firefox at T-12.
2. Moved places stay while the same graph is open (also when it is read again) and are let go by the layered reset or by opening another graph. REQ-GA-032 says "while the graph is open". Proposal: keep.
3. Settings words ("View settings", "Connections", "Arrange by itself", "Reset to layers") are mine. Proposal: keep; the owner may change them.

## T-11: Left column and history

**What was done**
- `graph_app/panel.js` (R6, written again for the hooks of the interface note): `stepFields(step, kind, info)` gives `[name, label, value]` for `kind`, `toolbox_id` and, for a processing or loop-controlling step of a workflow graph, `trust`, `lifecycle`, `reason`, `changed_since_trusted`, `code` (a missing value `none`, a yes/no value `yes` or `no`, REQ-GA-036, 037); `connectionFields(edge)` for `from`, `to`, `role`; `storedText(item)` (`JSON.stringify(…, null, 2)`).
- `graph_app/history.js` (R6, written again): `historyEntries(versions, current)` newest first with who and when, the current one marked; `neighbour(versions, shown, direction)`, null beyond the ends (REQ-GA-038, 040).
- `graph_app/viewer.js`: the left column holds the problems, the selection (`p[data-field]` as `label: value`, `pre[data-stored-text]`, or "Nothing selected.") and the step list (`li[data-step-id]` per drawn step, missing steps included: a tab stop each, Enter or a click selects, the arrow keys move; REQ-GA-041 on the page side); `selectStep`, `selectConnection`, `selectNothing` (REQ-GA-044); a new picture empties the selection. The history row: `#history-open` (offered once a graph is open), the entries `li[data-version]` with `data-current` and `aria-selected` on the shown one (click or Enter shows it), `#history-previous` and `#history-next` with `disabled` where no step is offered; `openHistory`, `showVersion(n)` (the version read-only, named in the status bar as `version n of m` with its author and time, REQ-GA-039), `previous`, `next`. Opening a graph resets its history.
- `graph_app/graph.css`: styles for the fields, the stored text (mono font from the tokens), the step list and the history row, all from the tokens. `tests/js/graph-app-files.test.mjs`: the file list gets `panel.js` and `history.js`.
- Unit tests written first and seen red (4: the modules were missing): `graph-panel.test.mjs` (5) and `graph-viewer-history.test.mjs` (3: the step list by click and Enter with a missing step; an unknown ID and a new version leave no field; the history buttons and the marked entry).

**Tests green (my runs, feedback only):** `graph_view_page.test.mjs` 15/15 (TC-GA-017 to 030 and the helper check; TC-GA-017 had waited for `selectStep` since T-08); `node --test "tests/js/*.test.mjs"` 225 pass; TC-GA-031, 032 OK.

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2588 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 225 pass; acceptance scripts all OK, `graph_view_page.test.mjs` 15/15 included, except the browser checks of T-12 (`test_graph_view_browser.py` 7 errors) and the known reds `test_decide_guard.py`, `test_judge_calibration.py`.

**Deliberate defects (TR-VIEW-021), run once each, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| `changed_since_trusted` left out of the fields | TC-GA-029 | fails |
| the history oldest first | TC-GA-030 | fails |

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. The left column shows the fields the interface note names; a data step's `value` and a step's other stored values are only in the stored text. REQ-GA-036 says "its known values as labelled fields". Proposal: keep (the stored text holds everything); widen at EDIT if wanted.
2. Field labels ("toolbox ID", "changed since trusted", "holds code") and button words ("History", "Previous version", "Next version") are mine. Proposal: keep; the owner may change them.
3. A selection is let go when another version is shown (the step may not exist there). Proposal: keep.

## T-12: The page in Firefox

**What was done**
- `graph_app/drawing.js`: `visDrawing(container, vis)` on the vendored vis-network 10.1.2. Colours and the font are the tokens as the browser resolves them (a probe element: vis draws on a canvas and cannot read `var(--…)`), read again when the system's colour scheme changes (REQ-GA-016); data steps ellipses, processing steps boxes, loop-controlling steps a hexagon drawn around its text (vis puts a hexagon's label outside the shape; the prototype's renderer, R6), untrusted and missing steps with a dashed border in `--danger`; connections with arrows, dashed where the page says so, rounded or straight. Layout: `randomSeed` the page's fixed seed and the solver `barnesHut` with `avoidOverlap` (REQ-GA-031); the layered reset as vis's hierarchical layout from the levels (left to right). After the first stabilisation physics is switched off, so a settled graph keeps its places; a dropped step is held (`fixed`) where it was dropped (REQ-GA-032). `onDragEnd`, `onStabilized`, and `onSelect` (a click on a step, a connection or empty space: an addition to section 3 of the interface note, see the open questions). The read-only test hook `window.graphViewTest` (`settled`, `positions()`, `domPosition(id)`, `labels()`, `labelColour()`, TR-VIEW-010, 013).
- `graph_app/viewer.js`: a click in the picture selects the step or connection, or nothing on empty space (through `onSelect` where the drawing has it); the "View settings" button and its popover moved into the picture's header (D-458).
- `graph_app/graph.css`: the left column a column whose selection scrolls on its own, so the step list stays in sight; the settings in the picture's top right corner.
- `app.js` and `index.html` were already the entry of the interface note (T-07).
- **Not done: `graph_app/graph-view.js` and `tests/js/graph-view.test.mjs` are kept** (finding F-2): the protected smoke check `tests/smoke/smoke_stack.py` lists `graph-view.js` in `GRAPH_FILES` (the files the graph container must serve, equal to `graph_app/`), so removing it would break a protected check. The file is no longer loaded by the page.

**Findings on the way, each caught by a browser check:**
1. TC-GA-037 (dropped step jumped): the page let vis stabilise twice on opening (adding the data, then an explicit `stabilize()`), so `settled` was reported after the first round while the second still moved the steps. Now the data goes in with `setData`, which stabilises once.
2. TC-GA-037 (step moved by the settings): every settings change passed `physics` and switched the solver on again with `fit`, which moved the view. Now the drawing settles again only when the arrangement is switched from off to on, and then without fitting the view.
3. TC-GA-038 (settings out of reach by Tab forward): D-458.

**Tests green (my runs, feedback only):** `test_graph_view_browser.py` 7/7 (TC-GA-033 to 039) in three runs in a row (Firefox of Playwright, headless, 1280 × 800); `graph_view_page.test.mjs` 15/15; `test_graph_view_files.py` OK; `node --test "tests/js/*.test.mjs"` 225 pass. With Track A this is every VIEW check (A-175, once installed, changes TC-GA-025 only).

**Regression set (2026-11-23, sequential):** unit suite exit 0 (2588 tests, 5 skipped, 2 expected failures); `node --test "tests/js/*.test.mjs"` 225 pass; every acceptance script OK (`test_view_backend.py`, the IF-104 v2 suite, `test_graph_view_files.py`, `test_graph_view_browser.py` included) except the known reds `test_decide_guard.py`, `test_judge_calibration.py`; `graph_view_page.test.mjs` and the JS contract suites 49 pass; model check OK; traceability check: the same 549 ERROR lines as at the plan gate (`39a47d7f`), none new, none gone (older items: IF-001 to 006, REQ-GATE, REQ-EVAL, TC-API-001 …, not of this goal).

**Deliberate defects (TR-VIEW-021), run once each in Firefox, then restored (`cmp` against the copy):**

| Defect | Check | Result |
|---|---|---|
| a button in the empty EDIT area | TC-GA-033 | fails (`1 != 0 : EDIT`) |
| a fixed light background (`background: white !important`) | TC-GA-034 | fails (white instead of the dark `--page-bg`) |
| a link around the stored name in the step list (`innerHTML`) | TC-GA-035 | fails (the `<img …>` part became markup) |
| a random seed | TC-GA-036 | fails (other places on the second opening) |
| the arrangement saved on drop (`PUT …/arrangement`) | TC-GA-037 | fails (a PUT was sent) |
| step list entries without keyboard focus (no `tabindex`) | TC-GA-038 | fails (`step:step.check` not reached) |
| a planted stylesheet `https://example.invalid/x.css` | TC-GA-039 | fails (the outside request is listed) |

**Finding F-2 (for the owner; protected smoke check):** the plan has T-12 remove `graph_app/graph-view.js` and its unit test, but `tests/smoke/smoke_stack.py` (protected) names `graph-view.js` among the graph container's files. Proposal: keep the file until an amendment changes `GRAPH_FILES` of the smoke check (then remove both in one commit), or keep it for good as a dead file; either way the page does not load it.

**Open questions for Verify / the owner (behaviour only in the code, P25):**
1. `onSelect(fn)` was added to the drawing of section 3 of the interface note (a click in the picture selects; REQ-GA-036 says "when the owner selects a step", and without it only the step list selects). The recording drawing of the node checks does not have it; the viewer calls it only where it exists. Proposal: name it in the interface note at the merge.
2. After the first stabilisation the solver stays off until the owner switches the arrangement off and on again; dragging one step does not move the others. Proposal: keep (REQ-GA-031, 032).
3. The layered reset runs left to right (`direction: 'LR'`). Proposal: keep.

## A-175 installed (2026-11-23)

The owner installed A-175 (`tools/apply_amendment_a175.sh --do`, D-454). After the install: `graph_view_page.test.mjs` 15/15; `test_graph_view_browser.py`, `test_view_backend.py`, `test_graph_view_files.py` OK (the browser checks seed `ctx.small` with its new step through CORE). The planned defect of TC-GA-025 (`isWorkflow` always true) run again: TC-GA-025 now **fails** on it, restored after. Finding F-1 closed.

## Layout after the owner's look (2026-11-23, D-459)

The owner looked at the page in Firefox and asked for a different arrangement of the frame (D-459). Changed: `graph_app/viewer.js` (the areas are direct children of the root, in the Tab order list, band, left column, picture, actions, history, status; the store part without a visible heading, `aria-label` "Store"), `graph_app/graph.css` (a grid with named areas: the graph list above the left column and as wide as it, the slim band of search and store above the picture; the graph list does not stretch the band's row, `contain: size`; the selection and the step list share the left column), `graph_app/drawing.js` (the solver starts the steps without a place in their layers, left to right, and relaxes them from there, `barnesHut` with `springLength` 140, `avoidOverlap` 0.6: before, steps either overlapped or settled in a tall column the view had to zoom far out for, so labels were tiny). `tests/js/graph-viewer-frame.test.mjs`: the store part has no heading.

Checks after the change (my runs): `node --test "tests/js/*.test.mjs"` 225 pass; `graph_view_page.test.mjs` 15/15; `test_graph_view_files.py` OK; `test_graph_view_browser.py` 7/7 in three runs. Screenshots in light and dark: no page errors.

Open for Verify: REQ-GA-012 says each area is "visible by its label"; the store part now carries its label only for screen readers (the owner's wish).
