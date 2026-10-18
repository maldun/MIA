# extraction: model draft (extract.llm@1, skill extract_claims) against the rules baseline

Run on 2026-10-18, light profile (gemma4:12b-it-qat), 51 texts, 1 run each, 111 s in total (2.2 s per text).

| | rules | llm-light |
|---|---|---|
| texts extracted perfectly | 32 of 51 (62.7 %) | 35 of 51 (68.6 %) |
| precision | (rules baseline: F1 0.705) | 64.7 % (44 of 68) |
| recall | | 91.7 % (44 of 48) |
| F1 | 0.705 | 0.759 |
| claims not in the source | 0 | 0 (the anchoring step works) |
| texts without claims left clean | | 9 of 11 |

Paired comparison: only rules right 9, only model right 12, sign test p = 0.66: **not distinguishable from chance** with 51 cases and one run.

What the numbers say:
- The weak point of the model is not what it finds but **duplicates: 17 of the 24 wrong claims** (the same claim twice). Precision without duplicates would be about 90 %. A deduplication step (same anchor, same data) is the next cheap fix.
- Remaining: wrong data 4, spurious 3 (2 invented claims in texts without claims).
- Units are the weakest tag (3 of 7); the model is better than the rules on paraphrase, quotation and two-in-one cases.
- Single run: repeat runs are needed before a claim of "better" (see the lesson of verify.computable).

## With the tidy step (extract.llm@2), 3 repeats each, 2026-10-19

| | extract.llm@1 | extract.llm@2 (+ code.tidy_claims) |
|---|---|---|
| behaves as expected | 68.0 % (104 of 153) | 85.0 % (130 of 153) |
| precision | 68.2 % | 84.8 % |
| recall | 93.8 % | 88.9 % |
| F1 | 0.789 | 0.868 |
| duplicates | 48 | 4 |
| wrong type | 3 | 10 |
| missed | 0 | 1 |
| texts without claims left clean | 84.8 % | 90.9 % |
| stable over repeats | 84.3 % | 90.2 % |

Paired over the 51 texts: only v1 right on 2, only v2 right on 14, sign test p = 0.004.

Caveats: (1) the rules of the tidy step were written after reading the outputs of the first run on this same suite, so the gain is optimistic until it is confirmed on texts that were not used (a second extraction suite would do). (2) The price is recall (93.8 to 88.9 %) and wrong types (3 to 10): where the step keeps the specific claim in place of a fact, the model sometimes chose the specific type wrongly. Next candidates: look at the 10 wrong types; the rules baseline stays the reference (F1 0.705).
