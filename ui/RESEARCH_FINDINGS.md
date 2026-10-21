# Research findings and sources (state of 2026-10-21)

What the literature check for `REQUIREMENTS_RESEARCH.md` established, what it did not, and where each statement comes from. Numbers in brackets refer to the list in section 4.

**How well each source was checked** (the letter follows the reference):
- **R** read by me in the full text (PDF converted to text, passages read).
- **T** full text fetched and read through a tool's summary; I did not read it line by line, numbers not compared with the PDF.
- **P** the arXiv/publisher page (title, authors, abstract, venue) read.
- **S** only a search-result summary seen.
- **M** from memory, not checked in this session.

A statement below is only as good as the weakest check of its sources. Before a number goes into a publication, read the paper.

## 1. Findings

**Multi-agent debate and its alternatives**
- F1. Across seven datasets with GPT-3.5 (and MedQA with GPT-4 and Mixtral 8x7B), no debate protocol (Society of Minds, Multi-Persona, ChatEval) beat the simpler methods reliably; Medprompt (ensembling without debate) was best overall and cheaper; debate costs more calls and tokens [1, T].
- F2. In the paper's analysis of debating behaviour (MedQA only, no numbers in the text) Society of Minds has the largest area over four behaviour measures (consensus accuracy, any agent correct, answer changes, diversity of first answers). That describes the debate, not the final accuracy, where SoM was best or tied on one of seven datasets [1, T].
- F3. Debate is sensitive to its settings. Prompting agents to agree a given share of the time ("agreement modulation") gave about 15 percent for Multi-Persona and about 5 percent for SoM on a USMLE subset, and made Multi-Persona the best protocol on MedQA; the strong result is for MedQA only. The tuned settings transferred to GPT-4 but not well to Mixtral 8x7B [1, T].
- F4. Later work: plain majority voting accounts for most of the gain usually credited to debate, and a theoretical argument says debate alone does not raise expected correctness; changing how agents update their beliefs toward correction made debate more effective [2, P+S]. With 7 to 8 billion parameter models, unguided homogeneous debate did not beat isolated self-correction and used 2.1 to 3.4 times the tokens [3, S]. At equal numbers of responses debate was worse than self-consistency by majority vote [4, P+S].
- F5. Not found: a test of role-specialised agents with different evidence, grounded by checked quotes, on a literature task with small models. Two to four searches per strand, not an exhaustive review.

**Diversity of problem solvers**
- F6. Hong and Page (2004) report, in an agent-based model plus a theorem, that a random group drawn from a diverse pool can beat a group of the best individual performers, because the best performers in a large pool become similar in how they solve problems [5, S].
- F7. The result is contested. Thompson argues the mathematics does not support the strong claims and that the randomness of group formation, not diversity, explains the success [6, S]; Singer defends the diversity reading and asks for a clearer account of functional diversity [8, P]; Grim and colleagues show that the result depends on the landscape: on smoother landscapes ability trumps diversity [7, P]. *Consequence for MIA:* diversity must mean different ways of solving (different roles, different evidence, different tools), not copies of one model; and whether it helps is to be measured, not assumed (variant of the requirements: N copies of the same role against N different roles with the same call budget).

**Contributing views instead of debating**
- F8. STORM asks questions from several perspectives, taken from existing articles on similar topics, against grounded sources. Against an outline-driven retrieval baseline, more articles were judged well organised (+25 percent absolute) and broad (+10 percent); editors found carried-over source bias and unrelated facts wrongly associated [9, P+S].
- F9. Mixture-of-Agents: independent proposers and an aggregator; models answered better when shown other models' answers, even weaker ones; measured on general answer quality [10, P+S].

**Literature agents and screening**
- F10. PaperQA2 reports expert-level results on retrieval, summarisation and contradiction detection and introduces LitQA2 [11, P+S]. OpenScholar and the benchmark ScholarQABench (2,967 expert-written queries and 208 long-form answers in four fields) [12, P+S]. An evaluation of LLM reference generation, abstract writing and review composition [13, P].
- F11. LLM abstract screening: recall depends strongly on the review, prompt and model; most models are specific but miss true includes; a two-model actor-critic improved discrimination and calibration but sensitivity only a little [14, P+S]. Further studies (a 5-model ensemble with about 97 percent recall and 54 percent precision; two broad reviews that never reached 95 percent recall) were seen only in search results and are not listed as references.
- F12. Retraction status: OpenAlex's single `is_retracted` flag misclassified corrections and expressions of concern for part of the data; Crossref has finer status information, partly in an experimental API [15, P+S].

**Vocabulary, discovery across fields, analogies**
- F13. Query expansion by prompting an LLM gives useful extra terms without training [16, P]; an LLM can be asked to write queries in the jargon of other disciplines [17, P]; grounding in trusted vocabularies (MeSH, UMLS) is advised against invented terms (practitioner guide in search results, S). The "vocabulary problem" (Furnas et al., 1987) is the classic statement [M].
- F14. Literature-based discovery (Swanson's "undiscovered public knowledge"; ABC model) finds connections between literatures; classic methods only predict pairwise links between concepts, which motivates LLM work [18, P+S].
- F15. Analogies: representing ideas by purpose and mechanism beat TF-IDF, LSA, LDA and GloVe retrieval on product descriptions [19, P+S]; LLMs struggle to abduce the shared structure of scientific analogies [20, P+S]; abstracting the units before mapping improves LLM analogical reasoning on narratives [21, P]; benchmarks for isomorphic cross-domain problems [22, P] and for interdisciplinary idea recommendation [23, P].
- F16. Not found: a benchmark for "which method of another field solves this problem".

**Verified transfer cases**
- F17. *Squaring the square*: Brooks, Smith, Stone and Tutte (1940) treated a squared rectangle as an electrical network (squares as wires, widths as currents, heights as voltage drops; Kirchhoff's current law); the first perfect squared square was published by Sprague in 1939; the smallest has 21 squares (Duijvestijn, 1978) [24, T].
- F18. *z-transform in an operator setting* (user's example): in Kunisch and Reiterer, Section 3.1 introduces vector valued discrete signals "in analogy to the notation which is used in signal processing"; Appendix A, "Vector Valued z-Transforms and Structural Properties of the Discrete Solution Operator", defines the z-transform of such signals and shows (Lemma A.6) that the z-transform of the discrete solution operator is given through the resolvent R(z) = (I + G_A k(z))^(-1), used to prove Theorem 3.6. The abstract and the introduction do not mention it [25, R].
- F19. *Gröbner bases in continuous optimisation* (user's example): in Bredies, Lorenz and Reiterer, Appendix A.2 "Tools from Algebraic Geometry" says: "We make here use of the theory of Gröbner bases for solving algebraic equations", to prove Proposition 5.1 (discreteness of quasi-global minimizers for rational p) by showing through a reduced Gröbner basis that a variety is finite. The abstract does not mention it [26, R, preprint SFB report 2014-015].
- F20. *Lesson for retrieval from F18 and F19:* both transfers are in appendices or methods sections, not in abstracts, and one of them was missed by a first text search because the source spells "Gröbner" with an umlaut while the query said "Groebner". Abstract-first screening and exact word matching both miss such cases (requirements RV16, RV53).

**Observed while building phase 1 (2026-10-22, live calls and recorded answers; our own observation, not literature)**
- F21. Crossref's standard works answer carries an `updated-by` list with entries of type `retraction` and `correction` (source: Retraction Watch), with dates. For the retracted Lancet paper of 1998 (DOI 10.1016/S0140-6736(97)11096-0) it lists a correction of 2004-03-06 and a retraction of 2010-02-06; the title begins with "RETRACTED:". So the finer status Hauschke and Nazarovets [15] found in a Labs API is now in the main API (recorded in `tests/fixtures/scholar/crossref_retracted.json`). OpenAlex's `is_retracted` flag is therefore only used as a hint.
- F22. Semantic Scholar's unauthenticated search answered HTTP 429 on every attempt on the day of the test (four tries over about a minute), so it is optional and needs a key (`semantic_scholar_key`); the recorded answer is `semanticscholar_429.json`. arXiv's API redirects http to https and was slow (a read timeout at 20 seconds in one live run).
- F23. Retraction notices come back as records of their own (PubMed: "Retraction--Ileal-lymphoid-nodular hyperplasia ..."), so they must be recognised and excluded as evidence.
- F24. Per-source relevance differs strongly for the same query: OpenAlex ranked Tutte's 1950 "Squaring the Square" first for "electrical network squared square dissection"; Crossref and PubMed returned loosely related items (mean squared error, neural network activity). Screening (phase 3) is needed; plumbing alone does not give a review.

## 2. What is not established

- That Society of Minds (or any debate) helps small models on literature tasks: open (F5). The evidence for unguided homogeneous agents is negative (F4).
- That experts of related fields find sources a single model misses (H0 of the requirements), and that a transfer scout finds methods of other fields: untested (F5, F16).
- That an answerability percentage can be calibrated: untested.
- Numbers in F1 to F3 are from a tool's reading of the paper page; F4 to F15 from abstracts and search summaries. None of F6 to F15 has been read in the full text.

## 3. Why this is a research project and not an engineering task

The benchmark of the requirements (published reviews, date cut-off, historical transfers) is meant to produce the missing evidence. Negative results (voting among roles is as good as debate; no gain from aliases) are results too and keep the cheaper method.

## 4. References

1. Smit, A., Duckworth, P., Grinsztajn, N., Barrett, T. D., Pretorius, A. (2024). Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs. *Proceedings of the 41st International Conference on Machine Learning (ICML)*, PMLR 235. arXiv:2311.17371 (v3, 18 Jul 2024). https://arxiv.org/abs/2311.17371 · https://proceedings.mlr.press/v235/smit24a.html [T; venue from the PMLR page]
2. Choi, H. K., Zhu, X., Li, S. (2025). Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models? NeurIPS 2025 (Spotlight). arXiv:2508.17536. https://arxiv.org/abs/2508.17536 [P; the 7B table values come from a search summary]
3. Bertalanič, B., Fortuna, C. (2026). The Cost of Consensus: Isolated Self-Correction Prevails Over Unguided Homogeneous Multi-Agent Debate. arXiv:2605.00914; listed for ACM CAIS 2026. https://arxiv.org/pdf/2605.00914 [S]
4. Huang, J., Chen, X., Mishra, S., Zheng, H. S., Yu, A. W., Song, X., Zhou, D. (2024). Large Language Models Cannot Self-Correct Reasoning Yet. ICLR 2024. arXiv:2310.01798. https://arxiv.org/abs/2310.01798 [P+S]
5. Hong, L., Page, S. E. (2004). Groups of diverse problem solvers can outperform groups of high-ability problem solvers. *Proceedings of the National Academy of Sciences* 101(46), 16385-16389. https://doi.org/10.1073/pnas.0403723101 · https://pmc.ncbi.nlm.nih.gov/articles/PMC528939/ [S; the publisher page refused access]
6. Thompson, A. (2014). Does Diversity Trump Ability? An Example of the Misuse of Mathematics in the Social Sciences. *Notices of the American Mathematical Society* 61(9), 1024 ff. https://doi.org/10.1090/noti1163 [S; title and page from a search summary and a library record, to be checked]
7. Grim, P., Singer, D. J., Bramson, A., Holman, B., McGeehan, S., Berger, W. J. (2019). Diversity, Ability, and Expertise in Epistemic Communities. *Philosophy of Science* 86(1), 98-123. https://doi.org/10.1086/701070 [P]
8. Singer, D. J. (2019). Diversity, Not Randomness, Trumps Ability. *Philosophy of Science* 86(1), 178-191. https://doi.org/10.1086/701074 [P]
9. Shao, Y., Jiang, Y., Kanell, T. A., Xu, P., Khattab, O., Lam, M. S. (2024). Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models (STORM). *NAACL 2024 (Main)*. arXiv:2402.14207. https://arxiv.org/abs/2402.14207 [P+S; the percentages from a search summary]
10. Wang, J., Wang, J., Athiwaratkun, B., Zhang, C., Zou, J. (2024). Mixture-of-Agents Enhances Large Language Model Capabilities. arXiv:2406.04692. https://arxiv.org/abs/2406.04692 [P+S]
11. Skarlinski, M. D., Cox, S., Laurent, J. M., Braza, J. D., Hinks, M., Hammerling, M. J., Ponnapati, M., Rodriques, S. G., White, A. D. (2024). Language agents achieve superhuman synthesis of scientific knowledge. arXiv:2409.13740. https://arxiv.org/abs/2409.13740 [P+S]
12. Asai, A., He, J., Shao, R., Shi, W., Singh, A., et al. (25 authors) (2024). OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs. arXiv:2411.14199. https://arxiv.org/abs/2411.14199 [P+S]
13. Tang, X., Duan, X., Cai, Z. G. (2025). Large Language Models for Automated Literature Review: An Evaluation of Reference Generation, Abstract Writing, and Review Composition. EMNLP 2025 (Main). arXiv:2412.13612. https://arxiv.org/abs/2412.13612 [P]
14. Godhwani, K., Benrimoh, D. (2025). LLM-Assisted Abstract Screening with OLIVER: Evaluating Calibration and Single-Model vs. Actor-Critic Configurations in Literature Reviews. arXiv:2512.20022. https://arxiv.org/abs/2512.20022 [P+S]
15. Hauschke, C., Nazarovets, S. (2024; Journal of Information Science 2025). (Non-)retracted academic papers in OpenAlex. arXiv:2403.13339. https://arxiv.org/abs/2403.13339 [P+S]
16. Jagerman, R., Zhuang, H., Qin, Z., Wang, X., Bendersky, M. (2023). Query Expansion by Prompting Large Language Models. arXiv:2305.03653. https://arxiv.org/abs/2305.03653 [P]
17. Zheng, C., Zhang, Y., Huang, Z., Shi, C., Xu, M., Ma, X. (2024). DiscipLink: Unfolding Interdisciplinary Information Seeking Process via Human-AI Co-Exploration. arXiv:2408.00447. https://arxiv.org/abs/2408.00447 [P+S]
18. Alkan, A. K., Sourav, S., Jablonska, M., et al. (17 authors) (2025). A Survey on Hypothesis Generation for Scientific Discovery in the Era of Large Language Models. arXiv:2504.05496. https://arxiv.org/abs/2504.05496 [P+S]; Swanson's ABC model from search summaries (Wikipedia, Elicit blog) [S]
19. Hope, T., Chan, J., Kittur, A., Shahaf, D. (2017). Accelerating Innovation Through Analogy Mining. KDD 2017 (also IJCAI 2018). arXiv:1706.05585. https://arxiv.org/abs/1706.05585 [P+S]
20. Yuan, S., Chen, J., Ge, X., Xiao, Y., Yang, D. (2023). Beneath Surface Similarity: Large Language Models Make Reasonable Scientific Analogies after Structure Abduction (SCAR). Findings of EMNLP 2023. arXiv:2305.12660. https://arxiv.org/abs/2305.12660 [P+S]
21. Khojasteh, M., Jiang, Y., De Giorgis, S., van Harmelen, F., Ilievski, F. (2026). Enhancing Structural Mapping with LLM-derived Abstractions for Analogical Reasoning in Narratives (YARN). arXiv:2603.29997. https://arxiv.org/abs/2603.29997 [P+S]
22. Abdaljalil, S., Serpedin, E., Kurban, H. (2026). IsoSci: A Benchmark of Isomorphic Cross-Domain Science Problems for Evaluating Reasoning versus Knowledge Retrieval in LLMs. arXiv:2607.01431. https://arxiv.org/abs/2607.01431 [P]
23. Shen, Y., de Sousa, D. X., Marçal, R., Guo, H., Zhu, X. (2025). IDRBench: Understanding the Capability of Large Language Models on Interdisciplinary Research. arXiv:2507.15736. https://arxiv.org/abs/2507.15736 [P]
24. Squaring the Square. logicpuzzles.ca/blog/squaring-the-square (read 2026-10-21). The original: Brooks, R. L., Smith, C. A. B., Stone, A. H., Tutte, W. T. (1940). The dissection of rectangles into squares. *Duke Mathematical Journal* 7, 312-340 [M, not checked]. [T for the blog]
25. Kunisch, K., Reiterer, S. A Gautschi Time-stepping Approach to Optimal Control of the Wave Equation. Preprint, Institute for Mathematics and Scientific Computing, University of Graz. https://static.uni-graz.at/fileadmin/_files/_homepages/_karl_kunisch/Papers/278_KK.pdf [R; place and year of the journal version not checked]
26. Bredies, K., Lorenz, D. A., Reiterer, S. (2015). Minimization of Non-smooth, Non-convex Functionals by Iterative Thresholding. *Journal of Optimization Theory and Applications* 165(1), 78-112. https://doi.org/10.1007/s10957-014-0614-7 · preprint: SFB-Report No. 2014-015, Karl-Franzens-Universität Graz, https://imsc.uni-graz.at/mobis/publications/SFB-Report-2014-015.pdf [R for the preprint; the journal version was not read]
