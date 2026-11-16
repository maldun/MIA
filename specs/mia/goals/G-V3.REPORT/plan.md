# Plan: G-V3.REPORT (a report at the end of every skill run)

**Requirements:** REQ-WFM-139, 140, 141 (N-2.3), REQ-CLV-048 to 052 (N-1.1), changed REQ-CLV-043 and REQ-WFM-137; amendment `specs/mia/amendments/A-154-report-of-a-skill-run.md`, decision D-340.   **Status:** Approved (the checks reviewed one by one and the design decisions answered by the owner, 2026-11-16, D-341; `plan-review.md`). Open before T-04: the browser checks (decision 6)

## Deployment and feedback (M51)
- Environment for the current-state deployment: none: the goal is a change of the existing page and the skills; the owner tries it on the running MIA (`/lookup` question, Full run, Report part)
- Deploy command: as today (`deploy/build.sh`, unchanged); Early tasks: none
- Feedback slices: T-01 to T-02 (back end, visible in the files list and the run record), T-03 to T-04 (the Report part); not done yet: all
- Living prototype (M46): none: short goal
- Source of each fact (P26): requirements.md of N-2.3 and N-1.1 → mirror; satisfy and allocate links in `architecture.sysml`

## Design decisions the tests rely on (approved by the owner, D-341)
1. **The skill hands its report to the runtime** through a new need `run_report` (`run_report(markdown)`), next to `files`, `reports` and `monitor`; it is added to `NEEDS` of `extension_loader.py` and to the objects `chat_service.py` hands over. A skill that does not ask for it gets the runtime's fallback report. (The need `reports` stays for the structured record of REQ-WFM-038.)
2. **The runtime owns the file and the first line.** It stores the report as `<skill>-<date>-<question words>.md` in the files volume (the name rule of `file_store.py`), puts one line at the top that names the state (`Done`, `Stopped` or `Failed`, with the reason of a failure on the same line), then a blank line, then the skill's own text unchanged. The fallback body is built from the record: result, reason, figures; an empty result says `no output`.
3. **The record names it:** `report` in the run record (`skill_runs.py`, IF-101 v18, IF-302 v12), empty until the run ends; the file is also in `files`.
4. **Text rules (REQ-WFM-141):** a web address is written as `<address>` only if it is http or https without spaces; all other text of the runtime body is escaped (every Markdown and HTML special character with a backslash). A skill's own text is the skill's to escape (`research_chat.format_report` does it for `/lookup`).
5. **Front end (REQ-CLV-049, 052):** the pure rule `reportHref` in `markdown.js` and `renderReport` (marked and DOMPurify with its own URI rule, no image, no form, no frame); the Report part is a `<details>` in the Full run that fetches `/api/files/<name>`.
6. **Browser checks (decided, D-341):** TC-CLV-048, 050, 051 and the browser half of TC-CLV-052 are written as a second payload once the owner has built the browser image `localhost/mia-browser` (`tests/browser/Containerfile`); the stub server `ui/tools/skill_run_stub_server.py` gets a scripted run with a report with that payload. T-04 starts after it is installed.

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 | REQ-WFM-139, 140, 141, REQ-WFM-137 (report is stored as data) | TC-WFM-139, 140, 141, TC-IF-101-41, -42 (real variants), TC-IF-302-08 | red tests installed |
| T-02 | REQ-WFM-139 for the three skills | `tests/test_lookup_report.py` (adapted), new unit tests for `/review` and `/search` reports | T-01 |
| T-03 | REQ-CLV-049, 052 (renderer) | TC-CLV-049 and the unit half of TC-CLV-052 (`tests/js/report-render.test.mjs`) | – |
| T-04 | REQ-CLV-048, 050, 051, REQ-CLV-043 (exception) | TC-CLV-048, 050, 051, TC-CLV-052 (browser; written first, see decision 6) | T-01, T-03, browser tests installed |
| T-05 | documentation, skill versions, FB-08 | docs run; `trace_check`, `goal_check`, `check_sysml` clean | T-02, T-04 |

## Tasks

### T-01: The run report in the runtime
- Implements: REQ-WFM-139, 140, 141; REQ-WFM-137 (the report is stored as data)
- Tests to turn green: TC-WFM-139, 140, 141 (`tests/acceptance/test_skill_run_report.py`); the real variants of TC-IF-101-41 and -42; TC-IF-302-08 stays green
- Touches: `run_report.py` (new: the state line, the fallback body, the escaping), `chat_service.py` (the object `run_report`, the report at the end of every task run, also stopped and failed), `skill_runs.py` (`end(..., report=)`, the field in `record`), `extension_loader.py` (`NEEDS`), `architecture.sysml` only if a part changes
- Must not touch: protected material, the skills, the front end
- Depends on: red tests installed (`plan-step4/protected.patch`)
- Demonstrator after this task: after any `/lookup` the files list holds a report file and the run record names it
- Done when: the listed tests green, all other tests unchanged
- Notes: the ChatService already keeps the files of a run through `_file_putter`; the report is put through the same path so it is in `files`. The first line wording is not fixed by a requirement: the tests accept `Done`/`succeeded`, `Stopped`, `Failed` (any case).

### T-02: The skills hand over their reports
- Implements: REQ-WFM-139 for `lookup`, `review`, `search`
- Tests to turn green: `tests/test_lookup_report.py` (adapted to `run_report`), new unit tests for the `/review` and `/search` reports (`tests/test_review_report.py`, `tests/test_search_report.py`)
- Touches: `extensions/lookup/` (manifest needs `run_report` instead of `files`, `entry.py`), `research_chat.py` (the interim `files=` of 36cc3a9 becomes the hand-over), `extensions/review/` (hands its Markdown report over; the `.md` and `.tex` files stay), `extensions/search/` (query and results, escaped), the manifests' `version`
- Must not touch: protected material, `chat_service.py`
- Depends on: T-01
- Demonstrator after this task: a `/lookup` report with its sources as links, downloadable
- Done when: the listed tests green, all other tests unchanged
- Notes: every manifest version is bumped (the skill-record sync compares it); `/search` has no model, so no eval is needed (no prompt, no model step in this goal).

### T-03: The renderer of the report
- Implements: REQ-CLV-049, REQ-CLV-052 (unit half)
- Tests to turn green: TC-CLV-049 and the unit half of TC-CLV-052 (`tests/js/report-render.test.mjs`)
- Touches: `templates/static/chat/markdown.js` (`reportHref`, `renderReport`), nothing else
- Must not touch: protected material, `renderMarkdown` and its hooks (the chat messages keep their rules: mailto and relative links stay as they are there)
- Depends on: –
- Demonstrator after this task: none visible (merge into T-04 if a reviewer prefers)
- Done when: the listed tests green, `node --test "tests/js/*.test.mjs"` unchanged otherwise
- Notes: DOMPurify hooks are global to the library: the report must not leave its rules installed for the chat (use `DOMPurify.removeHook` or a second instance); a browser test covers this in T-04.

### T-04: The Report part in the Full run
- Implements: REQ-CLV-048, 050, 051; REQ-CLV-043 (exception), REQ-CLV-049 and 052 in the page
- Tests to turn green: TC-CLV-048, 050, 051 and the browser half of TC-CLV-052 (after decision 6), TC-CLV-043 stays green
- Touches: `templates/index.html` (the part), `templates/static/chat/skill-run.js` (`drawFull`: the part, the three states), `skill-run-model.js` (the model of the part), `templates/static/chat/i18n/*` (three sentences), `ui/tools/skill_run_stub_server.py` (a scripted run with a report), `ui/README.md`
- Must not touch: protected material; the other texts of the view stay `textContent` (REQ-CLV-043)
- Depends on: T-01, T-03; the browser tests installed
- Demonstrator after this task: the owner's wish of FB-08: the sources in the Full run are links
- Done when: the listed tests green, all other tests unchanged
- Notes: the download is the existing `/api/files/<name>` link; the part is open once the run has ended (open point 1 of A-154).

### T-05: Documentation, versions, records
- Implements: documentation (M21), FB-08 closed as Planned to Done, Phases table of the goal
- Tests to turn green: `trace_check.py`, `goal_check.py`, `check_sysml.sh`, `check_sysml_model.py`
- Touches: `ui/README.md`, `specs/mia/feedback/FB-08.md`, `goals/G-V3.REPORT/goal.md` (Phases and status), `implementation-log.md`
- Must not touch: protected material
- Depends on: T-02, T-04
- Done when: the listed checks clean (the errors that were there before stay as they are)
- Notes: Verify runs in a fresh context before the merge (goal Phases table).

## Size check
Five tasks, two nodes, no new part; the review of the checks fits one sitting (5 acceptance tests, 2 contract tests, 6 unit tests, 4 browser tests still to write).
