# MIA: collected requirements (baseline of 2026-10-24)

Purpose: one place that says **what MIA is required to do today**, collected from the five requirement documents, the README and the git history, so that the high-level specification (`high-level-spec.md`) and the SysML v2 model (`architecture.sysml`, `model/`) start from a common baseline instead of from five overlapping documents.

This file does not replace the sources. It condenses them, gives every requirement group a **status**, and lists where the sources disagree (section 4). Source ids are kept (`RV23`, `CG11`, `ST10` ...) so that every line can be traced back.

## 1. Sources

| Short | File | Lines | What it covers | Own status line |
|---|---|---|---|---|
| CHAR | `ui/REQUIREMENTS.md` | 212 | 3D character, expressions, gestures, editor, preset API, remote access, integration with MIA | phases 1 to 6, 8 built; 9 prepared, optional |
| CHAT | `ui/REQUIREMENTS_CHAT.md` | 341 | chat page, mood line, chat log, socket events | C1 to C5 built (README); C6 optional, not built |
| CORE | `ui/REQUIREMENTS_CORE.md` | 821 | tasks, skills, pipelines, library, verification, memory, behaviour, strategies, context graph, event log | header still says "nothing built" (stale, see 4) |
| RES | `ui/REQUIREMENTS_RESEARCH.md` | 253 | literature review as the main research task | phase 1, 1b, 2a, 2b, toy suite built; 2c paused |
| DB | `deploy/REQUIREMENTS_DB.md` | 57 | shared state for several instances | postponed |
| README | `README.md`, `deploy/README.md`, `ui/README.md` | | installation, configuration (91 options), commands, structure, what was built per phase | |

## 2. Status legend

**Built** = code and tests exist (README or git history). **Partly** = some of the group exists. **Proposed** = written down, nothing built. **Postponed** = decided to wait. **Dropped** = decided against.
Status is taken from `ui/README.md` and the commit log, not from the requirement documents, which were not always updated. It was not re-verified by running the tests.

## 3. Requirements by capability

### 3.1 Goal, context and constraints

| Id | Requirement | Source | Status |
|---|---|---|---|
| G-1 | MIA is a personal virtual assistant, "long term and evolving"; the aim is to deepen the owner's understanding of machine learning and to automate everyday tasks, not state-of-the-art algorithms | README | standing |
| G-2 | The project has a research character: how much quality a small, free, local model reaches inside clever pipelines with verification, small helpers and a little learning. Every decision should be **measurable** | CORE intro | standing |
| C-1 | Free and local: Ollama models, SearXNG for search, no paid API | CORE 1.1 | Built |
| C-2 | Hardware envelope: one consumer GPU with 16 GB (RX 7800 XT), 62 GB RAM, light model `gemma4:12b-it-qat`, full model `gemma4:26b`, `num_ctx` 8192; one model loaded at a time (`OLLAMA_MAX_LOADED_MODELS=1`) | CORE 1.1, RES RV20 | Built (16 GB RX 7800 XT, confirmed 2026-10-24) |
| C-3 | Host: Fedora, AMD (ROCm) with NVIDIA and CPU as alternatives; podman or docker | CHAR 8, README | Built |
| C-4 | Python 3.11 to 3.13 (3.12 tested), nothing needs `torch`; Godot 4.6.1, GDScript only, Compatibility renderer; chat in plain HTML/CSS/ES modules without build step or framework | README, CHAR 4.3/4.8, CHAT 3.1 | Built |
| C-5 | Everything stays on the host and the private network; no external scripts, fonts or services on the page; only search and scholarly queries leave the machine | CHAR 5, CHAT 1/3.7, CORE X, RES 10 | Built |
| C-6 | Licence GPL-3.0-or-later | README | Built |
| C-7 | Not goals: fine-tuning Gemma, multi-user operation, a generic workflow engine, legs and feet of the character | CORE 1 | standing |

### 3.2 Character (3D avatar)

| Id | Requirement | Source | Status |
|---|---|---|---|
| CH-1 | The VRoid character is rendered in the browser by a Godot web export, on desktop and phone, toon look, orbit and zoom (mouse and touch), named views `body`, `bust`, `face` | CHAR 1, 4.3, 4.4 | Built |
| CH-2 | Asset inspection and a reproducible Blender-to-Godot export script; every shape key can be driven | CHAR 4.1, 4.2 | Built |
| CH-3 | Expression engine: an expression is a set of shape-key weights plus optional bone offsets; JSON preset format with `name, description, weights, bones, tags, source (manual, llm, llm_edited)`; smooth blending (~0.25 s); unknown keys rejected, values clamped, corrections logged | CHAR 4.4 | Built |
| CH-4 | 14 required presets (the six keys of `expressions.json` plus `neutral, happy, sad, angry, surprised, embarrassed, smug, thinking`) | CHAR 4.4 | Built |
| CH-5 | Automatic blinking (suppressed when eyes are closed), idle motion (breathing, head sway), speaking mouth animation (`speaking` preset or `set_speaking()`); real lip sync is out of scope | CHAR 4.4, 6 | Built |
| CH-6 | Gestures (14 so far) as keyframed arm and hand animations authored as directions; a preset may name a gesture; a gesture names its face; gesture editor | CHAR 4.4, ui/README | Built |
| CH-7 | Custom background pictures from a folder, switchable; plain colour if none | CHAR 4.4, deploy | Built |
| CH-8 | Slider editor on phone and desktop: list, filter, load, save as new, overwrite, rename, delete, reset; presets stored on the server so all devices share them; writes need a token | CHAR 4.5, 4.7, Q5 | Built |
| CH-9 | Expressions from a text description by the local LLM: prompt with shape-key names and examples, JSON-schema output, validation, one retry, latency hiding, keep / edit / reject, feedback log used as examples | CHAR 4.6 | Built (real-model try-out still open) |
| CH-10 | All expression input goes through one central API, so lip sync, webcam tracking, vision feedback can be added later | CHAR 6 | Built |
| CH-11 | Character variants per task (parts shown or hidden, colours, default idle gesture), variant store and editor, switching with the task | CORE 7 (V1 to V6) | Proposed (surfaces inspected, V4 answered) |
| CH-12 | Performance: 30+ fps on a mid-range phone, 60 on desktop; reasonable initial download; works without the LLM | CHAR 5 | Built, not re-measured |

### 3.3 Chat page and server

| Id | Requirement | Source | Status |
|---|---|---|---|
| CT-1 | Modern chat: character full window, translucent panel at the right (wide) or bottom sheet with three snap heights (phone), collapsible with caption mode | CHAT 4.1, 7 | Built (C1, C4) |
| CT-2 | Mood and status line replaces the fixed headline; phrase from `moods.json` by emotion, activity overrides mood (thinking, speaking, dreaming, offline, model switch); server is the source of truth; hold time 10 minutes; editable | CHAT 4.3, 6.4 | Built (C2, C3) |
| CT-3 | Bubbles, timestamps, day separators, sanitised markdown with code copy, streaming per message, typing indicator, emotion badge, system notes, automatic-message marker, penalties never shown as user messages | CHAT 5.1 | Built (C3) |
| CT-4 | Composer: auto-grow, Enter sends on desktop (newline on phones), stop button, queue of one, slash-command palette with confirmation for dangerous commands, draft kept, 8000 characters | CHAT 5.2 | Built |
| CT-5 | History: last 50 on load, paging, autoscroll rules, at most about 300 messages in the DOM, live sharing between devices | CHAT 5.3 | Built |
| CT-6 | Connection indicator, reconnect with backoff, drafts kept | CHAT 5.4 | Built |
| CT-7 | Sound: mute and volume, autoplay hint, speaker icon on the message being spoken | CHAT 5.5 | Built |
| CT-8 | Append-only chat log (`data/chat_log.jsonl`), separate from the LLM memory, bounded size, deletable | CHAT 6.2 | Built (C2) |
| CT-9 | Socket.IO events `chat_send / chat_stop / chat_start / chat_delta / chat_done / chat_message / chat_status / chat_error`; REST `history, status, commands, clear`; exchanges run in a background task, one at a time; the socket handler never blocks; rate limit per connection | CHAT 6.3, 6.4 | Built |
| CT-10 | Design tokens, themes dark / light / system (WCAG AA), reduced motion, 44 px touch targets, keyboard use, screen-reader semantics, one i18n dictionary (English now, German prepared), strict CSP, no CDN | CHAT 3, 4.2, 9 | Built (C5) |
| CT-11 | Chat commands: `/light! /full! /dream! /goodnight! /break! /time!` and (added later) `/lookup /search /research` | CHAT 5.2, README, RES RV3 | Built |
| CT-12 | Optional C6: regenerate, speak again, search, export, accent presets, German texts | CHAT 12 | Proposed |
| CT-13 | Out of scope: voice input, attachments, message editing, push, installable app, translating answers (accounts were out of scope here and are **in scope since 2026-10-24**, D-1) | CHAT 13 | standing |

### 3.4 Voice

| Id | Requirement | Source | Status |
|---|---|---|---|
| VO-1 | Speech by Kokoro on onnxruntime with a light voice effect (preset `anime`); RVC and Coqui removed; sentence-wise streaming, `sentence_pause`, warm-up | README | Built |
| VO-2 | Speech text is filtered: single-asterisk actions are not spoken, markup is stripped, "times" instead of the asterisk | README, CORE 13a | Built |
| VO-3 | Voice clips for expressions (`expressions.json`), intro sounds, "Hey, listen!" attention sounds with a chance | README | Built |
| VO-4 | Exactly one page plays the audio (fix for echo); stop also stops speech (setting) | ui/README, CHAT 14.10 | Built |

### 3.5 Tasks, skills, pipelines, library

| Id | Requirement | Source | Status |
|---|---|---|---|
| TK-1 | A task is a skill file plus a pipeline, not a model; tasks: `chat`, `lookup` (formerly research), `storytelling`, `schedule`, later summarise, translate, "think it through" | CORE 2, 3 | chat, lookup, summarize Built; storytelling, schedule Proposed |
| TK-2 | Skill files (Markdown with front matter): version, model profile, pipeline, tools, budget, prompts, schemas, examples; reloaded on change; a broken file never stops MIA; every stage names its schema | CORE 3 (S1 to S4) | Built |
| TK-3 | Pipelines are JSON graphs of node kinds `model, tool, code, map, branch, loop, ask_user`; runner enforces budgets, emits events, retries locally, validates graphs, is testable with a fake model | CORE 4 (P1 to P5) | Built |
| TK-4 | Library of versioned immutable node and pipeline entries (files are the truth, SQLite is a derived index), statuses draft / tested / trusted / retired, selection by task description with statistics, models add drafts only | CORE 4a (L1 to L17) | Built |
| TK-5 | Workflows, agent sessions included, as process graphs in the Co-Simulation Process Graph model: node classes, `(ID, IID)` identity, simulation subgraphs, contraction as a view, preparation as part of the graph, explicit validation rules | CORE 4b (PG1 to PG19) | Partly (events and context graph built; graph-to-runner generation Proposed) |
| TK-6 | Strategies: plan as data with targets, small contexts, consolidation by code, fast first and calls on demand, templates with challengers, typed plans, plan checks in code, router in code | CORE 13b (ST1 to ST13) | Built (ST10 to ST13), challenger tier Proposed |
| TK-7 | Storytelling: premise, outline, scene loop with state file, consistency checks, user steers each scene | CORE 13.2 | Proposed |
| TK-8 | Character variant shown for the active task; the chat shows the active task | CORE 7, V5 | Proposed |
| TK-9 | Models per skill (profile or named model), per role; context size per skill; long text never stuffed whole; embeddings and classifiers on the CPU | CORE 6 (M1 to M5) | Partly |
| TK-10 | Graph viewer and editor | CORE 10 | ~~Dropped 2026-10-22~~ **Reversed 2026-10-24 (D-9): a graph app on the shared database is wanted**; edits by models stay proposals as diffs (G3) |

### 3.6 Verification and trust

| Id | Requirement | Source | Status |
|---|---|---|---|
| VE-1 | Code verifies what code can: formats, arithmetic, units, dates, overlaps, quote present in source; the model verifies only what code cannot | CORE 1.5, 12.2 | Built |
| VE-2 | Hard checks (`fixed_code`, `script`, `citation`, `web_confirm`) with one interface `pass / fail / inconclusive / not_applicable`; run before judgement styles; a fail wins over any debate verdict | CORE 12.2 (HC1 to HC7) | Built (measurement of precision open) |
| VE-3 | Script sandbox: separate process, AST whitelist, no network or project files, limits; two tiers (bubblewrap standard, rootless podman strong); if unavailable the check is **off**, never weakened; web only through the broker | CORE HC2, HC2a, HC2b | Built |
| VE-4 | Verification styles with one interface: `hard, single, consistency, good_bad_cop, trial, trial_jury, trial_experts`; gate so expensive styles run only on open claims; fixed turns and tokens; "unresolved" always allowed | CORE 12.1 (VS1 to VS7) | Built as drafts; not yet measured |
| VE-5 | Claims out of prose (extraction) with anchored quotes | CORE phase 4 | Built |
| VE-6 | Web content is untrusted data: delimited fields, narrow tools per stage, size and type limits, private addresses blocked, injection signals flagged; every query logged | CORE 11 (X1 to X5) | Built |
| VE-7 | Verifier sees claim and passage only; different view or model than the generator where possible; calibration reported, "unknown" is a first-class outcome | CORE 12 | Partly |

### 3.7 Research

| Id | Requirement | Source | Status |
|---|---|---|---|
| RS-1 | **Lookup**: quick fact check with sources; plan, search, fetch, extract with verbatim quotes, synthesise, verify, repair; DuckDuckGo fallback; no quote that is not in its source; "unknown" when nothing is found; cheap path first (a trusted source before a model) | CORE 13.1, RES RV3, RV40 | Built (baseline, decompose, escalate, typed plans) |
| RS-2 | **Literature review** (`research`): input question, scope, cut-off date, budget; output a structured report with sources kept and dropped and why, findings per sub-question with anchors, conflicts, answerability in percent with gaps and next keywords; a low figure is a valid result; no claim to verify truth | RES RV4 to RV6, RV27 | Proposed (phases 1 to 2b built, rest open) |
| RS-3 | Work top down in levels: system analyser, component determiner, scheduler; pieces sized to a share of the context window by code | RES RV1, RV2 | Proposed |
| RS-4 | Roles: fixed planner, collector, source expert; adjustable number of domain experts (0, 1, k) from a field graph; roles are views of one model or separate models (`review_role_models`) | RES RV10 to RV13, RV20, RV44/RV45 | Proposed (settings exist in config) |
| RS-5 | Scholarly sources (OpenAlex, Crossref, PubMed, arXiv, Semantic Scholar with a key): one record format, de-duplication, strict date cut-off, retraction status from Crossref | RES RV15, RV32a, phase 1 | Built |
| RS-6 | Source trust table (prior per class and venue, editable, with reasons); preprints marked; retracted works dropped and listed | RES RV14, RV15 | Built |
| RS-7 | Screening in two stages (abstract first, recall-oriented, then pieces of full text with verbatim anchors); full text open access only; PDF converted inside the sandbox | RES RV17, RV18, RV34 | PDF conversion Built; screening Proposed |
| RS-8 | Weigh, synthesise in the context graph, gap check, one citation step, sufficiency check by code | RES R5 to R7, RV19, RV22 | Proposed |
| RS-9 | Budgets in slices: first slice 60 s, then an intermediate report with a recommendation and a question whether to continue; hard limits on sources, calls, tokens, time, API requests; checkpoint every K sources | RES RV30, RV30a | Built (`Budget.extend`); recommendation Proposed |
| RS-10 | Answerability computed by code from anchored evidence (coverage, weight, diversity, agreement, recency, effort), calibrated on the benchmark; fixed set of causes for a low figure | RES RV23, RV24 | Proposed |
| RS-11 | Every reference in a report must be a source the run retrieved; invented reference is a failure by definition | RES RV27 | Built in the scoring (`review_score.py`) |
| RS-12 | Cross-field work: keyword aliases kept as proposed `same_as`, accepted only with evidence; findings keep their field of origin; normalise diacritics before matching | RES RV41 to RV43a | Proposed |
| RS-13 | Method transfer (optional, off by default): problem signature, catalogue of transfer templates with executable applicability tests, free scout as challenger, retro-discovery benchmark | RES RV43 to RV53 | Proposed |
| RS-14 | Evaluation: reference set of published reviews with included works, time cut-off, development and held-out halves, difficulty tiers 0 to 3, measures (recall, precision, conclusion agreement, calibration, hallucinated references = 0, quote anchoring = 100 %), guard against tuning into noise | RES 11 (RV30a to RV34), phase 2 | Toy tier Built; real cases paused at 2c |
| RS-15 | Reward as a vector, limits are constraints, guards against gaming; learning only changes configuration and graph weights, never model weights | RES RV35 to RV38 | Proposed |

### 3.8 Memory and behaviour

| Id | Requirement | Source | Status |
|---|---|---|---|
| ME-1 | Conversation memory: history in `memories.json`, long-time summaries, "dreaming" (summary, summary of summaries, reset, "pretend you woke up"); `/dream!`, `/goodnight!` | README, CORE 13a | Built (the early design) |
| ME-2 | Target memory: five tiers (working, episodic never overwritten, semantic with provenance, procedural lessons, commitment ledger), consolidation at rest with add / update / contradict / no-op, verified writes, retrieval at answer time within a token budget, a page to inspect and delete records, a memory test set with the current dreaming as baseline | CORE MM1 to MM7 | Proposed |
| EM-1 | Emotion keyword on the first line of each answer maps to expression, gesture and mood (`emotion_map.json`, new emotions added by data) | CHAR 4.9, README | Built |
| EM-2 | Target: emotion out of band (schema field or small classifier), list generated from the preset library, mood as a state with decay, sentence-level timing | CORE EM1 to EM5 | Proposed |
| BF-1 | Behaviour rules as library entries with detectors; speech rules (no bold, no emphasis, no stage directions, sparing actions, times) are the first rules; signals logged | CORE BF1, BF2 | Built for speech rules |
| BF-2 | Target consequences: silent repair, selection statistics, written lessons, examples, optional training; guards against sycophancy, Goodhart and reward hacking; the playful scolding only as optional character behaviour, never in the history | CORE BF3 to BF6 | Proposed (penalties still scold in the history, see 4) |

### 3.9 Logging, tracing, evaluation, learning

| Id | Requirement | Source | Status |
|---|---|---|---|
| LG-1 | Every run is stored; typed events with a schema (`run, seq, type, actor, parent, round`), one run id everywhere (web, scholar, model, checks), secrets removed, negative information logged as carefully as positive | CORE 9 L1, CG11 to CG13, 13d (LG1 to LG7) | Built |
| LG-2 | Content store by hash for prompts, answers and pages, retention by age, chat texts off by default | CORE CG14, 13d | Built |
| LG-3 | The context graph is a view of the log: replay as a pure function, explain an answer back to the query, diff two runs, cost per actor, export as DOT or Mermaid, offline reproduction of a run | CORE CG1 to CG16, `tools/run_explain.py` | Built (steps 1 to 5) |
| LG-4 | Context assembly for a pipeline step from a view within a token budget | CORE CG3, PG16 | Proposed (rendering Built, use in running pipelines open) |
| EV-1 | Evaluation harness: suites with truth and expectation, variants, repeats, cost counting, intervals, paired sign test; recorded web for offline tests; test first for every behaviour change | CORE 9 | Built (suites: hard_checks, computable, extraction, verdicts, research, research_compound, plans, web_checks, behaviour, review_toy) |
| EV-2 | LLM judge with a rubric calibrated on the owner's ratings; verifier calibration | CORE L4, L5 | Proposed |
| LN-1 | Learning ladder: rules and logging, small router, contextual bandit over pipeline variants, learned verifier, learned controller, distillation; each optional, switchable, logged beside the default, hold-out cases, approval gate for model-made changes (G3) | CORE 8, G3, 12 | Proposed (level 0 Built) |

### 3.10 Deployment, access, operation

| Id | Requirement | Source | Status |
|---|---|---|---|
| OP-1 | Configuration in `setup_cfg.json` (not in git), tracked example with every option, a test keeps the example complete, `python config.py` lists missing options | README | Built |
| OP-2 | Start `python -m MIA` (Ollama container managed or external, speech process, web app, HTTPS proxy); orderly shutdown by Ctrl+C, `/break!`, `/goodnight!`, SIGTERM; helpers in their own session | README | Built |
| OP-3 | Podman compose stack (MIA, Ollama, SearXNG, Caddy HTTPS) with ROCm and NVIDIA overrides, `deploy/up.sh` (character, memories, calibration, backup, restore, data takeover), backgrounds mounted read-only | deploy/README | Built |
| OP-4 | Secure context for the 3D character: `localhost` or HTTPS; self-signed proxy on the LAN; Tailscale serve for remote access, never funnel; tailnet members can chat without login | README, CHAR 4.8 | Built (Tailscale not tried against a real tailnet) |
| OP-5 | Tokens: `editor_token` for writes to presets, gestures and clearing history, `chat_token` optional; allowed-origin rule; rate limit | README, CHAT 6.4 | Built |
| OP-6 | Documented reproducible setup from scratch, tests (Python 814+ tests, `node --test`, headless browser checks, phone checklist) | CHAR 5, CHAT 11 | Built |
| OP-7 | Shared state for several instances in PostgreSQL behind a storage layer; **one shared MIA with one memory**; migration files to database and back | DB | Proposed since 2026-10-24 (was postponed) |

## 4. Where the sources disagree or are out of date

Found while collecting. None of these is fatal; each should be settled once and the sources corrected, otherwise the model inherits the contradiction.

1. ~~**Hardware.**~~ **Resolved 2026-10-24.** CORE 1.1 said RX 7700 XT with 12 GB, CHAR 8 said RX 7800 XT. `fastfetch` reports an AMD Radeon RX 7800 XT and Ryzen 9 5900X (24 threads), and the driver reports 17,163,091,968 bytes of VRAM, i.e. **16 GB**. CORE 1.1, M3 and the open questions were corrected; the memory budget for models is 16 GB, not 12 GB.
2. **Status lines are stale.** CORE says "draft for review, nothing built"; `ui/README.md` documents phases 1 to 5 of the core as built. RES says "Nothing here is built yet" but phase 1 to 2b are built. CHAR 4.7 still suggests FastAPI, while its own decision note says MIA's Flask app is the backend.
3. **README describes the old video design.** "Some mp4 files for expression", "media files for expressions" in the program structure, and `python -m python3.10 -i speak.py ... --generate` predate the 3D character and the Python upgrade.
4. ~~**Duplicate requirement ids.**~~ **Repaired 2026-10-24.** In `ui/REQUIREMENTS_RESEARCH.md` the transfer scout is now `RV54` and its executable test `RV55` (the ids `RV44`/`RV45` stay with the number of domain experts and the fair comparison, because `review_request.py` cites `RV44`); in `ui/REQUIREMENTS_CORE.md` the evaluation items of section 9 are `EL1`..`EL6` (the library keeps `L1`..`L17`; the docstrings of `harness.py`, `metrics.py`, `run_log.py` were updated); the second step (4) of the 13d build order is `(4b)`. Left as they are, because they are unique: `RV43a`, `RV32a`, `RV30a` and the position of `CG10`.
5. **Emotion channel.** CORE EM1 wants emotion out of band and BF3/BF5 want no scolding in the history; the code still uses the in-band keyword and `penalties.json` messages. Both are intended to be replaced, but until then the requirements and the code disagree.
6. **Privacy statement is not uniform.** CHAT and CHAR say nothing leaves the host; RES and CORE correctly say the query text of a search or a scholarly lookup leaves the machine (and an optional e-mail address only if configured). One precise statement is needed (done in NFR-5).
7. **Naming of the research task.** `/lookup` is the old research and `/research` the future review (RV3), but skills, pipelines, suites, module `research.py` and recorded baselines still say `research`. RV3 defers the rename; the model therefore uses the target names and notes the code names.
8. **Chat commands.** The command list of CHAT 5.2 predates `/lookup`, `/search` and `/research`; the server list (`GET /api/chat/commands`) is the real source.
9. **Dropped but still referenced.** P6 of CORE ("viewer first, editor later") and the phase list `5. Graph viewer and editor` conflict with section 10, which drops both.
10. **Multi-instance vs single instance.** CHAT 6.4 and the file storage assume one instance with one running exchange at a time; DB assumes several. Postponed, but any new component should use the storage interfaces proposed there so the door stays open.
11. **Language.** CORE asks where translation happens (research answers in the question's language, sources in English); RES open question 4 repeats it. Undecided.
12. **Open questions that block requirements** (collected): editor protection beyond Tailscale (CHAR Q5, answered by the token); which behaviours matter most and whether the daily memory digest is wanted (CORE 16); accessories per task variant; which Qwen model is usable on 16 GB (M3); user PDF library as a source (RES Q3); report figure as percent or bands until calibrated (RES Q7); roles as views first (RES Q8); is method transfer wanted in every review (RES Q0).

## 5. Quantified targets found in the sources

| Target | Value | Source |
|---|---|---|
| Frame rate | 30+ fps phone, 60 fps desktop | CHAR 5 |
| Expression blend | ~0.25 s default | CHAR 4.4 |
| Chat first meaningful paint | < 1 s on the home network | CHAT 10 |
| Chat JavaScript size | < 100 KB gzipped (without vendored libraries) | CHAT 10 |
| Messages in the DOM | at most about 300 | CHAT 5.3 |
| Stream deltas | at most about 20 per second per message | CHAT 6.4 |
| Rate limit | 10 messages per minute per connection | CHAT 6.4 |
| Chat log | at most 10 000 messages | CHAT 6.2 |
| Mood hold time | 10 minutes | CHAT 4.3 |
| Cheap research try | well under 15 model calls per question on the light model | CORE ST4 |
| Piece size | input at most 50 % of `num_ctx` | RES RV2 |
| Review first slice | 60 s, further slices on request | RES RV30a |
| Checkpoint | every 10 sources | RES RV19 |
| Default review budget | screen 40, read 10, calls 150, tokens 400 000, seconds 60, API requests 80 | README |
| Hallucinated references | 0 | RES RV33 |
| Quote anchoring | 100 % | RES RV33 |
| Sandbox cost | about 65 ms (bubblewrap), about 0.9 s (podman) | CORE HC2a |
| Speech | real-time factor 0.28 (Kokoro alone, Ryzen 9 5900X) | README |
