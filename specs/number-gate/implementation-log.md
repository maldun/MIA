# Implementation log: number gate (Plan iteration 1)

Plan baseline: tag `plan-baseline-it1`. My test runs are feedback, not verification (Verify decides).

## T-01 Number check in code – done 2026-10-24
- Implements: REQ-NUM-001..006, IF-001 (`checks.number_check` and helpers `_quantities`, `_same_quantity`, `_holds`, `_judge_quantity`; reuses `_agrees`, `parse_number`, `_UNITS`)
- Tests reported green: `tests/acceptance/test_number_check.py` 7 of 7; `tests/test_checks.py` 47 (5 new edge tests); the other touched modules unchanged (harness 24, metrics 18, verification 16, library 36, pipeline 26, compound 12, research 23, run_explain 16, evidence 9, external suite 13)
- Decisions:
  - Evidence is converted into the unit and scale of the claim, then `_agrees(claimed, actual, 0.01, raw)` decides, so the rounding the claim shows scales with the scale word (4.8 million against 4.83 million passes, against 4.9 million fails).
  - Units come from the `checks._UNITS` tables plus percent and money symbols or words; the words in, st, b, pt and cup are never read as units.
  - A quantity with a bound in the evidence ("more than 23 million") decides nothing.
  - Several claimed numbers: any fail gives fail, else any pass gives pass, else inconclusive.
  - Quantity match: the same unit dimension, or both without unit and one shared content word in the three words after the number.
- Findings for T-07 (how much the check decides on the dev sample), no protected test needed:
  - A claim with neither unit nor noun after the number (a year: "built in 1937") never matches, so it is inconclusive. Conservative on purpose (HC4); count how many dev claims this leaves undecided.
  - If the evidence has several values of the claimed dimension (300 m and 20 m), any agreeing value gives pass: a claim "20 m tall" would pass against the tower sentence. This is a possible false pass; measure it on the dev sample before deciding whether to tighten it (nouns of the first window).
  - Arithmetic claims (sum of albums and singles) are out of scope of the check.
- Commit: see git log (`feat: number check (T-01)`).

## T-02 Stability metric with facts – done 2026-10-24
- Implements: REQ-STAB-001, REQ-STAB-002, IF-004 (`metrics.same_facts`, `case_is_stable`, `repeat_lists`, `stability_report`; `metrics.stability` unchanged)
- Tests reported green: `tests/acceptance/test_stability.py` 5 of 5 (incl. the regression TC-STAB-003 and the 1000-seed property test); TC-IF-004 in `test_contracts.py`; `tests/test_metrics.py` 22 (4 new); all other touched modules unchanged
- Decisions: a fact key is (entity without case and diacritics, number as float, unit, SHA-1 of the normalised quote); facts compare as a multiset, so a repeated fact counts twice; records without a `facts` field compare by status alone, so old runs still work; `inconclusive` and `none` are one status.
- Still red in `test_contracts.py`: TC-IF-005 (T-03).

## T-03 Harness features – done 2026-10-24
- Implements: REQ-EVAL-001, -002, -003, -004, IF-005 (`harness.Suite.select`, `Harness.run(pin, include_retired)`, `Harness._pinned`, `suite_sha1`, `sample_cases`, `case_input`; `tools/eval.py` options `--pin`, `--sample`, `--sample-seed`, `--include-retired`)
- Tests reported green: `test_harness_pin.py` 5 of 5, `test_contracts.py` 5 of 5 (TC-IF-005 now green); `tests/test_harness.py` 28 (4 new); all other touched modules unchanged. Acceptance overall: 28 of 29 plus the benchmark skeleton; red are the 6 gate tests (T-08) and BM-GATE-001 (T-13).
- Decisions:
  - The pin reaches the model through `skill["model"]["options"]` of a copy of the skill (the pipeline runner already passes those to `model.chat`), in the four skill-based targets (pipeline, plan, research, extraction). The pin name and digest are recorded in the header only; which model answers is still chosen by the variant (`--model`). T-05 checks that the digest of the running model equals the pin.
  - `PINS` (MP-light) lives in `tools/eval.py`, copied from `eval-spec.md`; a change there is an amendment first.
  - `--sample` selects ids with `sample_cases` and hands them to `Harness.run` as `only`; an empty sample stops with a message instead of running everything.
  - A sample of pairs with an odd N is one case short rather than splitting a pair.
  - `case_input` is the interface of IF-005; the gate pipeline (T-08) decides how it uses seed and temperature, because the model options already carry them.
- Open for T-05: whether the real Ollama adapter honours `seed` and `temperature` in `options` (the fake model only proves they are passed).
- Added with T-03 for T-05: `tools/eval.py` reads the suites from `MIA_SUITES` when set (a worktree finds the labelled suites of the main checkout, where the installed suites live); `tools/run_t05_smoke.sh` runs the T-05 smoke and determinism spike in one go (digest check, 10 dev cases per suite for single and cops, 6 cases twice).
- Finding on the suites (no test needed, it is data): a VitaminC `pair:` tag groups 3 to 4 cases of one claim (75 of 100 groups do not have 2 cases), a Wikidata pair has 2 except 2 pairs whose other half is retired. `sample_cases` keeps a whole group together, so a sample of N cases can be a little short of N.
