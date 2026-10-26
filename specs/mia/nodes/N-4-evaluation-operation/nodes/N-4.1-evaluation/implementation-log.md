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
