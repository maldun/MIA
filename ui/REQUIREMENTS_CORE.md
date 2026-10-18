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

## 4a. The library: nodes and pipelines as a growing knowledge base

Pipelines (4) and the pieces they are made of are not buried in skill files: they live in a **library** of reusable, versioned, documented entries from which a task
pulls what it needs. The checks of 12.2, the verification styles of 12.1 and the model views are entries of this library, not special code. Over time the library is the
knowledge base of what works for which kind of task (and the thing the learning ladder of 8 and the harness of 9 operate on).

**Two kinds of entries**

| Entry | What it is | Examples |
|---|---|---|
| **node** | one reusable step with a declared interface | `check.quote_in_source`, `check.date_arithmetic`, `check.script_sandbox`, `check.web_confirm`, `view.entailment`, `view.prosecutor`, `view.juror_numbers_only`, `tool.web_search`, `code.chunk_text` |
| **pipeline** | a graph that wires nodes (by reference) and sets their parameters | `research_v1`, `verify.single`, `verify.trial`, `verify.jury_experts`, `story.scene_loop` |

A node entry (one JSON file, immutable once it has a version number above 0):

```
{ "id": "check.quote_in_source", "version": 2, "kind": "code",            # kind: model | tool | code | script | ask_user (the node kinds of 4)
  "title": "Quote occurs in the source", "description": "...",
  "tags": ["check", "citation", "exact"], "applies_to": {"claim_types": ["quotation", "citation"], "tasks": ["research"]},
  "inputs":  {"schema": {...}},  "outputs": {"schema": {...}},           # JSON schemas: wiring is validated against them
  "params":  {"normalize_space": {"default": true}},
  "body":    {"function": "quote_in_source"},                            # or a prompt template + schema (model), or a script (script)
  "needs":   {"tools": [], "sandbox": false, "model": null},
  "cost":    {"tokens": 0, "seconds": 0.01, "calls": {}},                # an estimate; measured values come from the run log
  "safety":  {"reads_web": false, "runs_code": false},
  "status":  "trusted",                                                  # draft | tested | trusted | retired
  "origin":  {"by": "manual", "parent": null, "created": "...", "note": "..."} }
```

A pipeline entry is the format of 4 with two additions: nodes can be **references** (`{"id": "q1", "use": "check.quote_in_source@2", "params": {...}, "wire": {...}}`)
as well as inline nodes, and a header with `tags`, `applies_to`, `goal`, `cost_class`, `status`, `origin` (with `parent` for lineage: which pipeline it was derived from and why).

**Storage: files are the truth, a database is the index.**
- L1. Entries are files: `library/nodes/<id>/<version>.json` and `library/pipelines/<id>/<version>.json` for the shipped ones (in the repository, reviewed with git) and the same
  structure under `data/library/` for the user's and for model-made ones. Plain text, diffable, editable by hand, easy to share.
- L2. A SQLite index (`data/library.sqlite`) is built from the files and can be deleted and rebuilt at any time. It holds the searchable fields (id, version, kind, tags, applies_to,
  status, cost), the dependency graph (which pipeline uses which node version), and the **statistics** (see below). SQLite because it is in the standard library, needs no server and
  is enough for thousands of entries. Semantic search over descriptions (embeddings, computed on the CPU, 6) is a later addition to the same index, not a different store.
- L3. Versions are immutable: a changed node or pipeline is a new version; runs refer to `id@version` (the run log already records pipeline and skill versions, it gains the node
  versions), so every earlier run and evaluation stays reproducible. `retired` entries stay readable.
- L4. Skills (3) refer to pipelines of the library by `id` (or `id@version`, or a selector, see below) and keep what is about the task as a whole: persona, model profile, budget,
  triggers, variant, voice, lines of the status block. Prompts of model nodes move into the library nodes (views); the skill may still override parameters.
- L5. Inline nodes (as in the current pipelines) remain allowed for experiments; a command promotes an inline node or a whole pipeline into the library as a draft.

**Pulling from the library ("selection")**
- L6. A selector asks for entries by a task description: `{"kind": "pipeline", "tags": ["verify"], "applies_to": {"claim_type": "numeric"}, "max_seconds": 60, "stakes": "low"}`.
  The library answers with candidates, ranked. Ranking, in order of introduction: (1) hard filters (status, applicability, tools available, sandbox available, budget); (2) the measured
  statistics of the candidates for this kind of task (quality, cost, time) from the harness and the run log; (3) later a contextual bandit over the candidates (8, level 2) with exploration
  limited to `tested` entries.
- L7. The research pipeline does not hard-code its checks: a `select` step asks the library which checks apply to each extracted claim (numeric, date, quotation, citation, plain fact),
  runs the hard ones first and passes the open claims on to a verification style chosen by stakes and budget (12.1, VS3).
- L8. Selection is explainable: the result lists why each candidate was chosen or dropped (filter, statistic); the choice is written to the run log.

**Statistics and the knowledge that accumulates**
- L9. For every node version and pipeline version the index keeps running statistics per task type: runs, success and failure rates, latency, tokens, and, from labelled test cases and user
  feedback, quality measures (for verifiers: precision and recall of flags, calibration; 9, L5). Statistics are derived from the run log and the harness and can be recomputed.
- L10. The library also stores **cases**: a claim or task description, the checks and styles that were applied, the verdict, and the later outcome (user correction, hard-check result).
  Cases make "for claims like this, check X worked" retrievable (similar-case lookup by tags first, embeddings later) and are the training data for routing and the verifier models.
- L11. Nothing is deleted by learning: low-performing entries are marked `retired` or demoted in the ranking; the reason and the numbers stay with them.

**Making entries (by hand, by the harness, by a model)**
- L12. Lifecycle: `draft` (new, never used automatically) -> `tested` (passed the harness on its test cases; may be chosen when exploring) -> `trusted` (beats the baselines; chosen by default)
  -> `retired`. Promotion is a decision of the user, supported by the harness report (9, L3); it is never automatic.
- L13. Entries proposed by a model (a new view, a changed pipeline, a script) are always `draft` with `origin.by` naming the model, and shown to the user as a diff (G3). A `script` node is
  pinned by the hash of its text: any change is a new version, and the sandbox rules (HC2) apply to every script, however trusted.
- L14. Safety classes (`reads_web`, `runs_code`) are part of the interface; a pipeline's class is the maximum of its nodes, and the skill declares the maximum it may use (for example a
  chat skill without web access cannot select a pipeline that reads the web).
- L15. Validation on load: references resolve, wiring matches the schemas, loops are bounded, tools exist, no cycles in the dependency graph; a broken entry is reported and skipped
  (like a broken skill file, S1).

**Interface for people and models**
- L16. A command line tool (`tools/library.py`): `list`, `search`, `show`, `validate`, `reindex`, `stats`, `promote`, `diff`; later the graph viewer/editor of 10 reads and writes the same files.
- L17. The same operations are available to pipelines as tools (`library.select`, `library.describe`) so that a planning step can inspect what exists; writing is limited to drafts.

Open questions: whether very small helper models (classifier, verifier) are library entries too (probably yes, kind `model_file`, with their training data and evaluation attached); how the
chat page names and shows a chosen pipeline ("which checks ran") without overloading the status block; whether shared libraries between users are wanted (probably later, with signing).

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
- X5. Scripts written by a model run only in the sandbox of HC2 (never in the MIA process, never with network or project files); without a working sandbox the `script` check is disabled.
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

### 12.1 Verification styles (interchangeable pipeline nodes)

A verification style is a sub-graph that takes a claim (or a hypothesis) and the evidence and returns a verdict `supported | contradicted | unresolved`, a confidence, and the full
transcript (logged). The skill file selects the style; the harness compares them at equal token cost; the bandit (8, level 2) may choose among them later.

| Style | Roles | Notes |
|---|---|---|
| `hard` | no model judgement: the hard checks of 12.2 only | strongest where it applies; its coverage is limited |
| `single` | one entailment question: claim + passage only | baseline, cheapest; also used as a gate for the others |
| `consistency` | N samples of `single` with different views (order, wording, temperature), vote | baseline from the literature (Wang et al.) |
| `good_bad_cop` | two views commit independently first, then see each other's position and revise; capped rounds | risk: conformity and sycophancy, so positions are fixed before the exchange and "disagreement remains" is a valid outcome |
| `trial` | **prosecutor** (attacks the hypothesis), **defender** (supports it and rebuts the prosecutor), **judge** (tests the hypothesis, questions both, gives the verdict) | arguments must cite verbatim evidence passages (code checks the quotes); the judge never wrote the claim; the order of prosecutor/defender is swapped on a second pass to measure position bias |
| `trial_jury` | like `trial`, but the verdict comes from a **jury of several viewpoints** (experts) that each judge the same case, then their verdicts are combined (majority, or weighted by measured reliability) | the experts differ by **context and question**, not only by a role label (for example a dates-and-numbers checker that sees only numbers, a source-reliability viewpoint that sees metadata, a domain expert with a domain-specific excerpt); disagreement inside the jury is reported |
| `trial_experts` | `trial`, plus experts that the judge can call as witnesses for a specialised answer in this context | experts have narrow tools and contexts; their answers count as evidence, not as verdicts |

Common requirements:
- VS1. Every style has the same interface, so one node can be replaced by another without changing the rest of the pipeline.
- VS2. Roles are separate prompts and separate views (what each role sees is defined in the skill file); models can differ per role (a different model for the judge or for one juror).
- VS3. Gate: the hard checks (12.2) run first; the expensive styles run only on the claims they leave open and that `single` marks as uncertain (or on claims above a stakes threshold), because debate does not beat cheap baselines on easy cases
  (Smit et al.; the later critique in 14).
- VS4. Fixed maximum number of turns and tokens per style; "unresolved" is always allowed.
- VS5. The harness reports, per style: accuracy against labelled claims, calibration, cost (tokens, seconds), position bias (swap test), conformity (how often a juror or cop changes
  to a wrong position after seeing the other), and the share of errors that it has in common with the generator (L5).
- VS6. Jury aggregation is configurable (majority, unanimity required, weighted by the measured reliability of each viewpoint). Weights are learned from the logs only after enough labelled
  cases (8, level 3), with hold-out cases.
- VS7. Open research questions: does a different context help more than a role label (jury of experts versus single judge with a persona)? Does the jury reduce shared errors compared with
  one judge? When does the added cost pay off?

### 12.2 Hard checks (executable and external evidence)

The styles of 12.1 are judgements by models. **Hard checks** are different: a program runs or the outside world is asked, and the result is evidence that does not depend on the
generator's opinion. They come first in the order of verification (cheap and strong before expensive and soft), and a style only sees the claims that the hard checks could not settle.

Interface (same for all): `check(claim, context) -> {status: pass | fail | inconclusive | not_applicable, evidence, transcript, cost}`. An applicability step decides which checks fit a claim
(numeric, date or time, quotation, citation or URL, code, plain factual statement). Results are logged with the exact script, query or URL.

| Check | What it does | Strength |
|---|---|---|
| `fixed_code` | built-in functions: arithmetic, units, dates and weekdays, JSON/format validity, schedule overlaps, "this quote occurs verbatim in this page" | exact, deterministic |
| `script` | the model writes a short Python script that computes or tests the claim (a number, a date, a sorting or counting statement, a consistency check on given data); it runs in a **sandbox** and its output is the evidence | strong for computable claims; see the caveat below |
| `citation` | every cited URL is reachable, the quote is in the page, title and date match the claim, the source is not the search result page itself | exact for existence, says nothing about truth |
| `web_confirm` | independent web search for the key facts of a claim, with a query that is **not** copied from the draft; requires agreement of at least two independent sources (different domains, no mirrors of each other); a second, disconfirming query ("X myth", "X false", "X correction") looks for contradictions | medium, depends on the sources |
| `lookup` (later) | structured free sources (for example Wikidata or Wikipedia APIs, official data portals) for named facts: dates, numbers, definitions | medium to strong for what they contain |

Requirements:
- HC1. Hard checks run **before** the styles. A claim that fails a hard check is `contradicted` regardless of any debate verdict; a pass counts as evidence for the judge or jury, not as proof
  (a script can be wrong, a source can be wrong). `inconclusive` and `not_applicable` pass the claim on to the styles. The combination rule is in one place and covered by tests.
- HC2. **Sandbox for generated scripts** (the most security-relevant part of this plan):
  - a separate process per script, started with `python -I`, no network, no access to the project or home directory (a throw-away working directory; use an OS sandbox such as bubblewrap
    or `unshare` when available, and resource limits as the minimum), CPU time, memory, process count and output size limits, a wall-clock timeout;
  - an AST check before running: only a whitelist of modules (`math`, `statistics`, `fractions`, `decimal`, `datetime`, `re`, `json`, `itertools`, `collections`, `string`) and no `open`, `exec`,
    `eval`, `__import__`, attribute tricks to builtins, or `os`/`sys`/`subprocess`/`socket`; data comes in as a JSON file or constant and the result goes out as one JSON line on stdout;
  - the script, input, output, exit status and timings are logged; a script is never run twice with changed inputs hidden from the log;
  - if no real sandbox is available the check is **off**, not weakened, and the status block says so.
- HC2a. **Two sandbox backends, chosen per operation** (built, measured on the development machine). `bubblewrap` (namespaces, read-only root, seccomp, limits; 65 ms) is the **standard** tier for many small
  pure calculations. A **rootless podman container** (one container per run, never a pod, because the containers of a pod share one network namespace) is the **strong** tier: it adds SELinux confinement
  (`container_t` with its own category label; the machine runs SELinux enforcing), hard cgroup limits (a fork bomb is stopped by the pids limit) and a seccomp profile made stricter than podman's default;
  it costs about 0.9 s per run and an image (`tools/sandbox/build_image.sh`). The strong tier is used when an operation is exposed to hostile influence or matters most: a script with web access, parsing of hostile
  documents, input that is tainted by unchecked web or file text, code from outside, high stakes. If the strong backend is missing the operation is refused, never weakened (optionally degraded, and marked).
  Stronger isolation can follow by changing the OCI runtime of the strong tier (gVisor `runsc`, or a micro VM with `crun-krun`/Kata, which need KVM; `/dev/kvm` is not present on this machine today).
- HC2b. **Web access of scripts** only through the broker (`broker.py`), over the standard input and output of the sandbox (no socket, no mounted file, so also no conflict with SELinux): GET and search, the same
  safety rules and web log as MIA's own tools, budgets per script, nothing else leaves the sandbox. No curl, no sockets. A later option: run the page fetcher and HTML extraction itself in a sandbox with network
  but no files and no access to this machine's services (so a parser bug in hostile HTML cannot touch MIA), with the DNS answer pinned by the broker.
- HC3. **Test-oracle caveat for scripts.** A script written by the same model that made the claim can encode the same misconception (it checks what the model believes, for example a wrong formula).
  Mitigations: the script is generated from the *claim*, not from the draft's reasoning; it must print the values it used; the judge or verifier sees the script (a different view or model reviews
  that the script tests what the claim says); numeric claims are computed in two independent ways when cheap (for example `decimal` and `fractions`); the harness measures how often a passing
  script was still wrong (L5).
- HC4. **Web confirmation rules.** The query is built from the claim's key entities and numbers, not from its wording (confirmation bias in the query is the main risk of searching "does X hold?");
  a disconfirming query is always run for `web_confirm`; "nothing found" is `inconclusive`, never `fail`; source quality is part of the evidence (domain type, date, whether it is a primary source),
  and results from the research task's own sources do not count as independent confirmation of themselves. All fetched text is untrusted data (X1).
- HC5. Hard checks are interchangeable nodes like the styles (same node interface), can be combined in a skill (`checks: [citation, fixed_code, script, web_confirm]`) and have budgets
  (scripts, searches, seconds per claim).
- HC6. The harness reports per check: coverage (share of claims it applies to), precision of `fail` flags, false passes, cost, and the disagreement rate with the style verdicts. Disagreements between a
  hard check and a style are logged as interesting cases for the user's own review.
- HC7. Open research questions: how much of the factual error of a local model can be settled by hard checks alone, and how much is left for judgement styles? Is a disconfirming query worth its cost?
  How often does a model-written verification script share the misconception of the claim?

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

## 13a. Emotions, behaviour feedback (rewards and penalties) and memory: review of the early experiments

MIA started with three experiments that carry a lot of weight today: emotions as keywords in the text, penalties as scolding messages, and "dreaming" as a summary of the session.
They worked well enough to build the character on. This section records what they do, what is fragile, and what replaces them. Nothing here is built yet; it has to be reviewed first.

### What the code does today (communicator.py, penalties.json, moods.py)
- **Emotions**: the first message of every conversation (`EMOTION_QUESTION`) asks the model to start every answer with one keyword from `emotion_map.json` and a newline. The keyword is cut out of the
  streamed text, mapped to an expression (and a mood line in the page). A missing or unknown keyword counts as "forgotten".
- **Penalties**: when an emotion is missing, `penalties.json` provides a scolding message ("MIA! You have forgotten adding the emotion ...", plus an apology line at random) that is sent to the model **as the next
  user message**, so it becomes part of the memory. It was a joke at the start; in effect it is a correction channel that costs tokens and pollutes the history.
- **Dreaming** (`emulate_dreaming`): the model summarises the whole chat (about 2000 words), the summaries of past sessions are summarised again into a long-term summary (a summary of summaries), the history is
  cleared, the persona is sent again and the summaries are given back as the new beginning, with the instruction to "pretend you just woke up". The raw history is overwritten.
- **Tasks**: lines marked `TASK:` in the chat are supposed to survive in the summaries; the hourly time check asks the model whether something is due.

### Assessment
- Emotions as in-band keywords depend on the model's discipline in every single answer; the penalty exists *because* that fails. The keyword channel also carries only one emotion per answer position,
  without intensity, and the list of emotions in the prompt is separate from the presets and gestures that the character can really show.
- Scolding is the wrong tool for format errors: constrained decoding and schemas prevent them, a silent retry repairs them, and neither needs to enter the memory. The *idea* behind the penalty (unwanted
  behaviour should have a consequence that changes later behaviour) is sound and is worth a proper design (see below).
- Dreaming by summary is "compaction", used widely, and a reasonable first approximation of what sleep does (compress, keep what matters). Its known weaknesses: it is lossy and the loss is silent;
  a summary of summaries drifts further with every round; a hallucinated or wrong statement in a summary becomes a permanent "fact" without a trace to its source; details cannot be recovered after the raw
  history is gone; tasks inside prose can be dropped; and the model that summarises is the weak local model, so quality varies. With a context of 8192 tokens, memory design is not a detail.
- Neuroscience gives a better analogy than "summarise": in complementary-learning-systems theory, fast episodic storage (hippocampus) is replayed during rest to train slower semantic storage (cortex),
  which extracts regularities, while episodes fade; memory is also rewritten when recalled (reconsolidation). Translated: keep the episodes, **extract** structured knowledge from them with links back,
  **merge** it with what is known (add, update, contradict, forget), and **retrieve** by relevance when needed, instead of replacing the past by one text.

### Requirements: emotions
- EM1. Emotion is **out of band**: a separate small structured step or field (schema: emotion from the list, optional intensity, optional second emotion with the sentence it starts at) next to the text,
  not a keyword in the spoken text. Options to evaluate in the harness: (a) schema-constrained output with the emotion field first and the text streamed after it; (b) a separate quick call (or the
  small classifier of 8, level 1 on the CPU) that labels the finished text or each sentence; (c) a mix, where (a) is used and (b) repairs missing values. A missing emotion is repaired silently, never penalised.
- EM2. The list of emotions is **generated from the preset library** (the expression presets and gestures the character can show), so a new preset can be used without editing a prompt; the mapping file becomes data.
- EM3. Emotion can be a **state** and not only a label: a mood (valence and arousal, as in the circumplex model of affect) that moves with the conversation and decays with time, from which the label and the
  expression strength follow. The existing mood tracker (hold time, activity) is the first form; the question is whether the model, the user's tone or both drive it.
- EM4. Emotion timing: with sentence-level labels the character can change its expression while it speaks (the voice pipeline already works per sentence).
- EM5. Test cases for emotions (a scenario and the acceptable expressions) belong to the harness (9); the choice between (a), (b), (c) is made by measurement, including latency.

### Requirements: behaviour feedback (the reward and penalty system)
The goal: unwanted behaviour is **detected**, **recorded** and **changes later behaviour**, without scolding inside the conversation and without training the model to please instead of to be right.
- BF1. **Behaviour rules** are library entries (4a): a named rule with a detector (a hard check where possible: format, language, forbidden markup in speech, a claim without source, tone words; a model view only where
  code cannot decide), a severity, a description of the wanted behaviour, and examples. Rules are data; a skill lists the rules it is held to. The rules of the old first message (no markdown in speech, "times"
  instead of the asterisk, no stage directions) become the first rules.
- BF2. **Signals**: automatic (detector hits, hard-check failures, retries, budget overruns), explicit (the user marks a message: thumbs, "wrong", "too long", a category), and implicit (regeneration, edits,
  quick corrections). Every signal is a line in the run log with the run, the node, the rule and the sign (reward or penalty). Nothing is hidden: the user can see the list of recent violations and rewards.
- BF3. **Consequences**, in order of introduction; each one needs the signals of the previous ones:
  1. repair: the run repairs the output silently (retry with the violated rule named, a deterministic fix such as removing markup); the conversation history stays clean;
  2. selection: rule hits per prompt or pipeline variant feed the statistics of the library, so variants with fewer hits are chosen more often (bandit, 8, level 2);
  3. lessons: a recurring violation produces a short written lesson ("do not use asterisks for emphasis, your voice cannot say them"), kept in a procedural memory (below) and put into the context when the
     situation matches (verbal reinforcement, as in Reflexion), with the user's approval for lessons that change tone or persona;
  4. examples: pairs of a bad and a good answer (the repaired one) are stored and retrieved as few-shot examples for the stage that failed;
  5. training (optional, last): the pairs are a preference dataset for an offline adapter (DPO-style) of the local model, only if the earlier consequences are not enough.
- BF4. **Protection against the usual failures of reward systems**: (a) *sycophancy*: approval of the user must not be the only reward, because models trained on approval learn to agree and flatter; rewards for
  factual answers come from hard checks and sources, and thumbs are weighed against them; (b) *Goodhart*: any learned selection is evaluated on held-out test cases that it never sees; (c) *reward hacking*: a
  detector that is easy to satisfy without being right (for example an emotion keyword present but wrong) is paired with a second signal; (d) a rule or lesson is a draft until the user accepts it (L12, L13).
- BF5. **The joke stays in the character, not in the mechanism**: the playful scolding and apology can remain as an optional character behaviour (an embarrassed expression, a self-deprecating line spoken or
  shown once), generated from a violation record after the repair, configurable and off by default for long sessions. It never enters the model's history as a user message.
- BF6. Honest limits: reward and penalty change the *pipeline* (prompts, examples, selection, memory) far more reliably than they change the *model*. Changing the model's weights is the last, optional step (BF3.5).

### Requirements: memory and dreaming
- MM1. **Tiers**: (1) working memory, the recent turns verbatim; (2) episodic memory, the raw chat log and run log, **never overwritten** (they already exist: `chat_log.jsonl`, `data/runs`); (3) semantic memory, structured
  facts and preferences about the user, the world of the story and the projects, each with provenance (source message ids, date, confidence); (4) procedural memory, the lessons and rules of BF3; (5) a **commitment
  ledger**, tasks and appointments as records (text, due time, status, source), replacing the `TASK:` convention inside prose. The hourly time check reads the ledger (code decides what is due; the model only phrases the reminder).
- MM2. **Consolidation** ("dreaming") is a library pipeline, run when idle, at night or by `/dream!`, on the light model: select the episodes since the last run; extract candidate facts, preferences and commitments as
  structured records with source ids; compare each candidate with the existing records and decide add, update, contradict (keep both with dates and mark the older one), or no-op; write per-topic summaries
  that link to their sources (they are an index into the episodes, not a replacement); apply decay (rarely used, low-importance items fade from retrieval, they are not deleted); produce a short **digest**
  for the user ("what I took from today"), which can be corrected.
- MM3. **Memory writes are verified**: a candidate fact must be supported by its source message (the hard checks of 12.2 apply: the quote is in the source); text from the web or from files never becomes a
  fact about the user; contradictions are surfaced, not silently resolved. Eager consolidation after every message is expensive, so batches at rest are the default.
- MM4. **Retrieval at answer time** replaces "continue from the compressed text": the context is assembled within the token budget from the persona, the matching lessons, the retrieved facts (embeddings on the CPU
  plus recency and importance, and tags), a short rolling summary of the current session, and the recent turns. The "pretend you woke up" step is dropped; waking up is just a fresh context with the relevant memories.
- MM5. **User control**: a page to look at, edit and delete memory records and lessons (privacy and correction); every change is logged; export is a file copy.
- MM6. **Evaluation**: a memory test set (a scripted conversation, then consolidation, then questions on recall, update of a changed fact, contradiction, temporal order, commitments, and "unknown") in the
  harness; the current summary-based dreaming is the **baseline** and the new method must beat it at equal or lower token cost. Public benchmarks of long-term conversational memory exist (LoCoMo,
  LongMemEval) and can be used as a reference, but the own set reflects the real use.
- MM7. Open research questions: how much of the benefit of consolidation comes from structure (records with provenance) and how much from retrieval? Does batch consolidation at rest lose measurable quality compared
  with eager writes? Do lessons (procedural memory) reduce rule violations measurably compared with a longer system prompt?

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

Debate, juries and multi-agent verification (see 12.1)
- Irving, Christiano, Amodei 2018, AI safety via debate. arXiv:1805.00899
- [S] Khan et al. 2024 (ICML), Debating with More Persuasive LLMs Leads to More Truthful Answers. arXiv:2402.06782
- [S] Du et al. 2023 (ICML 2024), Improving Factuality and Reasoning in Language Models through Multiagent Debate. arXiv:2305.14325
- [S] Smit et al. 2024 (ICML), Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs. arXiv:2311.17371
- [S] If Multi-Agent Debate is the Answer, What is the Question? arXiv:2502.08788
- Liang et al. 2023, Encouraging Divergent Thinking in LLMs through Multi-Agent Debate. arXiv:2305.19118 (abstract not retrieved in the search)
- Chan et al. 2023, ChatEval. arXiv:2308.07201; Verga et al. 2024, Replacing Judges with Juries (PoLL). arXiv:2404.18796
- Michael et al. 2023, Debate Helps Supervise Unreliable Experts. arXiv:2311.08702; Kenton et al. 2024, On Scalable Oversight with Weak LLMs Judging Strong LLMs. arXiv:2407.04622
- Zheng et al. 2023, Is "A Helpful Assistant" the Best Role for LLMs? arXiv:2311.10054; Wang et al. 2023, Solo Performance Prompting. arXiv:2307.05300; Wang et al. 2024, Mixture-of-Agents. arXiv:2406.04692
- Court-style agents (for example AgentCourt, arXiv:2408.08089): not verified, read before citing

Executable and tool-based verification (see 12.2)
- Gao et al. 2022, PAL: Program-aided Language Models. arXiv:2211.10435
- Chen et al. 2022, Program of Thoughts Prompting. arXiv:2211.12588
- Gou et al. 2023, CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing. arXiv:2305.11738
- (from memory, to be checked) work on property-based testing and test-oracle problems from software engineering applies to model-written checks (Barr et al. 2015, The Oracle Problem in Software Testing: A Survey, IEEE TSE)

Memory, consolidation and behaviour feedback (see 13a)
- [S] Sharma et al. 2024 (ICLR), Towards Understanding Sycophancy in Language Models. arXiv:2310.13548 (found in the search: RLHF preference data favour answers that agree with the user)
- [S] Mem0 (Chhikara et al. 2025: structured facts extracted and consolidated at write time), A-Mem (Xu et al. 2025: linked agentic notes, arXiv:2502.12110), Zep (Rasmussen et al. 2025: temporal knowledge graph); MemGPT (Packer et al. 2023, arXiv:2310.08560: paging between context and external storage; critics note latency and dependence on the model's memory decisions); the search summaries did not give the Mem0 and Zep arXiv numbers
- [S] LoCoMo (Maharana et al. 2024, arXiv:2402.17753) and LongMemEval (Wu et al. 2024, arXiv:2410.10813): benchmarks of long-term conversational memory (existence confirmed in the search); recent 2026 papers on consolidation cost and reconsolidation (arXiv:2609.16053, 2605.16045, 2609.05441) were seen only as abstracts
- Park et al. 2023, Generative Agents: Interactive Simulacra of Human Behavior. arXiv:2304.03442 (memory stream, retrieval by recency, importance and relevance, reflection that links to sources; not seen in the search)
- McClelland, McNaughton, O'Reilly 1995, Why there are complementary learning systems in the hippocampus and neocortex, Psychological Review (consolidation by replay); Nader, Schafe, LeDoux 2000, Fear memories require protein synthesis in the amygdala for reconsolidation after retrieval, Nature (reconsolidation); Russell 1980, A circumplex model of affect, Journal of Personality and Social Psychology (valence and arousal). From memory, check before citing
- Bai et al. 2022, Constitutional AI: Harmlessness from AI Feedback. arXiv:2212.08073; Rafailov et al. 2023, Direct Preference Optimization. arXiv:2305.18290; Skalse et al. 2022, Defining and Characterizing Reward Hacking. arXiv:2209.13085 (all from memory, check)

Local research agents (implementations to learn from)
- [S] LearningCircuit/local-deep-research; langchain-ai/local-deepresearcher; OpenDeepResearcher-via-searxng (GitHub)

## 15. Phases (proposal)

1. **Foundation**: run log (L1), event stream (E), pipeline runner with fake model tests (P), skill loader (S); `chat` ported as the reference skill. Status block in the chat page.
1b. **Library** (4a): node and pipeline entries as files, the SQLite index, validation, `select` with hard filters and statistics from the run log, `tools/library.py`; the existing `chat` and `summarize` pipelines move into it as the first entries, the web tools and `chunk_text` become the first nodes. **This comes before the checks**, so they are written as library nodes.
1c. **Behaviour layer** (13a), in two parts that do not block the research work: (i) *signals first*: behaviour rules as library entries, violation and reward lines in the run log, silent repair instead of scolding, emotion as a structured step (EM1 to EM5, measured against the keyword method); (ii) *memory* later: ledger of commitments, structured memory with provenance, consolidation pipeline, retrieval, memory page, and the memory test set with the current dreaming as the baseline.
2. **Research**: SearXNG setup (DuckDuckGo fallback), tools with the safety rules (X), the research pipeline and its test set; harness (L3); hard checks first (`fixed_code`, `citation`, `web_confirm`, then the sandboxed `script` check); first comparisons (direct vs. pipeline, with/without verify, hard checks vs. styles).
3. **Storytelling**: story state, scene loop, interactive UI; test set with consistency checks.
4. **Variants**: inspect the VRM parts (V4), variant store and API, editor, switching with the task.
5. **Graph viewer**, then editor with proposals (G).
6. **Routing and learning** (8, levels 1–3), `schedule` skill.
7. Optional: controller and distillation (8, levels 4–5).

## 16. Open questions
- Behaviour layer (13a): which unwanted behaviours matter most to you (the list starts with the format rules of the first message)? Should the playful penalty stay as an optional character moment? Is the digest of a consolidation something you want to see every day? Which facts about you should never be stored?

- Which meshes does the VRM have for accessories and clothes (V4)? Do we need additions in Blender?
- Which Qwen model and context length are usable on 12 GB with acceptable speed (to be measured with the harness, M3)?
- Language: research answers in the question's language; the sources may be English. Where is translation done, and does it hurt claim checking?
- Which feedback controls does the chat page get (thumbs, "wrong source", edit) to feed L1 without annoying the user?
- Does the status block also show for chat (probably only for runs longer than a few seconds)?
