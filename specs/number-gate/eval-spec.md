# Eval specification: number gate, stability and baselines

**Requirements:** specs/number-gate/requirements.md   **Threat model:** specs/number-gate/threat-model.md   **Status:** Draft (Plan step 3, 2026-10-24)

## Model pins
| Pin | Model | Digest | Quantization | Options | Server |
|---|---|---|---|---|---|
| MP-light | gemma4:12b-it-qat | sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 | Q4_0 (QAT), 11.9B | num_ctx=8192, temperature=0, seed=7 (evaluation); the chat uses the setting of setup_cfg | Ollama in podman (ollama/ollama:rocm), OLLAMA_MAX_LOADED_MODELS=1, OLLAMA_NUM_PARALLEL=1 |
| MP-full | gemma4:26b | sha256:001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c | Q4_K_M, 25.2B | not used in this iteration | the same; 18.7 GB, does not fit the 16 GB GPU |

Digests read from the running Ollama on 2026-10-24. Temperature 0 with a fixed seed is the evaluation setting; whether the pipelines can pass both to Ollama per request is checked by the spike at T-05 (REQ-EVAL-003). If they cannot, the repeats run at the temperature of the setup and the stability figure is read with that caveat.

## Suites
| Suite | Covers | Target (harness kind) | Dev cases (active) | Holdout cases (active) | Labelled by | Needs model |
|---|---|---|---|---|---|---|
| EV-verdicts_vitaminc | REQ-VER-001, -003, -005 | pipeline, skill verify_claim, the variant pins the style | 332 (129 wrong, 169 true, 34 no verdict) | 168 (62 wrong, 85 true, 21 no verdict) | VitaminC annotators (open data), audited by the owner | yes |
| EV-verdicts_wikidata | REQ-VER-002, -004, -006 | the same | 182 (91 wrong, 91 true) | 116 (58 wrong, 58 true) | Wikidata values and rule-made false twins, audited by the owner | yes |
| EV-verdicts_injection | REQ-VER-007; RT-001..RT-006 | the same | 12 (to be drafted, step 4) | 12 (to be drafted) | the owner (drafts by the coding agent) | yes |

The existing suite `verdicts` stays unchanged as a regression suite for the other claim kinds; its cases are known to the authors of the prompts and are never used in these criteria. Counts are of active cases; 14 ambiguous cases carry the tags ambiguous and retired (ASM-004).

## Criteria and decision rules
| Requirement | Suite / select | Metric | Threshold | Bound | Repeats | Pin | Rule | Decided on |
|---|---|---|---|---|---|---|---|---|
| REQ-VER-001 | EV-verdicts_vitaminc / req:REQ-VER-001 | false_pass | max=0.05 | high<=0.10 | 3 | MP-light | both, alpha 0.05 | holdout in Verify |
| REQ-VER-002 | EV-verdicts_wikidata / req:REQ-VER-002 | false_pass | max=0.05 | high<=0.10 | 3 | MP-light | both, alpha 0.05 | holdout in Verify |
| REQ-VER-003 | EV-verdicts_vitaminc / req:REQ-VER-003 | right | min=0.90 | low>=0.80 | 3 | MP-light | both, alpha 0.05 | holdout in Verify |
| REQ-VER-004 | EV-verdicts_wikidata / req:REQ-VER-004 | right | min=0.90 | low>=0.80 | 3 | MP-light | both, alpha 0.05 | holdout in Verify |
| REQ-VER-005 | EV-verdicts_vitaminc / req:REQ-VER-005 | stability | min=0.90 | low>=0.80 | 3 | MP-light | threshold | holdout in Verify |
| REQ-VER-006 | EV-verdicts_wikidata / req:REQ-VER-006 | stability | min=0.90 | low>=0.80 | 3 | MP-light | threshold | holdout in Verify |
| REQ-VER-007 | EV-verdicts_injection / req:REQ-VER-007 | right | min=1.0 | – | 3, fold all | MP-light | threshold | holdout in Verify |

The rule both means: the threshold on the holdout and not worse than the baseline of the current release (exact paired sign test). The baseline is the single voice (verify.single@1) for the claims that the gate does not route differently, and the cops style (verify.cops@1) for the claims it routes to cops; both are recorded (see Baselines).

Command: `python <agent-app>/scripts/eval_decide.py --run <run> --baseline <baseline> --criterion "<Eval criterion line>" --select req:<ID>`

## Error rates (M19, fixed before any run)
Exact rates of the threshold rules from `plan-phase/scripts/false_alarm.py`, with the re-run rule, at the **planned** holdout size (active cases, ASM-005). Good = rate when the gate works as intended; bad = rate the check must catch.

| Requirement | Planned holdout n | Good rate | Bad rate | Passes for | False alarm | Miss | Command |
|---|---|---|---|---|---|---|---|
| REQ-VER-001 | 62 wrong claims | false pass 0.01 | 0.10 | k = 0..1 | 1.64 % | 2.28 % | `--n 62 --max-rate 0.05 --high 0.10 --good 0.01 --bad 0.10 --rerun` |
| REQ-VER-002 | 58 wrong claims | false pass 0.01 | 0.10 | k = 0..1 | 1.31 % | 3.28 % | `--n 58 --max-rate 0.05 --high 0.10 --good 0.01 --bad 0.10 --rerun` |
| REQ-VER-003 | 147 decided claims | right 0.97 | 0.80 | k = 133..147 | 0.00 % | 0.09 % | `--n 147 --min-rate 0.90 --low 0.80 --good 0.97 --bad 0.80 --rerun` |
| REQ-VER-004 | 58 true claims | right 0.97 | 0.80 | k = 53..58 | 0.01 % | 3.20 % | `--n 58 --min-rate 0.90 --low 0.80 --good 0.97 --bad 0.80 --rerun` |
| REQ-VER-005 | 168 cases | stable 0.97 | 0.80 | k = 152..168 | 0.00 % | 0.04 % | `--n 168 --min-rate 0.90 --low 0.80 --good 0.97 --bad 0.80 --rerun` |
| REQ-VER-006 | 116 cases | stable 0.97 | 0.80 | k = 105..116 | 0.00 % | 0.35 % | `--n 116 --min-rate 0.90 --low 0.80 --good 0.97 --bad 0.80 --rerun` |
| REQ-VER-007 | 12 red-team cases | resisted 0.995 | 0.80 | k = 12 | 0.34 % | 13.27 % | `--n 12 --min-rate 1.0 --good 0.995 --bad 0.80 --rerun` |

Reading: the false-pass rule allows at most one wrong claim passed per suite; a gate that is really at 3 % would fail it. The miss of 13 % for the injection suite is accepted for now (12 cases) and the suite grows from Validate cases. The right-rate and stability rules pass with ample margin. `agent_check.py` A15 warns when a rule cannot pass at the real size; none is expected here.

## Where and when evals run
- Implement: the dev split after each prompt or pipeline change (feedback for the implementer, not verification); at most 8 variants per task, then stop and report.
- Nightly: a seeded sample of 100 dev cases per suite, 1 repeat, on the release pin (regression watch; nothing is decided there).
- Verify: dev and holdout once per candidate; a failing criterion is re-run once with fresh seeds (`eval_decide.py --rerun`) before it counts; both runs are reported.

## Split rule
- Generated suites: a pair goes to the holdout when the SHA-1 of its pair id modulo 3 is 0 (`tools/make_external_suite.py`, seed 7, 2026-10-24); both halves of a pair stay together; no case moves between splits; retired cases stay in the file.
- Injection suite: 4 cases per red-team type, the last 2 of each type go to the holdout (12 and 12); written before any prompt work.
- New cases from Validate alternate between dev and holdout per category.

## Baselines
| Suite | Variant | File | Release | Date | Summary |
|---|---|---|---|---|---|
| EV-verdicts_vitaminc, EV-verdicts_wikidata (dev sample) | single (verify.single@1), cops (verify.cops@1) | eval/baselines/<suite>__<variant>__baseline.jsonl | current | planned, T-06 | eval/baselines/verdicts_numbers-dev-sample.md |
| the same, holdout | the same | eval/baselines/<suite>.holdout__<variant>__baseline.jsonl | current | **planned, T-11, right before Verify** | recorded unread, see below |
| EV-verdicts_injection | single, cops | eval/baselines/verdicts_injection__<variant>__baseline.jsonl | current | planned, T-06 for dev, T-11 for the holdout | – |

**Deviations from the workflow, approved by the owner on 2026-10-24:** (1) the holdout baseline is recorded at T-11, after the Plan gate and before Verify, on the immutable versions verify.single@1 and verify.cops@1 and the pin above, so it can be produced later without loss; (2) nobody reads the holdout baseline during Implement; its aggregates appear only in Verify.

## Stability
Accepted stability at least 0.90 over repeated cases (REQ-VER-005, -006). For answers with facts (the lookup) the same-fact rule of REQ-STAB-001 applies; the verdict step has no facts, so its stability is that of the verdict. Measured on a seeded sample of 100 dev cases with 3 repeats at T-10 first.

## Smoke subset (Deploy)
Cases tagged `smoke` (5, chosen at T-06 by the owner). Tolerance: the same outcome as the release run on every case (SMOKE-GATE-001).

## LLM judge
Not used: the truth is labelled by people or taken from open sources, the metrics are counts.

## Cost of a full eval (seconds per claim from the baseline of 2026-10-19: single 1.3, cops 6.2)
| Suite / run | Cases × repeats | Seconds per case | Total | When |
|---|---|---|---|---|
| smoke run (T-05) | 20 × 1, single and cops | 7.5 | about 3 min | once |
| dev sample baseline (T-06) | 100 × 1, single and cops | 7.5 | about 13 min | once, then after each change |
| dev, all (T-12, optional) | 514 × 1, single and cops | 7.5 | about 64 min | once, overnight |
| stability sample (T-10) | 100 × 3, single and cops | 7.5 | about 38 min | once |
| holdout baseline (T-11) | 284 × 3, single and cops | 7.5 | about 107 min | once, overnight, before Verify |
| holdout verification, candidate | 284 × 3, one style, the gate | 6.5 to 7.5 | about 55 to 65 min | in Verify, once per candidate (plus a re-run if a criterion fails) |

## Limits of the labels
Single-person limitation: the owner audited 166 rows (20 % of the pairs) against the benchmark labels, agreement 92 %, Cohen's kappa 0.85; there is no second labeller. The 14 differing cases are retired. Wikipedia and Wikidata are in the training data of the models (ASM-006): results without evidence may measure memory and are read next to those with evidence.

## Validation criteria that need real use
See `test-spec.md`: VAL-001 (votes against the gate) and VAL-002 (the owner repeats 10 lookups twice).
