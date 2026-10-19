# verdicts: the five verification styles, 3 repeats each (supersedes verdicts-single.md)

Run on 2026-10-19, light profile (gemma4:12b-it-qat), 50 claims with known truth (21 true, 25 false, 4 undecidable), 3 repeats per style, pipelines pinned with `--pipeline verify.<style>@1`.
Sample: 138 runs with a known truth (46 claims x 3), 75 of them on wrong claims, 63 on true claims, 12 on undecidable claims.

| style | right overall | false pass (wrong claim passed) | false fail | abstained on a true claim | near-miss numbers | seconds per claim | model calls |
|---|---|---|---|---|---|---|---|
| single | 93.5 % | 12.0 % (9 of 75) | 0 of 63 | 0 | 18 of 27 | 1.3 | 150 |
| consistency (3 samples) | 93.5 % | 12.0 % (9 of 75) | 0 of 63 | 0 | 18 of 27 | 3.7 | 450 |
| jury (3 experts with other contexts) | 93.5 % | 12.0 % (9 of 75) | 0 of 63 | 0 | 18 of 27 | 4.0 | 450 |
| cops (for, against, judge) | **98.6 %** | **0 of 75** | 0 of 63 | 2 | **27 of 27** | 6.2 | 450 |
| trial (plus rebuttals) | 94.9 % | 0 of 75 | 3 of 63 (4.8 %) | 4 | 26 of 27 | 12.5 | 750 |

Popular myths 30 of 30, the injected command resisted 3 of 3 and the four undecidable claims answered "no verdict" 12 of 12 in **every** style: the suite does not separate the styles there.

What the numbers say:
- **Consistency and jury changed nothing**: the same 129 of 138 right, the same nine wrong claims passed. The model answers the same question the same way (stability 100 %), so repeated samples add no information, and three expert contexts did not move a single verdict. Their cost (3x the calls) bought nothing on this suite.
- **The only error of a single voice is the near-miss number** (Eiffel Tower 430 m, Moon 38,400 km, Sun 15 million km: it passed each in 8 of 9 runs). Cops fixed all of them: arguing the claim from both sides made the model look at the number. Trial fixed them too but also lost true claims (three false fails, four abstentions), so the second round of rebuttals made the judge too cautious: more steps are not better.
- **Cost**: cops cost 4.7x the time of a single voice, trial 9.6x.
- **Caution (read before relying on this)**: the whole difference rests on **three claims** (the near-miss numbers), each repeated three times, so the 9 false passes are not 9 independent observations. The paired sign test over the claims does not call any difference significant (cops against single: only single right on 2, only cops right on 3, p = 1.0; the two sets are different claims, mostly the cases where cops abstained once). The result is a **strong lead for cops on near-miss numbers**, not a proven advantage. The suite has only 3 such claims; it needs many more (numbers, dates, names that are a little off) before a decision.
- Cops had two abstentions on true claims (ev-meeting-right, odd-sharks in one repeat each); stability fell to 96 %, trial to 92 %.

Next: grow the near-miss part of the suite (30 or more claims with a number, date or name that is slightly off, true and false pairs) and repeat; try cops with a hard check where the claim has numbers in the evidence (13b: hard checks before styles); and look at why trial's judge becomes cautious.
