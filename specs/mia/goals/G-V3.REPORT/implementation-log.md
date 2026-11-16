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
