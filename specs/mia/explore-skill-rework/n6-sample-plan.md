# N-6 builder: larger marked sample and FR-42 text (Explore note, draft 2026-11-07)

Status: draft for the owner. Branch `explore-n6-sample` (worktree `.claude/worktrees/explore-n6-sample`), parallel to the G-V2 Plan on master. Touches only this folder; no production code, no suite, no requirement file.
Input: `spikes.md` (Spike C result), `proposals-for-owner.md`. Label truth is set by the owner only.

## 1. What the sample must decide
Bar (owner, spike C): at least 68 % of marked items right, at most 5 % invented, shares of the marked items. Option 1 had 72 marks: 0 invented (95 % upper bound about 4 %), 93.1 % right. Too small to accept a rate of invented items above zero.

## 2. Size (computed, exact binomial; the numbers are a proposal until the owner confirms)
- **Invented, the binding one:** mark **120 items**; accept option 1 if at most **4** are invented. A true rate of 8 % (LightRAG's level) is accepted with 3.2 % probability; a true rate of 2 % is accepted with 90.6 %.
- **Right:** at 120 items the 68 % bar needs 91 right; a true rate of 90 % passes with certainty, a true rate of 60 % essentially never. The invented rule decides; right needs no extra marks.
- 72 marks already given count if drawn the same way (random order, after the checks); 48 more needed, if the owner accepts them as part of the 120.
- Items from different documents are not independent; with 10 documents of 12 items each, treat the result as a screen. Hence the new documents below.

## 3. New documents (candidate; owner picks)
Spike C used 8 Wikipedia pages and 2 abstracts, all general English prose. Candidate additions, each about 12 000 characters, so the verdict does not only hold for tutorial text:
- a German Wikipedia page (MIA is used in German),
- a long arXiv abstract plus introduction of a technical paper,
- a documentation page (MIA's own `ui/README.md` section is local, not confidential),
- a news-style or forum text with pronouns and quotes (the weak spot: 36 of 45 refusals were relation quotes without both ends).
Sampling: per document **10 entities and 6 relations** (changed from 6 and 4 on 2026-11-07 with the owner's OK: 3 x 16 = 48 new marks), random order, seed 20261107 written down before the draw; the builder runs once per document (temperature 0), no tuning on these documents after the marking.

## 4. FR-42 candidate text (technology independent; Draft, proposed 2026-11-08, not applied to any requirement file)
- "When MIA builds a context graph from a document, it shall refuse every proposed item whose name does not occur in that document."
- "Every relation in a built context graph shall carry the passage of the document that states it, and both ends of the relation shall occur in that passage or in the sentences directly before or after it."
- Outcome (Given / When / Then): given proposals built from a document, when the owner marks a random sample of at least 120 of them, then at most 4 are marked invented and at least 91 right. (Evidence so far: 113 right, 0 invented of 120.)
- **Provisional (owner, 2026-11-08):** the neighbour part of the second sentence is proposed now on thin evidence (20 of 20 right, invented bound about 14 %) and is improved in Validate: the owner marks more relations that only the neighbour rule accepts (target: at least 60 in all with at most 3 invented, so that the invented bound is at most 5 %), drawn with a fixed seed from real runs. A `Provisional: VAL-nnn` mark and the id are given in Plan of goal C (ids are held by the G-V2 session). If the check fails, the sentence falls back to the strict text ("... in that passage").

## 5. Owner's answers (2026-11-07; decision id to be assigned when merged, ids are held by the G-V2 session)
1. **Size:** 120 marked items, at most 4 invented, kept for now; the sample may be **extended later** (a larger n is then a new, written decision before the extra marks are looked at).
2. **Documents added:** arXiv abstract + introduction, MIA's own README section, news or forum text. The German Wikipedia page is not added.
3. **Relation rule:** neighbouring sentences are allowed for the ends of a relation (pronoun case). Before it becomes a requirement, check it on the 36 refused relations of the spike C run.

## 6. Done and next steps
- Done 2026-11-07: builder run on the 3 documents (`spikes/lightrag/option1-run-n6/`, 107 accepted, 7 refused, strict relation rule kept for comparability); 48 items drawn; marking page `forms/n6-sample-marking.html` (generator `spikes/lightrag/make_marking_n6.py`, answers saved as `n6-sample-marks.json`).
- **Result (2026-11-07):** 120 marks, 113 right, 0 invented: the rule (at most 4 invented, at least 91 right) is met; details and caveats in `spikes.md`.
- **Neighbour rule is unmeasured:** 35 of the 43 refused relations would pass it; none is marked. Before the second FR-42 sentence is proposed, the owner marks a sample of them (suggestion: all 35 are too many; 20, drawn with a fixed seed, same four classes, same at most 5 % invented bar). Until then FR-42 uses the strict text.
- Drawn 2026-11-07: 20 of the 35 neighbour-rule relations, seed 20261108 (candidates sorted by document, source, relation, target before the draw); page `forms/n6-neighbour-marking.html`, answers saved as `n6-neighbour-marks.json` (generator `spikes/lightrag/make_marking_neighbour.py`). Bar for the relaxed rule: at most 5 % invented, at least 68 % right, as in spike C.
- **Neighbour sample marked (2026-11-07):** 20 right, 0 invented (`forms/n6-neighbour-marks.json`). The 68 % right bar is shown, the 5 % invented bar is not (upper bound about 14 %). Choice for the owner: propose the neighbour sentence in FR-42 now as a Draft with this evidence, or mark more first (about 40 more marks would bring the bound to 5 % only if 0 stay invented: 0 of 60 gives about 4.9 %).
- **Owner's decision 2026-11-08:** propose the neighbour sentence now as a Draft, improve it in Validate (section 4).
- Open:
- Pick the 3 documents and fix the seed; run option 1 once per document (spike folder `spikes/lightrag/`, throwaway) and draw 6 entities and 4 relations per document; prepare the marking form like `forms/spike-c-option1-marking.html`.
- The owner marks 48 new items (plus the 72 given, if drawn the same way); score with `score_marks.py`.
- FR-42 text (section 4, second sentence with neighbours) goes into the Plan review of goal C; not applied here.
