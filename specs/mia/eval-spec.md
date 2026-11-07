# Eval specification: MIA (G-V1), the criteria the number gate does not cover

**Requirements:** specs/mia/requirements.md and the node requirements under specs/mia/nodes/   **Number gate:** specs/number-gate/eval-spec.md (REQ-VER-001 to -007, unchanged, its pins are reused here)   **Threat model:** specs/mia/threat-model.md   **Status:** Draft for the owner (2026-10-31, prepared by the coding agent; nothing here is decided until the owner approves it at a Plan gate)

Why this file: the owner set four requirements out of G-V1 because no eval criterion and no model pins were fixed (D-117 REQ-TLS-006, D-119 REQ-RUN-006, D-125 REQ-RUN-007), and the approved task N-2.4.1 T-08 (A-35, the review as a workflow of the library) needs an eval criterion before it starts. This draft proposes those criteria. Items marked **Owner** are decisions, not proposals the agent may settle.

## Model pins
| Pin | Model | Digest | Quantization | Options | Server |
|---|---|---|---|---|---|
| MP-light | gemma4:12b-it-qat | sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3 | Q4_0 (QAT), 11.9B | num_ctx=8192, temperature=0, seed=7 (evaluation) | Ollama 0.40.5 in podman (container `ollama`), OLLAMA_MAX_LOADED_MODELS=1, OLLAMA_NUM_PARALLEL=1 |
| MP-full | gemma4:26b | sha256:001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c | Q4_K_M, 25.2B | not used for criteria in G-V1 (18 GB, does not fit the 16 GB GPU alone) | the same |

The pins are those of `specs/number-gate/eval-spec.md`. Checked on 2026-10-31 with `podman exec ollama ollama list`: the ids `38044be4f923` and `001e5dafc3c7` are unchanged, the server is Ollama 0.40.5 (the full digests were read on 2026-10-24; Verify compares them again with `ollama show`). A pin changes only by amendment, with a new baseline for every suite that uses it. The coder model of the local coder (`xentriom/gemma-4-12B-coder…`) is a development tool, never a pin.

## What is an eval criterion here, and what is not
| Requirement | Kind | Why |
|---|---|---|
| REQ-TLS-006, REQ-WFX-016, REQ-BE-067 (AC-3: 0 invented references, 100 % of cited quotes found in their source) | **hard check on every output** plus an eval count | It must hold always, so it cannot be a rate: the quote check and the source check are code (`quote_in_source`, the source records of IF-402). The eval counts the violations over a suite to show the code is on every path; any violation is a FAIL, there is no tolerance. |
| REQ-RUN-006 (AC-22: fewer than 15 model calls for the first try on the light model) | **measurement per case** on the lookup suites | The calls are counted by code (`model_call` events); the model decides how many steps it takes, so it is measured on the pinned model, every case and every repeat. |
| REQ-RUN-007 (AC-19: first text within 10 s, median of 20, also while a review slice runs) | **benchmark**, not an eval | No truth label: a time on the host with the pinned model. Belongs in `benchmarks/` (protected), with the pin and the host recorded. |
| N-2.4.1 T-08 (REQ-RUN-013 AC-9, the review entry) and AC-3 per tier (TC-MIA-003) | **eval criterion** against a baseline | Recall and precision of the sources depend on the model; the rule `both` (threshold and not worse than the baseline of the current review). |

## Suites
| Suite | Covers | Target (harness kind) | Dev cases | Holdout cases | Labelled by | Needs model |
|---|---|---|---|---|---|---|
| EV-research | REQ-RUN-006; REQ-TLS-006 (lookup part) | research (skill `research`, pipeline of the variant) | 20 (`eval/suites/research`) | **none yet: 12 proposed** (`research.holdout`) | the owner | yes |
| EV-research_compound | REQ-RUN-006 | research | 16 (`eval/suites/research_compound`) | **none yet: 8 proposed** | the owner | yes |
| EV-review_toy | T-08; AC-3 tier 0; REQ-TLS-006 (review part) | review (`tools/review_suite.json`, `world.json`, fictional papers) | 7 (`eval/suites/review_toy`) | **none yet: 7 proposed** (`review_toy.holdout`, a second fictional corpus) | the owner | yes |
| EV-hard_checks | the code checks (number, quote, source) | checks | existing (`eval/suites/hard_checks`, incl. `n-planted-figure`, red on purpose) | – (no model, deterministic) | the owner | no |

**Gap (Owner):** none of the lookup and review suites has a holdout; every case in them has been seen during prompt work (they are starter suites). A criterion decided on them would measure tuning, not the product. Proposal: the owner writes or approves new holdout cases before any decision (the numbers above), drafted by the coding agent in `specs/mia/eval-drafts/` from the categories below and labelled by the owner; they go to `.holdout` folders and are never opened in Implement.

## Case scenarios (M39, approved before cases are written)
| Category (tag) | Given | When | Then | Cases |
|---|---|---|---|---|
| lookup, one fact (`single`) | a question whose answer is on one page of the recorded web | the lookup runs, 3 repeats on MP-light | the answer, every cited quote found in its page, fewer than 15 model calls | research dev 7; holdout 4 proposed |
| lookup, several steps (`multi-hop`, `chain`, `calculation`) | a question that needs two or three pages or a calculation | same | the same; the calls of the first try stay below 15 also when the run escalates later | research dev 7 + compound dev 16; holdout 4 + 8 proposed |
| unknown is right (`unknown`, `trap`) | a question the recorded web cannot answer, or a page that answers a similar question | same | "not found" or the honest gap, no invented source | research dev 7; holdout 4 proposed |
| review, conclusion (`basic`) | a conclusion question and the fictional corpus | the review runs, 3 repeats on MP-light | the gold answer with the verbatim sentence of the paper; recall and precision of the sources counted by `review_score.py` | review_toy dev 7; holdout 7 proposed |
| review, traps (`retracted`, `cutoff`, `inconclusive`, `unanswerable`) | a retracted paper, papers after the cut-off, a small study, a question without answer | same | retracted works dropped and listed, 0 cut-off violations, inconclusive and unknown said as such | inside the review cases above |

## Criteria and decision rules
Proposals; thresholds and bounds are the owner's (M19: fixed before any run, never changed to get a PASS).

| Requirement | Suite / select | Metric | Threshold | Bound | Repeats | Pin | Rule | Decided on |
|---|---|---|---|---|---|---|---|---|
| REQ-TLS-006 (AC-3, invented references) | EV-research + EV-review_toy / all | pass (a case passes when it has 0 invented references and every cited quote is found) | min=1.0 | – | 3, fold all | MP-light | threshold | holdout in Verify |
| REQ-RUN-006 (AC-22) | EV-research + EV-research_compound / all | pass (model calls of the first try < 15) | min=1.0 | – | 3, fold all | MP-light | threshold | holdout in Verify |
| T-08 / AC-3 recall (tier 0) | EV-review_toy / all | right (gold answer with its sentence) | min=**Owner** (proposal 0.70) | low>=**Owner** | 3 | MP-light | both, alpha 0.05 | holdout in Verify of T-08 |
| T-08 / AC-3 traps (tier 0) | EV-review_toy / tag `retracted`, `cutoff` | pass (retracted dropped and listed, 0 cut-off violations) | min=1.0 | – | 3, fold all | MP-light | threshold | holdout in Verify of T-08 |

Command: `python ~/.claude/skills/agent-app/scripts/eval_decide.py --run <run> --baseline <baseline> --criterion "<Eval criterion line>" --select req:<ID>`

Note on `fold all` with `min=1.0`: one bad repeat of one case fails the criterion. That is intended for the two "must hold always" lines; the re-run rule (one re-run with fresh seeds) still applies.

## Error rates (M19, fixed before any run)
Computed with `~/.claude/skills/plan-phase/scripts/false_alarm.py` at the proposed holdout sizes.

| Requirement | Planned holdout n | Good rate | Bad rate | False alarm | Miss | Command |
|---|---|---|---|---|---|---|
| REQ-TLS-006 | 19 cases (12 research + 7 review) | violation 0.0 | 0.05 | 0.00 % | 61.2 % | `--n 19 --max-rate 0.0 --good 0.0 --bad 0.05 --rerun` |
| REQ-RUN-006 | 20 cases (12 + 8) | over 15 calls 0.0 | 0.05 | 0.00 % | 58.9 % | `--n 20 --max-rate 0.0 --good 0.0 --bad 0.05 --rerun` |
| T-08 recall | 7 cases | **Owner** | **Owner** | – | – | after the thresholds are fixed |

Reading, worked out on 2026-10-31 for scale: with a zero-tolerance rule at n = 36 a product that really fails 5 % of the cases passes in 29 % of the Verify runs; at n = 12 and a 10 % failure rate in 49 %. Small suites cannot catch rare violations; that is why REQ-TLS-006 rests on the code check on every output, and the eval only shows that the check is on the path. The review recall at n = 7 can show a broken pipeline, not a small difference (the suite says so itself): the owner decides whether T-08 needs a larger review suite (tier 1) before its criterion can decide.

## Benchmarks with the pin (not eval criteria)
| Requirement | Benchmark | Measure | Limit | Runs | Pin and host | Where |
|---|---|---|---|---|---|---|
| REQ-RUN-007 (AC-19) | first text of a chat answer, idle and while a review slice runs | seconds from send to the first streamed text | median <= 10 s in both conditions | 20 each | MP-light; the host of `CLAUDE.md` (facts from the machine at the run: `fastfetch`, `ollama ps`) | `benchmarks/` (protected: a plan amendment), tool of N-4.1 T-05 |

## Where and when evals run
- Implement: the dev split after each prompt or pipeline change (feedback only); at most 3 variants per task unless the plan says otherwise.
- Verify: dev and holdout once per candidate; a failing criterion is re-run once with fresh seeds (`eval_decide.py --rerun`).
- Nightly: none in G-V1 (one GPU shared with the users).

## Split rule
- New holdout cases are written for the holdout only (the existing dev cases have been seen and stay dev). Per category, cases alternate dev and holdout when Validate adds new ones.
- Holdout lives in `eval/suites/<suite>.holdout/`, runs only in Verify; no case moves between splits (retire and add).

## Baselines
| Suite | Variant | File | Release | Date | Summary |
|---|---|---|---|---|---|
| EV-research | research.escalate@1 (current default) | eval/baselines/research__escalate__baseline.jsonl (+ `.holdout`) | current `goal/v1` | to record at the gate (dev); holdout before Verify, results only | eval/baselines/research-escalate.md (2026-10-19, 20 questions, 3 repeats: calls per question 1 to 11) |
| EV-research_compound | research.decompose (current) | eval/baselines/research_compound__decompose__baseline.jsonl | the same | to record | eval/baselines/research-decompose.md |
| EV-review_toy | the current review (`review_chat.run_review`) | eval/baselines/review_toy__review__baseline.jsonl | the same | to record **before T-08 starts** (the baseline T-08 must not be worse than) | – |

## Stability
Accepted stability (share of repeated cases with identical outcome) >= 0.90 for the lookup and review suites, as for the number gate. Below that, a run is a finding (stop condition in Implement).

## Smoke subset (Deploy)
Cases tagged `smoke`: 2 per lookup suite and 2 of the review suite, chosen by the owner. Tolerance: the same outcome as the release run on every smoke case.

## LLM judge
Not used: the truth is a gold answer and a gold sentence set by people; the scores are counts by code (`review_score.py`, the quote and source checks).

## Cost of a full eval (from the baseline of 2026-10-19: lookup 2.2 to 7.8 s per question)
| Suite / run | Cases × repeats | Seconds per case | Total | When |
|---|---|---|---|---|
| EV-research + compound, dev | 36 × 3 | about 5 | about 9 min | after each change of a lookup pipeline |
| the same, holdout | 20 × 3 | about 5 | about 5 min | Verify only |
| EV-review_toy, dev | 7 × 3 | to measure (a review is many calls) | – | after each change in T-08 |
| REQ-RUN-007 benchmark | 40 runs | about 10 to 60 | about 20 min | once per candidate |

## Validation criteria that need real use
See `specs/mia/test-spec.md` VAL-001 to VAL-006; VAL-006 ("fast and light enough in daily use") reads the REQ-RUN-007 benchmark next to the users' impression.

## Decisions for the owner (in this order)
1. Do the three set-out measurements come back into G-V1 with this spec (REQ-TLS-006, REQ-RUN-006, REQ-RUN-007), or stay out and come with the next goal?
2. Holdout cases: write or approve 12 + 8 lookup and 7 review holdout cases (drafted by the agent in `specs/mia/eval-drafts/`, labelled by you).
3. T-08: the recall threshold and bound (proposal min 0.70, low 0.50 at n = 7, only to catch a broken pipeline), or first a larger review suite (tier 1).
4. REQ-RUN-007 as a benchmark under `benchmarks/` (a plan amendment that installs it).
5. The rule for `n-planted-figure` in `number_check` (conflicting values `fail` or `open`): it changes EV-hard_checks and is re-measured on the verdict suites of the number gate.

## G-V2.CONVERT: conversion of the skills (REQ-WFM-057 to 066, 069, 110 to 115)

Written 2026-11-07 in Plan step 3. A skill is converted when its converted record reproduces the outcomes of the v0.1.0 skill on the dev split of its own suite on the same pin (REQ-WFM-059); the numbers are in the criterion lines of REQ-WFM-110 to 114 (starting guesses under D-187: margin 0.10, 3 repeats, threshold rule, settings version 1 of REQ-WFM-069). These are dev-split equivalence checks, not holdout decisions: the suites are starter suites without holdout (see Suites above), so they show that nothing got worse, not that a skill is good.

### Which suite belongs to which skill
| Skill (v0.1.0 pipeline) | Suite that decides | Dev cases | Other suites (run, reported, not decided) | Requirement | Form after this goal |
|---|---|---|---|---|---|
| research (research.escalate@1) | EV-research | 20 | EV-research_compound (16) | REQ-WFM-110 | converted if the criterion passes |
| plan_question (plan.free@1) | EV-plans | 36 | – | REQ-WFM-111 | converted if the criterion passes |
| verify_claim (verify.single@1) | EV-verdicts | 50 | EV-verdicts_injection (12), EV-verdicts_wikidata (184) | REQ-WFM-112 | converted if the criterion passes |
| verify_computable (verify.computable@2) | EV-computable | 39 | – | REQ-WFM-113 | converted if the criterion passes |
| extract_claims (extract.llm@1) | EV-extraction | 51 | – | REQ-WFM-114 | converted if the criterion passes |
| extract_claims_rules (extract.rules) | EV-extraction | 51 | – | REQ-WFM-115 (equal outputs, no model) | converted if all 51 outputs are equal |
| chat, check_speech, memory_write, summarize | none | – | – | none | old runner; reason: part of the user interface (owner 2026-11-07), revisited in another goal |
| review_abstract, review_full, review_keywords, review_section, review_summary | none of their own (EV-review_toy exercises the review as a whole, 7 cases) | – | – | none | old runner; the same reason |

The skill-to-suite link is the `target.skill` field of each `suite.json`; EV-behaviour (target kind `text_rules`) and EV-review_toy (target skill `review`, no skill of that name) name no skill of the table and decide nothing here. Two skills share EV-extraction; their baselines differ by variant (`extraction__rules__baseline.jsonl`, `extraction__llm-light__baseline.jsonl`). The reason for the nine skills is the text REQ-WFM-060 requires; the owner gave it as one reason for all nine.

### Baselines of the converted skills (A-120 records them; none is a committed run file yet)
| Skill | Variant | Reference now (case share behaving as expected) | Source | Repeats | To do before any converted run |
|---|---|---|---|---|---|
| research | research.escalate@1 | 0.92 (55 of 60 case-repeats, 0.917) | eval/baselines/research-escalate.md, 2026-10-19 | 3 | record the run file |
| plan_question | plan.free@1 | 0.64 (69 of 108) | eval/baselines/research-planners.md, 2026-10-19/20 | 3 | record the run file |
| verify_claim | verify.single@1 | 0.93 (43 of 46 with a known truth; 4 of 4 undecidable right) | eval/baselines/verdicts-single.md, 2026-10-19 | 1 | re-record at 3 repeats |
| verify_computable | verify.computable@2 | 0.92 | eval/baselines/computable-gemma4-12b.md, 2026-10-18 | 1 | re-record at 3 repeats |
| extract_claims | extract.llm@1 | 0.69 (35 of 51 perfect) | eval/baselines/extraction-llm-light.md, 2026-10-18 | 1 | re-record at 3 repeats |
| extract_claims_rules | extract.rules | 0.63 (32 of 51), deterministic | eval/baselines/extraction-rules.md, 2026-10-18 | 1 (deterministic) | record the run file for the equality check |

### Error rates (M19, fixed before any run)
`false_alarm.py --n <n> --min-rate <min> --good <reference> --bad <reference - loss> --rerun`, computed 2026-11-07.

| Requirement | n | Minimum (k of n) | Good rate | False alarm | Miss at a loss of 0.25 | Miss at a loss of 0.15 |
|---|---|---|---|---|---|---|
| REQ-WFM-110 | 20 | 0.82 (17) | 0.92 | 0.0050 | 0.1242 | 0.4981 |
| REQ-WFM-111 | 36 | 0.54 (20) | 0.64 | 0.0122 | 0.0638 | 0.4637 |
| REQ-WFM-112 | 50 | 0.83 (42) | 0.93 | 0.0001 | 0.0171 | 0.3586 |
| REQ-WFM-113 | 39 | 0.82 (32) | 0.92 | 0.0001 | 0.0577 | 0.5053 |
| REQ-WFM-114 | 51 | 0.59 (31) | 0.69 | 0.0064 | 0.0233 | 0.3652 |

Reading: a conversion that loses a quarter of the right cases is caught with a miss of at most 0.12; one that loses 0.15 passes in 36 to 51 % of the checks. The suites are too small to see a small loss, so the guard against a silently changed prompt or step order is REQ-WFM-058 (same model calls, exact, no model). The reference rates of four suites come from one repeat and carry their own uncertainty (Wilson 95 % half-width 0.07 to 0.15 over the cases), larger than the margin of 0.10 for three of them; a bigger suite or more repeats would narrow it, which is the owner's call (settings version 2 of REQ-WFM-069).

### Case scenarios
No new cases are written for G-V2.CONVERT: the five suites exist and are labelled by the owner; the only change of eval material is the tag `split:dev` and the baseline files (A-120, protected, applied by the owner).

### Where and when they run
Stage 4 (test-spec.md, TC-WFM-110 to 114), on MP-light with one model loaded, after the converted skill passes TC-WFM-058 and TC-WFM-115 and before it is switched from the old runner (REQ-WFM-057). The dev runs of Implement are feedback; the decision run for the record of REQ-WFM-060 is made once per skill, re-run once on a FAIL, and logged with the versions of skill, pipeline and settings.
