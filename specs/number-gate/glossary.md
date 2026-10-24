# Glossary: number gate, stability and baselines

Used by the requirements linter (L1) and as context for the assessor (L3). "Avoid" lists synonyms that must not be used in requirements.

| Term | Definition | Model element | Unit | Avoid |
|---|---|---|---|---|
| verification gate | code that routes a claim through the hard checks and one judgement style and returns the verdict | VerificationGate | – | verifier, checker |
| number check | deterministic comparison of the number in a claim with the values for the same quantity in the evidence | NumberCheck | – | number verifier |
| judgement style | a pipeline that lets models judge a claim: single voice, consistency, jury, cops, trial | – | – | method, mode |
| cops style | judgement style: argue for, argue against, judge (pipeline verify.cops) | – | – | good cop bad cop |
| single voice | judgement style with one model call (pipeline verify.single) | – | – | baseline model |
| argue step, judge step | model steps of the cops style (views view.argue, view.judge) | ArgueStep, JudgeStep | – | the model, the AI |
| claim | one statement to verify; a fact is a statement inside a result, see below | Claim | – | assertion |
| number claim | a claim that contains at least one number | – | – | numeric fact |
| wrong claim | a claim whose label in the suite is false | – | – | negative |
| true claim | a claim whose label in the suite is true | – | – | positive |
| no-verdict claim | a claim for which the right answer is no verdict (truth null, expect inconclusive) | – | – | unanswerable |
| near-miss number | a number that is a few percent, a swapped digit, a unit of ten or a few years away from the true value | – | – | typo number |
| evidence | source passages given with a claim; untrusted text | Evidence | characters | sources, context |
| verdict | supported, refuted or unclear | Verdict | – | answer |
| false pass | a wrong claim that receives the verdict supported | – | % of the wrong claims | false positive |
| right rate | share of decided claims that receive the verdict that the label demands | – | % | accuracy |
| fact | one statement in a result, reduced to a triple of entity, number with unit and quote hash | – | – | finding |
| same fact | two facts whose normalised entity, number with unit and quote hash agree; order and wording are ignored | – | – | similar fact |
| stable case | a case whose repeats all return the same verdict and the same set of facts | – | – | consistent case |
| stability | share of the stable cases among the cases with at least two repeats | StabilityMetric | % | reliability |
| repeat | one more run of the same case with the same pin, seed, temperature and sources | – | – | retry |
| suite | collection of labelled cases in eval/suites/<name>/ (EV-<name>) | – | – | test set, benchmark |
| holdout | the part of a suite that is decided only in Verify (folder <name>.holdout) | – | – | test split |
| dev split | the part of a suite that the implementer may run at any time | – | – | training set |
| retired case | a case tagged retired: not run, not counted; the 14 ambiguous cases carry it | – | – | deleted case |
| ambiguous case | a case where the owner's label differs from the benchmark label in the audit | – | – | wrong label |
| audit sample | the 20 % of the pairs that the owner labelled blind and compared with the benchmark labels | – | – | validation set |
| model pin | model name, digest, quantisation and options (MP-...) | – | – | model version |
| harness | the program that runs suites against a target and records the runs (harness.py, tools/eval.py) | Harness | – | test runner |
| run header | the first line of a saved run with versions, pin, seed, temperature and suite hashes | – | – | metadata |
