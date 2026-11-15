# Implementation log: G-V2.CONVERT

Line of work `goal/v2.convert`, supervised. Test runs here are feedback, not verification (Phase 4 verifies).

## T-CV-02: Settings record of the equivalence check
- Requirement: REQ-WFM-069. Files: `skill_converter.py` (`EquivalenceSettings` implemented, the other stub bodies untouched).
- Tests reported green (own run, 2026-11-15): TC-WFM-069 (`SettingsAreVersioned`). The other tests of `tests/acceptance/test_skill_conversion.py` stay red until T-CV-03 to T-CV-08 (18 failures, all other tasks); `test_call_recording.py` stays green.
- Design: the folder holds `settings-<n>.json` (one file per version, written with mode "x", never overwritten) and `results.jsonl` (append only). Version 1 is written at first use with the defaults margin 0.10, repeats 3, rule threshold. `update` accepts only these three keys (`ValueError` otherwise) and writes max+1; a result names the version current when it is recorded.
- Deviation: none. No data file in the repo: the folder is given by the caller (the plan says "configuration record and its reader"; where the real folder lives is for T-CV-03/T-CV-09 to decide).
- Finding: `trace_check` reports 554 error lines before and after (unchanged); no id of this task among them.
- Finding: the full `unittest discover -s tests` did not finish in the session (more than 25 min, several runs in parallel, podman tests). Only `tests/acceptance/test_skill_conversion.py` imports `skill_converter`, so no other module can change; that module went from 19 failures (before) to 18 (after), `test_call_recording.py` 5 of 5 green before and after.

## T-CV-03: Per-skill state, old runner until accepted, record of the check
- Requirements: REQ-WFM-057, REQ-WFM-059, REQ-WFM-060. Files: `skill_converter.py` (`SkillConverter`, `decide_acceptance`, `conversion_records` implemented; `run_converted` and `compare_outputs` stay stubs for T-CV-04 and T-CV-08).
- Tests reported green (own run, 2026-11-15): TC-WFM-057 (2 tests), TC-WFM-059 (3), TC-WFM-060 (1), TC-WFM-069 stays green. `test_skill_conversion.py` 18 failures before, 12 after (all of TC-WFM-058 and 115, later tasks); `test_call_recording.py` 5 of 5 green. `trace_check`: 554 error lines before and after.
- Design: `SkillConverter` keeps the state in memory (a skill starts unconverted; `mark_converted` accepts only `accepted` with verdict PASS, else `ConversionError`); the converted loader is called only for a converted skill. `decide_acceptance` calls `eval_decide.py` (`--json`) in a subprocess with the criterion line and the optional `--rerun`; a FAIL without re-run is reported as such and is not accepted; a failing call of the script is NOT DECIDED. `conversion_records(skills_dir, checks=None)` lists every `.md` of the folder: the six skills of `eval-spec.md` get a reason ("not converted yet: the equivalence check of REQ-WFM-11x on <suite> has not been run") until a recorded check is passed in `checks`; the nine others get the owner's reason of 2026-11-07.
- Deviation / open: the state is not persisted (no file, no store); where the real record lives (and how `checks` is fed from the decision runs) is for T-CV-09 / the stage 4 steps to decide. The `checks` parameter is an addition to the stub signature, optional.
- Finding: TC-WFM-059 copies the criterion of REQ-WFM-110 with min 0.82, the requirement says 0.85 since A-122; the test numbers (17 of 20 pass, 16 and 15 fail) hold for both, test not edited.
