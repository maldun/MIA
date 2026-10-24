# MIA: high-level requirements (draft 1, 2026-10-24)

Derived from the baseline in `01_current_requirements.md`. These are the requirements the system is judged by; the detailed documents (`ui/REQUIREMENTS_*.md`) stay as the lower level that refines them. The same requirements, with stakeholders, structure and allocation, are formalised in `sysml/` (ids match: `HLR-01` is `requirement def <'HLR-01'>`).

Form: *MIA shall ...* One statement per requirement, written so that a test, a measurement or an inspection can say yes or no. Verification: **T** test (automatic), **M** measurement (harness, with repeats), **I** inspection, **D** demonstration (manual checklist).

## 1. Stakeholders and what they need

| Stakeholder | Role | Main concern |
|---|---|---|
| Owner | the one user, also the developer and researcher | a companion and assistant that is pleasant to talk to, runs on their own hardware, can be trusted on facts, and is a vehicle for research on small models |
| Viewer | the owner or a guest on a phone or other computer in the home or the tailnet | opens a link and chats; the character works on a phone |
| Host operator | the owner as administrator | install, update, back up, shut down cleanly, keep the GPU usable for other programs |
| Researcher | the owner reading results | every claim traceable, every comparison fair and repeatable, no number without its limits |

There is exactly one owner; multi-user operation is a stated non-goal.

## 2. Constraints (given, not negotiable in this draft)

| Id | Constraint |
|---|---|
| CON-1 | Free and open: local models through Ollama, self-hosted search, no paid API, GPL-3.0-or-later |
| CON-2 | Hardware envelope: one consumer GPU with 12 GB, 62 GB RAM, one language model loaded at a time |
| CON-3 | Python 3.11 to 3.13, Godot 4.x with GDScript only, chat page in plain HTML/CSS/ES modules without a build step |
| CON-4 | The 3D character needs a secure browser context: `localhost` or HTTPS |
| CON-5 | Remote access only inside a private network (Tailscale); never a public port |

## 3. High-level requirements

### 3.1 Interaction

**HLR-01 Conversation.** MIA shall let the owner hold a conversation in a web browser on desktop and phone, with answers appearing while they are written, the ability to stop an answer, one waiting message while she is busy, a history that survives reload, and the same conversation visible live on every connected device.
*Rationale:* the point of an assistant. *Baseline:* CT-1..CT-9, CT-11. *Verification:* T (socket tests with a stub LLM, browser checks), D (phone checklist).

**HLR-02 Embodied character.** MIA shall show her emotional state and speech through a 3D character: facial expressions that blend smoothly, arm gestures, a moving mouth while speaking, blinking and idle motion, driven through one central expression API; if the character cannot load, the chat shall still work.
*Baseline:* CH-1..CH-10, EM-1, CT-1. *Verification:* T (bridge and engine tests), D (contact sheet of the 14 presets), M (frame rate).

**HLR-03 Voice.** MIA shall speak her answers aloud sentence by sentence using a voice synthesised on the host, speaking only what is meant to be heard (no markup, no stage directions), and shall let the owner mute or stop her.
*Baseline:* VO-1..VO-4. *Verification:* T (speech-text filter, streamer), D.

**HLR-04 Transparency of state and method.** MIA shall tell the owner in one short line how she feels and what she is doing, and shall let the owner open, for any answer produced by a task, a step-by-step account of how it came about; the accurate description shall always come from real event data, never from a model.
*Baseline:* CT-2, CORE E1..E5. *Verification:* T, D.

**HLR-05 Owner-shaped appearance and persona.** MIA shall let the owner change expressions, gestures, backgrounds, mood phrases, emotions and persona as data, without changing code, and shall protect changes that affect all devices with a token.
*Baseline:* CH-4..CH-9, CT-2, OP-5. *Verification:* T, D.

**HLR-06 Accessible on every supported device.** MIA shall be usable by keyboard and screen reader, in dark and light themes, with reduced motion respected, on widths from 320 to 2560 px in current Chrome, Firefox and Safari (iOS 16+).
*Baseline:* CT-10. *Verification:* T (a11y script), D (phone checklist).

### 3.2 Intelligence

**HLR-07 Tasks as skills.** MIA shall perform each kind of work (chat, lookup, literature review, storytelling, scheduling, summarising) as a *task*, defined by a human-readable skill file and a pipeline, selectable by the owner, with the choice never made silently for tasks that reach the internet.
*Baseline:* TK-1, TK-2, RS-1, CT-11. *Verification:* T.

**HLR-08 Workflows as data.** MIA shall define every pipeline and agent workflow as validated, versioned data in a library of reusable entries with a lifecycle (draft, tested, trusted, retired); entries proposed by a model shall remain drafts until the owner approves them, shown as a diff and tried on the test set first.
*Baseline:* TK-3..TK-5, TK-10. *Verification:* T (validation, library tests), I.

**HLR-09 Small-model strategies.** MIA shall reach useful quality with small local models by splitting work into narrow steps with structured outputs and testable targets, by keeping every model input inside a fixed share of the context window, by letting code do everything code can do, and by spending more calls only when a target is unmet.
*Baseline:* TK-6, TK-9, RS-3. *Verification:* M (calls per question, accuracy against the one-prompt baseline).

**HLR-10 Model management.** MIA shall run on a local model server, shall let the owner switch between a light and a full model, shall free GPU memory on request, and shall say plainly when the model server is unreachable.
*Baseline:* C-1..C-3, CT-11. *Verification:* T, D.

### 3.3 Trust

**HLR-11 Verify before asserting.** MIA shall check what can be checked by code first (arithmetic, dates, schemas, quotes present in their source, executable claims), shall use model judgement only for the rest, and shall treat "unknown" and "unverified" as proper answers; a failed hard check shall outweigh any model verdict.
*Baseline:* VE-1, VE-2, VE-4, VE-5, VE-7. *Verification:* M (precision and recall of flags, calibration), T.

**HLR-12 Untrusted input stays data.** MIA shall treat all text from the web, papers, PDFs and users as data that never acts as instruction; shall run model-written scripts and parse hostile documents only inside an isolating sandbox; and if the sandbox is missing shall refuse the operation instead of weakening it.
*Baseline:* VE-3, VE-6, RS-7. *Verification:* T (injection and escape cases), I.

**HLR-13 Honest confidence.** MIA shall state how sure she is only with figures computed by code from anchored evidence, shall never show a source she did not retrieve, and shall report limits (contamination, small samples, missing access) with every result.
*Baseline:* RS-10, RS-11, EV-2. *Verification:* M (hallucinated references = 0, quote anchoring = 100 %, calibration plot).

### 3.4 Research

**HLR-14 Lookup.** MIA shall answer a factual question quickly with the sources and verbatim quotes that support it, preferring a trusted source to a model judgement, and shall say "unknown" when nothing supports an answer.
*Baseline:* RS-1, RS-6. *Verification:* M (research suites on recorded pages).

**HLR-15 Literature review.** Given a research question, an optional field scope, a cut-off date and a budget, MIA shall produce a structured report of the literature found: sources kept and dropped with reasons, findings per sub-question with verbatim anchors, conflicts between sources, an answerability figure with its parts, open gaps and suggested next keywords; she shall work in time slices (first 60 s), give an intermediate report with a recommendation at the end of each slice, and continue only when the owner agrees.
*Baseline:* RS-2..RS-5, RS-7..RS-10, RS-12. *Verification:* M (benchmark against reference reviews, tiered), T (toy world). *Status:* the largest open requirement.

**HLR-16 Knowledge of sources.** MIA shall record where a source comes from and how far she trusts it (class, venue, date, peer-review status, retraction or correction status read from the metadata), shall keep the owner's edits of that trust, and shall honour a time cut-off strictly.
*Baseline:* RS-5, RS-6. *Verification:* T (recorded API fixtures).

**HLR-17 Method transfer (optional).** On request MIA shall look for methods from other fields that fit the structure of the problem, offering few ranked candidates marked as hypotheses unless an executable test on a toy instance passed.
*Baseline:* RS-13. *Verification:* M (retro-discovery cases), T (executable tests). *Status:* proposed, off by default.

### 3.5 Memory and behaviour

**HLR-18 Memory.** MIA shall remember the relationship over time: keep the raw conversation, keep structured facts, preferences and commitments with a link back to their source, consolidate at rest, retrieve what is relevant within the token budget, let the owner inspect, correct and delete any record, and never store a fact about the owner that came from web or file text.
*Baseline:* ME-1, ME-2. *Verification:* M (memory test set against today's dreaming as baseline), T. *Status:* today only the early summary-based dreaming exists.

**HLR-19 Behaviour rules and feedback.** MIA shall detect violations of defined behaviour rules, repair them silently, record them as signals, and let signals change later behaviour through selection, written lessons and examples; reward for factual answers shall come from checks and sources, not from the owner's approval alone; no correction shall enter the conversation memory as a scolding.
*Baseline:* BF-1, BF-2, EM-1, EM-2. *Verification:* T, M.

### 3.6 Observability, evaluation and learning

**HLR-20 Traceability.** MIA shall write every run as typed, schema-checked events carrying one run id through every model call, web or API request and check, with secrets removed; any statement in an answer shall be traceable back to the query that found its source; any recorded run shall be replayable into its graph and reproducible offline, and two runs shall be comparable event by event.
*Baseline:* LG-1..LG-4. *Verification:* T (replay and reproduction of recorded runs), I.

**HLR-21 Measurable quality.** MIA shall be evaluated by a harness that runs pipeline variants on fixed suites with repeats, intervals and cost counting; every behaviour change shall start with a test case; claims of improvement shall hold on held-out cases.
*Baseline:* EV-1, RS-14, RS-15. *Verification:* T (harness tests), I.

**HLR-22 Optional learning.** MIA shall learn only from logged signals, only in discrete choices of configuration and graph weights (never model weights unless the owner decides so later), with every learned choice logged next to the default, switchable off, and reversible.
*Baseline:* LN-1, RS-15. *Verification:* T, M.

### 3.7 Operation

**HLR-23 Local-first privacy.** MIA shall keep conversations, memory, logs and models on the host; the only data leaving the host shall be the text of a web search or scholarly query (and an e-mail address only if the owner configured one); the page shall load nothing from the internet.
*Baseline:* C-5, CT-10, VE-6. *Verification:* T (strict CSP, request audit in browser test), I (web log).

**HLR-24 Secure access.** MIA shall be reachable from other devices only over HTTPS inside the home network or the owner's tailnet; shall require a token for actions that change shared data or delete history; shall check origins and limit message rates.
*Baseline:* OP-4, OP-5. *Verification:* T, D (a phone outside the home network, not yet done).

**HLR-25 Operable.** MIA shall be installable and runnable from a single configuration file and one command (venv or compose stack), shall shut down in an orderly way that saves her memory, shall back up and restore her data, and shall report missing options after an update.
*Baseline:* OP-1..OP-3, OP-6. *Verification:* T, D.

**HLR-26 Efficient on the given hardware.** MIA shall give a chat answer's first text within seconds on the light model, shall keep every task under explicit budgets (steps, seconds, calls, tokens), and shall end a run that exceeds a budget with what she has and a statement of what is missing.
*Baseline:* C-2, CT-9, RS-9, CORE 1.8. *Verification:* M.

**HLR-27 Room to grow (postponed).** MIA shall keep her state behind storage interfaces so that several instances can later share one memory in a database without changing the components that use it.
*Baseline:* OP-7, CT-8. *Verification:* I now, T when built. *Status:* postponed by decision of 2026-10-21.

## 4. Priorities and the gap between baseline and target

| Group | Today | Main gap | Suggested order |
|---|---|---|---|
| Interaction (HLR-01..06) | built | C6 extras; real-phone and Tailscale try-outs | maintain |
| Intelligence (HLR-07..10) | mostly built | storytelling, schedule, graph-to-runner generation, variants | after research |
| Trust (HLR-11..13) | built, not measured | measure verification styles and calibration; verifier-vs-generator error sharing | next, cheap |
| Research (HLR-14..17) | lookup built; review phase 1 to 2b built | real reference cases (2c paused), full text, baseline review (2e), numbers (2f), then screening and roles | **first**: it is the project's research question |
| Memory and behaviour (HLR-18, 19) | early design only | everything in CORE 13a | after the review baseline |
| Observability (HLR-20..22) | built | context assembly in running pipelines; judge calibration; bandit | continuous |
| Operation (HLR-23..27) | built | Tailscale try-out; database postponed | maintain |

This ordering follows the owner's redirect of 2026-10-21 (research as literature review first) and the principle that nothing is claimed without a baseline number.

## 5. Decisions needed before the model is final

1. Confirm the GPU (12 GB constraint; sources name two cards).
2. Accept the unique-id repair of duplicate `RV44`, `RV45`, `L1..L6` (baseline section 4, item 4), so that SysML ids can map one to one onto detailed requirements.
3. Accept the single privacy statement of HLR-23.
4. Decide whether the detailed documents are edited to the new ids, or the SysML model carries the mapping (the model currently carries it in `doc` text and in the `Trace` metadata).
5. Choose the next work item after the model: HLR-15 phase 2c (confirm labels of the four real cases), or measuring HLR-11 (verification styles).
