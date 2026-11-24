# Verification report: G-V4.VIEW (graph viewer: pull from the data source and draw)

**Goal:** G-V4.VIEW (subgoal of G-V4), supervised, accepted by Stefan Reiterer (owner)
**Branch:** `goal/v4.view` @ 2f68b280 (plan gate 39a47d7f, RULES merged at b961c573)   **Plan baseline:** `plan-baseline-g-v4-view` (82327296)
**Date:** 2026-11-23   **Reviewer:** an independent AI reviewer (Opus 5.5, fresh context, never saw the implementation chat), with two read-only reviewer subagents (Track A, Track B); every finding they reported that is listed below was re-checked by me in the code, and the ones marked *reproduced* were run in Firefox or against the provider. No person has read this report yet.

## Verdict
**Proposal: not yet verified; back to Implement for V-1 to V-5, and the owner's networked image build for V-15**, then a short re-verify of the fix commits. Otherwise the goal is close. Each of the 70 requirements has a green check. Each check ran under its test requirements. Protected material differs from the baseline only by A-175, installed byte for byte, and by the owner's deny rule (D-446 (2)). Every check of TR-VIEW-021 has a logged defect run, and I repeated three of them myself. The other findings (V-6 to V-14) are low; the owner can accept them as deviations or send them to Plan.

The reasons for not verifying yet are things the owner would feel at the page:
- V-1: the arrow keys in the graph list throw an error in Firefox.
- V-2: a dragged step jumps back when the system switches between light and dark.
- V-3 to V-5: three backend gaps (a lost database connection never recovers; the `before` of editor entries is stored unchecked; malformed items give a 500).

The protected checks do not see V-1 to V-5.

- [ ] Verified by the owner. Date:

## Automated checks (all run by me; Python 3.12 venv `mia312`, node, Playwright 1.64.1 Firefox)
| Check | Result |
|---|---|
| Clean state | Fresh detached checkout `/home/maldun/prog/Python/MIA-v4-view-verify` at 2f68b280 (VIEW checks, unit suite, my defect runs); the acceptance regression in the worktree, one script at a time |
| Protected material since the baseline (`git diff b961c573 HEAD` on `tests/acceptance`, `tests/helpers`, `tests/smoke`, `tests/integration`, `contracts`, `benchmarks`, `eval/`, test requirements, `deferred.md`, `decomposition.yaml`, `tests/fixtures/graph_view`) | Only 3 files, all A-175 (`fe03ab23`): byte-identical to `specs/mia/amendments/A-175/`. The changes between 82327296 and b961c573 are the merge of RULES, verified there. `.claude/settings.json` +2 deny rules (D-446 (2), `1431f94b`): a person reads the diff (M20) |
| Installed suites (TR-VIEW-015) | IF-104 v2 suites byte-identical to A-174 (which replaced A-171's suite files); mocks to A-171; IF-302 suite, mock and contract to A-172; IF-104 v1 suites (Python and JS) identical to `goal/v4` |
| Skips | No `skip` or `xfail` in VIEW's acceptance files. The JS contract suite skips its 11 `[real]` cases as planned, with the reason that the Python suite runs them over HTTP |
| IF-104 v2 contract (Python) | 33/33: 11 cases (TC-IF-104-17 to 27) each on mock, files and PostgreSQL 16 (podman, throw-away). None skipped (TR-VIEW-001) |
| IF-104 v2 contract (JS mock) | 11 pass, 11 `[real]` skipped as planned |
| IF-302 record tables | 28/28 (TC-IF-302-13, 14 on the real side and on the mock side) |
| `test_view_backend.py` | 9/9 (TC-API-018 to 025, TC-OPR-011) |
| `test_graph_view_files.py` | 2/2 (TC-GA-031, 032) |
| `graph_view_page.test.mjs` | 15/15 (TC-GA-017 to 030) |
| `test_graph_view_browser.py` (Firefox, headless) | 7/7 in each of three runs in a row (15 to 18 s) |
| `tests/js/*.test.mjs` | 225/225 |
| Unit suite (fresh checkout) | Ran 2588 in 671 s: **1 error** (4 skipped, 2 expected failures). The error is `test_delivery_on_stack` (V-15): the offline image build (`--network none`, M2) misses the pip layer that T-02's Containerfile change made new (`RUN pip install -r MIA/requirements.txt -r MIA/requirements-db.txt`). Re-run in the worktree: same error. The implementer's runs show 5 skips, so this test most likely skipped there (no model server, or an image missing) |
| Acceptance regression, every script one by one | 76 scripts in 266 s: **74 exit 0**. The 2 reds are the known reds outside VIEW, `test_decide_guard.py` and `test_judge_calibration.py` (import errors; files identical to `goal/v4`; G-V3.REPORT F-3) |
| Traceability `trace_check.py` | 549 ERROR lines, the same set line for line as at the plan gate (39a47d7f). None names a VIEW item (`goals/` requirements move into the node files at the merge) |
| Goal check `goal_check.py` | 82 errors, the same set as at the plan gate. They include GL10 for VIEW's outcome criteria (FR-48 and later live in the goal's own `top-level-spec.md`) |
| Model consistency `check_sysml_model.py` | OK |
| `refactor_check.py --base plan-baseline-g-v4-view` | 0 refactoring commits, no findings |
| `agent_config_diff.py` | 1 info: `.claude/settings.json` (+2 deny rules, the owner's D-446 (2)) |
| Static and security tools | None configured (CLAUDE.md); none installed, and none added (needs approval). Done by hand instead: a grep for HTML sinks (`innerHTML`, `insertAdjacentHTML`, `eval`, `new Function`, `document.write`) in `graph_app/` found none; no `subprocess` or `open(` in `graph_api_v2.py` or `record_tables.py`; untrusted IDs reach the file store only through `quote(…, safe="")` |
| Agent material | Nothing agentic touched: no skill, prompt, pipeline, eval suite or model pin (`git diff b961c573 HEAD -- skills library eval` is empty). The checks of `agent-app-verify` A to G do not apply |

## Verification matrix
All 70 requirements use the Test method. Each check below passed in my runs. The last column says where a finding qualifies the result.

| Requirements | Check(s) | Result |
|---|---|---|
| REQ-API-018, 023, 024, 025 | TC-IF-104-17 (mock, files, postgres) | pass |
| REQ-API-019 | TC-API-018 | pass |
| REQ-API-020 | TC-API-019 | pass (V-12 f: database without URL) |
| REQ-API-021, 022, 050 | TC-IF-104-26 | pass; **V-3** (a real lost connection is not covered) |
| REQ-OPR-011 | TC-OPR-011; SMOKE-VIEW-001 at Deploy | pass (reading the file); the built image is Deploy's |
| REQ-API-026 | TC-IF-104-18 | pass |
| REQ-API-027, 028, 029 | TC-IF-104-19 | pass (V-12 b) |
| REQ-API-030 | TC-API-020, TC-IF-104-17; v1 TC-IF-104-01 to 05 | pass |
| REQ-API-031 | TC-API-025, TC-IF-104-23 | pass |
| REQ-API-032, 033, 037 | TC-IF-104-20 | pass |
| REQ-API-034 | TC-IF-104-22 | pass; V-6 (two saves at once) |
| REQ-API-035 | TC-API-025, TC-IF-104-22 | pass |
| REQ-API-036 | TC-API-021 | pass |
| REQ-API-038, 051 | TC-IF-104-21 | pass; **V-4** (`before` unchecked) |
| REQ-API-039 | TC-API-022 | pass |
| REQ-API-040, 042 | TC-API-023 (042 also TC-IF-104-20) | pass |
| REQ-API-041 | TC-IF-104-24 | pass (V-12 c) |
| REQ-API-043, 044 | TC-IF-104-25 | pass (V-12 e) |
| REQ-RTB-010, 011 | TC-IF-302-13, 14 | pass |
| REQ-API-045 | TC-IF-104-27 | pass |
| REQ-API-046 | TC-IF-104-22, 23, 25 | pass |
| REQ-API-047 | TC-API-024 | pass (note O-1) |
| REQ-API-048 | TC-IF-104-22, 25 | pass; **V-5** (500 on malformed items), V-7 (wrong types) |
| REQ-API-049 | TC-IF-104-22, 24 | pass |
| REQ-GA-012, 013 | TC-GA-033 | pass (012: the store part's label is for screen readers only, D-459; the owner looks) |
| REQ-GA-014, 015 | TC-GA-031, 032 | pass |
| REQ-GA-016 | TC-GA-034 | pass; V-12 h (the check is weak) |
| REQ-GA-017, 018 | TC-GA-021 | pass; V-10 (the store entry is never updated) |
| REQ-GA-019, 021 | TC-GA-017 | pass |
| REQ-GA-020 | TC-GA-018 | pass |
| REQ-GA-022 | TC-GA-019 | pass; V-8 (a 401 while a graph is open) |
| REQ-GA-023 | TC-GA-020 | pass; V-11 (other errors are silent) |
| REQ-GA-024, 025 | TC-GA-022, 023 | pass |
| REQ-GA-026, 027 | TC-GA-024 | pass |
| REQ-GA-028 | TC-GA-025 (after A-175) | pass |
| REQ-GA-029 | TC-GA-035 | pass |
| REQ-GA-030, 033 | TC-GA-026, 027 | pass |
| REQ-GA-031 | TC-GA-036 | pass |
| REQ-GA-032 | TC-GA-037 | pass; **V-2** (reproduced: the step jumps back on a theme switch) |
| REQ-GA-034, 035 | TC-GA-028, 037 | pass; V-9 (reproduced: storage blocked gives a blank page) |
| REQ-GA-036, 044, 037 | TC-GA-029 | pass; V-12 g (a click in the picture is not tested) |
| REQ-GA-038, 039, 040 | TC-GA-030 | pass |
| REQ-GA-041 | TC-GA-038 | pass; **V-1** (reproduced: the arrow keys throw) |
| REQ-GA-042, 043 | TC-GA-039 | pass |

**Accepted cases (binding map in `plan.md`).** Their witnesses are green: AC-009, AC-010, AC-011, AC-012, AC-013, AC-015, AC-016, AC-035, and AC-014 up to its save step. AC-014 is qualified by V-2. The demonstration of the exit criterion on the owner's host with `store: database` is still open (see Notes).

## Test requirements (M41)
| TR | Met | How verified |
|---|---|---|
| TR-VIEW-001 Both stores, skips visible | yes | 33 IF-104 v2 cases ran on mock, files and postgres 16 (local image), none skipped |
| TR-VIEW-002 Fixture graphs | yes | `tests/fixtures/graph_view/graphs.json` changed only by A-175 |
| TR-VIEW-003 Fresh stores and accounts | yes | read: `core_stores.fresh_backend` per check; the browser checks start a server per check and log in once |
| TR-VIEW-004 JS mock | yes | JS contract suite passes on the mock in the same run |
| TR-VIEW-005 Fake DOM | yes, with a limit | colour, focus and request claims are made only in Firefox. Limit: the fake DOM's `children` is an Array, which hid V-1 |
| TR-VIEW-006 Fault wrappers fire | yes | read in `test_view_backend.py` and the suite. The unreachable store is a wrapper only (V-3) |
| TR-VIEW-007 Store setting as in production | yes | TC-API-018, 019 go through a copy of the configuration and the environment |
| TR-VIEW-008 Firefox reference | yes | Playwright 1.64.1, pinned in `requirements-browser.txt`, installed in `mia312`; headless; viewport and timeout as required |
| TR-VIEW-009 One origin | yes | `tests/helpers/graph_view_server.py` |
| TR-VIEW-010 Settled | yes | `graphViewTest.settled` |
| TR-VIEW-011 Every request recorded | yes | `page.on("request")` from the first navigation |
| TR-VIEW-012 Keyboard only | yes, with a limit | key presses only. TC-GA-038's `reach()` falls back to Tab when an arrow key does not move the focus, so it does not see V-1 |
| TR-VIEW-013 Colours from the browser | yes, with a limit | V-12 h |
| TR-VIEW-014 Checks that wait for RULES | yes | RULES was merged at b961c573; TC-API-025 is green |
| TR-VIEW-015 Installed suites unchanged | yes | see the automated checks |
| TR-VIEW-016, 017 Smoke checks | Deploy | SMOKE-VIEW-001, 002 run in Deploy |
| TR-VIEW-018 Exact values | yes | read |
| TR-VIEW-019 Times | yes | read |
| TR-VIEW-020 File checks | yes | TC-GA-031 hashes bytes; TC-GA-032 scans as required. Also: `tokens.css` and `templates/static/chat/tokens.css` are byte-identical (`cmp`) |
| TR-VIEW-021 Each check able to fail | yes | All 32 checks have a logged defect run (`implementation-log.md`, one table per task; TC-GA-025 again after A-175). I repeated three in the fresh checkout, then restored it: the filter that ignores the description fails TC-GA-018, and a mark on every step fails TC-GA-024. For the origin check removed in the blueprint only, TC-API-024 stays green, see O-1 |

### My deliberate defects and reproductions (scripts in `specs/mia/goals/G-V4.VIEW/verify-repro/`, run as `<venv python> <script> <checkout>`; defect runs by hand in a fresh checkout)
| Run | Result |
|---|---|
| `list-filter.js` searches only the ID | TC-GA-018 fails (expected) |
| `step-marks.js` marks every step | TC-GA-024 fails (expected) |
| `graph_api_v2.py:340` blueprint origin check off | TC-API-024 still green: the app-wide guard (`accounts_api.install_guard`) refuses the foreign Origin first (O-1) |
| `repro_f1.py`: ArrowDown on the first graph entry in Firefox | the focus stays on `chain.fifty`; page error `list.children.filter is not a function` (**V-1**) |
| `repro_f3.py`: drag step.check by 100 px, then the colour scheme turns dark | x moves 967 → 1067 (dropped) → 902 after the switch (**V-2**) |
| `repro_f2.py`: Firefox with every cookie and site data blocked | `localStorage` throws `SecurityError`; 0 areas drawn, blank page (V-9). With only DOM storage switched off, the page works |

## Goal acceptance (supervised goal: for information)
| Item | State |
|---|---|
| Protected material identical to the baseline except approved amendments | yes (A-175) |
| Every in-scope requirement's check green | yes (70 of 70) |
| No frozen requirement changed against `goal/v4` | goal check: no new errors against the plan gate |
| Every stop logged instead of worked around | yes. F-1 became A-175; F-2 was decided by D-500; the plan deviations are logged per task |
| Exit criterion | not yet. OC-1 to OC-8 need the owner's look on the host with files and with `store: database` (Deploy, with SMOKE-VIEW-001, 002) |

## Code against the architecture
- `webApp.graphApiV2` → `graph_api_v2.py`, status `built`. The imports (`graph_model`, `graph_rule_set`, `storage`, `toolbox`, `workflow_library`, `accounts`) follow existing flows; `web_app.py` registers the blueprint under its session (REQ-API-030).
- `persistence.graphRecords` → `record_tables.py`, unchanged in the model (D-439).
- **V-13:** in `part def GraphApp` (`specs/mia/architecture.sysml:350` ff.), `pageFrame`, `graphList`, `detailsColumn` and `historyList` are still `proposed`. `graphView` is `partly` and names `graph_app/graph-view.js`, which the page no longer loads (D-500); the built modules (`viewer.js`, `drawing.js`, `api.js`, `adapter.js`, `panel.js`, `history.js`, `settings.js`, `arrangement.js`, …) are named nowhere.

## Specification vs. code (M42)
**Missing behaviour (specified, not or not fully done):** V-1 to V-5, V-8 to V-10 (findings below).

**Behaviour only in the code (P25).** The owner kept these for Verify:
- `onSelect` in the drawing interface
- the view settings in the picture's header (D-458)
- the store part without a visible heading (D-459)
- a step ID used twice is drawn once
- the two-line label
- a `remove_step` entry carries `connections`
- `changed_since_trusted` fixed false until CODE
- the store route's live and copy fields fixed until TRANSFER
- `graph-view.js` kept (D-500)

New, for the owner to accept or write into the specification (all low, V-14):
1. Untrusted steps get a dashed `--danger` border (`drawing.js:57`). This is beyond the one-word marks, and it looks like the dashes of a missing step.
2. The stored text of a missing step is shown as `{id, missing: true}` (`viewer.js:244`).
3. The settings key is `mia-graph-viewer-settings`; bad stored values are dropped silently.
4. The arrow keys move through the graph list. The interface note names them only for the step list.
5. "Arrangement on" settles once, then turns physics off.
6. Fixed layout numbers: layers 220 px apart, `avoidOverlap`, 400 iterations, `fit`.
7. "Reset to layers" is inside the settings popover.
8. Previous and Next work only after the history is opened.
9. The texts "version n of m" and "Nothing selected."
10. A transform step without trust is marked untrusted, but its trust fields are hidden in the left column.
11. Answers can arrive out of order when two graphs are opened quickly; nothing guards this.
12. Backend:
    - A step whose toolbox entry has an empty reason gets the made-up reason "it is in the toolbox" (`graph_api_v2.py:98`).
    - A restore to the current content writes nothing and answers `changed: false`.
    - A restore version that is not a whole number gives 404, not `invalid`.
    - Places are rounded half to even and have no size limit; extra keys in a place are dropped.
    - `store: database` without `MIA_DATABASE_URL` stops the start.

**Changes outside the Touches lists:** `README.md` (instead of `deploy/README.md`), `setup_cfg.example.json`, `deploy/setup_cfg.compose.json`, a comment in `deploy/compose.yaml`, `tests/test_record_tables.py`, `api.js` and `app.js` in T-07. All of them are logged in the implementation log; none is protected.

**Tests against their scenarios.** The acceptance tests follow their Given/When/Then and use the real `create_app`, the real `web_app` or the real page. Three are weaker than their scenarios suggest (V-12 g, h, and TC-GA-038, see V-1).

## Quality evidence per characteristic (M32)
| Characteristic | Evidence | Gap |
|---|---|---|
| Functional suitability | 70 requirements, 70 green checks | V-1 to V-5 |
| Performance efficiency | NFR-11 has no bound; SMOKE-VIEW-002 measures in Deploy | not now (D-425 E-H) |
| Compatibility | IF-104 v1 suites unchanged and green; IF-104 v2 the same on mock, files and postgres | – |
| Interaction capability | keyboard (TC-GA-038), light and dark (TC-GA-034), the owner's look (D-459) | V-1, V-2, V-8, V-10, V-11; NFR-10 in Validate |
| Reliability | TC-IF-104-26, TC-API-023 | V-3, V-6 |
| Security | session, Origin and owner on every write (TC-API-024, TC-IF-104-27, unit test without Origin); text only (TC-GA-035); nothing from outside (TC-GA-039); no HTML sinks | V-5 (a 500 leaks a werkzeug HTML page, no data) |
| Maintainability | one module per part; unit tests per helper | V-13 |
| Flexibility | store chosen by configuration (TC-API-018, 019) | – |
| Safety | not applicable (read-only viewer, no actuators) | – |

## Open deferrals (M26)
None in `specs/mia/deferred.md` touches VIEW.

## Review findings
| ID | Severity | Finding | Where | Destination |
|---|---|---|---|---|
| V-1 | medium | **The arrow keys in the graph list throw in Firefox** (REQ-GA-041). `list.children.filter(…)`: an `HTMLCollection` has no `filter`, so the focus does not move and a page error is raised. *Reproduced.* The fake DOM's `children` is an Array, and TC-GA-038 falls back to Tab, so no check sees it | `graph_app/viewer.js:86`; `tests/js/fake-dom.mjs:45`; `tests/acceptance/test_graph_view_browser.py:229` | Implement: a regression test first (unit test with an `HTMLCollection`-like `children`), then `Array.from`. Plan amendment (owner's choice): the browser checks fail on any `pageerror` |
| V-2 | medium | **A dragged step jumps back when the colour scheme changes** (REQ-GA-032, AC-014). The theme listener calls `drawing.show(drawing.data, …)` with the data of the last opening, so the graph settles again. *Reproduced* (x 1067 → 902) | `graph_app/drawing.js:117` | Implement: a regression test, then re-colour without a re-show. Plan amendment if a browser check should cover it |
| V-3 | medium | **A PostgreSQL store never recovers, and MIA does not start while the database is down** (REQ-API-021, 050). `PostgresBackend` opens one connection in `__init__` and never reopens it, and `web_app.py` builds the backend at import. A database restart leaves every graph route at 503 until MIA restarts; a database that is down at start stops the whole web app instead of answering `store_unreachable`. TC-IF-104-26 uses a wrapper that raises, never a real lost connection. MIA runs on files until TRANSFER's owner gate (D-460), so nobody feels this today | `storage_postgres.py:30`; `web_app.py:663-671, 723` | Plan amendment: `storage_postgres.py` (N-3.1) is outside VIEW's Touches. A reconnect or a lazily opened backend, with a check on a real stopped container; or hand it to TRANSFER |
| V-4 | medium | **The `before` of editor entries is stored as sent** (REQ-API-038, NFR-20). The play-back checks only `after`, so an entry with a false `before` is kept as an `editor` record and the history shows a false former value (reproduced by the Track A reviewer; I confirmed it in the code) | `graph_api_v2.py:172-183` | Implement (compare `before` with the current version, or record the server's value); or a Plan amendment if a check of `after` alone is meant |
| V-5 | low–medium | **Malformed steps or connections give a 500 HTML page** (REQ-API-048). Only "`nodes` and `edges` are lists" is checked; a connection without `id`, or with an object `id`, crashes in `derive`. Nothing is written | `graph_api_v2.py:240`, `:133` | Implement: a regression test, then `invalid` with detail `graph` |
| V-6 | low | **The stale-version check is not atomic with the write** (REQ-API-034). Two owner tabs that both save on version 4 get 5 and 6, and the record of 6 says `from_version: 4` | `graph_api_v2.py:266`, `:300` | Implement (a lock in `GraphWriter`), or accept: only the owner writes, and EDIT brings the page's save |
| V-7 | low | **Wrong value types do not give `invalid`** (REQ-API-048 against IF-104 v2's list). `expected_version: "2"` gives `conflict`; `changes: "x"` gives `changes_do_not_match`; `description: 5` gives `refused` | `graph_api_v2.py:170, 266` | Plan: decide which text binds, then Implement |
| V-8 | low | **A 401 while a graph is open leaves its content** (REQ-GA-022). The problem list, the step list, the left column (with the stored text) and the history stay; Previous and Next then send `GET /graphs/null?version=n` | `graph_app/viewer.js:107-114` | Implement |
| V-9 | low | **With cookies and site data blocked, the page stays blank** (REQ-GA-035 "with the storage blocked the page opens"). `app.js` reads `localStorage` outside any try. *Reproduced.* The same setting blocks the session cookie, so the page could only have shown the login note | `graph_app/app.js:10` | Implement |
| V-10 | low | **The store entry is set once** (REQ-GA-018 "whether that store answers"). After a later 503 it still says "reachable" beside "store does not answer" | `graph_app/viewer.js:204` | Implement, or a Plan note if "at start" is meant |
| V-11 | low | **Errors other than 401 and 503 show nothing** (a 404 between list and opening, a 500, MIA down) | `graph_app/viewer.js:120` | Plan: state the behaviour |
| V-12 | low | Evidence gaps: (g) selection by a click in the picture and "a click on empty space empties the column" (REQ-GA-036, 044) run in no test, and the `onSelect` path is untested; (h) TC-GA-034 compares the page's resolved `var(--text)` with itself, not with the colour given to the drawn labels; TC-IF-104-26 uses a wrapper, not a real outage (see V-3); no test of a restore by a non-owner (the code refuses it) | `tests/acceptance/test_graph_view_browser.py:141-144`; `graph_app/drawing.js:116` | Plan amendment (protected checks), or unit tests in `tests/js` for (g) |
| V-13 | low | The model's `GraphApp` parts are not updated after Track B (statuses and modules, see "Code against the architecture") | `specs/mia/architecture.sysml:350` ff. | Implement or Commit: update statuses and modules, then `check_sysml.sh` |
| V-14 | low | Behaviour only in the code, items 1 to 12 above | see above | Owner: accept, or write it into the specification (Plan) |
| V-15 | medium | **The release image with T-02's Containerfile has not been built; the offline delivery test fails** (`tests/test_delivery_on_stack.py`, REQ-OPR-011). The new pip layer is not in the podman cache, and the test never downloads. TC-OPR-011 only reads the file. Nothing is wrong in the code as far as I can see; the build needs network once | `deploy/Containerfile`; `tests/test_delivery_on_stack.py:139` | The owner builds the image once with network (`podman build -f deploy/Containerfile -t <image> .`), then I re-run the test; it also belongs to Deploy (SMOKE-VIEW-001) |

**Notes, no action:**
- **O-1:** the blueprint's own Origin check is defence in depth behind the app-wide guard. TC-API-024 can fail only when both are removed, and that is how the log ran its defect. The blueprint's stricter part (a write without `Origin` is refused) is covered by `tests/test_graph_api_v2.py:70`.
- `plan.md` says `test_view_backend.py` has 12 red tests; the file at the baseline has 9 test methods (8 TC-API plus TC-OPR-011), unchanged since. The difference is a counting slip in the plan.

## Accepted-deviation candidates
V-6, V-7, V-11, V-12, V-13 and the items of V-14. V-3 also qualifies if the owner hands it to TRANSFER, since MIA runs on files until TRANSFER's gate.

## Notes for Commit, Deploy and Validate
- **Close look at the page (the owner's rule), in Firefox:**
  - keyboard only: ArrowDown in the list (V-1), Enter, the step list, settings;
  - drag a step, then switch the system to dark (V-2);
  - open a graph, log out in the main app, then use History and Previous (V-8);
  - stop the store after opening: the band and the notice (V-10); stop MIA and click a graph (V-11);
  - `sample.broken`: can a missing step be told from an untrusted one (V-14 item 1)?
  - `chain.fifty`: zoom and readability after `fit`;
  - an empty store.
- **Deploy:** SMOKE-VIEW-001 (image with `psycopg`, `store: database`), SMOKE-VIEW-002 (opening time, measured); the owner's look with `store: database` (exit criterion).
- **Commit** (from `plan.md`): move the 70 requirements, the checks and TR-VIEW-001 to 021 into the node files; fill the Witnesses of AC-009 to AC-016 and AC-035; and the model (V-13).
- **Validate:** NFR-10 (first use without help), light and dark readability, the 220 px layers on large graphs.

## Owner's decisions on the findings (D-501, 2026-11-23)
| Finding | Decision |
|---|---|
| V-1, V-2 | back to Implement: a regression test first (unit test in `tests/js`), then the fix; no amendment of the protected checks |
| V-4, V-5 | back to Implement: regression tests first |
| V-3 | handed to G-V4.GRAPHSTORE.TRANSFER (makes the database store live); an accepted deviation of VIEW |
| V-8, V-9, V-10, V-13 | back to Implement |
| V-6, V-7, V-11, V-12, V-14 | accepted deviations; V-7, V-11 and the V-14 items written into the specification at Commit |
| V-15 | the owner builds the image once with network; then the reviewer re-runs `tests/test_delivery_on_stack.py`. **Done 2026-11-24:** the owner built `mia-view-check` (`podman build -f deploy/Containerfile`, psycopg 3.3.9 installed in the release stage); the offline delivery test then ran 5 tests in 50 s: OK. V-15 closed |

Re-verify after the fixes: the automated checks in full (protected diff, trace, goal and model checks, unit suite, every acceptance script, `tests/js`, Firefox checks three times), my reproductions `repro_f1.py`, `repro_f2.py`, `repro_f3.py` again, and a review of the fix commits only.

## Re-verify of the fixes (D-501, 2026-11-24)
**Reviewer:** an independent AI reviewer (Opus 5.5, a fresh session that did not write the fixes and never saw the implementation chat). **Branch:** `goal/v4.view` @ 673bdedc (fix range `f02c8f00..d8df65cf`, then two docs-only commits). Python 3.12 venv `mia312`, node, Playwright Firefox. All checks ran one after another in the worktree, which had no local changes.

**Automated checks (rerun in full)**
| Check | Result |
|---|---|
| Protected material since b961c573 | `tests/acceptance/graph_view_page.test.mjs`, `tests/fixtures/graph_view/graphs.json` and VIEW's `test-requirements.md` are byte-identical to `specs/mia/amendments/A-175/`. `.claude/settings.json` has the owner's +2 deny rules (D-446 (2)). The fix range touches no protected file |
| `test_view_backend.py` / `test_graph_view_files.py` | 9/9 / 2/2 |
| IF-104 v2 contract (Python) | 33/33: mock, files and PostgreSQL 16 under podman; none skipped |
| `graph_view_page.test.mjs` | 15/15 |
| `test_graph_view_browser.py` | 7/7 in each of three runs in a row (13, 12, 14 s) |
| `tests/js/*.test.mjs` | 230/230 (225 + 5 new) |
| Unit suite | Ran 2590 in 483 s, OK (5 skipped, 2 expected failures). The fifth skip is `test_delivery_on_stack`: "no model server answers" (Ollama was not running). V-15 stays closed on the owner's run of 2026-11-24, since the fix range does not touch `deploy/` |
| Every acceptance script, one at a time | 76 scripts: 74 exit 0. The 2 reds are the known `test_decide_guard.py` and `test_judge_calibration.py` (`behaviour` has no `FUNCTIONS`; G-V3.REPORT F-3) |
| `check_sysml.sh` (all models) / `check_sysml_model.py` | 4 files, 0 errors, 0 warnings / OK |
| `trace_check.py` / `goal_check.py` | 549 ERROR lines / 82 errors. Each is the same set, line for line, as a run on the plan gate's tree (39a47d7f) |

**The new tests are real regression tests.** I ran the 5 new JS tests and the 2 new backend tests against the tree before the fixes (`git archive f02c8f00`). All 7 fail there (`graph-settings.test.mjs` fails as a file, because `pageStorage` does not exist yet), and all pass on HEAD. Each test follows its Given / When / Then.

**Findings**
| Finding | Re-verify | Evidence |
|---|---|---|
| V-1 | **closed** | `Array.from(list.children)`. `repro_f1.py`: ArrowDown moves the focus `chain.fifty` → `chat`, no page error |
| V-2 | **closed** | The scheme listener updates `font`, `color` and `ctxRenderer` of the nodes and the edge options in place. These are all the colour-dependent properties `visNode` and `visOptions` set, so nothing keeps the old colour. No `setData`, the solver is not restarted. `repro_f3.py`: x 966.9 → 1066.7 (dropped) → 1066.7 after the theme switch, no error |
| V-4 | **closed** | `apply_change` compares each entry's `before` with the value `derive` would write. My probe: an addition with `before` null or missing is kept; with `{}` or `0` it is refused with `changes_do_not_match` |
| V-5 | **closed, in the narrowed form** (handover point 1) | A connection object without a text `id` now gets 422 `invalid`, detail `graph`, on save and check. My probe sent 16 malformed bodies (step id a list, object, number or missing; a step that is text or null; step data text or a list; a connection id that is a number; a connection without `from`; `from` a list or an object; a connection that is text; connection data a list or text; `description` a number). **None gives a 500**: save answers `invalid`, `rules_broken` or `refused`, and check answers 200 with the rule report or `invalid`. REQ-API-048's promise that a bad request is refused, writes nothing and is never a crash is met. Which error code binds for a wrong *type* (`rules_broken` or `refused` instead of `invalid`, e.g. connection data that is a list → `refused`) is the open question of V-7, already an accepted deviation; the V-5 question goes to Commit with it, as the log proposes |
| V-8 | **closed** | A 401 also empties the problem list, step list, selection and history, and switches the history buttons off. The new unit test sees no read of `null` |
| V-9 | **closed** | `repro_f2.py` cannot show it (it blocks every cookie, so `GET /graph/` answers 401: 0 areas before and after; the implementer reported the same). My own variant, `verify-repro/repro_f2_storage.py`, keeps the cookies and makes only the `localStorage` getter throw `SecurityError`. Before the fix: 0 areas, page error "The operation is insecure.". At HEAD: 8 areas, 6 entries, no error, and a graph opens |
| V-10 | **closed** | A 503 sets the entry to "not reachable" and the next answer sets it back. Without a 503 the entry keeps what the store route said at start, as the existing test expects (handover point 3) |
| V-13 | **closed** | `GraphApp` parts `built`. Every module the model names exists in `graph_app/`; `graph-view.js` is no longer named (D-500). Model checks 0/0 |
| V-15 | closed (unchanged) | owner's build and run, 2026-11-24 |

**New findings:** none. The fix commits change only the files of their tasks plus `architecture.sysml` (V-13), and add no behaviour beyond the finding they fix.

**Proposal: verified with accepted deviations** (V-3 handed to TRANSFER; V-6, V-7, V-11, V-12, V-14 accepted, D-501). For Commit: V-7, V-11, the V-14 items and the V-5 question go into the specification; then the close look at the page by the list in "Notes for Commit, Deploy and Validate".

- [ ] Re-verify accepted by the owner. Date:
