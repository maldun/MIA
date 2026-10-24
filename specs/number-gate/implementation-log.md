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
