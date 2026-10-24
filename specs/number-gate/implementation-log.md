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

## T-05 Smoke run and spike – run 2026-10-24 (owner ran `tools/run_t05_smoke.sh`; log `data/eval/t05.log` in the main checkout)
Eval runs (dev split only, feedback not verification). Pin MP-light (digest checked against the server: equal), seed 7, temperature 0, 1 repeat, `verify.single@1` and `verify.cops@1` (skill_version 1). 10 dev cases per suite, so every figure below has a very wide interval.

| Suite | Style | Right overall | False pass | Coverage | Seconds per case | Calls |
|---|---|---|---|---|---|---|
| verdicts_vitaminc | single | 9 of 9 decided | 0 of 3 | 100 % | 7.5 (first case loads the model; 1.6 to 1.7 warm) | 10 |
| verdicts_vitaminc | cops | 8 of 9 | 0 of 3 | 89 % | 7.0 | 30 |
| verdicts_wikidata (no evidence) | single | 5 of 10 | 1 of 5 | 80 % | 1.3 | 10 |
| verdicts_wikidata (no evidence) | cops | 4 of 10 | 2 of 5 | 80 % | 5.5 | 30 |

Findings:
1. **The run header is complete** (pin with digest, seed and temperature, repeats, pipeline, skill version, SHA-1 of the suite files): REQ-EVAL-001 holds on the real harness.
2. **Seed 7 and temperature 0 do not make a run reproducible.** The same 6 VitaminC cases run twice gave one different status (vc-5ed50880c9e77c000848cf60_3: inconclusive, then fail) with different reasoning text. Direct spike on the Ollama API: 6 identical calls, and calls interleaved with other prompts, always gave byte-identical answers (hash a422dcb5 every time). Running that one case four times through the pipeline gave inconclusive, fail, fail, fail; run again straight after, fail four times. So the answer of a borderline case depends on the server's cache state (cold prefill against a cached prefix), not on the seed. Consequences: (a) the stability metric (REQ-STAB, REQ-VER-005/006) measures a real effect and must be read as "stability under server state", not as noise from sampling; (b) bit-exact reproduction of a run cannot be promised at this pin, only statistical reproduction; (c) the runs of T-06/T-10/T-11 should keep the harness order (repeat-major, other cases between the repeats), which is the realistic setting. No requirement changes yet; HLS AC-2 asks for stability, which is exactly what is measured. To raise with the owner at T-07: whether REQ-VER-005 (stability min 0.90) is the right bar for borderline claims.
3. **Wikidata without evidence is a coin toss for this model**: right 40 to 50 %, false pass 20 to 40 % (n = 5 wrong claims, interval 4 to 62 %). The criteria REQ-VER-002 (false pass at most 5 %) and REQ-VER-004 (right at least 90 %) look unreachable by judgement alone, as the plausibility lines warned. Too few cases for a decision; T-06 has 50 per suite. If it holds: stop condition "criterion looks unreachable" and a decision at T-07 (for example: without evidence the gate abstains, and the criteria are about the abstention).
4. **Cost** is close to the cost table of the eval spec (single 1.3 to 1.7 s warm, cops 5.5 to 7 s); the model load of about 6 s happens once per run.
5. The first VitaminC cops case that failed (vc-5ed50880c9e77c000848d32c_3, true) was answered inconclusive, no false pass in the smoke sample.

Next: T-06 (`tools/run_t06_baseline.sh`, about 15 minutes).

## T-06 Dev-sample baseline – run 2026-10-24 (owner ran `tools/run_t06_baseline.sh`, twice; log `data/eval/t06.log` in the main checkout)
Dev split only, pin MP-light (seed 7, temperature 0), 1 repeat, 50 cases per suite (seeded sample, groups kept together), `verify.single@1` and `verify.cops@1`. Baseline copies `eval/baselines/<suite>__<style>__devsample.jsonl` exist (the second run did not overwrite them). Feedback for me, not verification; intervals are 95 % Wilson over claims with a verdict.

| Suite | Style | Right overall | Coverage | False pass | False fail | Seconds per case | Calls |
|---|---|---|---|---|---|---|---|
| vitaminc | single | 86.7 % (39 of 45; 74–94) | 97.8 % | 11.1 % (2 of 18; 3–33) | 11.1 % (3 of 27) | 1.4 | 50 |
| vitaminc | cops | 77.8 % (35 of 45; 64–87) | 88.9 % | 11.1 % (2 of 18; 3–33) | 11.1 % (3 of 27) | 6.6 | 150 |
| wikidata (no evidence) | single | 34.0 % (17 of 50; 22–48) | 64 % | 28 % (7 of 25; 14–48) | 32 % (8 of 25) | 1.3 | 50 |
| wikidata (no evidence) | cops | 32.0 % (16 of 50; 21–46) | 60 % | 16 % (4 of 25; 6–35) | 40 % (10 of 25) | 5.9 | 150 |

- Against the criteria (REQ-VER-001 false pass at most 5 %, -003 right at least 90 %): VitaminC single is 11 % false pass, 87 % right: a gap of about 6 points and 3 points, plausible by prompt work or a gate. Wikidata (REQ-VER-002/-004) is far off: 28 % false pass and 34 % right overall; as the plausibility lines warned, the model does not know obscure facts, and no style helps. **Stop condition "criterion looks unreachable" for REQ-VER-002 and REQ-VER-004 on the judgement alone: decision at T-07.**
- The second, identical run changed 2 of 45 VitaminC single answers (coverage 97.8 % to 95.6 %: two answers moved between a verdict and inconclusive); cops and both Wikidata runs were identical. Together with the T-05 finding this is the server-state effect, now measured: about 4 % of VitaminC single cases flip between two runs. That is the order of magnitude to expect in T-10 (stability), against a threshold of 0.90.
- Cost matches the cost table (cops about 4 to 5 times single).

## T-07 first evidence – the number check on the dev split (no model; to decide with the owner)
Run of `checks.number_check` on all 332 active dev cases of verdicts_vitaminc (truth known), after fixing one bug found by this very analysis (a currency symbol between a bound and its number hid the bound: "less than $ 44 billion" was compared for equality; regression test in `tests/test_checks.py`; the one-sided noun match of REQ-NUM-006 for "₹50 crore" against "18 Crore" came with it):

| Check says | claim true | claim false | no verdict |
|---|---|---|---|
| pass | 88 | 16 | 7 |
| fail | 12 | 58 | 10 |
| inconclusive | 68 | 55 | 16 |
| not_applicable | 1 | 0 | 1 |

- The check decides 191 of 332 cases (58 %). Of the 129 false claims it passes 16 (12 %); of the 169 true claims it fails 12 (7 %). That is the same order as the model (single: 11 % and 11 %), not better. The 28 wrong decisions are mostly claims whose number is right but whose subject is swapped (Tupac against Makaveli; Bulls against Pacers; "initially lost" against "initially won" in 2011), spelled-out numbers ("two-year"), and European thousands marks ("300.000"). A number check cannot tell those apart; this is the limit of the idea, not a bug.
- Wikidata: all 182 cases are `not_applicable` (no evidence), as designed.
- Crossed with the model on the 50-case sample (45 with a verdict): the check agrees with the model on 38 of 45 decisions; the errors overlap (both wrong on the same 2 false claims). "Check first, model otherwise" gives 38 right, 4 false pass, 3 false fail (single); the model alone has 2 false pass, 3 false fail. So the check as an override does not help on this sample, and as a veto it would have turned one correct model pass (true claim) into a fail.
- Decision needed from the owner (T-07), options in the report to the owner.
- Decided 2026-10-24: option 1 (A-01, see `amendments.md`).

## T-08 Gate pipeline – code done 2026-10-24, waiting for the changed acceptance tests of A-01
- Implements: REQ-GATE-001..006, IF-003 (as amended by A-01). New: `number_gate.py` (gate_prepare, run_number_check, gate_evidence, gate_record, gate_abstain; registered in `core.py`), library pipeline `verify.number_gate@1` (draft), library nodes `check.number@1`, `code.gate_prepare@1`, `code.gate_evidence@1`, `code.gate_record@1`, `code.gate_abstain@1` (draft). `verify.single@1`, `verify.cops@1` and the skill `verify_claim` are untouched.
- Route: a claim with a number and no evidence answers unclear (0 calls); a claim without a number takes the single voice (the evidence is only cut to 4000 characters); other claims get the number check, its line first in the evidence of every judgement step (`Number check: <status> - <detail>`, and for fail "Code found a contradiction between the claim and the evidence."), then cops by default or single when `style` is given. The check is logged as a `check_run` event (name number_check, result pass/fail/skipped for inconclusive) before the first model call.
- Tests reported green: new unit tests `tests/test_number_gate.py` 10 of 10; `tests/acceptance/test_number_gate.py`: TC-GATE-001, -004, -005 green; TC-GATE-002, TC-GATE-003 and TC-IF-003 fail **only because they still hold the expectations that A-01 replaced** (check decides without a model call; empty evidence goes to cops; calls 0 for a failed check). With the patch of A-01 applied on a copy outside the repository all 7 tests pass. `tools/library.py validate`: 69 nodes, 24 pipelines, 0 problems. All other touched modules unchanged (checks 48, harness 28, metrics 22, verification 16, library 36, pipeline 26, compound 12, research 23, run_explain 16, evidence 9, external suite 13).
- Decisions: `seconds` in the record is the time from the route decision to the record (it does not include the harness overhead); `calls` is by route (0, 1 or 3), not counted from events; `style` is a run input, not a skill field, so the skill `verify_claim` keeps its version; an unknown style stops the run with an error.
- Open for the owner: apply `specs/number-gate/A-01-tests.patch` (or write the tests yourself) and check `tests/smoke/smoke_gate.py` for expectations about the Wikidata cases (they now answer unclear); then T-08 is green by the acceptance tests.
- Smoke (2026-10-25): the owner tagged the 5 smoke cases with `tools/tag_smoke_cases.py` (VitaminC `vc-5ed7ad02c9e77c00084a6f6d_1` true, `vc-5ed50882c9e77c000848f869_2` false; Wikidata `wd-Q1049868-tower-height-true`, `wd-Q180558-river-length-false`, `wd-Q110994774-bridge-year-true`). I wrote the body of SMOKE-GATE-001/-002 as `specs/number-gate/smoke-gate.patch` for the protected `tests/smoke/smoke_gate.py` (to be applied by the owner). Run on a copy outside the repository against the real server (venv python, pin MP-light, `verify.number_gate@1`): green, 5 cases: the Wikidata cases answer unclear, the VitaminC cases pass/fail as expected, the header digest equals the digest of the server. This is the first real-model run of the gate (5 cases, dev; feedback only). The "release run" of SMOKE-GATE-001 is, until a release exists, the stable answer of the T-06 baselines.
- Residual risk for T-09 and Verify: the check line stands in the same field as the evidence text (a first line and a separator), so an evidence text could imitate it; the injection suite (EV-verdicts_injection) measures whether a judge can be talked out of a "Number check: fail" line.
