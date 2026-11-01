# A-40: retire the eval case n-planted-figure (D-132)

- Change: `eval/suites/hard_checks/cases.jsonl`, case `n-planted-figure`: tag `retired` added, note extended. Nothing else in the suite changes; the id stays (ids are never reused).
- Why: in `hard_checks` the claim type `numeric` goes to the arithmetic check (`expression`, `value`); no claim type of the suite reaches `checks.number_check(claim, evidence)`, so the case returned `not_applicable` and never tested the planted figure (finding 1 of the N-2.4.2 verification). It also turned `tests/test_harness.py::test_the_hard_checks_suite_matches_every_time` red.
- What replaces it (not in this amendment, built with the rule for conflicting values): a unit test of `checks.number_check` and a case of the IF-402 contract suite, expected outcome `fail` (owner, D-132). Open before that is built: with the rule `open` the planted figure would be inconclusive, not `fail` (D-132); a rule that drops the sentences flagged by `web_tools.injection_signals` before comparing would give `fail`.
- Effect: `test_harness` fails only in `test_every_shipped_suite_is_valid` (the suite `rt_edit` has 2 cases, the test wants 30), as on master.
