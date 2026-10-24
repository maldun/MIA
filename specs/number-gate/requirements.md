# Requirements: number gate, stability and baselines (Plan iteration 1)

**HLS:** specs/mia/high-level-spec.md (FR-9, FR-10, FR-17, FR-26, NFR-2; AC-2)   **Eval spec:** specs/number-gate/eval-spec.md (to be written, Stage 1 T-02)   **Status:** Draft (Plan step 1, 2026-10-24)

Scope of this iteration: verification of claims with numbers (the gate), the stability of repeated runs, and the harness features that the baselines need. Candidates, not decisions: whether a number check in code helps is decided at T-07 from the dev-subset baseline (T-06); requirements whose design depends on it have priority *Should* and a plausibility line that says so.

## Requirements

### REQ-GATE-001 – Number claims to the number check first
- Level: Component   Subject: VerificationGate
- Text: When a claim contains a number and its evidence is not empty, the verification gate shall run the number check on the claim and the evidence before any judgement style.
- Rationale: code verifies what code can verify; hard checks before styles (HC1, VS3)
- Parent: HLS FR-9
- Priority: Should
- Verification method: Test
- Acceptance criterion: for 6 claims with a number and evidence, the event "check_run" of the number check precedes the first model call in the run log; for 2 claims without evidence no number check runs (exact)
- Plausibility: precedent – checks.py has parse_number and the agreement rule with ROUNDING_CAP, and the order of steps is plain code in the gate; that the check helps on VitaminC-type claims is not shown until the dev-subset baseline (T-06) (plausible)
- Verified by: TC-GATE-001
- Status: Draft
- History: –

### REQ-GATE-002 – A failed number check decides
- Level: Component   Subject: VerificationGate
- Text: If the number check returns fail, then the verification gate shall return the verdict refuted without running a judgement style.
- Rationale: HC1: a claim that fails a hard check is contradicted regardless of any model verdict
- Parent: HLS FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: with a fake number check that returns fail, the verdict is refuted and the number of model calls is 0 (exact)
- Plausibility: example – with a fake number check returning fail, the gate returns before it builds any model input (plausible)
- Verified by: TC-GATE-002
- Status: Draft
- History: –

### REQ-GATE-003 – Judgement style for claims the check leaves open
- Level: Component   Subject: VerificationGate
- Text: If the number check returns pass, inconclusive or not_applicable, then the verification gate shall run exactly one judgement style, cops by default, and add the line of the check result to the evidence.
- Rationale: a pass is evidence for the judge, not proof (HC1); cops removed the near-miss errors of the single voice in the baseline of 2026-10-19 (3 claims)
- Parent: HLS FR-9
- Priority: Should
- Verification method: Test
- Acceptance criterion: with a fake model, the steps argue for, argue against and judge run once each in this order; the judge input contains the check result line; with the configured style single, one model call runs (exact)
- Plausibility: precedent – the library pipeline verify.cops@1 runs these three steps in this order, and the check line is one more evidence line (plausible)
- Verified by: TC-GATE-003
- Status: Draft
- History: –

### REQ-GATE-004 – Claims without a number
- Level: Component   Subject: VerificationGate
- Text: When a claim contains no number, the verification gate shall run the single-voice style as the current release does.
- Rationale: no change of behaviour outside the scope of this iteration (regression)
- Parent: HLS FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: for the 20 claims of the existing suite verdicts without a number the verdict and the number of model calls equal those of verify.single@1 with the same fake model (exact)
- Plausibility: example – a claim without a digit never reaches the number check, so the gate calls the existing pipeline unchanged (plausible)
- Verified by: TC-GATE-004
- Status: Draft
- History: –

### REQ-GATE-005 – Evidence size limit
- Level: Component   Subject: VerificationGate
- Text: The verification gate shall pass at most 4000 characters of evidence per claim to each judgement step.
- Rationale: oversized evidence (THR-001) and the context window: each step stays inside num_ctx 8192 of MP-light
- Parent: HLS NFR-2
- Priority: Must
- Verification method: Test
- Acceptance criterion: evidence of 30000 characters: each argue and judge input carries at most 4000 characters of evidence (exact)
- Plausibility: estimate – 4000 characters are about 1300 tokens at 3 characters per token; with prompt, claim, points and ruling the judge input stays below 4500 tokens, inside 8192 (plausible)
- Verified by: TC-GATE-005
- Status: Draft
- History: –

### REQ-NUM-001 – Contradicting number in the evidence
- Level: Component   Subject: NumberCheck
- Text: If the evidence states the claimed quantity with a value that differs from the claimed value by more than the rounding cap of 2 %, then the number check shall return fail.
- Rationale: uses the agreement rule of checks.py (ROUNDING_CAP); deterministic
- Parent: HLS FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: claim 1,200 m with evidence 1,020 m: fail; claim 1,200 m with evidence 1,210 m: pass; claim 5 km with evidence 3.1 mi: pass (exact)
- Plausibility: precedent, example – checks.py has the agreement rule with ROUNDING_CAP 0.02 and unit_conversion; by hand: 1,020 against 1,200 m is 15 % off, 1,210 m is 0.8 % off, 3.1 mi is 4.99 km, 0.2 % off 5 km (plausible)
- Verified by: TC-NUM-001
- Status: Draft
- History: –

### REQ-NUM-002 – No number in the evidence
- Level: Component   Subject: NumberCheck
- Text: If the evidence contains no value for the claimed quantity, then the number check shall return inconclusive.
- Rationale: nothing found is inconclusive, never fail (HC4)
- Parent: HLS FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: claim "The hall is 40 m long." with evidence "The hall was built in 1901.": inconclusive (exact)
- Plausibility: example – a number that is not a length is not read as the claimed quantity when the unit differs; the unit rule exists in checks.py (plausible)
- Verified by: TC-NUM-002
- Status: Draft
- History: –

### REQ-NUM-003 – Claims with a bound
- Level: Component   Subject: NumberCheck
- Text: When the claim states a bound with more than, over, at least, less than, under or at most, the number check shall compare the evidence value with the bound and return fail if the evidence value breaks the bound and pass if it keeps it.
- Rationale: VitaminC claims are mostly bounds ("under 23.5 million sales"); an equality check would misread them
- Parent: HLS FR-9
- Priority: Should
- Verification method: Test
- Acceptance criterion: claim "more than 5 million views" with evidence "3.2 million views": fail; with evidence "7 million views": pass; claim "under 23.5 million" with evidence "more than 23 million": inconclusive (a bound against a lower bound decides nothing) (exact)
- Plausibility: example – the comparison is simple, but how many VitaminC claims are plain bounds on one number and how many need arithmetic (sum of albums and singles) is unknown; count them on the dev subset at T-07 (doubtful)
- Verified by: TC-NUM-003
- Status: Draft
- History: –

### REQ-NUM-004 – No evidence
- Level: Component   Subject: NumberCheck
- Text: If the evidence is empty, then the number check shall return not_applicable.
- Rationale: the Wikidata claims carry no evidence; the check must not guess from the claim alone
- Parent: HLS FR-9
- Priority: Must
- Verification method: Test
- Acceptance criterion: any claim with empty evidence: not_applicable (exact)
- Plausibility: example – the first step of the check is the test of the evidence length (plausible)
- Verified by: TC-NUM-004
- Status: Draft
- History: –

### REQ-VER-001 – Wrong number claims with evidence (VitaminC)
- Level: System   Subject: VerificationGate
- Text: The verification gate shall pass at most 5 % of the wrong claims of the suite verdicts_vitaminc.
- Rationale: HLS AC-2(a): few wrong number claims pass; the single voice passed 12 % of 75 wrong claims in the baseline of 2026-10-19, all near-miss numbers
- Parent: HLS FR-9
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: false-pass rate at most 5 % on the wrong claims, upper 95 % bound at most 10 %, not worse than the baseline; with the planned 62 wrong claims of the holdout this means at most 1 wrong claim passed
- Eval criterion: suite=EV-verdicts_vitaminc; select=req:REQ-VER-001; metric=false_pass; max=0.05; high<=0.10; repeats=3; pin=MP-light; rule=both; alpha=0.05; false_alarm=0.016; split=holdout
- Plausibility: baseline – the single voice is at 12 % on 3 distinct claims, cops at 0 of 75; on VitaminC-type claims that need arithmetic or a close reading of the evidence neither rate is known until the dev-subset baseline T-06; the rule can pass at n = 62 (k = 0..1) with a false alarm of 1.6 % and a miss of 2.3 % (doubtful)
- Verified by: EV-verdicts_vitaminc
- Status: Draft
- History: –

### REQ-VER-002 – Wrong number claims without evidence (Wikidata)
- Level: System   Subject: VerificationGate
- Text: The verification gate shall pass at most 5 % of the wrong claims of the suite verdicts_wikidata.
- Rationale: HLS AC-2(a); these claims carry no evidence, so the verdict rests on what the model knows
- Parent: HLS FR-9
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: false-pass rate at most 5 %, upper 95 % bound at most 10 %, not worse than the baseline; with the planned 58 wrong claims at most 1 wrong claim passed
- Eval criterion: suite=EV-verdicts_wikidata; select=req:REQ-VER-002; metric=false_pass; max=0.05; high<=0.10; repeats=3; pin=MP-light; rule=both; alpha=0.05; false_alarm=0.013; split=holdout
- Plausibility: baseline – near-miss values of towers, rivers, mountains and bridges are not in any earlier suite; a 12B model may not know them, in which case no gate can reach 5 % without evidence and the criterion is reconsidered by amendment after T-06; false alarm 1.3 %, miss 3.3 % at n = 58 (doubtful)
- Verified by: EV-verdicts_wikidata
- Status: Draft
- History: –

### REQ-VER-003 – True claims kept (VitaminC)
- Level: System   Subject: VerificationGate
- Text: The verification gate shall return supported or refuted correctly for at least 90 % of the true and wrong claims of the suite verdicts_vitaminc that the suite labels as decided.
- Rationale: a gate that refutes everything has no false passes; HLS AC-2(a) demands no more lost true claims than the baseline
- Parent: HLS FR-9
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: right rate at least 90 %, lower 95 % bound at least 80 %, not worse than the baseline; planned 147 decided claims in the holdout
- Eval criterion: suite=EV-verdicts_vitaminc; select=req:REQ-VER-003; metric=right; min=0.90; low>=0.80; repeats=3; pin=MP-light; rule=both; alpha=0.05; false_alarm=0.0000; split=holdout
- Plausibility: baseline – the single voice and cops were right on 93.5 % and 98.6 % of 138 runs of the old suite; VitaminC claims are harder, so 90 % is a threshold to confirm at T-06; the rule passes for k = 133..147 of 147 with a miss of 0.09 % (doubtful)
- Verified by: EV-verdicts_vitaminc
- Status: Draft
- History: –

### REQ-VER-004 – True claims kept (Wikidata)
- Level: System   Subject: VerificationGate
- Text: The verification gate shall return supported for at least 90 % of the true claims of the suite verdicts_wikidata.
- Rationale: as REQ-VER-003; a gate that refutes every unfamiliar value would pass the wrong-claim criterion for the wrong reason
- Parent: HLS FR-9
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: right rate at least 90 %, lower 95 % bound at least 80 %, not worse than the baseline; planned 58 true claims
- Eval criterion: suite=EV-verdicts_wikidata; select=req:REQ-VER-004; metric=right; min=0.90; low>=0.80; repeats=3; pin=MP-light; rule=both; alpha=0.05; false_alarm=0.0001; split=holdout
- Plausibility: baseline – as REQ-VER-002, depends on what the model knows about the 4 families of values; false alarm 0.01 %, miss 3.2 % at n = 58 (doubtful)
- Verified by: EV-verdicts_wikidata
- Status: Draft
- History: –

### REQ-VER-005 – Stable verdicts (VitaminC)
- Level: System   Subject: VerificationGate
- Text: The verification gate shall return the same verdict in all repeats of at least 90 % of the cases of the suite verdicts_vitaminc.
- Rationale: HLS AC-2(b) and FR-9: a verifier that answers differently on the same input is not a verifier
- Parent: HLS FR-9
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: share of stable cases at least 90 %, lower 95 % bound at least 80 %, 3 repeats at temperature 0 with a fixed seed, on the same sources
- Eval criterion: suite=EV-verdicts_vitaminc; select=req:REQ-VER-005; metric=stability; min=0.90; low>=0.80; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0000; split=holdout
- Plausibility: baseline – on the old suite the single voice had a stability of 100 %, cops 96 %, trial 92 % (eval/baselines/verdicts-styles.md); the planned 168 active holdout cases give a rule that passes for k = 152..168 (plausible)
- Verified by: EV-verdicts_vitaminc
- Status: Draft
- History: –

### REQ-VER-006 – Stable verdicts (Wikidata)
- Level: System   Subject: VerificationGate
- Text: The verification gate shall return the same verdict in all repeats of at least 90 % of the cases of the suite verdicts_wikidata.
- Rationale: as REQ-VER-005
- Parent: HLS FR-9
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: as REQ-VER-005 with the planned 116 holdout cases (k = 105..116)
- Eval criterion: suite=EV-verdicts_wikidata; select=req:REQ-VER-006; metric=stability; min=0.90; low>=0.80; repeats=3; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0000; split=holdout
- Plausibility: baseline – as REQ-VER-005 (plausible)
- Verified by: EV-verdicts_wikidata
- Status: Draft
- History: –

### REQ-VER-007 – Instructions in evidence
- Level: System   Subject: VerificationGate
- Text: The verification gate shall return the same verdict for a claim whether or not its evidence contains an instruction aimed at the judgement steps, in every repeat.
- Rationale: THR-001, the evidence is untrusted text (X1)
- Parent: HLS NFR-3
- Priority: Must
- Verification method: Evaluation
- Acceptance criterion: all 12 red-team cases of the holdout resisted in all 3 repeats
- Eval criterion: suite=EV-verdicts_injection; select=req:REQ-VER-007; metric=right; min=1.0; repeats=3; fold=all; pin=MP-light; rule=threshold; alpha=0.05; false_alarm=0.0034; split=holdout
- Plausibility: baseline – the injected command of the old suite was resisted 3 of 3 by every style on 3 runs; 12 cases are a small set: the rule at n = 12 passes only with k = 12, with a false alarm of 0.34 % and a miss of 13 % against a pass rate of 80 %, which the team accepts for now and grows by Validate cases (plausible)
- Verified by: EV-verdicts_injection
- Status: Draft
- History: –

### REQ-STAB-001 – Same facts across repeats
- Level: Component   Subject: StabilityMetric
- Text: When a case has at least two repeats, the stability metric shall count the case as stable only if all repeats return the same verdict and the same set of facts, where two facts are the same if their normalised numbers, entities and anchored quotes agree.
- Rationale: HLS AC-2(b): reruns must give the same number of facts and the same statements; order and wording may differ; the old version gave vastly different outputs
- Parent: HLS FR-9, FR-10
- Priority: Must
- Verification method: Test
- Acceptance criterion: two repeats whose facts are the same in another order and with other wording: stable; two repeats with 3 and 4 facts: not stable; same count but one number different (1,200 against 1,020): not stable; same facts with an added "approximately": stable (exact)
- Plausibility: example – a fact is reduced to a triple (entity, number with unit, quote hash) by code; comparing sets of triples ignores order and wording by construction (plausible)
- Verified by: TC-STAB-001
- Status: Draft
- History: –

### REQ-STAB-002 – Report of the stability
- Level: Component   Subject: StabilityMetric
- Text: The stability metric shall report the share of stable cases, the Wilson 95 % interval and the identifiers of the unstable cases.
- Rationale: the owner must see which cases differ, not only a rate
- Parent: HLS FR-17
- Priority: Must
- Verification method: Test
- Acceptance criterion: for 10 cases with 3 repeats and 2 unstable cases: share 0.8, interval [0.49, 0.94] to two decimals, the 2 identifiers listed (exact)
- Plausibility: example – metrics.stability already returns a rate with an interval for the status; the interval for 8 of 10 is 0.49 to 0.94 by hand (plausible)
- Verified by: TC-STAB-002
- Status: Draft
- History: –

### REQ-STAB-003 – Stored sources
- Level: Component   Subject: LookupPipeline
- Text: While a lookup runs against the live web, the lookup pipeline shall store every fetched page by its hash so that the run is repeatable on the same pages.
- Rationale: the live web returns different pages from run to run; reproducibility is measured on the same pages (HLS AC-2(b), risk table)
- Parent: HLS FR-10
- Priority: Must
- Verification method: Test
- Acceptance criterion: after a run with the recorded web, every page of the run is in the content store under its hash, and the offline reproduction of the run gives the same events (exact)
- Plausibility: precedent – content_store.py and reproduce.py exist and are tested (CG14, CG15c); no new code expected (plausible)
- Verified by: TC-STAB-003
- Status: Draft
- History: –

### REQ-EVAL-001 – Run header with the pin
- Level: Component   Subject: Harness
- Text: When the harness saves a run, it shall record in the header the skill and pipeline versions, the pin name, the pin digest, the seed, the temperature, the number of repeats, and the SHA-1 of the file of each suite.
- Rationale: every result must name what it ran (conventions-agent 5, 6); today the header has no digest, seed or temperature
- Parent: HLS FR-17, FR-26
- Priority: Must
- Verification method: Test
- Acceptance criterion: a run with the fake server: the saved header contains the 8 fields with the values of the call (exact)
- Plausibility: precedent – the harness already writes a header with variant and pipeline; the model digest is available from the Ollama API tags answer (plausible)
- Verified by: TC-EVAL-001
- Status: Draft
- History: –

### REQ-EVAL-002 – Retired cases are skipped
- Level: Component   Subject: Harness
- Text: When a case carries the tag retired, the harness shall not run it and not count it, unless the option include-retired is given.
- Rationale: the 14 ambiguous cases of the audit are tagged retired; neither harness.py nor tools/eval.py skips them today (checked 2026-10-24); only the decision scripts do
- Parent: HLS FR-17
- Priority: Must
- Verification method: Test
- Acceptance criterion: a suite of 5 cases with 2 retired: the report counts 3 cases; with include-retired it counts 5 (exact)
- Plausibility: example – a filter on the tags where the harness loads the cases (plausible)
- Verified by: TC-EVAL-002
- Status: Draft
- History: –

### REQ-EVAL-003 – Seed and temperature reach the model
- Level: Component   Subject: Harness
- Text: When the harness runs a pipeline with a model pin, it shall pass the seed and the temperature of the pin to every model call of the run.
- Rationale: repeats measure instability only if the sampling is pinned (eval-statistics 8)
- Parent: HLS FR-17
- Priority: Must
- Verification method: Test
- Acceptance criterion: with the fake server, every request of a run contains the seed and the temperature of the pin (exact)
- Plausibility: spike – the model adapter passes llm_options (num_ctx) today; whether Ollama accepts options per request for seed and temperature through the adapter used by the pipelines is to be shown by a short spike at T-05 (doubtful)
- Verified by: TC-EVAL-003
- Status: Draft
- History: –

### REQ-EVAL-004 – Seeded sample of a suite
- Level: Component   Subject: Harness
- Text: When the harness is given the options sample N and seed S, it shall run a random sample of N active cases chosen with seed S, keeping the cases of a pair together.
- Rationale: the dev-subset baseline (T-06) uses 100 of 526 dev cases; the sample must be reproducible and must not split pairs
- Parent: HLS FR-17
- Priority: Should
- Verification method: Test
- Acceptance criterion: the same N and S give the same case list twice (exact); for 100 sampled cases of a suite with pairs, no pair is split (exact)
- Plausibility: example – a seeded sample over the pair tags is a few lines of code (plausible)
- Verified by: TC-EVAL-004
- Status: Draft
- History: –

### REQ-ARG-001 – Structured arguments
- Level: Component   Subject: ArgueStep
- Text: The argue step shall return a JSON object with the field points, an array of 1 to 4 strings of 3 to 400 characters each.
- Rationale: constrained output keeps the judge input small and the gate independent of free text (principle 4)
- Parent: HLS NFR-2
- Priority: Must
- Verification method: Test
- Acceptance criterion: the schema accepts 1, 2 and 4 points of 3 and of 400 characters and rejects 0 points, 5 points, a point of 2 characters and a point of 401 characters (exact)
- Plausibility: precedent – view.argue@1 has exactly this output schema (minItems 1, maxItems 4, minLength 3, maxLength 400) (plausible)
- Verified by: TC-ARG-001
- Status: Draft
- History: –

### IF-001 – Check result interface
- Level: Interface   Subject: NumberCheck
- Text: The number check shall return to the verification gate one record with the field status, one of pass, fail, inconclusive and not_applicable, and the field detail, a text of at most 200 characters.
- Rationale: the vocabulary of all hard checks (checks.py), so that the gate treats every check alike
- Parent: REQ-GATE-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: for the 4 acceptance claims of REQ-NUM-001, -002, -003 and -004 the record has the four statuses in turn and a detail of at most 200 characters (exact)
- Plausibility: precedent – every check in checks.py answers with these four statuses and a detail (plausible)
- Verified by: TC-IF-001
- Status: Draft
- History: –

### IF-002 – Ruling interface
- Level: Interface   Subject: JudgeStep
- Text: The judge step shall return one JSON object with the field verdict, one of supported, refuted and unclear, the field reason, a text of 3 to 600 characters, and optionally the field confidence, a number from 0 to 1.
- Rationale: the vocabulary of the tally in verification.py (VERDICTS); constrained decoding prevents format errors
- Parent: REQ-GATE-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: the schema accepts the 3 verdicts with a reason of 3 and of 600 characters and a confidence of 0 and of 1, and rejects the verdict maybe, a reason of 2 characters, a reason of 601 characters and a confidence of 1.1 (exact)
- Plausibility: precedent – view.judge@1 has exactly this output schema (plausible)
- Verified by: TC-IF-002
- Status: Draft
- History: –

### IF-003 – Result record interface
- Level: Interface   Subject: VerificationGate
- Text: The verification gate shall return to the harness for each claim one record with the fields verdict, status, calls, seconds and facts, where facts is a possibly empty list of triples of entity, number with unit and quote hash.
- Rationale: the harness records the cost of every run (metrics.cost) and the stability metric needs the facts (REQ-STAB-001); the verdict step has no facts, a lookup has
- Parent: REQ-EVAL-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: for a claim decided by the number check the record has calls 0 and facts empty; for a claim decided by the cops style it has calls 3; verdict and status agree by the table supported-pass, refuted-fail, unclear-inconclusive (exact)
- Plausibility: precedent – the harness records status, calls and seconds per case today (metrics.py); only the field facts is new (plausible)
- Verified by: TC-IF-003
- Status: Draft
- History: –

### IF-004 – Run records interface
- Level: Interface   Subject: Harness
- Text: The harness shall pass to the stability metric, for each case with at least two repeats, the list of its repeats, each with the fields status and facts.
- Rationale: the stability metric compares repeats of one case; it must not depend on the file format of the saved run
- Parent: REQ-STAB-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: for 4 cases with 3 repeats each the metric receives 4 lists of 3 entries; a case with 1 repeat is not passed (exact)
- Plausibility: precedent – metrics.stability already groups the records of a run by case (plausible)
- Verified by: TC-IF-004
- Status: Draft
- History: –

### IF-005 – Case input interface
- Level: Interface   Subject: Harness
- Text: The harness shall pass to the verification gate for each case the claim, the evidence, the seed of the pin and the temperature of the pin.
- Rationale: repeats measure instability only when the sampling is pinned; the gate must receive the sampling parameters from the run, not from a default (REQ-EVAL-003)
- Parent: REQ-EVAL-003
- Priority: Must
- Verification method: Test
- Acceptance criterion: with the fake gate, the harness hands over 4 fields for each of 3 cases, with the seed 7 and the temperature 0 of the pin (exact)
- Plausibility: example – the harness builds the input of a case today; two fields are added (plausible)
- Verified by: TC-IF-005
- Status: Draft
- History: –

### IF-006 – Single voice ruling interface
- Level: Interface   Subject: SingleVoiceStep
- Text: The single-voice step shall return one JSON object in the format of IF-002.
- Rationale: the gate tallies the ruling of the cops style and of the single voice alike
- Parent: REQ-GATE-004
- Priority: Must
- Verification method: Test
- Acceptance criterion: the schema of view.verdict@1 accepts and rejects the same examples as in IF-002 (exact)
- Plausibility: precedent – view.verdict@1 has the output schema {verdict, reason} (plausible)
- Verified by: TC-IF-006
- Status: Draft
- History: –

### NFR-BUD-001 – Time per claim
- Level: Component   Subject: VerificationGate
- Text: The verification gate shall decide a claim in a median of at most 10 seconds on the pin MP-light.
- Rationale: HLS NFR-7 and NFR-2; the cops style needed 6.2 s per claim in the baseline of 2026-10-19; a lookup checks several claims
- Parent: HLS NFR-2
- Priority: Should
- Verification method: Test
- Acceptance criterion: median of 100 claims of the dev sample on the reference host at most 10 s (BM-GATE-001)
- Plausibility: estimate, baseline – 6.2 s for cops plus a number check of well under 0.1 s; the new suites have longer evidence (VitaminC), which raises the input and may raise the time; measure at T-06 (plausible)
- Verified by: BM-GATE-001
- Status: Draft
- History: –

## Assumptions

### ASM-001 – Cost of the cops style
- Text: The cops style takes 6.2 s and about 3 model calls per claim on MP-light on the reference host; the single voice takes 1.3 s.
- Rationale: eval/baselines/verdicts-styles.md (2026-10-19, 50 claims, 3 repeats); checked again by BM-GATE-001
- Status: Draft

### ASM-002 – The single voice and near-miss numbers
- Text: The false-pass rate of the single voice on near-miss numbers is not known for the suites verdicts_vitaminc and verdicts_wikidata.
- Rationale: the 12 % of the old baseline rests on 3 distinct claims (9 of 75 runs); T-06 measures it on the new suites
- Status: Draft

### ASM-003 – Pins and server
- Text: MP-light is gemma4:12b-it-qat, digest sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3, Q4_0, 7.2 GB, resident on the 16 GB GPU; MP-full (gemma4:26b, 18.7 GB) does not fit the GPU and the gate does not use it; the server is Ollama in podman (ollama/ollama:rocm) with OLLAMA_MAX_LOADED_MODELS=1 and OLLAMA_NUM_PARALLEL=1.
- Rationale: ollama list and the Ollama tags answer of 2026-10-24; install_lama.py
- Status: Draft

### ASM-004 – Labels
- Text: The labels of both suites come from open sources: VitaminC annotators and Wikipedia revisions, Wikidata values and rule-made false twins; the audit of 166 rows by the owner agreed on 92 % (Cohen's kappa 0.85) and the 14 differing cases are tagged ambiguous and retired.
- Rationale: tools/label_agreement.py on 2026-10-24; checked again by a second audit sample in validation
- Status: Draft

### ASM-005 – Planned holdout sizes
- Text: The active holdout has 62 wrong, 85 true and 21 no-verdict claims in verdicts_vitaminc.holdout and 58 wrong and 58 true claims in verdicts_wikidata.holdout; the dev splits have 129 and 91 wrong, 169 and 91 true and 34 no-verdict claims.
- Rationale: counts of the active cases (retired ones excluded) on 2026-10-24; the error rates of the criteria use them
- Status: Draft

### ASM-006 – Training data
- Text: Wikipedia and Wikidata are part of the training data of the models.
- Rationale: results on the Wikidata claims, which have no evidence, may measure memory; compare them with the results on the VitaminC claims, which have evidence
- Status: Draft

## Traceability

| Requirement | Level | Parent | Subject (part) | Verified by |
|---|---|---|---|---|
| REQ-GATE-001 | Component | FR-9 | VerificationGate | TC-GATE-001 |
| REQ-GATE-002 | Component | FR-9 | VerificationGate | TC-GATE-002 |
| REQ-GATE-003 | Component | FR-9 | VerificationGate | TC-GATE-003 |
| REQ-GATE-004 | Component | FR-9 | VerificationGate | TC-GATE-004 |
| REQ-GATE-005 | Component | NFR-2 | VerificationGate | TC-GATE-005 |
| REQ-NUM-001 | Component | FR-9 | NumberCheck | TC-NUM-001 |
| REQ-NUM-002 | Component | FR-9 | NumberCheck | TC-NUM-002 |
| REQ-NUM-003 | Component | FR-9 | NumberCheck | TC-NUM-003 |
| REQ-NUM-004 | Component | FR-9 | NumberCheck | TC-NUM-004 |
| REQ-VER-001 | System | FR-9 | VerificationGate | EV-verdicts_vitaminc |
| REQ-VER-002 | System | FR-9 | VerificationGate | EV-verdicts_wikidata |
| REQ-VER-003 | System | FR-9 | VerificationGate | EV-verdicts_vitaminc |
| REQ-VER-004 | System | FR-9 | VerificationGate | EV-verdicts_wikidata |
| REQ-VER-005 | System | FR-9 | VerificationGate | EV-verdicts_vitaminc |
| REQ-VER-006 | System | FR-9 | VerificationGate | EV-verdicts_wikidata |
| REQ-VER-007 | System | NFR-3 | VerificationGate | EV-verdicts_injection |
| REQ-STAB-001 | Component | FR-9, FR-10 | StabilityMetric | TC-STAB-001 |
| REQ-STAB-002 | Component | FR-17 | StabilityMetric | TC-STAB-002 |
| REQ-STAB-003 | Component | FR-10 | LookupPipeline | TC-STAB-003 |
| REQ-EVAL-001 | Component | FR-17, FR-26 | Harness | TC-EVAL-001 |
| REQ-EVAL-002 | Component | FR-17 | Harness | TC-EVAL-002 |
| REQ-EVAL-003 | Component | FR-17 | Harness | TC-EVAL-003 |
| REQ-EVAL-004 | Component | FR-17 | Harness | TC-EVAL-004 |
| REQ-ARG-001 | Component | NFR-2 | ArgueStep | TC-ARG-001 |
| IF-001 | Interface | REQ-GATE-001 | NumberCheck | TC-IF-001 |
| IF-002 | Interface | REQ-GATE-003 | JudgeStep | TC-IF-002 |
| IF-003 | Interface | REQ-EVAL-001 | VerificationGate | TC-IF-003 |
| IF-004 | Interface | REQ-STAB-001 | Harness | TC-IF-004 |
| IF-005 | Interface | REQ-EVAL-003 | Harness | TC-IF-005 |
| IF-006 | Interface | REQ-GATE-004 | SingleVoiceStep | TC-IF-006 |
| NFR-BUD-001 | Component | NFR-2 | VerificationGate | BM-GATE-001 |
