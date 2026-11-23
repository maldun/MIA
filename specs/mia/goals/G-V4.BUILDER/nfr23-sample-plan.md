# NFR-23 marking samples: definitions and facts (light model), items and relations (full model)

Status: plan written 2026-11-23 **before any run or draw** (owner's choice in the session of 2026-11-23: both gaps, 240 marks; the 13 documents in the repo; run now with VIEW's session told). Throwaway spike on branch `spike/builder-samples`, code in `spikes/lightrag/`; not an eval run, no product code, no requirement changed. Truth is set by the owner only; the agent draws and lays out, never labels.

## 1. What the samples decide
NFR-23 (G-V4.BUILDER top-level spec, D-384): per sample of at least 120 marked proposals, at most 4 invented and at least 91 right.
- **Sample A, definitions and stated facts, light model** `gemma4:12b-it-qat` (the default, NFR-24). Until it passes, definitions and facts are not offered for confirmation (D-382).
- **Sample B, items and relations, full model** `gemma4:26b`. Until it passes, a full-model run is shown as unmeasured (D-384).

## 2. Builders (fixed before the runs; no change after a proposal has been looked at)
- B: `option1.py` unchanged (spike C, option 1: sentence chunks of at most 3000 characters, one model step with a JSON schema, a quote per proposal, the checks against the whole document: name in the document, quote a passage of the document, an entity's quote holds its name, a relation's quote holds both ends; strict relation rule, no neighbour sentences, as in the n6 sample). Only the model is set through `MIA_SPIKE_MODEL`.
- A: `option_df.py`, new: the same chunks and model call, its own prompt and schema (`definitions: [{term, definition, quote}]`, `facts: [{statement, quote}]`) and the checks of FR-99: the quote is a passage of the document (word for word, after the small normalisation of `checks.norm`); a definition's term occurs in the document and in its quote. A fact has no name to check; its quote is the only check.
- Both: `num_ctx` 8192, temperature 0, thinking off, one run per document; no tuning of prompt or checks on these documents after the run.

## 3. Documents
The 13 documents in the repo: `spikes/lightrag/docs/*.txt` (8 Wikipedia pages, 2 arXiv abstracts; spike C) and `spikes/lightrag/docs-n6/*.txt` (arXiv introduction, MIA README section, Wikinews article; n6 sample). Caveat (as before): items of one document are not independent, and the earlier samples used the same documents with the light model; sample B is new output of another model, sample A a new kind.

## 4. Draw (seed fixed here: 20261123)
From the **accepted** proposals of each run, per document in file-name order: shuffle with `random.Random(20261123)` (one generator per sample, used in that order), then take
- sample A: up to 5 definitions and up to 5 facts per document,
- sample B: up to 6 entities and up to 4 relations per document.
If a sample then holds fewer than 120, it is topped up from the accepted proposals not yet drawn (all documents pooled, shuffled with the same generator) until it holds 120. If fewer than 120 accepted proposals exist at all, the sample holds all of them and the shortfall is reported; NFR-23 then cannot be decided on this sample. The cards are shown in one random order (same generator), so marking can stop early; a stop before 120 decides nothing.

## 5. Marking and scoring
Two pages like the n6 page (`specs/mia/explore-skill-rework/forms/`): each card shows the proposal, the model's quote and the paragraph around it; the owner marks right, right but useless, wrong (the text says otherwise), invented (not in the text). The running tally on the page shows the NFR-23 rule (right of the marked, invented of the marked). The saved answers are scored with `score_marks.py`, which prints the NFR-23 verdict for a sample of at least 120 (at most 4 invented and at least 91 right) besides the old spike bar. A larger sample is a new written decision before extra marks are looked at (NFR-23).

## 6. Results
**Runs (2026-11-23/24, one per document, no failed model step; outputs in `spikes/lightrag/nfr23-run/`):**
- B, `gemma4:26b`, items and relations: 689 accepted (451 entities, 238 relations), 30 refused (22 relation quotes without both ends, 6 quotes not a passage of the document, 1 name not in the document, 1 quote without the name); 13 documents in about 36 minutes.
- A, `gemma4:12b-it-qat`, definitions and facts: 678 accepted (123 definitions, 555 facts), 3 refused (2 quotes without the term, 1 quote not a passage); about 19 minutes.

**Draw (seed 20261123, section 4):** sample A 120 cards (53 definitions, 67 facts; topped up, since definitions were short in several documents); sample B 128 cards (78 entities, 50 relations; no top-up). Pages: `specs/mia/explore-skill-rework/forms/nfr23-a-marking.html`, `nfr23-b-marking.html`; answers saved as `nfr23-a-marks.json`, `nfr23-b-marks.json`, scored with `score_marks.py`.

**Marks:** (the owner's; not yet given)
