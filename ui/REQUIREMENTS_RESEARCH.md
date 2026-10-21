# MIA research: a literature review of a research question (requirements, draft 1, 2026-10-21)

Replaces the idea "research = answer one question from a few web pages" (13.1 of `REQUIREMENTS_CORE.md`) as the **main** research task. The old pipelines stay as the quick path (RV3). Builds on 13b (strategies), 13c (context graph), 4a (library), 9 (evaluation), 12 (verification).
How to read it: **Decided** = from the discussion of 2026-10-21; **Proposal** = to be built and measured; **Evidence** = what the literature says, with how well it was checked. Nothing here is built yet.

## 1. Principle: break a problem down level by level (decided)

A small model cannot digest a whole problem, as a person cannot digest a whole PDF at once. So a task is worked **top down in levels**, and each level is done by a narrow role:

- RV1. **Three planning roles** (prompt views of a model, see RV20, not three programs):
  1. **System analyser**: describes the *structure* of the problem first: the concepts, the sub-questions, the fields involved, what kind of evidence would answer it, what is out of scope.
  2. **Component determiner**: takes that structure and names the *components*: which experts (RV10), which keyword sets, which source types.
  3. **Scheduler**: turns the components into the *tasks* in order, each with a budget (RV30) and a target a check can test (13b ST1).
- RV2. **Granularity matches the context window.** A piece of work is only handed to a model if its input fits a fixed share of the model's context (`num_ctx` of the profile, default budget 50 percent, the rest is for instructions and answer). Code counts tokens; if a piece is too big it is split **one level deeper** by the same procedure (sections of a paper, then paragraphs; sub-questions of a sub-question). The model is never asked to decide what fits.
- RV3. **Research is two tasks.** (a) **Fact check** of one statement: stays, but is cheap (RV40): first a source whose trust is high enough (RV14), a model only if that is not enough. (b) **Literature review** of a research question: the new main task (RV4). A single research question is too atomic to be the unit of research; the review is. Chat commands: `/research` and `/search` as today, `/review` new.

## 2. What MIA delivers: the literature review (decided)

- RV4. **Input:** a research question, optional scope (fields, languages, **a date: only literature published up to that date**, default today), a budget (RV30).
- RV5. **Output:** a structured report (RV27) with the sources found and why each was kept or dropped, the findings per sub-question with verbatim anchors, conflicts between sources, and an **answerability** figure in percent (RV23) with open gaps and suggested next keywords. A low figure is a valid result (RV24).
- RV6. **We do not claim to verify the truth** (decided). We judge how well the available literature lets us answer the question, and show what that judgement rests on.

## 3. Evidence: what the literature says, and what it does not (checked 2026-10-21)

Checked through search results and one fetched paper page (Smit et al.); the other papers only as abstracts or search summaries. The numbers must be read in the papers before they are cited in a publication.

- **Smit et al., "Should we be going MAD?" (ICML 2024, arXiv 2311.17371).** Compared Society of Minds (SoM), Multi-Persona, ChatEval, Ensemble Refinement, Self-Consistency, Medprompt (its ensembling parts) and single-agent prompting on 7 datasets with GPT-3.5 (MedQA, PubMedQA, MMLU, CosmosQA, CIAR, GPQA, Chess); GPT-4 and Mixtral 8x7B only on MedQA. Result: **no debate protocol beats the simpler methods reliably**. Medprompt (ensembling, no debate) was best overall and cheaper; SoM was the strongest debate method on MedQA (0.64 vs 0.65 for Medprompt) and showed the largest gain from debate over the first answer; self-consistency was best on MMLU. Debate costs more calls and tokens. The methods are **sensitive to hyperparameters**: Multi-Persona went from worst to best after tuning, and prompting agents to agree with each other X percent of the time ("agreement modulation") gave about 15 percent for Multi-Persona and 5 percent for SoM on a USMLE subset, while for one dataset (CIAR) disagreement helped. Limits stated by the authors: GPT-3.5 through an API; hyperparameters **transferred poorly to Mixtral 8x7B**; the tasks are multiple choice questions, **not literature reviews**.
  *Consequence:* "Society of Mind is the best approach" is **not** what the paper shows. It is a promising and competitive candidate whose benefit must be measured against an ensemble with the same number of calls on our models and our task (RV33). Roles and debate are built as interchangeable **judgement styles** (12.1), not as the only architecture.
- **PaperQA2 (FutureHouse, arXiv 2409.13740).** Agent with retrieval, summaries and answer steps; reports expert-level results on retrieval, summarisation and contradiction detection (70 percent of 2.34 contradictions per paper confirmed by experts) and the benchmark LitQA2. Search summaries only; part of the coverage is promotional.
- **OpenScholar / ScholarQABench (arXiv 2411.14199).** Retrieval-augmented LM for scientific questions, a benchmark of 2,967 expert-written queries and 208 long-form answers across computer science, physics, neuroscience, biomedicine; data and code released. A candidate for part of the benchmark (RV31). Abstract and summaries read.
- **LLM abstract screening for systematic reviews** (OLIVER, arXiv 2512.20022; a poster on local open-weight models; a psychiatry study; summaries only): recall depends strongly on review, prompt and model; most models are specific but miss true includes; two-model actor-critic improved discrimination and calibration but sensitivity only a little; a 5-model ensemble reached about 97 percent recall with about 54 percent precision; two broad-scope reviews never reached 95 percent recall with any model; a local Gemma beat a cloud model in one of five reviews. *Consequence:* screening is **recall-oriented**, uses several votes, keeps borderline papers for a second look (RV17), and its recall is measured against reference reviews (RV31).
- **Scholarly metadata:** OpenAlex, Semantic Scholar and Crossref offer free APIs; OpenAlex draws on Crossref. A 2024 study found OpenAlex's single `is_retracted` flag misclassified corrections and expressions of concern as retractions for part of the data; Crossref (which took over the Retraction Watch data) has finer status information, partly in an experimental API. *Consequence:* retraction status is read from Crossref and cross-checked, not taken from one flag (RV15).
- Not checked, from memory: OpenAlex's topic taxonomy (domains, fields, subfields, topics) as a starting point for the field graph (RV11).

## 4. The agents (roles) (proposal, from the discussion)

- RV10. **Field experts**: one role per related sub-domain (for a question about electricity: electrical engineering as the main field, physics and mathematics as related). Each expert proposes keywords (RV16), judges the relevance of text pieces from its point of view (RV18) and fills its section of the report (RV27).
- RV11. **Field graph.** A stored graph of fields and subfields with weighted edges ("how relevant is B for a question in A", 0 to 1). The system analyser looks the question up in it; the number of experts is the main field plus the related fields above a relevance threshold, **at most N_max** (default 3 related, to be optimised, RV33). The graph starts from a public taxonomy (OpenAlex topics, to verify) plus hand edits, is stored in the library (4a) as data, and its weights are corrected from experience: a field whose expert never contributed a cited finding loses weight, one that did gains (RV35).
- RV12. **Main-field lead**: one role for the main field that gathers the experts' findings into the answer and resolves or flags conflicts.
- RV13. **Literature acquirer**: finds sources, keeps the references and the **relevance of each source with its reasons**, runs the search log, and owns the source table of the report. **Methodology specialist**: rates the *design* of each study (randomised trial, cohort, review, simulation, opinion, ...) and proposes how the evidence is to be weighed; together with the acquirer it writes the overall structure of the report (RV27).
- RV20. **Roles are views, not necessarily models.** With one language model loaded at a time (`OLLAMA_MAX_LOADED_MODELS=1`, one slot) a role is a prompt, a context view (the pieces and the graph neighbourhood the role sees, 13c CG3) and a schema, run by the same model one after the other. Different models per role are an option to test (diversity of errors), not an assumption: swapping models costs time, and the evidence for diversity from different models is not checked here. Light model for screening, full model for synthesis is the first split to try.
- RV21. A **critic** role (tries to refute a finding, 12.1 styles) is a variant to compare, not a default.

## 5. The process (proposal)

Each stage is a library pipeline of narrow nodes (4a), runs under the limits of RV30, and writes into the context graph (RV25).

- R0. **Intake and scope:** question, date cut-off, budget; one clarifying question if the question is ambiguous.
- R1. **Analyse** (system analyser): structure of the question, sub-questions, fields via the field graph, inclusion and exclusion criteria, the kind of evidence that would answer it. Output: plan as data (13b ST1) with targets.
- R2. **Components and keywords** (RV16): each expert proposes keywords; code merges, normalises and writes one search string per source type.
- R3. **Acquire:** scholarly APIs (OpenAlex, Semantic Scholar, arXiv, PubMed, Crossref; free, rate-limited, polite) and SearXNG for grey literature (reports, standards, official statistics); de-duplicate by DOI and title; metadata kept: date, venue, authors, citation count, open-access link, **retraction and correction status**. Only items **dated up to the cut-off** pass (RV32).
- R4. **Screen** in two stages:
  - RV17. *Stage 1, abstract first:* title, abstract and, where the full text is available, the conclusion; several expert votes (the ensemble form is the baseline) produce a relevance score; recall-oriented thresholds; borderline papers go to stage 2 instead of being dropped; a paper that is clearly off topic is dropped with its reason logged.
  - RV18. *Stage 2, pieces:* the full text (open access only, RV34) is cut into digestible pieces by code (sections, then paragraphs, RV2); the experts judge which pieces are relevant to which sub-question; the relevant ones are extracted **verbatim with an anchor check** (the quote must occur in the source, as in 9). The relevance of the source is then judged from the pieces.
- R5. **Weigh:** source credibility from the trust database (RV14), study design from the methodology specialist, recency; one weight per finding, computed by code from these parts so that it can be shown.
- R6. **Synthesise in the graph** (RV25): findings per sub-question, conflicts (13c CG5), open slots; the gap check names the open sub-questions and proposes further keywords; new sources found through references of good papers (one citation step, limited) and new keywords are added to the graph.
- R7. **Judge** the answerability (RV23) per sub-question and overall.
- R8. **Report** (RV27).

- RV19. **When to stop:** (a) a **sufficiency check by code** (every sub-question has anchored findings of enough weight, or has been searched with the keywords tried, RV23) plus the experts' vote as one signal; the model's feeling "answered" alone never ends the search (models tend to be sure of themselves, 12); (b) the source budget; (c) every **K sources checked (default 10, to be optimised, RV33)** MIA gives an **intermediate report** and asks whether to continue, with a recommendation and the reason ("two sub-questions are open; different keywords may help"). The user answering "no" ends the run with the report as it stands.
- RV22. **Sub-questions:** if the analysis or the gap check shows that the question must be split, the sub-questions get their own pass through R2 to R7 under the same budget (shared, not multiplied), as a child of the question in the graph.

## 6. Source trust (decided: a database of how much we trust sources) (proposal for the design)

- RV14. A **source trust table** in the library (4a, versioned, editable by the user): a prior trust 0 to 1 per **source class** (peer-reviewed journal, conference proceedings, preprint, thesis, official statistics or government body, standards body, textbook, quality press, trade press, company blog, personal blog, forum, wiki, unknown) and per **venue or domain** where known (journal quartile or indexing from OpenAlex/Scimago-like data, domain entries added by hand), each with its *reason* and the date it was set. Trust is a **judgement of ours**, shown as such; it is a **prior**, never a proof: the anchor check decides whether a quote is genuine, and a high-trust source can still be contradicted.
- RV15. **Source facts are read, not guessed:** type, venue, date, citation count and **retraction or correction status** (Crossref first, cross-checked) come from the metadata. A retracted paper is dropped from the evidence and listed in the report as retracted; one with an expression of concern is kept with the flag. Preprints are marked as not peer reviewed.
- RV40. **Fact check path (cheap):** one statement is searched; if a source with trust at or above a threshold states it (anchored), that is the answer and no model judges it; if the sources are low trust, silent or in conflict, it is escalated: a single model judges with the passages (12.1 styles), and a statement that needs more than a lookup becomes a review (RV3). Whether a single model or a simple comparison with a reputable source is enough is **measured on the research suites** (the existing `research` and `research_compound` suites are the baseline).

## 7. Keywords and the context graph (proposal)

- RV16. Keyword set per expert: synonyms, narrower and broader terms, abbreviations, the usual wording in that field. Merged by code; each keyword keeps who proposed it and what it found (number of hits, number kept). Keywords that found nothing useful are not repeated.
- RV25. **The review's context graph** (13c): nodes for the question, sub-questions, fields, keywords, sources, pieces (quotes), findings, conflicts, open slots; edges as in CG1 plus `proposed_by` (expert), `found_by` (keyword), `cites`. New sources and keywords found during reading are added; the graph decides what is read next (open slots first) and renders each model call's context within the budget (RV2). It is written to the run log; the graph viewer (10) can show how a finding came about.

## 8. Answerability in percent (decided: no verification, a judgement) (proposal for the definition)

- RV23. The figure is **computed by code from anchored evidence**, not asked from a model, with its parts shown: (1) *coverage:* share of sub-questions with at least one anchored finding of enough weight; (2) *weight:* the sum of finding weights (RV5 and R5), saturating; (3) *diversity:* independent sources (not sources that cite each other for the same claim); (4) *agreement:* penalty for unresolved conflicts, none for resolved ones; (5) *recency* where the question asks for the current state; (6) *search effort:* how many keywords and sources were tried. The experts' vote on "is the question answered" is shown next to it. The first formula is a transparent rubric with weights set by hand; it is **calibrated** on the benchmark (RV31): the figure is called a probability only if the benchmark shows that findings at 80 percent are right about 80 percent of the time (a calibration plot is part of the report of the evaluation).
- RV24. A **low figure is not an error.** The report says why it is low in one of a fixed set of causes: too little literature found, sources are weak or old, sources conflict, sub-questions are open, keywords probably wrong (with proposed alternatives). The user can start a follow-up run with these.

## 9. The report (proposal)

- RV27. Structure, set by the acquirer and the methodology specialist from the analysis, filled by the experts: question and scope; method (search strings, sources, date cut-off, screening counts like a PRISMA flow: found, de-duplicated, screened, kept, read); the sources table (reference, class, trust, design, relevance and why); findings per sub-question by field, each with its anchors; conflicts and how they were weighed; limitations; answerability with parts; open gaps and next keywords. Markdown, shown in the chat in short form (status block 5) and saved as a file in the run folder. **Every reference in the report must be a source the run actually retrieved** (hard check: it resolves to a stored DOI or URL and its quotes anchor); an invented reference is a failure by definition.
- The chat shows the playful line and the accurate step in brackets as in 5 (stage, counts, budget used).

## 10. Limits, budgets, side effects (decided)

- RV30. **Every run has hard limits** set before it starts and shown in the intermediate report: sources screened (stage 1), sources read (stage 2), model calls, tokens, wall time, search and API requests (polite rates, caching). Defaults small; the user can raise them for a run. Reaching a limit ends the stage and produces an intermediate report; nothing continues without the user (RV19c). A run is stoppable at any time; the report so far is kept.
- Side effects: scholarly APIs and web search are read-only; nothing is installed or executed from a source; text from papers is untrusted data (prompt injection, 11); the learning of RV35 only changes numbers in configuration and graph weights, never weights of models.

## 11. Evaluation: benchmarks for literature reviews (proposal)

- RV31. **Reference set:** published literature reviews with a clear question and a known conclusion, of **varying outcomes** (supports, does not support, inconclusive), from 3 to 4 fields, open access where possible, including some of poor quality, outdated or contradicted by later work. Start with 10 to 20; candidates: parts of ScholarQABench, systematic reviews and meta-analyses whose included-study lists are public (abstract level when full text is not open). Split into a **development half** (tuning) and a **held-out half** (reported, never used for tuning).
- RV32. **Time cut-off:** for each reference review, only literature published **up to the review's search date** is allowed (the review itself and later papers are excluded by code). Limit that cannot be removed: the language model may have seen the review in training; reviews published after the model's cut-off date are preferred and the contamination risk is stated in every result.
- RV33. **Measures:** (a) *source recall and precision* against the reference review's included studies (at stage 1 and at the end); (b) *conclusion agreement* (direction and strength: supports, does not, inconclusive); (c) answerability calibration (RV23); (d) hallucinated references (must be 0); (e) quote anchoring (must be 100 percent); (f) calls, tokens, seconds. **Variants, same call budget where possible** so that cost is not confused with quality: A single model, one pass; B single model with ensemble screening and self-consistency on the conclusion (the Medprompt-like baseline); C roles with Society-of-Mind style rounds; D = C with agreement modulation (levels 0, 50, 90 percent); E with and without the field graph (RV11); F with and without abstract-first (RV17); G N_max and K varied. Repeats and the same statistics as 9; planners and debates are not deterministic, so stability is reported.
- When our conclusion **differs** from the reference, each case is classified: reference outdated (newer literature in the allowed window says otherwise), reference weak (low-quality studies, to be argued from the sources, not asserted), our miss (keywords, access, recall), our error (misreading, weighting). Only the last two count against the method; the first two are reported and may justify dropping a reference from the set (RV31), with the reason written down.
- RV34. Access: open-access full text only (Unpaywall-like links from the metadata); a paywalled paper is used at abstract level and marked so. A local collection of the user's own PDFs is a later source (own material may use a pre-built graph, 13c CG7).

## 12. Reward and learning (decided as a direction; the design is a proposal)

The language models are fixed; what can improve is the **agent**: its configuration, thresholds, role choices and field-graph weights. This is the ladder of 8 of `REQUIREMENTS_CORE.md` applied here.

- RV35. **Level 1, fixed defaults** (everything works without learning). **Level 2, logged signals** for every run: the parts of RV23, calls, seconds, the user's reaction (kept, edited, rejected sections; "continue" or "stop"; a rating if given). **Level 3, a bandit over discrete choices** (number of experts, K, thresholds, agreement level, light or full model per stage, which keyword style), tried first **offline on the development half of the benchmark**, later online with user feedback, each change logged next to the default choice and reversible.
- RV36. **The reward functional** is a **vector, not one number**, and is never optimised alone: benchmark-side quality (source recall, conclusion agreement, calibration), cost (calls and seconds), the user's signals. A scalar for the bandit is made as a weighted sum with a cost term, the weights written down and changed only by the user. **Limits are constraints, not penalties** (RV30): a configuration cannot buy quality by exceeding a budget.
- RV37. **Guards against gaming the reward** (the usual failure of learned agents): (a) the figure being optimised is computed by code from anchored evidence, the model does not see it and cannot write it; (b) shrinking the search to look more certain is caught because coverage and search effort are parts of the figure and the benchmark measures source recall; (c) the held-out half is never used for tuning; (d) a learned choice has to beat the default on the development half *and* hold on the held-out half before it becomes the default; (e) every learned change is shown in the report of the run ("this run used 4 experts because ..."); (f) everything can be switched off.
- RV38. The **intermediate report and "continue?"** (RV19c) is also the main place where the user's signal enters, at no extra effort.

## 13. What is reused and what is new

Reused: `search`/`fetch`/`extract` nodes with the quote check, SearXNG and its fallback, typed plans and plan checks (ST10, ST11), verification styles (12.1), the context graph (13c), the library with status and versions (4a), the evaluation harness and suites (9), the sandbox, the run log, the status block (5), the chat command mechanism (`/research`, `/search`).
New: scholarly API tools (OpenAlex, Semantic Scholar, arXiv, PubMed, Crossref) with caching and rate limits and **recorded fixtures for tests**; the field graph; the source trust table; the screening nodes (stage 1 and 2); the role runner (prompt, view, schema per role); budgets and the checkpoint dialogue in the chat; the report template; the reference set and its scoring; the answerability rubric and its calibration; `/review`.

## 14. Phases (proposal; each one measured before the next, tests first as in 9)

1. **Scholarly tools and source facts:** API tools with fixtures, de-duplication, metadata incl. retraction, the trust table with a first curated list. No agents yet.
2. **Baseline review (variant A) and the reference set** with scoring and the time cut-off: the numbers every later step is compared with.
3. **Screening:** abstract-first, ensemble votes, recall measured (variant B, F).
4. **Roles and the field graph:** experts, lead, acquirer, methodology specialist; variants C, D, E; the honest comparison with B at the same call budget.
5. **Context graph, gap check, stop rules, checkpoints** in the chat, the report.
6. **Answerability calibration** and the learning loop (RV35 to RV37).

## 15. Open questions

1. Which fields first? (The reference set and the first expert roles depend on it; the discussion used electrical engineering, physics, mathematics as an example.)
2. Abstract level only, or full text (open access) from the start? Full text is heavier on small models (RV2) but is where most evidence is.
3. The user's own PDF library as a source: soon or later?
4. Languages of the sources (English first?) and of the report (the user's language, as in chat).
5. Hardware budget per review: how many minutes are acceptable for a first review (an estimate for the screening alone: experts × abstracts × seconds per call; with 3 experts and 40 abstracts about 120 short calls)?
6. Whether the old `/research` keeps its name (quick fact check) and the new task is `/review`.
7. Whether a published report should list the answerability as "x percent" or as bands (low, medium, high) until it is calibrated.
8. Is it acceptable that the first versions use roles as views of one model (RV20), and that different models per role are tested later?

## 16. References

- Smit et al. "Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs." ICML 2024, PMLR 235; arXiv 2311.17371. https://arxiv.org/html/2311.17371v3 (page fetched and summarised by a tool; table values not checked against the PDF).
- Du et al. "Improving Factuality and Reasoning in Language Models through Multiagent Debate" (the Society of Minds method). Known from the Smit et al. comparison, not read here.
- "Language agents achieve superhuman synthesis of scientific knowledge" (PaperQA2, LitQA2). arXiv 2409.13740. Search summaries only.
- "OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs" (ScholarQABench). arXiv 2411.14199. Search summaries only.
- OLIVER, "LLM-Assisted Abstract Screening ... Single-Model vs. Actor-Critic Configurations". arXiv 2512.20022; further screening studies from search results (an ISPOR 2026 poster on local open-weight models; a Can J Psychiatry 2026 study). Summaries only.
- "(Non-)retracted academic papers in OpenAlex." arXiv 2403.13339. Search summary only.
- Evaluation of LLM-written literature reviews (hallucinated references, coverage). arXiv 2412.13612. Listed in search results, not read.
- Cochrane reviews and PRISMA as models for the search log and flow: known, not searched here (a search for Cochrane-based LLM benchmarks found nothing).
