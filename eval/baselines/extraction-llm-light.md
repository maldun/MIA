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
