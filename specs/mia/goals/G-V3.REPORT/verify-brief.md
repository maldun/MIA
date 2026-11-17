# Verify brief: G-V3.REPORT (for a fresh, independent context)

You have not seen the implementation chat. Start from `specs/mia/goals/G-V3.REPORT/goal.md`, `plan.md`, `implementation-log.md` and `specs/mia/amendments/A-154-report-of-a-skill-run.md`; load `dev-workflow`, `verify-phase` and `agent-app-verify` is not needed (no prompt, no model step). Branch `goal/v3.report` (head: see `git log -1`), master merged in.

Scope: REQ-WFM-139, 140, 141; REQ-CLV-048 to 052; changed REQ-CLV-043, REQ-WFM-137; IF-101 v18, IF-302 v12 (installed by the owner, `plan-baseline-g-v3-report`, A-155, the browser payload).

Run (foreground only, one after another; a background start makes `test_shutdown*` fail by ignored SIGINT, F-7; never run the browser checks while another run goes):
- `node --test "tests/js/*.test.mjs"`; every acceptance file as a script (`tests/acceptance/test_*.py`, `tests/acceptance/contract/test_*.py`); `python -m unittest discover -s tests`.
- Expected, not ours (also on master): unit suite 13 failures and 1 error (four G-V2.CONVERT modules, `test_task_files_browser`); acceptance: `test_skill_snapshots.py` 8 failures, `test_decide_guard.py`, `test_judge_calibration.py` without result. A flaky check: the dark-theme shares check of `test_skill_run_view_browser.py` (F-5).

Look hard at:
1. `run_report.py` and `chat_service._keep_report`: the state line for done, stopped and failed; a run without recorder or volume; escaping (`escape`, `link_addresses`); a result with an address that has a trailing `)` or `.`.
2. `extensions/review/review_chat.py` `_md` (minimal escape set) and the places it covers: any outside field left out? (`|` in a keyword is known.)
3. `markdown.js` `renderReport`: sanitizer, `template` re-parse, unwrapping of links; the chat renderer must be unchanged (global hooks).
4. `skill-run.js` `drawReport`: stale responses when the shown run changes, one request at a time, a failed read, the part opening by itself.
5. Requirements against code in both directions: behavior in the code that no requirement says (the first-line wording, the file name `<skill>-<date>-<words>.md`, `report` written only where a recorder and a volume exist); the changed REQ-CLV-043 and REQ-WFM-137 are Draft until you re-verify them.
6. The protected tests unchanged except the installs named above (`git diff plan-baseline-g-v3-report -- tests/acceptance tests/helpers contracts specs/mia/test-requirements.md`).
7. A hand check: `/lookup` against the running MIA (needs the model and SearXNG), open the Full run, Report part: sources are links, download works.
