# verdicts: verify.single@1 (one voice), first and only run so far

Run on 2026-10-19, light profile (gemma4:12b-it-qat), 50 claims, 1 run, 68 s (1.4 s per claim). The other four styles (consistency, jury, cops, trial) are built and tested with scripted replies, but were **not measured yet**: the run was stopped on purpose.

| | verify.single@1 |
|---|---|
| right overall | 93.5 % (43 of 46 claims with a known truth, interval 82 to 98 %) |
| false pass (a wrong claim passed) | 12.0 % (3 of 25) |
| false fail | 0 of 21 |
| claims nobody can decide: answered "no verdict" | 4 of 4 |
| evidence cases | 6 of 6 |
| the evidence that gives orders | resisted (1 of 1) |
| popular myths | 10 of 10 |
| true statements that sound wrong | 5 of 5 |
| well known facts | 15 of 15 |
| numbers | 6 of 9 |

The three false passes are the near-miss numbers: Eiffel Tower "about 430 metres", Moon "about 38,400 km", Earth to Sun "about 15 million km". A single voice agrees with a number that sounds about right. This is where the other styles
(and the hard checks, for numbers with data) have to show their worth. The popular myths, which are the classic trap for a small model, were all caught, so the suite may be too easy for the myths: more near-miss numbers, dates and
names would sharpen it.

To continue: for each style `python tools/eval.py run verdicts --variant <style> --pipeline verify.<style>@1`, then `python tools/eval.py compare verdicts single <style>`. About 40 minutes with MIA idle; use `--repeats 3` for a result that can be believed.
