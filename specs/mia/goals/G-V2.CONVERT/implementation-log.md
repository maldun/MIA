# Implementation log: G-V2.CONVERT

Line of work `goal/v2.convert`, supervised. Test runs here are feedback, not verification (Phase 4 verifies).

## T-CV-02: Settings record of the equivalence check
- Requirement: REQ-WFM-069. Files: `skill_converter.py` (`EquivalenceSettings` implemented, the other stub bodies untouched).
- Tests reported green (own run, 2026-11-15): TC-WFM-069 (`SettingsAreVersioned`). The other tests of `tests/acceptance/test_skill_conversion.py` stay red until T-CV-03 to T-CV-08 (18 failures, all other tasks); `test_call_recording.py` stays green.
- Design: the folder holds `settings-<n>.json` (one file per version, written with mode "x", never overwritten) and `results.jsonl` (append only). Version 1 is written at first use with the defaults margin 0.10, repeats 3, rule threshold. `update` accepts only these three keys (`ValueError` otherwise) and writes max+1; a result names the version current when it is recorded.
- Deviation: none. No data file in the repo: the folder is given by the caller (the plan says "configuration record and its reader"; where the real folder lives is for T-CV-03/T-CV-09 to decide).
- Finding: `trace_check` reports 554 error lines before and after (unchanged); no id of this task among them.
- Finding: the full `unittest discover -s tests` did not finish in the session (more than 25 min, several runs in parallel, podman tests). Only `tests/acceptance/test_skill_conversion.py` imports `skill_converter`, so no other module can change; that module went from 19 failures (before) to 18 (after), `test_call_recording.py` 5 of 5 green before and after.
