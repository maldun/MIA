# Verification report: G-V3.PANEL (the Skill run view), fourth run

**Goal:** G-V3.PANEL (subgoal of G-V3), supervised
**Branch:** goal/v3 @ `26dfe3c` (clean checkout by `git archive`; code identical to `054d382`)   **Date:** 2026-11-14   **Reviewer:** Claude Sonnet 5.5 (AI, fresh context, no memory of earlier sessions); the human reviewer has not yet read the marked items.
Earlier runs: `verification-report.md` (F-01 to F-12), `-run2.md` (F-13 to F-17), `-run3.md` (F-18, F-19). Very narrow run as in `verify-brief-run4.md`: only the fix of F-18 and F-19 and the regression checks.

## Verdict
**Not verified**, formally, for paperwork only; no finding is open and no defect remains.

Exact remaining reason: the decision row **D-338** in `review-log.md` does not exist (not found anywhere in `specs/` except hand-over, briefs and reports). TD-82 to TD-84 are now signed off by the owner (`Sign-off: maldun, 2026-11-14`), but 'Verified with accepted deviations' needs the row. It must name: F-15 (TD-82, REQ-WFM-135), F-16 (TD-83, REQ-WFM-133), F-17 (TD-84, REQ-CLV-036 and REQ-WFM-135) as accepted deviations with their triggers; and the sign-offs of TD-82 to TD-84 (2026-11-14); TD-81 / F-10 is already accepted by D-331. With that row the verdict becomes 'Verified with accepted deviations'. The 553 `trace_check` errors (8 above the tag: two TD-81, six TD-82 to TD-84) remain until the owner links the drafts in one amendment (his choice).

## Closing of F-18 and F-19
| Id | Probe (own, `vp/p18.py` and mutants in a `git archive` copy) | Result |
|---|---|---|
| F-18 | `_emit_status` with recorder raising / working / none, and payloads: dict with id, dict without id, `"plain"`, `None`, `[1]`, `{"id": None}`. Raising recorder: nothing raised, payload sent unchanged, exactly one `logger.error` line (id `r1` for the dict, `None` for the other payloads; cause in the line). Working recorder, dict with id: status enriched, zero log lines. No recorder: zero lines, payload unchanged | fixed |
| F-18, review | `run` is defined on the first line, before the `try`, so no use before definition. The lookup still reads `payload["id"]` inside the `try`: a non-dict still raises there (`TypeError`) and is swallowed with one log line, as before the third run; the `isinstance` only guards the log value. A dict without `id` (`KeyError`) is logged with id `None`. One more observation, not new: a dict with `id` and without `done`/`paused` for a found record raises `KeyError` outside the `try` (also before this round; `TaskMonitor` always sends them) | fixed, no regression |
| F-19 | my four mutants of the third run against the new tests: M3 (`open` notifies while quiet) killed; M3b (`open` never notifies) killed; M3c (`start()` calls `open(linked)` without `quiet`) killed; M5 (log call before the `try`) killed (2 failures). Extra mutants: the F-18 fix reverted (error), `isinstance` dropped (error): both killed | fixed, no survivor |

Test independence: both new Python tests and the new JS tests pass alone (`-m unittest ...TestEmitStatus.<name>`, `--test-name-pattern`); the patch of `chat_service.logger` is a `with` block, so it cannot leak; the JS test sets its own `doc.click` per call of `startView` (no shared state).

## Diff review (`git diff 5fb1991..HEAD -- chat_service.py tests templates`)
`chat_service.py`: 3 lines, as in the brief. `templates/`: unchanged. Tests: the JS helper `startView` now keeps the `click` handler and returns `doc`; the first test adds `assert.deepEqual(notes, [])` (no note at load); a new click test checks one note `workspace.failed` and the view stays on r7; two new Python tests (non-dict payload goes out unchanged; healthy recorder logs nothing and the status carries `state`). No assertion was loosened; no protected path touched.

## Automated checks (clean checkout of HEAD, venv `mia312`, Python 3.12)
| Check | Result |
|---|---|
| Full unit suite (alone, 430 s) | 2078 tests, 1 error (`test_tailscale`, known), 5 skipped, 1 expected failure: as expected |
| JavaScript | 167 pass, 0 fail |
| `test_emit_status_storage_error` 4, `test_chat_tasks` 12, `test_skill_runs_race` 1, `test_skill_run_gaps` 7 | OK |
| Browser (`tests/acceptance/test_skill_run_view_browser.py`, podman) | 12 OK, three runs (46.9 s, 47.7 s, 45.7 s), no flip; restart test 1 OK |
| Contract suites | IF-101 78 OK (2 skips); IF-302 16 OK; IF-102 24 OK; `contract_postgres.sh` 12 OK |
| `check_sysml_model.py` | OK |
| `trace_check.py` | 553 errors, as the brief says; no PANEL id besides TD-81 to TD-84 |
| `test_doc_check.py --tests-dir tests` | 2658 errors, same as the third run: the new tests add none |
| Protected material | `git diff 3791b27 HEAD` and `5fb1991..HEAD` list no path under `tests/helpers/`, `tests/acceptance/`, `tests/smoke/`, `tests/integration/`, `contracts/`, `benchmarks/`, `eval/`; the list against `plan-baseline-it2-panel` is the same set as in the third report |
| `specs/` since the third report | only `deferred.md` (three `Sign-off` lines, nothing else) and the brief of this run |

## Review findings
None new (ids F-20 onward unused).

## Facts, not findings
- The branch has not merged master; `goal/v3.chat` is a separate line. The look of the character in the changed box is VAL-012.
- Not run: the mutants of runs 1 and 2 (code of those places unchanged); a two-instance run on a shared database.
- Full suite and browser runs were done one after the other, in a `git archive` copy.

## Accepted deviations
F-10 (TD-81, D-331). F-15 to F-17 (TD-82 to TD-84): signed off by the owner 2026-11-14, awaiting the decision row D-338.
