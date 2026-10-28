# Design draft: the review workflow as a literature review (N-2.3 T-07, amendment A-18)

Status: draft for the owner (2026-10-28). Replaces the open-ended search loop of `ui/REQUIREMENTS_RESEARCH.md` R1 to R7 for the example workflow `review`; the building blocks (`scholar.py`, `review_request.py`, `review_score.py`, `source_trust.py`) stay.

## Stages
| # | Stage | Done by | Output |
|---|---|---|---|
| 0 | Keywords | model proposes, code builds the query strings, user may edit | concepts (PICO-like), per concept synonyms; one Boolean string per keyword and one combined string; written inclusion and exclusion criteria |
| 1 | Search | code (`scholar.Scholar.search`) | one lookup per keyword; every query logged with source, date, hits |
| 2 | Collect | code | works de-duplicated (`dedupe`), each with the keywords that found it; cut-off (`within`) and retraction (`retraction_state`) filter, every drop recorded with its reason |
| 3 | Abstract screening | specialised model per work | two independent judgements: relevance grade 0 to 3 and eligibility include / maybe / exclude with a reason code; one statement each with a verbatim quote (checked by `quote_in_source`) |
| - | **Checkpoint** | user | intermediate report with `recommend()`; the full-text stage and further slices only on agreement (REQ-WFM-019) |
| 4 | Full-text screening | model per section, only where the full text is open access | same output per section and a check whether the sections fit the conclusion; no full text: abstract grade stays, marked `abstract only` |
| 5 | Keyword extension | code counts, user approves | terms not in the set that occur in at least N = 3 screened works are proposed; approved terms go back to stage 1 (REQ-WFM-027) |
| 6 | Report | code | keywords and queries, flow count, per work: keywords, decision, grade, notes with anchors; per keyword the works found; gaps = keywords without an included work |

Ends (REQ-WFM-020) when every collected work has a final decision and no approved keyword is left, or a budget is used up. A model saying "done" does not end it.

## Methods behind it (what could be checked, 2026-10-28)
- **Screening in two stages with reasons, PRISMA 2020 flow counts:** title and abstract first (binary include / exclude, "maybe" goes on), full text second, exclusions logged with reasons; criteria tested on a small sample first. Sources: Berlin International University library guide "Screening the results", GWU Himmelfarb "Study selection and appraisal", Covidence help on exclusion reasons, PRISMA 2020 checklist (EQUATOR). Covidence records reasons at full text and as optional tags at abstract level; we record them at both.
- **Graded relevance 0 to 3:** the graded scale of IR evaluation (Jarvelin and Kekalainen 2002, ACM TOIS, four points; TREC introduced 3-point judgements in the 2000 web track and DCG with them). Used here as the per-work grade; nDCG over the ranked works is the metric to compare our ranking with the labelled review cases (`review_score.py`). The exact label names (0 not, 1 marginal, 2 relevant, 3 highly relevant) are ours: the search results did not confirm TREC's wording.
- **Not found / not checked:** Kitchenham's quality checklist for software engineering reviews and GRADE / CASP for the quality of evidence were not looked up; quality of evidence stays out of this version (relevance and quality are not mixed).
- Search by keyword with snowballing from references (Wohlin) is not in this version.

## Two judgements, not one (owner 2026-10-28)
Relevance (how closely the work concerns the research question, grade 0 to 3) and eligibility (include / maybe / exclude by the written criteria, with a reason code such as `outdated`, `off_topic`, `wrong_type`, `after_cutoff`) have different purposes and are kept apart: a historic work can be highly relevant (grade 3) and still be excluded as outdated. The grade orders the works and measures the ranking (nDCG); the eligibility decides what enters the report's included set. Code never derives one from the other; the report shows both, and excluded works with a high grade are listed as near misses (PRISMA asks for them).

## Decisions taken by the owner (2026-10-28)
Time slices kept as a checkpoint before the full-text stage; abstract-only grade when no open full text; a grade scale from the literature (decision plus 0 to 3 grade); new keywords after approval.

## Open for the owner
1. Combination rules of the stage results. Eligibility: the full-text decision replaces the abstract decision when there is one, else the abstract decision stands (abstract only). Grade: the final grade is the lowest of the abstract grade and the mean of the section grades rounded down when the sections do not fit the conclusion, else the highest; to be tested on scripted results and tuned on the dev cases of `eval/suites/review*`, never on the holdout.
2. N = 3 for the keyword extension and the 60 s first slice are starting values (REQ-WFM-027 is optimised, REQ-WFM-019 as before).
3. REQ-WFM-018 as a measurement (recall and precision per tier against the baseline) is unchanged and needs the pipeline first; REQ-WFM-021 is unchanged (cut-off and retraction happen in stage 2).
4. Requirements 027 and 028 are `Draft` until you approve A-18.
