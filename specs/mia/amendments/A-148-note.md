# A-148: REQ-FE-032 gets a check of its own (finding F-11, owner G-V3.PANEL)

Status: **approved** (2026-11-13, maldun, by the answer "approve" to the five drafts as written; D-number and review-log row follow).

## Why
`req_graph` G7 reports REQ-FE-032 (Skill run view) without a verifying check; it is among the 27 errors of the tag. The children REQ-CLV-030 to 047 verify it piece by piece.

## Change
In `nodes/N-1-web-frontend/requirements.md` the line "Verified by:" of REQ-FE-032 names the checks of its children that together show the view: TC-CLV-030, -031, -032, -033, -034, -036, -040 (status, phases, meters, controls, answers, full part, layout). No new test. `architecture.sysml` keeps `verifiedBy = (test, demonstration)`; the demonstration is VAL-012 (the look in the real window). History line: A-148.

## Done (2026-11-13), mechanism corrected
`req_graph` does not read the "Verified by" line of a requirement; it reads the column Verifies of the test-spec (or a marker or a SysML verify). REQ-FE-032 already named TC-CLV-030 and TC-CLV-040 there. So the change is in the N-1.1 `test-spec.md`: REQ-FE-032 is added to Verifies of TC-CLV-030 (table row and section). The test, `test_skill_run_view_browser.py`, is unchanged; the row needs the owner's review-log row for its new fingerprint.

## Check after
`python tools/req_graph.py` (G7 error for REQ-FE-032 gone; count 26).
