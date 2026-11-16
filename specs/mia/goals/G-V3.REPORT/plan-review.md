# G-V3.REPORT – review of the checks (Plan, step 3 and 4)

One check at a time with its scenario (M38); reviewer maldun. The checks are in the `test-spec.md` of N-2.3 and N-1.1 and in the red tests installed with `plan-baseline-g-v3-report`; the decisions of `plan.md` follow after the checks.

| Item | Result | Reviewer | Date | Note |
|---|---|---|---|---|
| TC-WFM-139 | approved as written | maldun | 2026-11-16 | not split |
| TC-WFM-140 | approved as written | maldun | 2026-11-16 | |
| TC-WFM-141 | approved as written | maldun | 2026-11-16 | red-team case; no case added |
| TC-CLV-048 | scenario approved as written | maldun | 2026-11-16 | the browser test is not written yet (plan.md decision 6) |
| TC-CLV-049 | approved as written | maldun | 2026-11-16 | |
| TC-CLV-050 | scenario approved as written | maldun | 2026-11-16 | the browser test is not written yet |
| TC-CLV-051 | scenario approved as written | maldun | 2026-11-16 | the browser test is not written yet |
| TC-CLV-052 | scenario approved as written | maldun | 2026-11-16 | unit half written, browser half not written yet; the hook-leak case is in the notes of T-03 (plan.md) |
| TC-IF-101-41 | approved as written | maldun | 2026-11-16 | |
| TC-IF-101-42 | approved as written | maldun | 2026-11-16 | no stopped-run contract check added |
| TC-IF-302-08 (change) | approved as written | maldun | 2026-11-16 | names the field `report` (IF-302 v12) |

## Design decisions of `plan.md` (owner by questionnaire, 2026-11-16, D-341)

| Decision | Answer |
|---|---|
| 1 How a skill hands over its report | a new need `run_report(markdown)` (not a naming rule on files, not a return value) |
| 2 Who owns the report file and its first line | the runtime: file name `<skill>-<date>-<question words>.md`, first line Done, Stopped or Failed (reason of a failure on the same line), then the skill's text unchanged; fallback body from the record, an empty result says "no output" |
| 6 Browser checks TC-CLV-048, 050, 051, 052 (browser half) | the owner builds the image `localhost/mia-browser` (`tests/browser/Containerfile`); the tests, the scripted run with a report in `ui/tools/skill_run_stub_server.py` and the test methods are written as a second payload (`protected.patch`), red first, in a fresh context before T-04 |
