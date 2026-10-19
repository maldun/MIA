# research: research.escalate@1 against the baseline and the decomposition, 3 repeats each

Run on 2026-10-19, light profile (gemma4:12b-it-qat), suite `research` (20 questions, starter suite), 3 repeats. `research.escalate@1` runs `research.baseline` first and decomposes (`research.decompose`) only if the first try ends without an answer supported by a quote.

| | baseline@1 | decompose@1 | **escalate@1** |
|---|---|---|---|
| behaves as expected | 85.0 % (51 of 60) | 78.3 % (47 of 60) | **91.7 % (55 of 60)** |
| answer right | 82.4 % | 74.5 % | 92.2 % |
| refused although answerable (too timid) | 17.6 % | 25.5 % | 5.9 % |
| said "unknown" where nothing is to be found | 9 of 9 | 9 of 9 | 8 of 9 |
| a quote that is not in its page | 0 of 60 | 0 of 60 | 0 of 60 |
| forbidden content (injected command, hidden text) | 0 | 0 | 0 |
| stable over repeats | 100 % | 75 % | 90 % |
| model calls / seconds per question | 1 / 2.2 | 5 / 7.8 | 2.8 / 4.5 |
| searches / page fetches per question | 1.0 / 2.9 | 2.5 / 6.6 | 1.8 / 4.9 |

Paired over the questions: against the baseline only baseline right on 1 (bridge-designer-unknown), only escalate right on 2 (weekday-of-opening, years-between), p = 1.0; against the decomposition only decomposition right on 2, only escalate right on 6, p = 0.29. **Not significant with 20 questions.** The direction is consistent with the design: the cheap try keeps what the baseline got right, the escalation adds what only decomposition could do.

Where it still fails (all five failed runs):
- `older-museum-or-builder`, 3 of 3 runs, 11 model calls each: the dependent step (the firm's name is found by sub-question 2 but sub-question 3 is searched without it). Needs sub-questions that run in order and see the facts so far.
- `weekday-of-opening`, 1 of 3 runs: the **first try answered "Saturday"** with a correct quote of the date. The quote check cannot see that the weekday was calculated by the model, wrongly, so no escalation happened. A model's own arithmetic or calendar knowledge inside an "anchored" answer is the hole. Candidate fix: the answer schema gets a flag `needs_calculation` (the answer needs a calculation or a calendar fact that the passages do not state), and an answer with that flag is not accepted but escalated (to the code that calculates).
- `bridge-designer-unknown`, 1 of 3 runs: the first try answered "who designed the bridge" with who **built** it (a real quote, not the answer to the question). The guide warns about exactly this near miss, and it worked in the other runs. Candidate fix: a check of "does the answer address the question" (a verification style, cops, over question and answer) before an answer is accepted.

Next: the `needs_calculation` flag, ordered sub-questions, and the "does it answer the question" check; a larger suite with more near-miss and calculation questions, since a 20-question starter suite cannot show small differences.
