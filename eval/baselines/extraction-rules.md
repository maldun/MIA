# Baseline of the suite `extraction`: the rule-based extractor (no model)

`python tools/eval.py run extraction --variant rules` (skill `extract_claims_rules`, pipeline `extract.rules@1`). Deterministic: the same numbers every time. 51 texts, 48 claims to find, 11 texts
without anything checkable. This is the floor that a model-based extractor has to beat or complement.

What the patterns do well: arithmetic, spans that are always verbatim (no claim is ever invented or reworded). What they miss: units and dates in free wording, two claims in one sentence, quotations with
attributions that are not a capitalised name, facts without numbers, and numbers that are no claims (a phone number, a page number, a year inside a name), where they invent claims.

```
running extraction (51 cases x 1) as variant 'rules' ...


suite extraction, variant rules: 51 cases x 1 run(s)
run on 2026-10-18 22:28 UTC, no changes to the defaults

behaves as expected:    62.7%  (95% interval 49 to 75%, 32 of 51)
   MISMATCH num-two-in-one-sentence got fail           expected pass           
   MISMATCH unit-route             got fail           expected pass           
   MISMATCH unit-marathon          got fail           expected pass           
   MISMATCH unit-flour             got fail           expected pass           
   MISMATCH date-moon-landing      got fail           expected pass           
   MISMATCH date-two-leap-years    got fail           expected pass           
   MISMATCH date-age               got fail           expected pass           
   MISMATCH date-days-between      got fail           expected pass           
   ... and 11 more

as an extractor, on 51 texts with 48 claims to find:
   precision (what it found is right)   77.5% (31 of 40)  [40 claims found]
   recall (what is there, it found)     64.6% (31 of 48)
   F1                                   0.705
   texts extracted perfectly            62.7% (32 of 51)
   texts without claims left clean      72.7% (8 of 11)   <- an invented claim there
   claims whose text is not in the source 0.0% (0 of 40)
   problems: missed 11, wrong_type 6, spurious 3
   NOT PERFECT num-two-in-one-sentence missed The area is 7 * 8 = 56 square metres and
   NOT PERFECT unit-route             missed The route is 5 km long, which is 3.1 mil
   NOT PERFECT unit-marathon          missed A marathon is 42.195 km, or about 26.2 m
   NOT PERFECT unit-flour             wrong type [('unit', 'fact')]
   NOT PERFECT date-moon-landing      wrong type [('date', 'fact')]
   NOT PERFECT date-two-leap-years    missed 2024 is a leap year, but 1900 was not a 
   NOT PERFECT date-age               missed She was born on 17 May 1990, so on 16 Ma
   NOT PERFECT date-days-between      wrong type [('date', 'fact')]

by tag (right / cases):
   citation                60.0%  (95% interval 23 to 88%, 3 of 5)
   date                    28.6%  (95% interval 8 to 64%, 2 of 7)
   fact                    75.0%  (95% interval 47 to 91%, 9 of 12)
   false-claim-still-extracted 100.0%  (95% interval 34 to 100%, 2 of 2)
   multi                   20.0%  (95% interval 4 to 62%, 1 of 5)
   negation                 0.0%  (95% interval 0 to 79%, 0 of 1)
   none                    72.7%  (95% interval 43 to 90%, 8 of 11)
   not-a-statement        100.0%  (95% interval 57 to 100%, 5 of 5)
   numbers-not-claims       0.0%  (95% interval 0 to 56%, 0 of 3)
   numeric                 85.7%  (95% interval 49 to 97%, 6 of 7)
   opinion                100.0%  (95% interval 44 to 100%, 3 of 3)
   quotation               40.0%  (95% interval 12 to 77%, 2 of 5)
   reported               100.0%  (95% interval 21 to 100%, 1 of 1)
   two-in-one               0.0%  (95% interval 0 to 56%, 0 of 3)
   unit                    28.6%  (95% interval 8 to 64%, 2 of 7)

cost: 0.0 s in total, 0.00 s per run, 0 model calls, 0 characters sent, 0 received
```

To measure the model-based extractor: `python tools/eval.py run extraction --variant llm-light --skill extract_claims`, then
`python tools/eval.py compare extraction rules llm-light`.
