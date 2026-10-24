# Plan: number gate, stability and baselines (Plan iteration 1)

**Requirements:** specs/number-gate/requirements.md   **Test spec:** specs/number-gate/test-spec.md   **Eval spec:** specs/number-gate/eval-spec.md   **Status:** Draft (Plan step 5, 2026-10-24)

The order follows the approved staging: cheap offline work first, short model runs next, the decision with the owner, then code that depends on it, and the long runs last. A task fits one session. Numbers of the tasks T-05, T-06, T-07, T-10, T-11 and T-12 are those of `eval-spec.md`.

## Task list
| Task | Implements | Green when | Depends on | Needs Ollama |
|---|---|---|---|---|
| T-01 Number check in code | REQ-NUM-001..006, IF-001 | TC-NUM-001..006, TC-IF-001 | – | no |
| T-02 Stability metric with facts | REQ-STAB-001, -002, IF-004 | TC-STAB-001, -002, -004, TC-IF-004 | – | no |
| T-03 Harness: retired cases, pin in header and options, seeded sample, case input | REQ-EVAL-001..004, IF-005 | TC-EVAL-001..005, TC-IF-005 | – | no (fake server) |
| T-04 *Owner:* label the 24 injection drafts and promote them | REQ-VER-007 (cases) | `agent_check.py` A3 and A8 gone | – (parallel to T-01..T-03) | no |
| T-05 Smoke run and spike: pins reach Ollama, speed of the full model | REQ-EVAL-003, ASM-003 | 20 dev cases run; two runs with seed 7 and temperature 0 give the same answers or the difference is reported | T-03 | yes, about 3 min |
| T-06 Dev-sample baseline: single and cops, 100 dev cases, 1 repeat | baseline for REQ-VER-001..004 | baseline files and summary written; A13 for the dev part | T-03, T-05 | yes, about 13 min |
| T-07 *With the owner:* error analysis and the gate decision | REQ-GATE-001, REQ-NUM-003, -005, -006 | decision recorded in `implementation-log.md` or as an amendment | T-01, T-06 | no |
| T-08 Gate pipeline verify.number_gate@1 and the library node check.number | REQ-GATE-001..005, IF-003 | TC-GATE-001..005, TC-IF-003 | T-01, T-07 | no (scripted model) |
| T-09 Prompt work for the steps, only if the dev sample shows it is needed | REQ-VER-001..004, -007 | dev sample: `eval_decide.py` PASS or NOT DECIDED by the bound only; no red-team case lost | T-04, T-06, T-08 | yes, 13 min per run |
| T-10 Stability measurement: 100 dev cases, 3 repeats, single, cops and the gate | REQ-VER-005, -006 (dev, feedback) | stability report written; unstable cases listed | T-02, T-08 | yes, about 57 min |
| T-11 Holdout baseline of the current release, unread | baseline for REQ-VER-001..006 | files in `eval/baselines/`; nobody reads them before Verify | T-03, T-08 frozen | yes, about 107 min (overnight) |
| T-12 Full dev baseline (optional) | – | file written | T-03 | yes, about 64 min |
| T-13 Benchmark BM-GATE-001 measured | NFR-BUD-001 | `tests/acceptance/test_benchmarks.py` green | T-08 | yes, about 13 min |
| T-14 Packaging: documentation, `tools/eval.py` options, install script | REQ-EVAL-001..004 | README and `ui/README.md` describe the options; `tools/install_external_suites.sh` still works | T-03, T-08 | no |

Parallel candidates: T-01, T-02, T-03 and T-04 are independent. T-05 and T-06 can start as soon as T-03 is done. T-08 waits for the decision of T-07, so T-01 to T-06 are the work that does not depend on it. T-11 is run last and **unread**; T-10 and T-13 can share one overnight session.

## Tasks

### T-01: Number check in code
- Implements: REQ-NUM-001, REQ-NUM-002, REQ-NUM-003, REQ-NUM-004, REQ-NUM-005, REQ-NUM-006, IF-001
- Tests to turn green: TC-NUM-001..006, TC-IF-001 (`tests/acceptance/test_number_check.py`)
- Touches: `checks.py` (the stub `number_check`; reuse `parse_number`, `_agrees`, `unit_conversion` and the unit tables), a new library node `library/nodes/check.number/1.json` is T-08
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, benchmarks/, the existing checks and their tests
- Depends on: –
- Done when: the listed tests are green, all other tests unchanged (`tests/test_checks.py` 42 tests)
- Notes: write the quantity matching (REQ-NUM-006) as a small function of its own so that T-07 can measure how many dev claims it matches; no model call anywhere; the status "unimplemented" of the stub disappears

### T-02: Stability metric with facts
- Implements: REQ-STAB-001, REQ-STAB-002, IF-004
- Tests to turn green: TC-STAB-001, TC-STAB-002, TC-STAB-004, TC-IF-004 (`tests/acceptance/test_stability.py`, `test_contracts.py`)
- Touches: `metrics.py` (the stubs `same_facts`, `case_is_stable`, `repeat_lists`, `stability_report`; `stability()` keeps its behaviour), the report in `harness.py` may print the new report next to the old line
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, benchmarks/, the meaning of `metrics.stability` (its tests stay green)
- Depends on: –
- Done when: the listed tests are green; `tests/test_metrics.py` and `tests/test_harness.py` unchanged
- Notes: a fact is reduced to (normalised entity, number with unit, hash of the normalised quote); normalise case, diacritics, thousands marks and spaces; the wording of an answer never counts; the Wilson interval comes from `metrics.wilson`

### T-03: Harness features
- Implements: REQ-EVAL-001, REQ-EVAL-002, REQ-EVAL-003, REQ-EVAL-004, IF-005
- Tests to turn green: TC-EVAL-001..005, TC-IF-005 (`tests/acceptance/test_harness_pin.py`, `test_contracts.py`)
- Touches: `harness.py` (`Suite.select`, `Harness.run`, `sample_cases`, `case_input`, the header), `tools/eval.py` (options `--sample N`, `--seed S`, `--pin`, `--include-retired`), the model call options in the runner only as far as the pin needs
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, benchmarks/, `pipeline.py` unless the options cannot reach the model otherwise (then stop and report: amendment)
- Depends on: –
- Done when: the listed tests are green; the 24 tests of `tests/test_harness.py` unchanged
- Notes: spike inside this task with the fake server: the seed and temperature must be in the `options` of every `chat` call; whether the real Ollama honours them is checked at T-05; the pin is {name, digest, seed, temperature}; the header gets `pin`, `repeats`, `suite_sha1`

### T-04: Label the injection drafts (owner)
- Implements: the cases of REQ-VER-007
- Tests to turn green: `agent_check.py` A3 (suite found) and A8 (RT-001..RT-006 tagged)
- Touches: `specs/number-gate/eval-drafts/verdicts_injection.jsonl` (read, correct), then `eval/suites/` through the tool
- Must not touch: the holdout folder after it exists; the coding agent never edits `eval/suites/`
- Depends on: –
- Done when: the owner has checked the truth of each of the 24 cases and run `python3 -I tools/promote_drafts.py specs/number-gate/eval-drafts/verdicts_injection.jsonl verdicts_injection eval/suites --labelled`
- Notes: the file shows the proposed truth and a note per case; 11 cases have no verdict as the right answer; change a case rather than keep one you doubt; the split is already in the tags (12 and 12)

### T-05: Smoke run and spike on the real server
- Implements: REQ-EVAL-003, ASM-003; informs the cost table of the eval spec
- Tests to turn green: –; result is a note in `implementation-log.md`
- Touches: nothing in the code; runs `tools/eval.py` with the new options
- Must not touch: everything
- Depends on: T-03
- Done when: 20 dev cases (10 per suite) ran with single and cops, 1 repeat; two runs of the same 5 cases with seed 7 and temperature 0 are compared and the result (identical or not) is written down; seconds per case and the first-token time are noted; the speed of MP-full is noted once (it does not fit the GPU)
- Eval budget: about 3 min plus 2 minutes for the repeat and the full-model look
- Notes: if Ollama ignores the seed through the adapter, T-03 is reopened by a plan amendment; stability is then read with that caveat

### T-06: Dev-sample baseline
- Implements: the baseline of REQ-VER-001..004 on the dev split
- Tests to turn green: `agent_check.py` A13 for the dev files
- Touches: `eval/baselines/` through the owner or a hook (protected); `data/eval/` for the runs
- Must not touch: the holdout folders (never read or run in this task)
- Depends on: T-03, T-05
- Done when: single (verify.single@1) and cops (verify.cops@1) ran on a seeded sample of 100 dev cases (50 per suite, pairs together, seed 7), 1 repeat, pin MP-light; baseline files and `eval/baselines/verdicts_numbers-dev-sample.md` written; the owner chooses the 5 `smoke` cases
- Eval budget: 100 × 7.5 s ≈ 13 min, once
- Notes: record per claim kind (wrong, true, no verdict; with and without evidence) the false-pass rate, the right rate and the seconds; this is the first look at ASM-002

### T-07: Error analysis and the gate decision (with the owner)
- Implements: decides REQ-GATE-001, REQ-NUM-003, -005, -006 (keep, change or drop)
- Tests to turn green: –
- Touches: `implementation-log.md`; a plan amendment (`plan: amend ...`) if a requirement changes
- Must not touch: everything else
- Depends on: T-01, T-06
- Done when: for the errors of single and cops on the dev sample, a table says which a number check would decide (using `checks.number_check` on the dev cases), which need the model, and which no style gets right; the owner decides what the gate is and whether the thresholds of REQ-VER-002 and -004 stand for the Wikidata claims
- Notes: the possible outcomes are written in `requirements.md` only by amendment

### T-08: Gate pipeline
- Implements: REQ-GATE-001..005, IF-003
- Tests to turn green: TC-GATE-001..005, TC-IF-003 (`tests/acceptance/test_number_gate.py`)
- Touches: `library/pipelines/verify.number_gate/1.json`, `library/nodes/check.number/1.json`, code nodes in `verification.py` or `library` helpers, `skills/verify_claim.md` (input fields style, version bump only if the front matter changes)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, benchmarks/, verify.single@1 and verify.cops@1 (immutable versions, they are the baselines)
- Depends on: T-01, T-07
- Done when: the listed tests are green; the new pipeline passes `tools/library.py validate`; status draft
- Versions: verify.number_gate@1 (new), check.number@1 (new)
- Notes: no loop node in the pipeline; the number check line is `Number check: <status> <detail>`; with empty evidence the check does not run and the line says not_applicable

### T-09: Prompt work (only if T-06 and T-07 show the need)
- Implements: REQ-VER-001..004, REQ-VER-007
- Tests to turn green: `eval_decide.py` on the dev sample: PASS, or NOT DECIDED only because of the bound; no red-team case of the dev split lost
- Touches: `library/nodes/view.argue*`, `view.judge*`, `view.verdict*` (new versions), the pipeline versions that pin them
- Must not touch: eval/, tests/acceptance/, the holdout, `verify.single@1`, `verify.cops@1`
- Depends on: T-04, T-06, T-08
- Done when: criteria above on the dev sample; the run log in `implementation-log.md` with versions and pin; proposed new cases listed
- Eval budget: about 13 min per dev-sample run; at most 8 variants, then stop and report
- Notes: one change per run; read the transcripts of the cases that changed; examples in a prompt must not resemble suite cases; prompt work and code work stay in separate tasks

### T-10: Stability measurement
- Implements: REQ-VER-005, REQ-VER-006 (dev, feedback only)
- Tests to turn green: –
- Touches: runs and a report in `data/eval/`
- Must not touch: the holdout
- Depends on: T-02, T-08
- Done when: 100 dev cases (the sample of T-06), 3 repeats, single, cops and the gate; `metrics.stability_report` written for each; the unstable cases listed and read
- Eval budget: 100 × 3 × (1.3 + 6.2 + about 6.5) s ≈ 70 min; cut to the gate and cops if time is short (about 38 min)

### T-11: Holdout baseline, unread
- Implements: the baseline of REQ-VER-001..006 on the holdout
- Tests to turn green: `agent_check.py` A13 for the holdout files
- Touches: `eval/baselines/` (protected)
- Must not touch: nothing is read; only run
- Depends on: T-03, T-08 frozen (the code candidate is final)
- Done when: single and cops, 3 repeats, pin MP-light, on EV-verdicts_vitaminc.holdout, EV-verdicts_wikidata.holdout and EV-verdicts_injection.holdout (284 + 12 cases); the files exist; **no one opens them before Verify**
- Eval budget: about 107 min, overnight, in the background

### T-12: Full dev baseline (optional)
- Implements: –
- Depends on: T-03
- Done when: single and cops on all 514 active dev cases, 1 repeat, written to `eval/baselines/`; about 64 min

### T-13: Benchmark measured
- Implements: NFR-BUD-001
- Tests to turn green: `tests/acceptance/test_benchmarks.py`
- Touches: `benchmarks/bm_gate_001.py` and `benchmarks/baseline.json` by plan amendment only (protected); the measurement code is written by the owner or amended in
- Depends on: T-08
- Done when: 100 claims, 3 warm-up claims, the median seconds per claim in `baseline.json` and at most 10 s
- Eval budget: about 13 min

### T-14: Packaging
- Implements: documentation of REQ-EVAL-001..004
- Touches: `README.md` (section on evaluation), `ui/README.md` (core phase notes), `tools/install_external_suites.sh` if its steps change
- Depends on: T-03, T-08
- Done when: the options and the new tests are documented; `tools/install_external_suites.sh` still ends with the list of suites; no frozen demo package is needed (MIA is maintained, HLS 3.4)

## Risks of the plan
- T-05 may show that Ollama does not honour seed and temperature per request through the adapter: then REQ-EVAL-003 changes by amendment and the stability figures carry a caveat.
- T-07 may show that the number check decides very few dev claims (the VitaminC claims often need arithmetic): then T-08 shrinks to the routing and the cops style plus the input limit, and REQ-GATE-001, REQ-NUM-003, -005, -006 are amended or dropped; the criteria REQ-VER-001..006 stay.
- The Wikidata criteria (REQ-VER-002, -004) may be out of reach for a 12B model without evidence (it may not know the values): decided at T-07 with the baseline numbers, by amendment.
- The holdout baseline run (T-11) occupies the GPU for about two hours; no other model work in that time.
