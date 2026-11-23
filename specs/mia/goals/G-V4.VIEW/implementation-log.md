# Implementation log: G-V4.VIEW

Goal: G-V4.VIEW   Line of work: goal/v4.view   Supervision: supervised (plan gate ticked by the owner, D-447)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 Record tables | done | see `git log` ("feat: T-01 record tables arrangements and graph_changes") | TC-IF-302-13, 14 (mock and real); `tests/test_record_tables_view.py` (6 unit tests) | `tests/test_record_tables.py`: the expected table set gets the two new tables (A-172) |
| T-02 Store setting, provider, access, image | done | see `git log` ("feat: T-02 store setting, v2 provider, access and image") | TC-API-019, 024, TC-OPR-011; TC-IF-104-26 (mock, files, postgres); `tests/test_graph_api_v2.py` (7 unit tests) | TC-API-018, 020 and TC-IF-104-27 wait for T-03 (they need the list, read and versions routes) |

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
