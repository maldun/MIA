# Implementation log: Evaluation (N-4.1)

## T-01 The harness reaches the platform through IF-105 (2026-10-26)
| Requirement | What was built | Tests |
|---|---|---|
| REQ-EVL-001 repeats, intervals, cost | `eval_platform.WorkflowTarget` (new, standard library only): one case = one `run_case` of IF-105 with pin, seed, temperature and optional budget as options; `Harness(platform=...)` registers it as the target kind `workflow`; the cost of a record is the `cost` of the run (calls, tokens, seconds); `metrics.case_table` (repeats and passes per case); `metrics.cost` and the report count tokens | `tests/test_eval_platform.py` (TC-EVL-001: 5 cases x 3 repeats, 12 of 15, interval 0.55 to 0.93, 45 calls, 27000 tokens, 135 s) |
| REQ-EVL-004 versions per run | header of every run: `workflow`, `workflow_version`, `pin` (name, digest, seed, temperature), `benchmark_version` (= `suite_sha1`); a workflow suite without a pin is refused | TC-EVL-004 (10 runs) |
| REQ-EVL-008 equal cases | `harness.require_same_cases` (case ids and repeats; names the differing cases); `tools/eval.py compare` stops with "not compared: ..." | TC-EVL-008 |
| REQ-EVL-011 only IF-105 | the adapter imports nothing but the standard library | TC-EVL-011 (inspection by `ast`) |

Existing tests unchanged and green: `tests/test_harness.py` (28), `tests/test_metrics.py` (22).

## Findings
- **F-1 (needs an owner decision): REQ-EVL-011 is met by the new adapter only.** The older targets in `harness.py` (checks, pipeline, extraction, plan, research) call the in-process Core directly and `harness.py` imports `pipeline.Tool`; they are what all eval suites and baselines of today run on. Moving them behind IF-105 means turning them into workflows of the platform, which N-2 provides; until then the two paths exist side by side. Options: (a) accept this until the N-2 integration step, (b) amend REQ-EVL-011 to say "new targets". Nothing was changed in the old targets.
- `tools/eval.py compare` used to compare the cases both runs had; it now refuses runs with different case lists, as REQ-EVL-008 says. A partial comparison is possible no more from the command line.
- Not done in T-01: TC-EVL-001 asks for the Wilson interval "in the report"; the report prints per-tag and match intervals as before, the per-case table is available as `metrics.case_table` but not printed.

## T-05 Measurement tools for first text and frame rate (2026-10-26)
| Requirement | What was built | Tests |
|---|---|---|
| REQ-EVL-007 | `tools/measure_latency.py` (`measure`: median, min, max of the runs after warm-up, failed runs counted; `chat_ask` + the command line: login, socket, first `chat_delta`); `tools/measure_fps.mjs` (`fpsOf`: median frame time to fps) | `tests/test_measure_latency.py` (TC-EVL-007: 1.0/2.0/3.0 s cycling, 20 runs after 3 warm-up: median 2.0 s), `tests/js/measure-fps.test.mjs` (60 and 30 fps, one long frame does not matter, no frames is an error) |

- **Not done:** the live mode of the latency tool (`chat_ask`) has not been run against a server; the baselines BM-MIA-001 and BM-MIA-002 of today's MIA ("measured first") need the real machine and are the owner's run. The frame times for the fps tool must be recorded in the browser; a recorder is not part of this task.

## T-02 Decisions only on held-out cases (2026-10-26)
| Requirement | What was built | Tests |
|---|---|---|
| REQ-EVL-002 | `tools/decide_guard.py`: refuses (NOT DECIDED, reason "dev split") any run that is not a holdout run (suite name ends in `.holdout`, or every record tagged `split:holdout`) and a mix of both; otherwise calls `eval_decide.py` of the agent-app skill with `--split holdout`. `Suite.select` leaves cases tagged `split:holdout` out of every suite that is not a `.holdout` suite, also with `only=` | `tests/test_decide_guard.py` (TC-EVL-002: dev refused, mixed refused, holdout PASS and FAIL through the real `eval_decide.py`, the harness never selects a held-out case in a dev run) |

- The skill's `eval_decide.py` itself does not refuse a dev run (it only filters with `--split`); the guard is the project's check around it. Use the guard for verdict criteria; `eval_decide.py` stays read-only.

## T-03 Judge calibration flag (2026-10-26)
| Requirement | What was built | Tests |
|---|---|---|
| REQ-EVL-003 | a record with a `judge` field (id of the model that gave the verdict) gets `counted`: `harness.mark_judge_verdicts` with the calibration records of `harness.load_calibrations` (one JSON per judge, written by `tools/label_agreement.write_calibration`); counted only with Cohen's kappa 0.6 or more (`JUDGE_KAPPA_MIN`, OPEN-7); `Harness.run` marks its records; `metrics.is_right`, `match_metrics` and `verification_metrics` leave a not counted verdict out | `tests/test_judge_calibration.py` (TC-EVL-003: no record, kappa 0.7, kappa 0.4, the limit 0.6, a record without kappa, the numbers leave the verdict out, write and read) |

- **Not done:** nothing sets `judge` on a record yet and `Harness.calibrations` is empty by default; a judging pipeline (and the choice of the calibration folder, `data/eval/calibration/` is only my proposal) comes with the first task that uses a model as judge. `label_agreement.py` compares the owner with the benchmark labels, not a judge with the users' ratings: only the record writer was added.
