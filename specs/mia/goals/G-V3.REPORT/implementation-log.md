# Implementation log: G-V3.REPORT

## T-01: The run report in the runtime
- Status: code done, waits for A-155 (two protected checks, see below)
- Requirements: REQ-WFM-139, 140, 141 (REQ-WFM-137)
- Done: `run_report.py` (new: state line, fallback body, escaping, http and https addresses as links, file name), `chat_service.py` (`_keep_report` after `chat_done`, the need `run_report` handed over, `observer.end(report=)`), `skill_runs.py` (`end(report=)`, `report` in `record`, None until the run ends), `skill_run_observer.py`, `extension_loader.py` (`NEEDS`).
- Tests reported green (feedback, not verification): `tests/acceptance/test_skill_run_report.py` (TC-WFM-139, 140, 141: 5 tests), `test_skill_runs.py`, `test_skill_run_observer.py`, `test_if_302_record_tables.py`, `test_chat_tasks.py`, `test_extension_loader.py`, `test_lookup_report.py`, `test_chat_repair.py`.
- Mutants, to see that the checks can fail: escaping switched off, and every scheme taken as an address: both killed by TC-WFM-141.
- Findings:
  - F-1 (needs a protected change): TC-IF-101-30 and -35 (real variants) assume that `files` holds only the skill's own files. Test: the two checks themselves, red in the real variants; proposed A-155 (`amendment-a155/`), payload built in a sandbox copy: mock and real green.
  - F-2: `tests/test_chat_tasks.py` (TC-WFM-037/038, unprotected) expected one file; changed to two files bound to the message of the run, in the T-01 commit.
  - F-2b: `tests/test_review_chain.py` (unprotected) had the same assumption; changed in commit `0206112`.
  - F-3 (not ours, found on the way): on master without any change of this goal, `unittest discover -s tests` fails 11 tests and has 1 error in `test_control_entries`, `test_converted_tools`, `test_core_converted`, `test_harness_converted` (G-V2.CONVERT); each module passes alone, they fail only together (order dependent, a module registry that leaks between modules: "no node call is registered", runs ending `failed ['step.write']`). Also on master: `tests/acceptance/test_skill_snapshots.py` fails 8, `test_decide_guard.py` and `test_judge_calibration.py` give no unittest result (exit 1). Not touched; for the owner.
  - `discover -s tests` does not reach `tests/acceptance` (no `__init__.py`): the protected tests run as scripts, one file at a time; the result of this task comes from both ways.
- Result (feedback, not verification): `unittest discover -s tests` 2410 tests, the same 12 failures as master and nothing else; acceptance scripts: only TC-IF-101-30 and -35 (real) red, waiting for A-155; the three files named in F-3 as on master.
- Decisions: the report is written only where a recorder and a files volume exist (a run without them has no record to name it); a volume that cannot take it is logged and the run is not lost (`_keep_report`).
- Open for Phase 4: the first-line wording (`# Done`, `# Stopped: <reason>`, `# Failed: <reason>`) is not in a requirement; the tests accept the words only.

## T-03: The renderer of the report
- Status: code done (fork, branch `goal/v3.report.t03`)
- Requirements: REQ-CLV-049, 052 (unit half)
- Done: `reportHref` (http or https, any case of the scheme, no whitespace or control character, else null) and `renderReport` in `templates/static/chat/markdown.js`: marked, then DOMPurify with its own call config (no img, form, frame, style, script; attributes href and title only; http and https addresses only); then, on a detached `template` element, every link whose address `reportHref` accepts gets `target="_blank"` and `rel="noopener noreferrer"`, every other link is unwrapped to its text. Without a DOM the report is escaped text (`<p>` and `escapeHtml`).
- Tests reported green (feedback, not verification): `tests/js/report-render.test.mjs` 7 of 7 (6 written in Plan step 4, one added: rendering a report does not change a chat message); `node --test "tests/js/*.test.mjs"` all green.
- Mutants: `reportHref` returning its input (checks 2 and 5 fail), the address rule reduced to `^https?:` (check 2 fails): both caught.
- Decisions: no DOMPurify hook is used at all (hooks are global to the library; the chat installs its own once): the target and rel attributes are set after sanitizing on a detached `template`, so the chat renderer cannot be changed by a report.
- Findings:
  - F-4: the DOM branch of `renderReport` (sanitize, `template`, `replaceWith`) cannot run in node (jsdom is not installed); it is covered by the browser checks TC-CLV-052 and TC-CLV-048 of T-04 (decision 6, browser image). Until then it is read, not run.
  - The chat renderer lets `mailto:`, `/path` and `#anchor` through; the report refuses them (REQ-CLV-049): `renderReport` does not reuse the chat rules.
