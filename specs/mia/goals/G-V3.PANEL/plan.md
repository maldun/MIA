# Plan: G-V3.PANEL (the Skill run view)

**Goal:** specs/mia/goals/G-V3.PANEL/goal.md   **Requirements:** REQ-FE-032 (N-1), REQ-CLV-024 and 030..047 (N-1.1), REQ-WFM-031, 036 (the link and the failure message belong to G-V3.CHAT), 038, 039 and 130..138 (N-2.3), REQ-RTB-007 (N-3.3), the contracts IF-101 v16, IF-302 v8, IF-102 v4 (A-140, A-141)   **Status:** Approved (owner maldun, 2026-11-08, task by task in three batches, D-307)

Line of work `goal/v3.panel`; supervised; no model step, no prompt, no eval suite. The red tests were written first in a session of their own (Step 4, commits `2f8867f`, `72bce48`, `e705709`) and installed by the owner; the implementing sessions never edit `tests/acceptance/`, `tests/helpers/`, `contracts/`, `eval/` or `test-requirements.md` (a change there is a plan amendment).

## Interface fixed by the red tests
The stubs carry the interface the installed tests expect; the tasks replace the stubs and keep these signatures.
- `skill_runs.py` (root, N-2.3): `SkillRunRecorder(storage, emit, clock=time.monotonic, now=None)` with `start(run, skill, version, account, phases=())`, `phase(run, name)`, `report(run, budget=None, counts=None, elements=None)`, `answer(run, text)`, `file(run, name)`, `end(run, state, reason=None, result="", material=())`, `record(run)`, `shown(account)`; the constructor subscribes to the table `history`, a notice with `version: None` deletes the run records of the account named in `author` (owner decision 2026-11-08). Note: `specs/mia/goals/G-V3.PANEL/run-recorder-interface.md`.
- `templates/static/chat/skill-run-model.js`: `headerModel`, `phaseModel`, `meterModel`, `applyStatus`, `controlsModel`, `controlAction`, `shownModel`, `elementsModel`. Note: `skill-run-view-interface-note.md`.
- Page hooks: `#skill-run-view`, `#srv-header`, `#srv-state`, `.srv-phase`, `.srv-meter[data-key]`, `.srv-count[data-key]`, `#srv-pause`, `#srv-resume`, `#srv-stop`, `#srv-reason`, `#srv-elements`, `#srv-empty`, `details#srv-full` with `#srv-result`, `#srv-answers`, `#srv-material`, `#srv-files`, `#srv-counts`, `#srv-share-strip`, `#srv-share-full`, `a.run-link`, `#character-box`, `#chat`.
- Record tables: `definitions()` names `skill_runs` (versioned, deletable), `validate("skill_runs", doc)` needs run, skill, skill_version, account, started, state.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 Table skill_runs in the Record tables and the storage | REQ-RTB-007, IF-302 v8, IF-102 v4 | TC-RTB-007; TC-IF-302-01 and -08, TC-IF-102-12 on the real providers | red tests installed |
| T-02 Run recorder | REQ-WFM-130, 131, 132, 133, 134, 135, 137, 138, 031 | TC-WFM-130..135, 137, 138 | T-01 |
| T-03 Spike: the events of a skill today, and the real-backend start of TC-CLV-038 | – (fixes REQ-WFM-136 and TC-CLV-038) | **done 2026-11-08**: the note `skill-events-today.md` is approved (D-309); no test | T-02 |
| T-04 Skill-runner adapter and the tests TC-WFM-136 and TC-CLV-038 | REQ-WFM-136, 130, 036 (failure and end hand-over only) | TC-WFM-136, TC-CLV-038 (both written first, Step 4b) | T-03 |
| T-05 IF-101 v16 on the real backend | REQ-API-015 (realise IF-101), REQ-WFM-134, 135 | TC-IF-101-31, -30, -34..39 on the real provider | T-02, T-04 |
| T-06 JS model of the view | REQ-CLV-030, 031, 032, 033, 034, 039, 044 | `tests/js/skill-run-model.test.mjs` (7 tests) | red tests installed |
| T-07 The strip: header, phases, meters, controls, reason, elements, empty view, text as text | REQ-FE-032, REQ-CLV-030..035, 039, 043, 044 | TC-CLV-030, 032, 035, 043 (browser) with T-06 | T-05, T-06 |
| T-08 Full run part, link from the chat, history and reload | REQ-CLV-024, 036, 037, 038 | TC-CLV-036, 037, 038 | T-07 |
| T-09 Layout, sizes, phone, shares in the browser | REQ-CLV-040..042, 045, 046, 047 | TC-CLV-040, 041, 042, 045, 046, 047 | T-07 |
| T-10 Retire the status card and its tests; document | REQ-CLV-023 (superseded), REQ-WFM-031 (reworded) | the old card tests removed or rewritten for the view (A-131 list), all other tests unchanged, README updated | T-08, T-09 |

## Tasks

### T-01: Table skill_runs in the Record tables and the storage
- Implements: REQ-RTB-007 (IF-302 v8, IF-102 v4, A-141)
- Tests to turn green: TC-RTB-007 (`tests/acceptance/test_skill_runs_table.py`); the real variants of TC-IF-302-01 and TC-IF-302-08 (`test_if_302_record_tables.py`) and TC-IF-102-12 (`test_if_102_storage.py`, with `tools/contract_postgres.sh` for the PostgreSQL backend)
- Touches: `record_tables.py` (DEFINITIONS, REQUIRED), the table list of the storage layer (`storage.py`, `storage_files.py`, the PostgreSQL backend and its schema if tables are listed there)
- Must not touch: protected material (above), `graph_tables.py`, `graph_rules.py`
- Depends on: red tests installed
- Done when: the listed tests are green on the file backend and, where podman and the image exist, on PostgreSQL; all other tests unchanged (the count of tables in REQ-RTB-001 changes from 14 to 15: the old test of the table list, if any, is a finding, not edited here)
- Notes: smallest task, run first; no new dependency

### T-02: Run recorder
- Implements: REQ-WFM-130, 131, 132, 133, 134, 135, 137, 138; REQ-WFM-031 (the monitor is created per run)
- Tests to turn green: TC-WFM-130, 131, 132, 133, 134, 135, 137, 138 (`tests/acceptance/test_skill_runs.py`)
- Touches: `skill_runs.py` (replace the stub), `task_monitor.py` only if the recorder needs a hook (the monitor stays usable alone: `tests/test_task_monitor.py` unchanged)
- Must not touch: protected material, `chat_service.py`, `pipeline.py`
- Depends on: T-01
- Done when: the listed tests are green, `tests/test_task_monitor.py` and all other tests unchanged
- Notes: texts are stored as given and never interpreted (WFM-137); a record has one version per change; `elements` is stored in the record although IF-302 v8 and the IF-101 run record do not list it: an open finding (owner decision pending), the tests follow the requirement; `shown(account)` is the run started last while any runs, else the one ended last

### T-03: Spike: the events of a skill today
- Implements: – (fixes the open parts of REQ-WFM-136 and TC-CLV-038)
- Tests to turn green: none; the result is a note `specs/mia/goals/G-V3.PANEL/skill-events-today.md`: which events and calls the review, lookup and search tasks send today (`chat_service.py` `pipeline_event`, `TaskMonitor`, `ask`, `_file_putter`, the task registry), how they map to the recorder calls, and how a test starts the real backend twice on file-backed storage with a seeded run record
- Touches: nothing (read only)
- Must not touch: everything
- Depends on: T-02
- Done when: the note is approved by the owner (decisions as a questionnaire), then the two missing tests (TC-WFM-136, TC-CLV-038) are written in a session of their own (Step 4b) and installed by the owner
- Notes: no adapter code before the note is approved

### T-04: Skill-runner adapter
- Implements: REQ-WFM-136 (runs without knowledge of the view), REQ-WFM-130 for lookup, search and review
- Tests to turn green: TC-WFM-136 (Step 4b)
- Touches: a new module `skill_run_observer.py` next to `chat_service.py` with the class `SkillRunObserver` (note `skill-events-today.md`, D-309), the six places in `chat_service.py` (start, phase, report, answer, file, end) only to call it, `task_monitor.py` (an optional `elements` argument of `update`, with T-02), the manifest field `phases` (REQ-WFM-039) and the phase strings of the review (`extensions/review/manifest.json`, `review_chat.py`: the review declares the names of its stages and sends exactly these names; a phase text that is not a declared name is not a phase change)
- Must not touch: protected material, the other skills and manifests (lookup and search declare no phases and are not changed), `pipeline.py`
- Depends on: T-03
- Done when: the listed test is green, all other tests unchanged, no skill file names the view (inspection part of TC-WFM-136)
- Notes: lookup and search have no phases (REQ-BE-078); material stays empty for today's skills; the review's manifest gets the `phases` field of REQ-WFM-039 and its phase strings are aligned to the declared names (a change of the review's strings, not of its interface; REQ-WFM-136 "without a change of the skill" is read as: no change for the view)

### T-05: IF-101 v16 on the real backend
- Implements: REQ-API-015 (realise IF-101), REQ-WFM-134, REQ-WFM-135 (the history deletion reaches the recorder), the wire of A-140
- Tests to turn green: TC-IF-101-31, -30, -34, -35, -36, -37, -38, -39 on the real provider (`test_if_101_chat_api.py`, the `_real` variants; the mock variants stay green)
- Touches: `chat_api.py`, `chat_ops_api.py`, `chat_service.py` (the task_status fields, the marker `skill_run`, the end text with the link, no `Files:` suffix, the failure message with the reason), `web_app.py` (routes `/api/skill-runs/shown`, `/api/skill-runs/<id>`, event `skill_run_changed`)
- Must not touch: protected material, `contracts/`, the mock
- Depends on: T-02, T-04
- Done when: the listed tests are green, TC-IF-101-24 and all other tests unchanged
- Notes: the end summary text itself is worded by G-V3.CHAT; until then the real backend gives the result text with the link added by code (the link form `[Open in the Skill run view](#run=<id>)`); `ui/tools/chat_mock_server.py` and its users are checked for the changed text

### T-06: JS model of the view
- Implements: REQ-CLV-030, 031, 032, 033, 034, 039, 044 (model part)
- Tests to turn green: `tests/js/skill-run-model.test.mjs` (TC-CLV-030, 031, 032, 033, 034, 039, 044)
- Touches: `templates/static/chat/skill-run-model.js` (replace the stub); may reuse `task-card-model.js` (`budgetText`)
- Must not touch: protected material, `task-card-model.js` itself (T-10 retires it)
- Depends on: red tests installed
- Done when: the 7 tests are green, `node --test "tests/js/*.test.mjs"` shows no new failure
- Notes: pure functions, no DOM; no dependency can be added (CLAUDE.md)

### T-07: The strip
- Implements: REQ-FE-032, REQ-CLV-030..035, 039, 043, 044 (page part)
- Tests to turn green: TC-CLV-030, 032, 035, 043 in `tests/acceptance/test_skill_run_view_browser.py` (scenarios header, meters, reason, hostile)
- Touches: `templates/index.html` (the view element and its hooks), a new `templates/static/chat/skill-run.js`, `socket.js` and `app.js` (wiring of `task_status`, `skill_run_changed`, the shown run), `components.css` and `messages.css`
- Must not touch: protected material, `chat.js` message rendering except what the removal of the card needs (T-10)
- Depends on: T-05, T-06
- Done when: the listed browser scenarios are green, the JS tests still green, no other browser test newly red
- Notes: texts go in as text nodes only (no `innerHTML`); the page sends one request per press and shows the state the backend reports

### T-08: Full run part, link, reload
- Implements: REQ-CLV-024 (files list in the view), 036, 037, 038
- Tests to turn green: TC-CLV-036, 037 (browser scenarios full, link), TC-CLV-038 (Step 4b)
- Touches: the page files of T-07, the link handling in `markdown.js` or `chat.js` (`a.run-link`, `#run=<id>`), the files list code that moves from the Files tab into the view
- Must not touch: protected material
- Depends on: T-07
- Done when: the listed tests are green, the files list behaviour of TC-CLV-024 (redraw after `files_changed`, no delete control) is kept in the view
- Notes: the page asks `GET /api/skill-runs/shown` on load and again after `skill_run_changed`

### T-09: Layout, sizes, phone, shares
- Implements: REQ-CLV-040, 041, 042, 045, 046, 047
- Tests to turn green: TC-CLV-040, 041, 042, 045, 046, 047 (browser scenarios layout, size, phone, shares, persist, scroll)
- Touches: `layout.css`, `layout.js`, `index.html`, `storage.js` (the shares, with the blocked-storage fallback), `settings.js`
- Must not touch: protected material, the character view (`character.js`) except its box size
- Depends on: T-07
- Done when: the listed scenarios are green at 1440 x 900, 1920 x 1080 and 360 x 800 px; the dark theme is run as TR-PANEL-001 asks (open: the driver covers the light theme only)
- Notes: defaults 16 % and 34 %, ranges 12 to 40 % and 20 to 60 %; 44 px targets on the phone layout only (REQ-CLV-042)

### T-10: Retire the status card, document
- Implements: REQ-CLV-023 (superseded by REQ-CLV-030 to 039), REQ-WFM-031 (reworded)
- Tests to turn green: none new; the old card tests (`tests/test_task_files_browser.py` card scenario, `tests/js/taskcard.test.mjs`, `tests/browser/task_files.py` card) are removed or rewritten for the view as listed in A-131; TD-01 moves to REQ-CLV-038 in `deferred.md` (needs the `Relaxed:` and `Target:` lines on REQ-CLV-038: a requirement change, owner approval first)
- Touches: `task-card.js`, `task-card-model.js` (removal), the old tests named above, `ui/README.md`, `CHANGELOG.md`
- Must not touch: protected material, `deferred.md` and the requirement texts without approval
- Depends on: T-08, T-09
- Done when: no card in the chat, all remaining tests green except the ones that wait for G-V3.CHAT, documentation updated

## Split check
10 tasks, above the usual 8. The cut would run between T-01 to T-05 (the run records and the wire, no browser) and T-06 to T-10 (the page), which can run in parallel after the red tests. **Decided by the owner (2026-11-08, D-307): keep one plan and one line of work**; the page needs the wire from T-05 for its browser checks, and each half already ends with checks of its own.

## Open before Implement starts
1. TC-WFM-136 and TC-CLV-038 are written in a session of their own (Step 4b); the T-03 spike note is approved: TC-WFM-136 against the observer, TC-CLV-038 with a new stub `ui/tools/real_backend_stub.py` (the chat stub server with a data folder and a seeded account, started twice with the folder mounted read-write; tried first, reported if it does not start).
2. TR-PANEL-001 (the harness versions were added in Step 4) is to be marked again in `req_review`.
(Closed on 2026-11-08: `elements` in the run record by A-143, D-306; the dark theme in the browser driver; the `starter` flag of the `skill_turns` suites.)
