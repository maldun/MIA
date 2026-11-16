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

## Plan step 4b: the browser checks (written during Implement, before T-04)
- Written: scenarios `report`, `report_wait`, `report_gone`, `report_hostile` in `tests/browser/skill_run_view.py`; the stub steps `file` and `file_deleted` in `ui/tools/skill_run_stub_server.py`; the hooks in `report-part-interface-note.md`; the four test methods (TC-CLV-048, 050, 051, 052 browser half) in `plan-step4b/protected.patch` for the owner to install (the protected file was not edited; built in a sandbox copy).
- Result in the sandbox, run alone: 16 tests, the 12 old ones pass, the 4 new ones fail on assertions (no `#srv-report` part, no note, no body): red for the right reason.
- Correction: plan decision 6 rested on my reading of a truncated list of images; `localhost/mia-browser` existed (2026-10-31).
- Finding F-4: while a full unit run was going I ran the browser checks at the same time; that run showed two extra failures (`test_task_files_browser`, one shares check in the dark theme). Run alone, the shares check passes. `test_task_files_browser` fails alone on master too (the Files tab of the old status card, superseded by the Skill run view): not ours, as F-3. Rule from this: browser and full runs never run together.
- Unit suite after A-155 (T-01 complete): the same 12 failures as master plus the 2 of `test_task_files_browser`, both also on master; nothing else.

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

## T-02: The skills hand over their reports
- Status: done (own runs, feedback and not verification); the branch is `goal/v3.report.t02`, not merged
- Requirements: REQ-WFM-139 for `lookup`, `review`, `search`
- Done: `/lookup` asks for the need `run_report` instead of `files` and `research_chat.run_research(..., run_report=)` hands over `format_report` (the interim `files=` of 36cc3a9 and its file naming are gone: the runtime names the file); `/review` hands over the report that the chat shows from `_keep`, its `.md` and `.tex` files stay; `/search` hands over its result text (escaped Markdown already). The three manifests ask for `run_report` and have the version 2.
- Tests reported green: `test_lookup_report` (8), `test_review_report` (4 and 1 expected failure, see F-1), `test_search_report` (5), `test_research_command` (31), `test_research` (62), `test_review_chain` (4), `test_chat_review` (8), `test_chat_tasks` (12), `test_extension_loader` (9), `test_chat_repair` (6), `test_chat_memory` (5), `test_skill_record_storage` (32), `test_workflow_voice` (5), `test_skill_catalog_loader` (20), `test_core_names_no_skill`, `test_runner_internet_by_command`, and `tests/acceptance/test_skill_run_report.py` (5). The whole suite was not run (another run was going on).
- Mutants (to see that the checks can fail): an address of any scheme written as a link in the lookup report: killed by `test_only_http_and_https_become_links`; the titles of /search not escaped: killed by `test_hostile_titles_and_addresses_stay_inert_in_the_report`.
- Hand-checked value: the first result of the /search report is `1. Rivertown Bridge opens` and, on the next line, `   https://gazette.example/bridge` (the format of `format_results`).
- Findings:
  - F-1 (not fixed, needs the owner): the report of `/review` (`format_report`) writes titles, notes and DOIs from the scholarly sources as they come, so a title such as `[x](javascript:alert(1)) <img ...>` is a live link and tag in the chat text, in the `.md` file and now in the run report. It was so before this goal; REQ-WFM-141 asks the reports to escape such text. Escaping in `format_report` changes the text the chat shows for `/review`. Test: `test_review_report.HostileTitles` (expected failure, strict until fixed); the Report part sanitizes on rendering (REQ-CLV-052), the downloaded file does not. Proposal: escape in `format_report` as `_plain` does for /search, and record a TD until then.
  - F-2: the stubs of the unprotected tests `test_research_command` (the /lookup and /search stubs), `test_chat_repair`, `test_chat_memory`, `test_chat_review` took `files=None`; the manifests now ask for `run_report`, so the argument is renamed `run_report=None` (forced by the interface change, no assertion weakened).
- Decisions: `/lookup` hands over a report for every answered question, also one without sources; an unanswered question, a stopped or failed run gets the runtime's report. A report that cannot be handed over is told in the chat text and never takes the answer away.
