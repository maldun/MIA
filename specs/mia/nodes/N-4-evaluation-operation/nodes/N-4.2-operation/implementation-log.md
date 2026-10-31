# Implementation log: Operation (N-4.2)

Goal G-V1 (line of work `goal/v1`). Method (owner's rule: test the existing code first, change only what fails).

## T-01 Report of missing options (2026-10-31, done at unit level; startup wiring open) – REQ-OPR-003

The existing code already reports missing options (`config.missing`, `python config.py [folder]`); the task added the test of TC-OPR-003 and completed the example file, which the test case assumes lists every option.

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-OPR-003 missing options reported | `config.missing(folder)` (unchanged): the options of `setup_cfg.example.json` that `setup_cfg.json` lacks, with the example's value; `config.py` as a command prints one line per option | `tests/test_missing_options.py` (3): two options removed from the real example give exactly these two, in `missing()` and in the printed report; none removed gives none |

Finding (existing failure of `tests/test_config.py`, `test_every_option_the_code_reads_is_in_the_example`): on `goal/v1` (f80c552) the scan of the code found 11 keys read by the code but not in `setup_cfg.example.json`, so the precondition of TC-OPR-003 ("the example lists every option") did not hold:
- 8 real options added by earlier tasks without the example: `files_dir`, `files_max_bytes`, `files_max_total_bytes`, `model_classes_file`, `review_answer_seconds`, `skill_options` (web_app.py), `workflow_speak`, `workflow_speak_tasks` (workflow_voice.py). Fixed: added to the example with the defaults of the code (1 GiB, 50 GiB, 1800 s, `{}` for the two maps, which the code treats like absent). No behaviour changes.
- 3 false positives of the scan, not options of the file: `MIA_PROXY_TRUST` (Flask `app.config` in accounts_api.py), `budget` and `model_pin` (`options` of a workflow run in run_workflow.py). Not fixed: the fix is in `tests/test_config.py` (`NOT_OPTIONS`), outside the task's bounds. The test still fails with these three.

The test file is new (`tests/test_missing_options.py`) instead of an extension of `tests/test_config.py` (plan note), so that the local model typed one whole file and no existing test was touched.

Local coder: `tests/test_missing_options.py` typed by the local model from an exact instruction (task `n42-t01-missing-options`, 1 attempt, 34 s); every instruction line found verbatim by script; verdict `ok`.

Tests reported green (feedback, not verification): `tests/test_missing_options.py` (3), `tests/test_config_local.py` (5), `tests/test_deploy.py` (16), `tests/test_requirements.py` (7); `tests/test_config.py` 13 of 14 (the 3 false positives above).

Open questions for the owner:
- Q1: add `MIA_PROXY_TRUST`, `budget`, `model_pin` to `NOT_OPTIONS` in `tests/test_config.py` (or narrow the scan to `cfg`)? Recommendation: add them to `NOT_OPTIONS` with a one-line reason each; a small follow-up in that test file.
- Q2: REQ-OPR-003 says "when MIA starts after an update"; nothing calls `config.missing` at start (`__main__.py`, `web_app.py` only call `ensure`). Wiring the report into the start touches `__main__.py`, outside T-01's files, and the wording of the start message is fixed by no requirement. Recommendation: one line in `__main__.py` after `ensure_config` that prints the report of `config.py` (same wording as the command), as an amendment of T-01's Touches; until then TC-OPR-003 (Unit) is met by the function and the command only.
- Q3: the 8 options added to the example are not described in README.md ("Configuration"), which the docstring of `config.py` promises. README.md is outside the task's files. Recommendation: describe them in the same follow-up as Q1.
