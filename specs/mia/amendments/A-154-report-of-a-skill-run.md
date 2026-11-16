# A-154 – Every skill run ends with a report (proposed 2026-11-16, FB-08)

Status: **Proposed** (all new items Draft; the owner reviews them one by one before they go into the node files).
Source: FB-08 (owner, 2026-11-16: sources in the Skill run view, Full run, after `/lookup`, should be hyperlinks). Decisions of the owner by questionnaire, 2026-11-16:

1. The report lives in a **run record field plus a file** of the files volume (the file is the download; the record names it).
2. REQ-CLV-043 gets an **exception for the report only**; every other text of a run stays plain text.
3. **Every skill run gives a short report**, also when it gives no output: a success or non-success message is written.
4. Placement: REQ-WFM and REQ-CLV, Draft, as an amendment.

Replaces the loose end of commit 36cc3a9 ("the report file of /lookup has no requirement"): `/lookup` is the first skill that writes such a report.
Not to be confused with REQ-WFM-038 (the structured report of `/review` as a database record) or REQ-WFM-036 (the spoken summary in the chat). Glossary term to add: **Run report** (the Markdown file that ends a skill run, named in its run record and shown in the Report part of the Full run).

## New requirements (Draft)

### REQ-WFM-139 – Every run ends with a report
- Level: low   Subject: TaskRuntime
- Text: When a skill run ends (done, stopped or failed), the Workflow management shall make sure that the run has a run report, a Markdown file of the files volume whose first line says whether the run succeeded, was stopped or failed, with the reason where there is one, also when the run gave no output; a skill writes its own report, and where it wrote none the Workflow management writes a short one from the run record (state, reason, result, figures).
- Rationale: refines REQ-BE-033; one place for what a run found, equal for every skill (owner 2026-11-16, FB-08); a run that gives nothing still says so
- Parent: REQ-BE-033
- Group: RV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a scripted run of each registered skill (lookup, review, search) that is done, one that is stopped and one that fails each leave a report file in the files volume whose first line names the state; a scripted skill that writes no report and gives no output still gets a report that says so (exact)
- Verified by: TC-WFM-139
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new

### REQ-WFM-140 – The run record names the report
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall hold the name of the run report in the field `report` of the run record when the run ends, and nothing in that field while the run is not over.
- Rationale: refines REQ-BE-033 and REQ-WFM-130; the Skill run view needs to know which of the files of a run is its report (a first `.md` file would be a guess); IF-101 v17
- Parent: REQ-BE-033
- Group: RV
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: the record of a running run has `report` empty; after the end it holds the name of the report file, which is one of the names in `files` and can be read from the files volume (exact)
- Verified by: TC-WFM-140, TC-IF-101 (contract v17)
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new; interface change IF-101 v16 to v17: one new field `report` (string or null) of the run record, no route changes

### REQ-WFM-141 – Addresses and texts in a report
- Level: low   Subject: TaskRuntime
- Text: The Workflow management shall write a web address in a run report as a link only where it is an http or https address without spaces, and write every other text that came from the web, a model or a user (answer, quote, title, reason) escaped, so that it forms no link, image, tag or script in a Markdown reader.
- Rationale: refines REQ-BE-033 and REQ-WFM-137; NFR-3; the sources are web text (TB-web, TB-result, OC-8 of G-V3); the file is also opened outside MIA
- Parent: REQ-BE-033
- Group: UT
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: reports of scripted runs whose sources and quotes are `javascript:alert(1)`, `data:text/html,...`, `file:///etc/passwd`, an address with `>` and a second link behind it, and the five hostile strings of TR-PANEL-005 contain no link whose target does not start with http:// or https://, and no unescaped tag or image (exact)
- Verified by: TC-WFM-141 (red-team case)
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new; first code: `research_chat.format_report` (36cc3a9)

### REQ-CLV-048 – Report part in the Full run
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall show in the Full run of the Skill run view an expandable part Report, whose summary line says the state of the run, that shows the run report of the run that is shown, and that has the download link of its file.
- Rationale: refines REQ-FE-032 (FR-46); the sources of a run are links in the window the owner looks at (FB-08)
- Parent: REQ-FE-032
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: in a headless browser after a scripted `/lookup`, the Report part is listed in the Full run with the state in its summary line, opens to the rendered report, and its download link is `/api/files/<name>` and returns the file byte for byte (exact)
- Verified by: TC-CLV-048
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new; split at the review of 2026-11-16 (REQ-CLV-050, 051 take the two other states)

### REQ-CLV-050 – Report part before the end of the run
- Level: low   Subject: WebFrontEnd
- Text: While the run that is shown has no report, the Chat and login views shall show in the Report part the sentence that the report comes when the run ends, and no download link.
- Rationale: refines REQ-CLV-048; a part that is empty without a word reads as broken
- Parent: REQ-FE-032
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-39: a scripted run that is still going shows the waiting sentence and no link; when the run ends the part shows the report without a reload (exact)
- Verified by: TC-CLV-050
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new, split from REQ-CLV-048

### REQ-CLV-051 – Report file that is gone
- Level: low   Subject: WebFrontEnd
- Text: Where the run report named in the run record is no longer in the files volume, the Chat and login views shall show in the Report part the sentence that the file was removed, and no download link.
- Rationale: refines REQ-CLV-048 and REQ-WFM-037 (the user deletes files in the volume, the record keeps the name)
- Parent: REQ-FE-032
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-39: after the report file is deleted in the volume the part shows the removed sentence and no link, and the rest of the Full run is unchanged (exact)
- Verified by: TC-CLV-051
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new, split from REQ-CLV-048

### REQ-CLV-049 – Links in the report
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall render the run report with the Markdown renderer of the messages, so that an http or https address is a link that opens in a new tab with `rel="noopener noreferrer"` and an address of any other kind stays text.
- Rationale: refines REQ-FE-032 and REQ-CLV-043; the one text of a run that may start an action, because the user clicks it and the owner asked for it (FB-08); the renderer of the chat (marked, DOMPurify) is the tested path
- Parent: REQ-FE-032
- Group: UT
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a report with a plain URL, a source without a URL, a `javascript:` URL, a `data:` URL and a URL inside Markdown text is shown with links only for the http and https addresses, each with target `_blank` and rel `noopener noreferrer` (exact)
- Verified by: TC-CLV-049 (browser), unit tests in `tests/js/` (renderer)
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new; split at the review of 2026-11-16 (REQ-CLV-052 takes the active content)

### REQ-CLV-052 – No active content from the report
- Level: low   Subject: WebFrontEnd
- Text: The Chat and login views shall let no image, script, style, form, frame or event handler of a run report come into the page, and shall make no request to another host when they show it.
- Rationale: refines REQ-FE-032 and REQ-CLV-043; NFR-3, TB-web and TB-result (OC-8 of G-V3); the report holds web text
- Parent: REQ-FE-032
- Group: UT
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-39: a report with the five hostile strings of TR-PANEL-005 and an `<img>` with an onerror handler is shown with no `script`, `img`, `link`, `iframe`, `style` or `form` node, no alert and no request to another host (exact)
- Verified by: TC-CLV-052 (browser, red-team case), unit tests in `tests/js/` (renderer)
- Status: Draft
- History: A-154 (proposed 2026-11-16, FB-08), new, split from REQ-CLV-049

## Changes of approved items

| Item | Change | Needs |
|---|---|---|
| REQ-CLV-043 | Text: "... shall show every text of a run (result, material found, answers, reason) as plain text that starts no action and loads nothing, **except the run report (REQ-CLV-048, REQ-CLV-049)**." Rationale: add "the report is the one text that may hold links, A-154". AC-39 unchanged for all other texts | amendment approved; status back to Draft until re-verified |
| REQ-WFM-137 | Text: add "report" to the list "(result, material, answers, reason, report)" | amendment approved |
| IF-101 | v16 to v17: field `report` in the run record (REQ-WFM-140); contract suite and mock follow | contract change by the owner of the interface |
| TC-CLV-043 / `tests/acceptance/test_skill_run_view_browser.py` | the probe "hrefs only `/api/files/<encoded>`" must leave the Report part out and check it under TC-CLV-049; the hostile strings stay in force everywhere else | **protected: plan amendment**, an agent must not edit it |
| TR-PANEL-005 | the fixed hostile list also applies to the report (TC-CLV-049, TC-WFM-141) | protected |

## Parts and code (for the plan, not decided here)

- Back end: a report writer used by every skill (a skill hands over its Markdown or nothing), the runtime fallback of REQ-WFM-139, the field `report` in `skill_runs.py` (`end(...)`), `chat_service.py` (the end of a task, also stopped and failed runs). `/lookup` is done in 36cc3a9 (file only, no field, no outcome line); `/review` already writes a `.md`; `/search` writes none.
- Front end: `skill-run.js` `drawFull` gets the Report part; the renderer is `markdown.js` (`renderMarkdown`). Only the report goes through it, the other texts stay `textContent` (REQ-CLV-043).
- Model: SysML parts and the glossary term "Run report", `check_sysml.sh` after the edit.
- Skill versions: `lookup` and `review` change tools/output, so their manifest versions are bumped in the task (TD for the skill-record sync).

## Open points for the owner (defaults proposed)

1. **Open or closed?** The Report part is open when the run has ended, closed while it runs (default).
2. **Stopped run:** the report says "stopped" and holds what was found until then (default).
3. **Long reports:** the view shows the first 200 KB and the download has the rest (default; the files volume already has a limit per file).
4. **The result text of the run** stays as it is; the report is a second view of it, not a replacement (default).

## Tests to write first (red), by item

| Item | Test | Where |
|---|---|---|
| REQ-WFM-139, 140, 141 | scripted runs of all skills, done, stopped and failed; record field; red-team strings | `tests/` (unit, new) and the contract suite for IF-101 v17 (protected, after approval) |
| REQ-CLV-049 | renderer red-team and the four cases: plain URL, source without URL, `javascript:` URL, URL inside Markdown text | `tests/js/` (new unit test) |
| REQ-CLV-048 | the Report part in a headless browser | protected acceptance, after approval |

## Review (one item per question, reviewer maldun)

The items are not in the node files yet, so `req_review.py` cannot fingerprint them; this table is the record until they move in.

| Item | Result | Reviewer | Date | Note |
|---|---|---|---|---|
| REQ-WFM-139 | approved as written | maldun | 2026-11-16 | |
| REQ-WFM-140 | approved as written | maldun | 2026-11-16 | IF-101 v17 still needs the contract-change step |
| REQ-WFM-141 | approved as written | maldun | 2026-11-16 | not split |
| REQ-CLV-048 | split into REQ-CLV-048 (part, state, download), REQ-CLV-050 (waiting), REQ-CLV-051 (file gone) | maldun | 2026-11-16 | the three are reviewed one by one; IDs 050, 051 are outside the range 030 to 049 of the plan, to be extended |
| REQ-CLV-048 (after split) | approved as written | maldun | 2026-11-16 | |
| REQ-CLV-050 | approved as written | maldun | 2026-11-16 | |
| REQ-CLV-051 | approved as written | maldun | 2026-11-16 | |
| REQ-CLV-049 | split into REQ-CLV-049 (links) and REQ-CLV-052 (no active content) | maldun | 2026-11-16 | both reviewed one by one |
| REQ-CLV-049 (after split) | approved as written | maldun | 2026-11-16 | note for Implement: the chat renderer (markdown.js ALLOWED_URI_REGEXP) also lets mailto:, /path and #anchor through; for the report only http and https may be links, so the report needs its own URI rule, not the chat's |
