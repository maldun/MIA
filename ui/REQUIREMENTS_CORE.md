# MIA core: tasks, skills and pipelines for small models (requirements, draft 1)

Status: draft for review, nothing of this is built yet. It follows `REQUIREMENTS_CHAT.md` (chat page) and `REQUIREMENTS.md` (character).
The project has a research character: the question is how much quality a small, free, local model can reach for everyday tasks when it is
embedded in clever pipelines with verification, small helper models and a little learning. Every decision below should therefore be
**measurable** (see 9, evaluation).

## 1. Principles

1. **Free and local.** Ollama models, SearXNG for search, no paid API. Hardware is the limit (RX 7700 XT with 12 GB, Ryzen 9 5900X, 62 GB RAM;
   `gemma4:12b-it-qat` as light and `gemma4:26b` as full model, both with `num_ctx` 8192 today).
2. **A task is a skill file plus a pipeline, not a model.** The same model serves all tasks with different prompts, budgets and tools. Other models
   (for example Qwen for long contexts) can be assigned per skill.
3. **Pipelines are data.** A pipeline is a small graph in JSON; prompts, budgets and tools live in the skill file. Code only provides the building blocks.
4. **Narrow steps, structured outputs.** Small models are weak at long instructions and strong at one clear step. Every model step that feeds a later
   step uses constrained decoding (JSON schema), as the expression generator already does.
5. **Code verifies what code can verify** (formats, dates, overlaps, quotes present in the source). The model verifies only what code cannot.
6. **Everything is visible and logged.** Each run emits a stream of events (shown live in an expandable block) and is stored with its inputs, outputs,
   timings and your feedback. This is the basis for evaluation and for any learning.
7. **Web content is untrusted data.** Fetched pages never act as instructions (see 11).
8. **Budgets are explicit.** Steps, seconds, search calls and tokens per run; a run that exceeds them ends with what it has and says so.

Non-goals for now: legs and feet of the character, fine-tuning the Gemma model, multi-user operation, a generic workflow engine.

## 2. Tasks

| Task | Goal | Pipeline | Tools | "Good" means |
|---|---|---|---|---|
| `chat` | quick, warm, in character | one pass (optional polish) | memory | answer in a few seconds, persona kept, no invented facts about the user |
| `storytelling` | long, coherent, creative, interactive | premise card, outline, scene loop with story state and checks | story state | consistency over many scenes, variety, the user steers each scene |
| `research` | accurate answers with sources | plan, search, read, extract, synthesize, verify | SearXNG, page fetch | every claim has a source passage; unknown stays unknown |
| `schedule` | structured plans | parse, constrain, validate | time functions | valid JSON, no overlaps (checked by code) |

Order of work (user decision): **research and storytelling first**, `chat` is moved onto the new runner as the simplest reference, `schedule` follows.
Candidates for later: summarize, translate, "think it through" (puzzles, maths).

The active task is chosen by the user first (menu, slash command, character variant). Automatic routing (see 8) comes later and starts as a suggestion.
Tasks may call each other (chat can call research: "look that up").

## 3. Skill files

One file per skill in `skills/` (Markdown with YAML front matter, plain text so that it can be versioned, diffed and edited by hand or by a model).

```
---
name: research
version: 1
description: answer factual questions with sources
triggers: ["look up", "find out", "is it true"]     # hints for the router, not hard rules
model: {profile: full, options: {num_ctx: 16384}}   # or another model name, for example a Qwen
pipeline: research                                  # file in pipelines/ (see 4)
tools: [web_search, fetch_page]
budget: {steps: 12, seconds: 180, search_calls: 6, fetch_calls: 10}
variant: researcher                                 # character variant shown while this task runs (see 7)
voice: calm
---
## prompts
### plan
...
### extract
...
## schemas
(JSON schemas for the structured outputs)
## examples
(few-shot cases per stage, kept short)
```

Requirements:
- S1. Skills are loaded at start and reloaded on file change; a broken file is reported in the log and does not stop MIA.
- S2. Every prompt stage names its schema; a missing schema is an error at load time, not at run time.
- S3. A skill has a version; each logged run records the skill and pipeline versions it used (needed for comparisons).
- S4. A skill can override model, options (context size, temperature), tools and budgets.

## 4. Pipelines as data

A pipeline is a directed graph (JSON) of steps. Kinds of nodes:
`model` (prompt stage with schema), `tool` (search, fetch, calendar), `code` (deterministic function), `map` (run a node for each item, in parallel when it
is cheap), `branch` (condition on a field), `loop` (repeat a sub-graph until a condition or a limit), `ask_user` (pause for the user, used by storytelling).

- P1. The runner executes the graph, enforces the budgets, and emits an event for each node start, finish, retry and error.
- P2. Nodes pass typed values (the schemas of 3); a node can only read what earlier nodes produced.
- P3. Failures are local: a node can retry with a stricter prompt, fall back to a default or end the run with a clear message.
- P4. The graph has no code execution from outside: new graphs are validated against a schema (node kinds, known tools, known functions, loop limits).
- P5. The runner is independent of the UI and testable with a fake model (like `FakeServer` in the character tests).
- P6. Graphs can be rendered as a diagram (viewer first, editor later, see 10).

## 5. Status events and the visible block

Each event has: run id, node id, kind (`start`/`done`/`retry`/`error`/`note`), a **playful line** and a **plain description** (shown in brackets),
timing and optionally a small payload (query text, URL, claim, score).

Examples: "Rummaging through the internet… (search: 'rust borrow checker', 3 queries)",
"Squinting at the sources… (extracting passages, page 4 of 9)", "Rereading my own homework… (verifying claim 5 of 8: supported)".

- E1. The chat shows one expandable block per answer ("how I got there"), live while the run is active, collapsed by default afterwards, kept in the chat log.
- E2. The playful lines come from the skill file (several variants per node kind, picked at random); the bracketed text is generated from the real event data and is always accurate.
- E3. A stage can set an expression and gesture on the character (thinking while reasoning, a hand movement when sources are found). Mapping lives in the skill file.
- E4. The user can stop a run at any time; partial results stay visible.
- E5. The event stream is the same data that is logged (8, 9), so the block and the evaluation never disagree.

## 6. Models and hardware

- M1. Models are chosen per skill (profile `light` or `full`, or a named model). The runner loads and unloads through Ollama and reports which model is active.
- M2. Slow, long-context models (for example a Qwen with a large context) are allowed for background-style tasks (research, long stories). The status block must
  make waiting bearable. Chat stays on the fast model.
- M3. Context size is a per-skill option. The cost of long contexts on a 12 GB card is real (the KV cache grows with the context; weights that do not fit run partly from
  RAM and are slow), so every skill has a measured timing in the test report (9) and the default context is the smallest one that works.
- M4. Long texts are never pushed whole into the context: pages and stories are cut into chunks, summarised and indexed (retrieval beats stuffing; models also use the
  middle of a long context worse than its ends, Liu et al. 2023).
- M5. Embedding and classifier helpers (small models, see 8) run on the CPU so the GPU stays free for the language model.

## 7. Character variants (visual mode indicator)

The same VRM model gets **variants**: different accessories, clothes or colours, each standing for a task (for example glasses and a notebook for research, a hat
or cloak for storytelling). The variant shows at a glance which mode is active.

- V1. A variant is data (a JSON document, stored like presets and gestures on the server with the same token and API rules): a list of mesh parts shown or hidden, material
  colour or texture overrides, optionally a default expression bias and a default idle gesture.
- V2. Skills name a variant; switching the task switches the variant, with a short animation (spin, flash or puff, to be decided). The user can also switch manually.
- V3. A variant editor in the character page (like the expression and gesture editors): toggle parts, pick colours, name and save, preview live.
- V4. No second model file is needed as long as variants only toggle parts and change materials; this requires that the VRM has separable meshes for accessories and
  clothes. **Open:** inspect the mesh and material names of the current model (`ui/godot/tools`, inspect step) and decide if a few meshes must be added in Blender.
- V5. The chat page shows the active task (small label or colour) next to the character so the state is visible without the 3D view.
- V6. More variants can be added later without code changes (data only).

## 8. Auxiliary models and learning (a ladder, each step only when the previous gives data)

0. **Rules and logging.** Logging of every run first (9). Task routing by explicit choice; trigger words only suggest.
1. **Small classifier router.** Sentence embeddings (CPU) plus logistic regression or a small MLP, trained on the logged conversations and your corrections.
   Suggests the task; the user can accept or overrule; the corrections become training data.
2. **Contextual bandit for pipeline variants.** Per task a handful of variants (self-review on/off, number of samples 1/3, search depth 1/2, which model).
   Thompson sampling or LinUCB over features of the request; the reward comes from cheap signals (thumbs, regenerate, edits, verifier pass rate, time).
   Bandits learn from tens of samples, which a single user can produce; full RL needs far more.
3. **Learned verifier or reward model.** A small model that scores answers or single claims (trained on your ratings and on automatic labels from code checks).
   This turns best-of-N and self-review from a hope into a tool, and it is itself a research object (calibration and precision, see 9).
4. **Learned controller** (when to search again, when to stop, when to escalate to a bigger model) trained offline on logged trajectories, with a cost-aware
   stop action. Only if levels 1–3 are in place and the logs are large enough.
5. **Distillation.** Use slow pipelines (best-of-N plus review) to produce good answers and use them to fine-tune a small adapter, so that one pass reaches the quality
   of many. Optional and last.

Requirements: every learned component is optional and can be switched off; the system works with fixed defaults; learned decisions are logged next to the default
decision, so they can be compared offline before they are trusted.

## 9. Evaluation and logging (what makes it research)

- L1. Every run is stored (JSONL in `data/runs/`): task, skill/pipeline versions, model, all node inputs and outputs, events with timings, the final answer, and the user
  feedback (thumbs, edit, regenerate, free note). Sensitive content stays on the machine.
- L2. A fixed **test set** per task (about 30 cases for research and storytelling at first, written by the user and the assistant, with notes on what a good answer is).
  Research cases include questions with a known answer, questions without an answer, and questions whose popular answer is wrong.
- L3. A harness runs a pipeline variant on the test set offline and reports quality, time and token use. Variants are compared on the same cases and seeds.
- L4. Quality is measured by several kinds of signal and never by a single one: code checks (format, quote present in source, dates), claim-level support against sources,
  an LLM judge with a rubric (calibrated against the user's own ratings, see 12), and pairwise user preferences.
- L5. For verifiers (the research object) the harness also reports: precision and recall of "unsupported" flags, calibration of confidence, agreement between verifiers,
  and what fraction of errors the verifier shares with the generator.

## 10. Graph viewer and editor

- G1. Viewer first: the pipeline graph is drawn, the current node is highlighted live during a run (the same events as the status block).
- G2. Editor second: edit prompts, budgets, tools, add or remove nodes in a validated way (P4); changes are saved as a new version of the pipeline, not in place.
- G3. Edits by a model (MIA or an assistant) are **proposals**: shown as a diff, checked against the test set (L3) in a dry run, applied only after user approval.
  Rationale: this makes "optimise the pipeline on the fly" safe and measurable, and it prevents the self-improvement loop from rewarding itself (Goodhart effect, see 12).
- G4. Technology is open (web view in the character page or a separate page). Existing open-source editors (for example NodeTool, PySpur, LangGraph-GUI) are references, not
  dependencies.

## 11. Security and robustness

- X1. Text from the web, files and users is data. It is placed in clearly delimited fields; stage prompts say that it contains no instructions; stages that act on it have
  narrow tools and schemas (prompt injection cannot be solved by prompting alone, so the tool set per stage is the real protection).
- X2. Web access only through the search/fetch tools with timeouts, size limits, a content-type filter and no execution of scripts; private addresses (localhost, LAN) are blocked.
- X3. A run never writes outside `data/`. Skill and pipeline files are read-only for models; changes go through proposals (G3).
- X4. The search tool logs every query (to the run log), so it can be checked what MIA asked the internet.

## 12. Verification: background and design consequences

This section collects the ideas the design is built on. (References in 14.)

**What does "verified" mean?** Four levels, from strong to weak:
1. *Deterministic checks.* Code decides: JSON validity, arithmetic, dates, overlaps, "this quote occurs in the page". These are cheap, exact and should be used wherever possible.
   Formal verification proper (proofs, model checking) is out of reach for free text, but the principle carries over: reduce the part that needs trust to the smallest possible kernel.
2. *Grounded verification.* A claim is checked against evidence (retrieved passages): is it entailed, contradicted or not mentioned? This is the core of attribution and citation work
   (Rashkin et al., Gao et al. RARR, Min et al. FActScore, Liu et al., Gao et al. ALCE). It is only as good as the retrieval and the entailment judge.
3. *Uncertainty-based checks.* No external evidence: sample several answers and see whether they agree (Wang et al. self-consistency; Manakul et al. SelfCheckGPT; Kuhn et al. and
   Farquhar et al. semantic entropy; Kadavath et al. "models know what they know"). Agreement is evidence of stability, not of truth; a model can be consistently wrong.
4. *Learned verifiers and judges.* A model scores answers or steps (Cobbe et al. outcome verifiers; Lightman et al. process supervision; Zheng et al. LLM-as-a-judge). They generalise
   imperfectly, show biases (position, length, self-preference), and can be exploited by the generator that is optimised against them (Gao et al., reward overoptimization).

**Why a model cannot simply check itself.** Huang et al. (2023) and Kamoi et al. (2024) show that intrinsic self-correction, without external feedback, often does not improve and can degrade
reasoning; improvements reported by earlier work were often due to oracle feedback or weak baselines. Self-Refine (Madaan et al.) and Reflexion (Shinn et al.) work best where there is a
reliable signal (tests, rules, retrieved evidence). The generator-verifier errors are correlated, because they share weights and training data. Consequences for MIA:
- Self-review is used with a **checklist or evidence** (sources, rules, code results), not as a free "is this right?".
- For research, the verifier sees only the claim and the source passage, not the draft (reduces anchoring on the draft; the Chain-of-Verification idea of independent answering).
- Whenever possible the verifier is a **different** model or a different prompt/view than the generator (diversity lowers shared errors). With Gemma 12B and 26B plus a Qwen this is
  available for free.
- Verification costs are scaled with difficulty (Snell et al., test-time compute): easy questions get one pass, uncertain ones more samples or a second round of search.

**Search-time compute vs. sampling.** Brown et al. (Large Language Monkeys) show that coverage grows with the number of samples, but picking the right one needs a verifier; without it,
majority vote saturates. That is why verifier quality (L5) is the limiting factor and why we measure it.

**Calibration.** A verifier that says "supported" must be right about as often as it says it (Guo et al. on calibration). The harness reports reliability curves, not only accuracy.
For the user-facing answer, "unknown" and "unverified" are first-class outcomes.

**Goodhart and self-improvement.** Once a learned component (reward model, bandit, pipeline editor) optimises against a score, it finds the weaknesses of the score. Mitigations here:
hold-out test cases that are never used for tuning, several independent signals (L4), user spot checks, and the approval gate of G3.

**Research questions this project can answer** (candidate notes for the user's own research):
- How much does claim-level grounded verification improve factual precision of a 12–26B local model with search, and at what cost in time?
- Does a verifier of a different model family reduce shared errors compared with self-verification?
- Which cheap signals (logged user behaviour) correlate with the claim-level quality, so they can serve as reward for the bandit?
- Does a bandit over pipeline variants beat the best fixed variant on the user's own tasks within a realistic number of interactions?

## 13. Task details (first two)

### 13.1 Research
Pipeline (each node one narrow step; `map` where written):
1. `understand`: rewrite the question; decide if search is needed at all (otherwise answer directly with a note "from memory, not verified").
2. `plan`: 2–4 search queries with the aspect each covers (schema: list of {query, purpose}).
3. `search`: SearXNG, merged and de-duplicated results, top N by simple scoring (code).
4. `fetch`: page text cleaned (code), cut into chunks.
5. `extract` (map over chunks of the top pages): passages that answer the aspects, copied **verbatim** with the URL (code checks that the quote occurs in the page).
6. `synthesize`: answer in the user's language written only from the extracted passages, with numbered sources; claims as a list so they can be checked.
7. `verify` (map over claims): supported / contradicted / not found in the cited passage; the verifier sees claim and passage only.
8. `repair`: unsupported claims are removed or marked "unverified"; contradictions trigger one more search round if budget allows (loop, limit 2).
9. `report`: final answer, source list, a short honesty line (what could not be verified), and the status block.

SearXNG: self-hosted, JSON output enabled, results from several engines; only the query leaves the machine and it reaches the upstream engines from the user's IP without cookies.
Rate limits and blocks by upstream engines are possible, so the tool retries with other engines and reports failures in the block.
**Fallback:** DuckDuckGo (no install) is a second search backend behind the same tool interface. It is used when SearXNG is not reachable or returns nothing, and the status block
says which backend answered. Its downsides (no official free API, scraped endpoints that can break or be rate limited, a single engine, fewer filters) are accepted for a fallback;
the backend is selected per skill in the config (`search_backends: [searxng, duckduckgo]`).

Acceptance: on the research test set the pipeline gives (a) no quote that is not in its source, (b) "unknown" on questions without an answer in most cases, (c) a measurable gain in claim
support over the direct answer of the same model.

### 13.2 Storytelling (interactive first)
State files per story (`data/stories/<id>/`): `premise.json` (genre, tone, setting, rules, style samples), `characters.json`, `outline.json`, `state.json` (who is where, inventory, time,
open threads, facts established), `scenes/NNN.md`, `summaries.json`.
Loop per scene:
1. `propose`: three short options for how the story could continue (schema), shown to the user (interactive). The user picks, edits or writes their own line (`ask_user`).
2. `plan_scene`: beats for this scene from the outline, the state and the chosen direction.
3. `draft`: the scene is written from beats + state + the summary of the last scenes + the last few paragraphs (not the whole text).
4. `update_state`: structured extraction of what changed (code merges it into `state.json`).
5. `check`: code and a short prompt compare the new scene with the state (characters in two places, dead characters speaking, broken rules); one repair attempt with the conflicts listed.
6. `summarize`: scene summary for the memory; the outline is adjusted when the story moves away from it (dynamic outline, DOME-like).
Options: polish pass for style, "continue on its own for N scenes" (later), read aloud with the voice, character expressions follow the scene mood.

Acceptance: a story over 20+ scenes keeps names, places and facts consistent in the test set checks; the state file alone is enough to resume after a restart.

## 14. References

Marked [S] were found in the web search of this project phase (2026 papers: claims are from search summaries and must be read before they are relied upon). The others are
fundamental sources from the author's knowledge, **to be checked for exact titles and numbers before citing them in any publication**.

Reasoning, tools, pipelines
- Wei et al. 2022, Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. arXiv:2201.11903
- Wang et al. 2022, Self-Consistency Improves Chain of Thought Reasoning. arXiv:2203.11171
- Yao et al. 2022, ReAct: Synergizing Reasoning and Acting in Language Models. arXiv:2210.03629
- Yao et al. 2023, Tree of Thoughts. arXiv:2305.10601
- Schick et al. 2023, Toolformer. arXiv:2302.04761
- Willard & Louf 2023, Efficient Guided Generation for LLMs (constrained decoding). arXiv:2307.09702
- Liu et al. 2023, Lost in the Middle: How Language Models Use Long Contexts. arXiv:2307.03172

Self-correction, verification, judges
- Cobbe et al. 2021, Training Verifiers to Solve Math Word Problems. arXiv:2110.14168
- Lightman et al. 2023, Let's Verify Step by Step. arXiv:2305.20050
- Madaan et al. 2023, Self-Refine. arXiv:2303.17651
- Shinn et al. 2023, Reflexion. arXiv:2303.11366
- Dhuliawala et al. 2023, Chain-of-Verification Reduces Hallucination in LLMs. arXiv:2309.11495
- Huang et al. 2023, Large Language Models Cannot Self-Correct Reasoning Yet. arXiv:2310.01798
- Kamoi et al. 2024, When Can LLMs Actually Correct Their Own Mistakes? arXiv:2406.01297
- Zheng et al. 2023, Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. arXiv:2306.05685
- Gao, Schulman, Hilton 2022, Scaling Laws for Reward Model Overoptimization. arXiv:2210.10760
- [S] Refining Over Resampling: Test-Time Self-Correction for LLM Reasoning (2026). arXiv:2608.05643
- [S] Self-Trained Verification for Training- and Test-Time Self-Improvement (2026). arXiv:2605.30290
- [S] FineVerify: Fine-Grained Self-Verification for Agentic Search (2026). arXiv:2606.00660
- [S] Multi-Agent Verification: Scaling Test-Time Compute with Multiple Verifiers (2025). arXiv:2502.20379

Test-time compute
- Snell et al. 2024, Scaling LLM Test-Time Compute Optimally Can Be More Effective than Scaling Model Parameters. arXiv:2408.03314
- Brown et al. 2024, Large Language Monkeys: Scaling Inference Compute with Repeated Sampling. arXiv:2407.21787

Grounding, attribution, hallucination, uncertainty
- Ji et al. 2022, Survey of Hallucination in Natural Language Generation. arXiv:2202.03629
- Rashkin et al. 2021, Measuring Attribution in Natural Language Generation Models. arXiv:2112.12870
- Gao et al. 2022, RARR: Researching and Revising What Language Models Say, Using Language Models. arXiv:2210.08726
- Min et al. 2023, FActScore. arXiv:2305.14251
- Liu et al. 2023, Evaluating Verifiability in Generative Search Engines. arXiv:2304.09848
- Gao et al. 2023, ALCE: Enabling LLMs to Generate Text with Citations. arXiv:2305.14627
- Asai et al. 2023, Self-RAG. arXiv:2310.11511
- Manakul et al. 2023, SelfCheckGPT. arXiv:2303.08896
- Kadavath et al. 2022, Language Models (Mostly) Know What They Know. arXiv:2207.05221
- Kuhn et al. 2023, Semantic Uncertainty. arXiv:2302.09664; Farquhar et al. 2024, Nature, Detecting hallucinations in LLMs using semantic entropy
- Guo et al. 2017, On Calibration of Modern Neural Networks. arXiv:1706.04599

Routing and learning
- Chen et al. 2023, FrugalGPT. arXiv:2305.05176
- Ong et al. 2024, RouteLLM. arXiv:2406.18665
- Li et al. 2010, A Contextual-Bandit Approach to Personalized News Article Recommendation (LinUCB). arXiv:1003.0146
- Russo et al. 2018, A Tutorial on Thompson Sampling. arXiv:1707.02038
- [S] OrcaRouter: A Production-Oriented LLM Router (2026). arXiv:2605.30736
- [S] SearchSkill (2026), arXiv:2605.09038; RL for LLM Multi-Agent Systems through Orchestration Traces (2026), arXiv:2605.02801

Storytelling
- Yang et al. 2022, Re3: Generating Longer Stories With Recursive Reprompting and Revision. arXiv:2210.06774
- Yang et al. 2022, DOC: Improving Long Story Coherence With Detailed Outline Control. arXiv:2212.10077
- [S] DOME: Dynamic Hierarchical Outlining with Memory-Enhancement (ACL 2025). arXiv:2412.13575
- [S] ConWriter (2026). arXiv:2608.05169

Local research agents (implementations to learn from)
- [S] LearningCircuit/local-deep-research; langchain-ai/local-deepresearcher; OpenDeepResearcher-via-searxng (GitHub)

## 15. Phases (proposal)

1. **Foundation**: run log (L1), event stream (E), pipeline runner with fake model tests (P), skill loader (S); `chat` ported as the reference skill. Status block in the chat page.
2. **Research**: SearXNG setup, tools with the safety rules (X), the research pipeline and its test set; harness (L3); first comparisons (direct vs. pipeline, with/without verify).
3. **Storytelling**: story state, scene loop, interactive UI; test set with consistency checks.
4. **Variants**: inspect the VRM parts (V4), variant store and API, editor, switching with the task.
5. **Graph viewer**, then editor with proposals (G).
6. **Routing and learning** (8, levels 1–3), `schedule` skill.
7. Optional: controller and distillation (8, levels 4–5).

## 16. Open questions

- Which meshes does the VRM have for accessories and clothes (V4)? Do we need additions in Blender?
- Which Qwen model and context length are usable on 12 GB with acceptable speed (to be measured with the harness, M3)?
- Language: research answers in the question's language; the sources may be English. Where is translation done, and does it hurt claim checking?
- Which feedback controls does the chat page get (thumbs, "wrong source", edit) to feed L1 without annoying the user?
- Does the status block also show for chat (probably only for runs longer than a few seconds)?
