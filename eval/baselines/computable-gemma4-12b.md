# Baselines of the suite `computable` (the pipeline `verify.computable`, a model writes a check script, the sandbox runs it)

Model: gemma4:12b-it-qat (the light profile), one run per case, 39 cases (19 true claims, 20 false). Run on 2026-10-18 with `python tools/eval.py run computable --variant <name>`.
Reproduce a variant with `--pipeline verify.computable@1` (baseline) or `@2`. The model is not deterministic: a repeat (`--repeats 3`) would show how stable these numbers are.

## What changed between the two runs

Version 1 gave the model a hand-written description of the data ("numbers (a list), claimed"). In the statistics cases the model then wrote `data["data"]` for `{"numbers": [...], "claimed": ...}`
and failed with a `KeyError` that did not say which keys exist, so even the repair could not fix it (8 of the 9 abstentions, `statistics` right in 2 of 10 cases).
Version 2 generates the shape of `data` from the real data (`code.describe_data`) and a `KeyError` names the keys that exist.

## Result

* coverage (claims decided at all): 79 % -> 95 %
* right overall: 77 % -> 92 %
* false pass (a wrong claim that passed): 0 of 20 in both runs (the 95 % interval still allows up to 16 %)
* false fail: 1 of 19 in both runs (bmi: the claim 22.9 for 22.857... is a rounded value and the script of this run demanded equality)
* cost per case: 12.7 s -> 8.4 s, model calls 77 -> 53 (fewer repairs)
* the paired difference is not significant with 39 cases (8 cases got better, 2 got worse, exact sign test p = 0.11): more cases or repeats are needed before it counts as proven

## Reports

### baseline-light (verify.computable@1)

```
running computable (39 cases x 1) as variant 'baseline-light' ...


suite computable, variant baseline-light: 39 cases x 1 run(s)  [pipeline verify.computable]
run on 2026-10-18 21:37 UTC, no changes to the defaults

behaves as expected:    76.9%  (95% interval 62 to 87%, 30 of 39)
   MISMATCH mean-right             got inconclusive   expected pass           
   MISMATCH mean-wrong             got inconclusive   expected fail           
   MISMATCH median-odd-right       got inconclusive   expected pass           
   MISMATCH median-odd-wrong       got inconclusive   expected fail           
   MISMATCH median-even-wrong      got inconclusive   expected fail           
   MISMATCH population-sd-right    got inconclusive   expected pass           
   MISMATCH population-sd-wrong    got inconclusive   expected fail           
   MISMATCH weighted-percentage-wrong got inconclusive   expected fail           
   ... and 1 more

as a verifier, on 39 claims (19 true, 20 false):
   decided (coverage)    79.5%  (95% interval 64 to 89%, 31 of 39)
   right among decided   96.8%  (95% interval 84 to 99%, 30 of 31)
   right overall         76.9%  (95% interval 62 to 87%, 30 of 39)
   FALSE PASS             0.0%  (95% interval 0 to 16%, 0 of 20)   <- a wrong claim that passed
   false fail             5.3%  (95% interval 1 to 25%, 1 of 19)
   precision of pass    100.0%  (95% interval 80 to 100%, 15 of 15)
   precision of fail     93.8%  (95% interval 72 to 99%, 15 of 16)
   errors                 0.0%  (95% interval 0 to 9%, 0 of 39)
   confusion: pass/true 15  pass/false 0  fail/false 15  fail/true 1  abstained true 3  abstained false 5
   WRONG mean-right               said inconclusive   truth True
   WRONG mean-wrong               said inconclusive   truth False
   WRONG median-odd-right         said inconclusive   truth True
   WRONG median-odd-wrong         said inconclusive   truth False
   WRONG median-even-wrong        said inconclusive   truth False
   WRONG population-sd-right      said inconclusive   truth True
   WRONG population-sd-wrong      said inconclusive   truth False
   WRONG weighted-percentage-wrong said inconclusive   truth False

by tag (right / cases):
   calendar               100.0%  (95% interval 51 to 100%, 4 of 4)
   everyday                75.0%  (95% interval 30 to 95%, 3 of 4)
   finance                100.0%  (95% interval 74 to 100%, 11 of 11)
   math                   100.0%  (95% interval 68 to 100%, 8 of 8)
   numeric                 76.9%  (95% interval 62 to 87%, 30 of 39)
   statistics              20.0%  (95% interval 6 to 51%, 2 of 10)
   text                   100.0%  (95% interval 34 to 100%, 2 of 2)
   trap                    80.0%  (95% interval 49 to 94%, 8 of 10)

cost: 494.0 s in total, 12.67 s per run, 77 model calls, 139677 characters sent, 75573 received
```

### shape-light (verify.computable@2)

```
running computable (39 cases x 1) as variant 'shape-light' ...


suite computable, variant shape-light: 39 cases x 1 run(s)  [pipeline verify.computable]
run on 2026-10-18 21:47 UTC, no changes to the defaults

behaves as expected:    92.3%  (95% interval 80 to 97%, 36 of 39)
   MISMATCH sales-tax-wrong        got inconclusive   expected fail           
   MISMATCH median-even-right      got inconclusive   expected pass           
   MISMATCH bmi-right              got fail           expected pass           

as a verifier, on 39 claims (19 true, 20 false):
   decided (coverage)    94.9%  (95% interval 83 to 99%, 37 of 39)
   right among decided   97.3%  (95% interval 86 to 100%, 36 of 37)
   right overall         92.3%  (95% interval 80 to 97%, 36 of 39)
   FALSE PASS             0.0%  (95% interval 0 to 16%, 0 of 20)   <- a wrong claim that passed
   false fail             5.3%  (95% interval 1 to 25%, 1 of 19)
   precision of pass    100.0%  (95% interval 82 to 100%, 17 of 17)
   precision of fail     95.0%  (95% interval 76 to 99%, 19 of 20)
   errors                 0.0%  (95% interval 0 to 9%, 0 of 39)
   confusion: pass/true 17  pass/false 0  fail/false 19  fail/true 1  abstained true 1  abstained false 1
   WRONG sales-tax-wrong          said inconclusive   truth False
   WRONG median-even-right        said inconclusive   truth True
   WRONG bmi-right                said fail           truth True

by tag (right / cases):
   calendar               100.0%  (95% interval 51 to 100%, 4 of 4)
   everyday                75.0%  (95% interval 30 to 95%, 3 of 4)
   finance                 90.9%  (95% interval 62 to 98%, 10 of 11)
   math                   100.0%  (95% interval 68 to 100%, 8 of 8)
   numeric                 92.3%  (95% interval 80 to 97%, 36 of 39)
   statistics              90.0%  (95% interval 60 to 98%, 9 of 10)
   text                   100.0%  (95% interval 34 to 100%, 2 of 2)
   trap                   100.0%  (95% interval 65 to 100%, 7 of 7)

cost: 328.4 s in total, 8.42 s per run, 53 model calls, 91735 characters sent, 51296 received
```

### Paired comparison

```
A = computable/baseline-light    B = computable/shape-light
on the 39 cases both ran (a case with repeats counts as the share of right runs):
   A right on 30.0, B right on 36.0
   only A right: 2   only B right: 8   exact sign test p = 0.109 (not distinguishable from chance with these cases)
   only A: median-even-right, sales-tax-wrong
   only B: mean-right, mean-wrong, median-even-wrong, median-odd-right, median-odd-wrong, population-sd-right, population-sd-wrong, weighted-percentage-wrong
   A: false pass 0 of 20, coverage 79%, 12.7 s per run, 77 calls
   B: false pass 0 of 20, coverage 95%, 8.4 s per run, 53 calls
```


---

# Correction after three repeats per case (added the next day)

The first comparison above had one run per case and **overstated the gain**: the single run of version 1 was a bad draw (77 % right), while over 117 runs (39 cases x 3) it is 89.7 % right.
The model is not deterministic: only 79.5 % (v1) and 84.6 % (v2) of the cases get the same status in all three runs. Conclusions from one run per case should not be trusted.

| 117 runs each (39 cases x 3) | v1 (`verify.computable@1`) | v2 (`verify.computable@2`) |
|---|---|---|
| decided (coverage) | 90.6 % | 97.4 % |
| right overall | 89.7 % | 94.9 % |
| false pass (wrong claim passed) | 0 of 60 (interval up to 6 %) | 0 of 60 (interval up to 6 %) |
| false fail (right claim refuted) | 1 of 57 | 3 of 57 |
| same status in all 3 runs | 79.5 % | 84.6 % |
| seconds per run / model calls | 11.3 / 209 | 8.7 / 160 |
| statistics cases right | 73.3 % | 93.3 % |
| paired difference per case | only v1 right in 3 cases, only v2 right in 6: exact sign test p = 0.51 | |

What holds: v2 decides more claims, is cheaper (23 % less time, 23 % fewer calls) and fixes the statistics cases; no wrong claim passed in either version in 60 + 60 tries.
What does not hold: a large jump in correctness, or a proven difference. A new weakness showed up: v2 refutes right claims that are **rounded** (`compound-interest-right`, `sales-tax-right`, `bmi-right`: the claim
says 54.0, the exact value is 53.9892, the script demands equality). The writer of the script does not know the precision of the claimed number. Candidate for the next version: tell the script the precision of the claim
(for example the claimed number as written) and the rule to round its own result to the same number of decimals before comparing.

## Reports of the repeat runs

### v1-r3

```
running computable (39 cases x 3) as variant 'v1-r3' ...


suite computable, variant v1-r3: 39 cases x 3 run(s)  [pipeline verify.computable@1]
run on 2026-10-18 22:14 UTC, pipeline=verify.computable@1

behaves as expected:    89.7%  (95% interval 83 to 94%, 105 of 117)
   MISMATCH mean-right             got inconclusive   expected pass           
   MISMATCH mean-wrong             got inconclusive   expected fail           
   MISMATCH median-odd-wrong       got inconclusive   expected fail           
   MISMATCH population-sd-wrong    got inconclusive   expected fail           
   MISMATCH vowels-right           got inconclusive   expected pass           
   MISMATCH population-sd-wrong    got inconclusive   expected fail           
   MISMATCH bmi-right              got fail           expected pass           
   MISMATCH sum-to-100-right       got inconclusive   expected pass           
   ... and 4 more

as a verifier, on 117 claims (57 true, 60 false):
   decided (coverage)    90.6%  (95% interval 84 to 95%, 106 of 117)
   right among decided   99.1%  (95% interval 95 to 100%, 105 of 106)
   right overall         89.7%  (95% interval 83 to 94%, 105 of 117)
   FALSE PASS             0.0%  (95% interval 0 to 6%, 0 of 60)   <- a wrong claim that passed
   false fail             1.8%  (95% interval 0 to 9%, 1 of 57)
   precision of pass    100.0%  (95% interval 93 to 100%, 50 of 50)
   precision of fail     98.2%  (95% interval 91 to 100%, 55 of 56)
   errors                 0.0%  (95% interval 0 to 3%, 0 of 117)
   confusion: pass/true 50  pass/false 0  fail/false 55  fail/true 1  abstained true 6  abstained false 5
   WRONG mean-right               said inconclusive   truth True
   WRONG mean-wrong               said inconclusive   truth False
   WRONG median-odd-wrong         said inconclusive   truth False
   WRONG population-sd-wrong      said inconclusive   truth False
   WRONG vowels-right             said inconclusive   truth True
   WRONG population-sd-wrong      said inconclusive   truth False
   WRONG bmi-right                said fail           truth True
   WRONG sum-to-100-right         said inconclusive   truth True

by tag (right / cases):
   calendar               100.0%  (95% interval 76 to 100%, 12 of 12)
   everyday                91.7%  (95% interval 65 to 99%, 11 of 12)
   finance                100.0%  (95% interval 90 to 100%, 33 of 33)
   math                    95.8%  (95% interval 80 to 99%, 23 of 24)
   numeric                 89.7%  (95% interval 83 to 94%, 105 of 117)
   statistics              73.3%  (95% interval 56 to 86%, 22 of 30)
   text                    66.7%  (95% interval 30 to 90%, 4 of 6)
   trap                   100.0%  (95% interval 85 to 100%, 21 of 21)

stability over repeats (same status every time):  79.5%  (95% interval 64 to 89%, 31 of 39)

cost: 1320.8 s in total, 11.29 s per run, 209 model calls, 374233 characters sent, 204502 received
```

### v2-r3

```
running computable (39 cases x 3) as variant 'v2-r3' ...


suite computable, variant v2-r3: 39 cases x 3 run(s)  [pipeline verify.computable]
run on 2026-10-18 21:57 UTC, no changes to the defaults

behaves as expected:    94.9%  (95% interval 89 to 98%, 111 of 117)
   MISMATCH compound-interest-right got fail           expected pass           
   MISMATCH median-odd-wrong       got inconclusive   expected fail           
   MISMATCH bmi-right              got fail           expected pass           
   MISMATCH days-between-right     got inconclusive   expected pass           
   MISMATCH sales-tax-right        got fail           expected pass           
   MISMATCH median-odd-right       got inconclusive   expected pass           

as a verifier, on 117 claims (57 true, 60 false):
   decided (coverage)    97.4%  (95% interval 93 to 99%, 114 of 117)
   right among decided   97.4%  (95% interval 93 to 99%, 111 of 114)
   right overall         94.9%  (95% interval 89 to 98%, 111 of 117)
   FALSE PASS             0.0%  (95% interval 0 to 6%, 0 of 60)   <- a wrong claim that passed
   false fail             5.3%  (95% interval 2 to 14%, 3 of 57)
   precision of pass    100.0%  (95% interval 93 to 100%, 52 of 52)
   precision of fail     95.2%  (95% interval 87 to 98%, 59 of 62)
   errors                 0.0%  (95% interval 0 to 3%, 0 of 117)
   confusion: pass/true 52  pass/false 0  fail/false 59  fail/true 3  abstained true 2  abstained false 1
   WRONG compound-interest-right  said fail           truth True
   WRONG median-odd-wrong         said inconclusive   truth False
   WRONG bmi-right                said fail           truth True
   WRONG days-between-right       said inconclusive   truth True
   WRONG sales-tax-right          said fail           truth True
   WRONG median-odd-right         said inconclusive   truth True

by tag (right / cases):
   calendar                91.7%  (95% interval 65 to 99%, 11 of 12)
   everyday                91.7%  (95% interval 65 to 99%, 11 of 12)
   finance                 93.9%  (95% interval 80 to 98%, 31 of 33)
   math                   100.0%  (95% interval 86 to 100%, 24 of 24)
   numeric                 94.9%  (95% interval 89 to 98%, 111 of 117)
   statistics              93.3%  (95% interval 79 to 98%, 28 of 30)
   text                   100.0%  (95% interval 61 to 100%, 6 of 6)
   trap                   100.0%  (95% interval 85 to 100%, 21 of 21)

stability over repeats (same status every time):  84.6%  (95% interval 70 to 93%, 33 of 39)

cost: 1013.1 s in total, 8.66 s per run, 160 model calls, 281264 characters sent, 159753 received
```

### Paired comparison

```
A = computable/v1-r3    B = computable/v2-r3
on the 39 cases both ran (a case with repeats counts as the share of right runs):
   A right on 35.0, B right on 37.0
   only A right: 3   only B right: 6   exact sign test p = 0.508 (not distinguishable from chance with these cases)
   only A: compound-interest-right, days-between-right, sales-tax-right
   only B: mean-right, mean-wrong, population-sd-right, population-sd-wrong, sum-to-100-right, vowels-right
   A: false pass 0 of 60, coverage 91%, 11.3 s per run, 209 calls
   B: false pass 0 of 60, coverage 97%, 8.7 s per run, 160 calls
```
