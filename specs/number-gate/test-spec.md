# Test specification: number gate, stability and baselines

**Requirements:** specs/number-gate/requirements.md   **Status:** Draft (Plan step 3, 2026-10-24)

Deterministic tests run with the fake model server (`FakeServer` of the existing tests, no Ollama) and with recorded pages (`FixtureWebSession`). Requirements that depend on the model are decided by the eval suites, see `eval-spec.md`; their criteria are not repeated here. Test ids and requirement markers follow `dev-workflow/references/conventions.md`; the tests live in `tests/acceptance/` (protected after the Plan gate).

## Test cases

| Test ID | Verifies | Level | Setup / inputs | Expected result | Limit / tolerance |
|---|---|---|---|---|---|
| TC-GATE-001 | REQ-GATE-001 | Component | 6 claims with a number and evidence, 2 claims with a number and empty evidence, fake model, run log | for the 6 claims the event check_run of the number check precedes the first model call; for the 2 claims no number check runs | exact |
| TC-GATE-002 | REQ-GATE-002 | Component | fake number check returning fail for a claim whose evidence would let the fake judge say supported | verdict refuted, number of model calls 0 | exact |
| TC-GATE-003 | REQ-GATE-003 | Component | fake number check returning pass, then inconclusive, then not_applicable; style cops; once with style single | cops: argue for, argue against, judge once each in this order, the judge input contains the check line; single: 1 model call | exact |
| TC-GATE-004 | REQ-GATE-004 | Component | the 20 claims without a number of the suite `verdicts`, fake model with scripted replies | verdict and number of model calls equal those of verify.single@1 on the same replies | exact |
| TC-GATE-005 | REQ-GATE-005 | Component | evidence of 30000 characters, then 4000, then 3999 | each argue and judge input carries at most 4000 characters of evidence; 4000 and 3999 are passed whole | exact |
| TC-NUM-001 | REQ-NUM-001 | Component | 1,200 m vs 1,020 m; 1,200 m vs 1,200 m; 1,200 m vs 1,210 m; 4.8 million vs 4.83 million; 4.8 million vs 4.9 million | fail; pass; fail; pass; fail | exact |
| TC-NUM-002 | REQ-NUM-002 | Component | "The hall is 40 m long." with "The hall was built in 1901."; with "The hall has 40 seats." | inconclusive; inconclusive | exact |
| TC-NUM-003 | REQ-NUM-003 | Component | "more than 5 million views" vs "3.2 million views"; vs "7 million views"; vs "5 million views"; "at least 3 albums" vs "3 albums"; "under 23.5 million" vs "more than 23 million" | fail; pass; fail (not strictly more); pass (bound included); inconclusive | exact |
| TC-NUM-004 | REQ-NUM-004 | Component | 5 claims with empty evidence, among them 2 without a number | not_applicable for all 5 | exact |
| TC-NUM-005 | REQ-NUM-005 | Component | 23.5 million vs 23,500,000; 5 km vs 3.1 miles; 5 km vs 3.0 miles; 1.2 km vs 1,210 m | pass; pass; fail; pass | exact |
| TC-NUM-006 | REQ-NUM-006 | Component | "The hall is 40 m long." vs "The hall has 40 seats."; "sold under 23.5 million records" vs "13 million albums and 9.8 million singles"; 40 m vs "length 41 m" | inconclusive; inconclusive; fail | exact |
| TC-ARG-001 | REQ-ARG-001 | Contract | outputs with 0, 1, 2, 4 and 5 points; points of 2, 3, 400 and 401 characters | accepted: 1, 2, 4 points and 3, 400 characters; rejected: 0 and 5 points, 2 and 401 characters | exact |
| TC-IF-001 | IF-001 | Contract | the 4 acceptance claims of REQ-NUM-001 to REQ-NUM-004 | status fail or pass, inconclusive, pass or fail by bound, not_applicable in turn; detail of at most 200 characters | exact |
| TC-IF-002 | IF-002 | Contract | judge outputs with the verdicts supported, refuted, unclear, maybe; reasons of 2, 3, 600 and 601 characters; confidence 0, 1 and 1.1 | accepted: the three verdicts, reasons of 3 and 600, confidence 0 and 1; rejected: maybe, 2, 601 and 1.1 | exact |
| TC-IF-003 | IF-003 | Contract | a claim decided by the number check; a claim decided by the cops style | calls 0 and facts empty; calls 3; verdict and status agree by supported-pass, refuted-fail, unclear-inconclusive | exact |
| TC-IF-004 | IF-004 | Contract | 4 cases with 3 repeats, 1 case with 1 repeat | the metric receives 4 lists of 3 entries with status and facts; the single repeat is not passed | exact |
| TC-IF-005 | IF-005 | Contract | fake gate, 3 cases, pin seed 7 and temperature 0 | the harness hands over 4 fields per case: claim, evidence, seed 7, temperature 0 | exact |
| TC-IF-006 | IF-006 | Contract | the examples of TC-IF-002 against the schema of view.verdict@1 | same accepts and rejects (verdict, reason; no confidence required) | exact |
| TC-STAB-001 | REQ-STAB-001 | Component | pairs of repeats: same facts in another order and wording; 3 facts against 4; same count with 1,200 against 1,020; same facts plus the word "approximately" | stable; not stable; not stable; stable | exact |
| TC-STAB-002 | REQ-STAB-002 | Component | 10 cases with 3 repeats, 2 of them unstable | share 0.8; Wilson 95 % interval [0.49, 0.94]; the 2 identifiers | two decimals |
| TC-STAB-003 | REQ-STAB-003 | System | a lookup on the recorded web of the suite `research`, then offline reproduction (`reproduce.py`) | every fetched page is in the content store under its hash; the reproduced run has the same events | exact |
| TC-STAB-004 | REQ-STAB-001 | Property | 1000 generated fact sets with random order and 3 rewordings each | no pair is judged not stable; seeds 1 to 1000 | 0 failures |
| TC-EVAL-001 | REQ-EVAL-001 | Component | a run with the fake server and the pin of the eval spec | the saved header has the 8 fields with the values of the call | exact |
| TC-EVAL-002 | REQ-EVAL-002 | Component | a suite of 5 cases, 2 tagged retired | report counts 3 cases; with include-retired 5 | exact |
| TC-EVAL-003 | REQ-EVAL-003 | Component | fake server that records the requests of a run | every request carries the seed and the temperature of the pin | exact |
| TC-EVAL-004 | REQ-EVAL-004 | Component | sample 20 with seed 7 on a suite with 30 pairs, twice | the same 20 cases twice; no pair split | exact |
| TC-EVAL-005 | REQ-EVAL-004 | Property | samples of size 10 to 60 with seeds 1 to 200 on the same suite | no pair split in any sample | 0 failures |
| BM-GATE-001 | NFR-BUD-001 | Benchmark | 100 claims of the dev split (50 per suite), MP-light, reference host | median of the seconds per claim | <= 10 s |

TC-STAB-004 and TC-EVAL-005 are property tests over fixed seeds, not noisy statistical checks: the code is deterministic, so they have no false-alarm budget. One value was recalculated by hand for TC-STAB-002: for 8 of 10 the Wilson centre is (0.8 + 1.96²/20) / (1 + 1.96²/10) = 0.7167 and the half width 0.2266, which gives [0.49, 0.94].

## Statistical checks (M19: fixed before any data; run in Verify and nightly on the dev split)

The statistical criteria are eval criteria; they are specified in `eval-spec.md` (criteria, decision rules, error rates). There are no statistical checks of code in this iteration.

| Test ID | Verifies | Statistic | n | Seeds | Criterion | Method | False alarm / miss (exact) | Paired fixed-seed test |
|---|---|---|---|---|---|---|---|---|
| (none) | – | – | – | – | – | – | see eval-spec.md | – |

## Benchmarks and baselines

| Benchmark | Verifies | Reference hardware | Repetitions (warm-up) | Baseline median (measured) | Budget / regression rule |
|---|---|---|---|---|---|
| BM-GATE-001 | NFR-BUD-001 | development host, RX 7800 XT 16 GB, MP-light, Ollama in podman | 100 claims once each (3 warm-up claims) | cops 6.2 s per claim on the old suite (verdicts-styles.md, 2026-10-19, mean); the median on the new suites is measured at T-06 | median at most 10 s; a rise of more than 20 % over the T-06 median after a change is a regression |

## Smoke tests (run in Phase 6, target environment)

| Test ID | Verifies | Target | Conditions | Expected result |
|---|---|---|---|---|
| SMOKE-GATE-001 | REQ-GATE-002, REQ-GATE-003 | the MIA compose stack with its Ollama | 5 cases tagged smoke, chosen at T-06 by the owner (3 from verdicts_wikidata dev, 2 from verdicts_vitaminc dev), pin MP-light | the same verdict as in the release run for every case |
| SMOKE-GATE-002 | REQ-EVAL-001 | the same | one run of 5 smoke cases | the run header names the digest of the model that the server really holds |

## Validation criteria (checked in Phase 7)

| ID | Criterion | How we check | Who | Agreement (if numeric): margin, mean or single values, method |
|---|---|---|---|---|
| VAL-001 | In four weeks of use, of the claims that users vote down (minus on an answer, FR-27) at most 1 in 10 had been rated supported by the gate | run log with the votes; the owner reads the flagged answers | owner and users | descriptive; no equivalence test (fewer than 30 events expected) |
| VAL-002 | The owner repeats 10 lookup questions twice: the same number of facts and the same statements in at least 9 of the 10 pairs, order and wording ignored | the stability metric on the two runs, then the owner reads the differing pairs | owner | descriptive; small sample |
