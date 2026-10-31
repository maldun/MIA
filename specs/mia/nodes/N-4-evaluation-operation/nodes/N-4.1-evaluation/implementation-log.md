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

## T-04 Baseline and suite checks (2026-10-26), REQ-EVL-005 done, REQ-EVL-009 open
| Requirement | What was built | Tests |
|---|---|---|
| REQ-EVL-005 | `tools/check_baselines.py`: every workflow id with a tested or trusted version needs a baseline file `<suite>__<variant>__baseline.jsonl`; the link is `library/baselines.json` (`{"verify.computable": {"suite": ..., "variant": ...}, "chat": null}`); names each workflow that lacks it, exit 1; read-only | `tests/test_check_baselines.py` (TC-EVL-005: only tested/trusted are checked, unregistered, registered without file, registered with file, no suite) |

- **Decision of the owner (2026-10-26): a field linking a workflow to its baseline. Deviation:** the link is a separate file `library/baselines.json` (next to `library/source_trust.json`) and not a key in the pipeline entries: a new key changes the content hash of the entry, so every tested/trusted workflow would need a new version only for bookkeeping. If you want the key in the entry anyway, the check reads `entry["baseline"]` in one place.
- **State today:** `python3 tools/check_baselines.py` names 5 workflows without a baseline (behaviour.speech, chat, extract.rules, summarize, verify.computable). `library/baselines.json` does not exist yet: which suite and variant belong to which workflow is a Plan decision (I did not invent it), and the baselines in `eval/baselines/` are `.md` reports, not `.jsonl`; the `.jsonl` baselines are made by recorded runs (protected, with the owner).
- **REQ-EVL-009 (TC-EVL-009) not run:** the check is `agent_check.py` of the agent-app skill on `eval/`; this session's sandbox refuses the command (any command line with `eval` as an argument), so it is for you to run: `python3 ~/.claude/skills/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval`.

## T-06 Document of the skill path (2026-10-26)
| Requirement | What was built | Tests |
|---|---|---|
| REQ-EVL-006 | `docs/skill-path.md`: the seven steps (idea, skill file and pipeline, validation, specification and benchmark, declaration, draft and promotion, time record) with the lookup (`research.baseline@1`, suite `research`) as the example; four blocks marked `run` (two Python, two bash) | `tests/test_skill_path_doc.py` (TC-EVL-006: every step has a section, the lookup is the example, the marked examples run from the repository root with a scripted model, links resolve) |

- The examples run the real harness, library and core with a scripted model: a lookup case over the recorded web (pass, one model call), `library.py validate`, `check_baselines.py` (exit code 1 expected: workflows without a baseline), draft, promotion and the time record with a fake clock.
- **Findings:** there is no skill called "lookup" in `skills/`; the lookup is the research family (`research.baseline`, `research.escalate`, ...), which the document says. The time record (idea to promotion) is `origin.created` and `status.json`; the *idea* date is not stored anywhere (the document says: keep it in `origin.note`); FR-20 wants it recorded, so the platform side (N-2.3) may need a field. `try_pipeline.py --check` needs the app's virtualenv (it imports `ollama`) and is shown unmarked.
- **N-4.1 state:** T-01 to T-06 built; T-07 (the proof-of-concept scenario, TC-EVL-010) waits for the N-2 and N-3 steps of the root plan; TC-EVL-009 (suites with holdout, `agent_check`) waits for the Plan material (the findings of the agent check: threat model and budgets are drafted on branch worktree-plan-threat-model-budgets, the dev/holdout split is the owner's).

## Gaps closed (2026-10-27, branch worktree-impl-n-4-1-gaps)
- TC-EVL-001: `format_report` prints "per case (passes / repeats)" with the Wilson interval when repeats > 1 (test in `tests/test_eval_platform.py`).
- Live mode of `tools/measure_latency.py` ran against the IF-101 mock (`chat-with-login`, in the image with `--network host`). Findings, fixed: the ack of `chat_send` was ignored (a full queue looked like a hang), and the next run counted the deltas of the previous answer. Now the ack is checked and each run waits for `chat_done` of the previous one, untimed.
- Caveat: the image has no `websocket-client`, so only long-polling is used; the mock gave a median of 5.0 s (5 runs) while a direct probe saw the first delta within 1 s. Treat the number as polling-bound, not a latency result; a real measurement needs the websocket transport (a dependency: owner decision).

## Verify fixes (2026-10-31, branch v1-n41b from goal/v1 at dc1ddc8, decision D-164)
Each finding first as a failing test (red seen), then the fix. Fake models and synthetic fixtures only; no eval run, no holdout suite or case opened.

| Finding | Commit | What changed | Tests (red, then green) |
|---|---|---|---|
| F1 (High) latency clock | fb0db96 | `measure(..., prepare=)`: `prepare` runs before the clock starts; the live mode returns `(prepare, ask)`, `socket_ask(client, ...)` takes any connected client; `prepare` waits for the previous `chat_done` | `test_the_clock_starts_after_the_previous_answer_has_ended`: fake socket, first text 0.1 s, end 0.5 s, 3 runs -> median ~0.1 s (red: `socket_ask` missing; the old code timed ~0.5 s) |
| F2 pin id | cab26a6 | `tools/eval.py` `pin_record(id)` = the PINS entry with its `id`; `WorkflowTarget` sends `pin["id"]` and needs id, seed, temperature; the header pin has the id too | `RealProvider` test on the real `run_workflow.WorkflowRuns` of the contract suite with the pin of `tools/eval.py` (red: `pin_unavailable`); the test `PIN` is now the shape of `tools/eval.py` |
| F3 IF-105 on the command line | 6b2dd67, f9be045 | `make_harness(cfg, core)` = `Harness(core, platform=WorkflowRuns(WorkflowLibrary(Storage(FileBackend(accounts_dir))), core, pins by id, held = digests of the model server))`; `run` exits "a run needs --pin (MP-light)"; `Harness._versions`: workflow + version, or skill + skill_version + pipeline for pipeline/research/plan/extraction, `pipeline: None` for code targets; the command line adds `commit` (git HEAD, None without git); docs (`ui/README.md`, `docs/skill-path.md`, `deploy/RUNBOOK.md`) show `--pin` | `CommandLine` (3 tests) and `VersionsOfEveryKind` in `tests/test_eval_platform.py` |
| F5a guard options | e3ec1aa | `decide_guard.parse`: `--run`/`--rerun` files (also `--x=path`, argparse abbreviations `--rer`) are taken out of the options and all checked; any spelling of `--split` (`--split=`, `--sp`, `--spl`) is NOT DECIDED; re-runs are passed as `--rerun` | `NoOptionOverridesTheHoldout` (3 tests; `eval_decide.py` replaced by a stub that fails if called before the refusal) |
| F5b holdout on the command line | e3ec1aa | `tools/eval.py --holdout`; without it `list` skips `*.holdout` folders unread (`harness.list_suites(root, holdout=)`, default unchanged), `cases` and `run` exit before reading the suite | `HoldoutSuitesOnTheCommandLine` (3 tests, synthetic `toy`/`toy.holdout` in a temp folder) |
| F8 suite version | 71d814d | `require_same_cases` also compares `benchmark_version` (else `suite_sha1`) and names the changed files | `test_runs_of_different_suite_versions_are_not_compared`; TC-EVL-008's "same" pair is now one suite under two variants |
| F6 mutants, F7 partial pin | 71d814d | none (tests only) | `test_a_run_of_the_harness_marks_the_judged_records`, `..._left_out_of_the_verification_numbers`, `test_is_right_has_no_answer_...`, `test_a_pin_without_id_seed_or_temperature_is_refused_per_case`; mutation probe on a scratch copy (removed): the 4 surviving mutants of Verify and the new version check are killed |
| F12 wording | 71d814d | compare: "(dev feedback, not a verdict: decide on the holdout)" instead of "a difference you can believe" | `test_a_comparison_says_it_is_feedback_not_a_verdict` |
| F9 model | 71d814d | `architecture.sysml` Evaluation: harness lists `eval_platform.py`, `tools/decide_guard.py`, `tools/check_baselines.py`, `tools/measure_latency.py`, `tools/measure_fps.mjs`; `judgeCalibration` partly (`harness.py`, `tools/label_agreement.py`); no new part | `check_sysml.sh`: 0 errors; `check_sysml_model.py`: OK |
| F10 test docs, scenarios | 71d814d | every test of the six node files: TC id first, `Example:`, Given/When/Then (also missing `req` markers added); test-spec.md `## Scenarios` (11 blocks, draft for review) | `test_doc_check.py` on the six files: 0 errors (was 34); `trace_check.py`: the N-4.1 Scenarios error is gone |
| F11 protected tests | e67542e | amendment A-63 drafted, not installed (see below) | checked on a scratch copy |

### A-63 (proposed, not installed)
`bash tools/apply_amendment_a63.sh` (look), `--do` installs: creates `tests/acceptance/test_{eval_platform,decide_guard,judge_calibration,check_baselines,skill_path_doc,measure_latency}.py` from the drafts in `specs/mia/amendments/A-63/tests/acceptance/` (three path lines one folder deeper and the `Run:` line), builds the node's test-spec.md (note line, each row names its file) and `docs/skill-path.md` from the installed files, runs the six protected tests on the host and removes the old `tests/` copies only when all pass. It refuses when an old copy changed after the drafts (`A63_DRAFT=1` redrafts). Scratch check: all six OK, `trace_check.py` output identical before and after, `test_doc_check.py` clean for them, a second run "nothing to do". The scratch check found that the F3 commit test needed git (f9be045).

### Stop: REQ-EVL-003 calibrations are never loaded (missing feature, needs a decision)
`Harness.calibrations` is `{}` everywhere: `load_calibrations` is called by no production code, and no target sets `judge` on a record, so the flag of REQ-EVL-003 never acts. The three surviving mutants are killed at unit level (the run test adds `judge` to its records itself). Wiring it (which folder, `data/eval/calibration/` was only a proposal of T-03; which target writes `judge`) is a feature for the first task that uses a model as judge; eval-spec.md has no judge in G-V1. Not built; question for the owner: accept as "built when the first judge comes" (scope row partly), or a task now.

### Decisions in code that no requirement states (for Verify / Plan, P25)
- `run` without `--pin` exits for every suite kind, also the code-only ones (D-164 says "every run requires --pin").
- A run saved before `benchmark_version`/`suite_sha1` existed is compared without the version check (old runs in `data/eval/` stay comparable); runs whose suite files differ in any byte are refused, also after only retiring a case.
- The header of a code target records `pipeline: None` and the git commit; a run without git records `commit: None`.
- The `--pin` sets seed, temperature and the header of the old targets, not the model: `--model full --pin MP-light` runs gemma4:26b with a header naming MP-light (unchanged behaviour, known since number-gate REQ-EVAL-003; open question).
- `held` asks the model server for the pin's digest at the first workflow run; no server means `pin_unavailable` per case, never a fallback.

### Open points
- `CLAUDE.md` (agent configuration, not mine to change) shows `python tools/eval.py run <suite> --repeats 3` without `--pin`; it now exits with the hint. Proposed text: `python tools/eval.py run <suite> --pin MP-light --repeats 3`.
- `agent_check.py --spec-dir specs/mia --eval-dir eval`: refused by this session's sandbox (the word as an argument); no file under `eval/`, skills or requirements changed, so its result should be the one of the Verify report. For the owner to run.
- `tests/test_harness.py::test_every_shipped_suite_is_valid` loads every suite of `eval/suites`, holdout ones included (no content printed); with `list_suites(holdout=False)` it could leave them out, but that would stop validating the holdout suites: owner's choice.
- The frame-rate half of TC-EVL-007 (`tests/js/measure-fps.test.mjs`) stays unprotected (no JS runner in `tests/acceptance/`).
- `decide_guard` checks `--run` and `--rerun`, not `--baseline` (a baseline may be a dev run by design).

## Owner decision D-166 (2026-10-31)
goal/v1 merged first (fc749e0; CLAUDE.md's eval line with `--pin`/`--holdout` comes from there, not edited here). REQ-EVL-003 stays partly with TD-07: nothing built, the stop above is answered.

| Item | Commit | What changed | Tests (red, then green) |
|---|---|---|---|
| test_harness never opens holdout suites | 4eb97ed | `harness.list_suites(root, holdout=False)` by default: `*.holdout` folders stay unread; `tools/eval.py` passes `--holdout` explicitly; `test_every_shipped_suite_is_valid` therefore skips them | `test_listing_never_opens_a_holdout_suite_unless_asked` (synthetic `toy.holdout` that is refused when read) |
| the pin decides the model | 97d4811 | `_pinned` replaces the skill's model by `{"name": pin name, options + seed, temperature}`; `Harness.run` refuses a variant `model` next to a pin; `tools/eval.py run` exits "--model together with --pin ... drop --model" before building a core; t05/t06/t09/t10 scripts drop `--model` (it equalled the pin's model); README and the usage text follow; the unit test of `_pinned` now expects the pin's model | `PinDecidesTheModel` (2 tests: every call of a pinned verify_claim run names gemma4:12b-it-qat; refusal in harness and command line) |
| A-63 re-checked | this commit | drafts redrafted (test_eval_platform.py changed); on a scratch copy of the merged branch: six protected tests OK, old copies removed, trace_check unchanged, test_doc_check clean, second run "nothing to do" | |

The open point "--pin does not set the model of the old targets" above is closed by 97d4811; "test_harness opens holdout suites" by 4eb97ed; CLAUDE.md by the owner (bc6df53).
