# Research: MIA as it is on 2026-10-24

Read-only. Written while collecting the requirements and converting them to the HLS. Facts carry a source; what was not looked at is listed at the end.

## Questions
1. What do the existing requirement documents ask for, and which of it exists? (answer: `baseline-requirements.md`, status per group)
2. Which hardware and models does MIA run on, and what is measured?
3. Where do the sources contradict each other?
4. What does the agent do today, and how well (measured baselines)?

## Summary
- MIA is a personal assistant with a 3D anime character, a chat page, a local voice and a "core" of skills, pipelines, verification and logging for small local models. A literature-review task is the next big goal. Five requirement documents (1 900 lines) plus the README describe it; `baseline-requirements.md` condenses them into 10 capability areas with a status each.
- Built: character, chat page and server, voice, skills and pipelines, library, hard checks, sandbox, verification styles (as drafts), lookup pipelines, event log, context graph, explain tool, evaluation harness with 10 suites (435 cases), scholarly tools, the toy tier of the review benchmark, compose deployment.
- Not built: literature-review pipeline (phases 2d to 6), memory beyond the early summary-based dreaming, out-of-band emotion, lessons and consolidation, storytelling, schedule, character variants, router and bandit, shared database (postponed).
- Hardware (measured today): AMD Ryzen 9 5900X (24 threads, 4.95 GHz), AMD Radeon RX 7800 XT with **16 GB** VRAM (driver: 17 163 091 968 bytes), 62.66 GiB RAM, Fedora 43, KDE Plasma on Wayland, Linux 6.18.13 (`fastfetch`, `/sys/class/drm/card*/device/mem_info_vram_total`). The sources said 12 GB; that was wrong and is corrected.
- All recorded baselines are on the **light** model `gemma4:12b-it-qat` (num_ctx 8192) (`eval/baselines/*.md`). There is no baseline for the full model `gemma4:26b`, none for chat quality, and none for any behaviour with the persona calibration.
- The model server was not running when this was written, so the model digests are unknown (`curl localhost:11434/api/tags` returned nothing). Pins need digests (agent-app convention 6).

## Relevant files (selection)
- `setup_cfg.example.json:9-16` models `gemma4:26b` / `gemma4:12b-it-qat`, `num_ctx` 8192, `keep_alive` 30m, `mode` rocm
- `ui/REQUIREMENTS.md`, `ui/REQUIREMENTS_CHAT.md`, `ui/REQUIREMENTS_CORE.md`, `ui/REQUIREMENTS_RESEARCH.md`, `deploy/REQUIREMENTS_DB.md`: the five documents
- `ui/README.md`: what was built per phase (the source of the status column)
- `core.py:24` `Core` loads a skill, takes the pipeline from the library, runs and logs
- `communicator.py`: history, calibration, emotion keyword, penalties, dreaming
- `chat_service.py`, `chat_api.py`, `chat_log.py`, `moods.py`: chat server side
- `checks.py`, `sandbox.py`, `broker.py`, `verification.py`: hard checks, sandbox, verification styles
- `events.py`, `run_log.py`, `content_store.py`, `context_graph.py`, `run_explain.py`, `reproduce.py`: log and views
- `harness.py`, `metrics.py`, `eval/suites/*`, `eval/baselines/*`: evaluation
- `review_request.py`, `scholar.py`, `source_trust.py`, `review_case.py`, `review_score.py`, `pdf_text.py`: research phase 1 to 2c
- `deploy/compose.yaml`, `deploy/up.sh`: container deployment

## Measured behaviour of the agent (from the baselines, not re-run today)
| Area | Result | Source |
|---|---|---|
| Verification, single voice vs cops (light model) | single passes 9 of 75 wrong claims (all near-miss numbers); cops passes 0 of 75 but costs 4.7x time (6.2 s vs 1.3 s per claim); the lead rests on 3 distinct claims, sign test not significant | `eval/baselines/verdicts-styles.md` |
| Consistency (3 samples) and jury (3 experts) | identical to single on this suite, at 3x the calls | same |
| Trial (with rebuttals) | too cautious: 3 false fails, 4 abstentions, 9.6x time | same |
| Suites | 10 suites, 435 cases: hard_checks 118, behaviour 67, extraction 51, verdicts 50, computable 39, plans 36, web_checks 31, research 20, research_compound 16, review_toy 7 | `wc -l eval/suites/*/cases.jsonl` |
| Review benchmark | toy tier (13 fictional papers, 7 cases) built; real cases paused at about 30 of 44 reference resolutions of the first one | `ui/REQUIREMENTS_RESEARCH.md` status of phase 2c |

I have not re-read the other baseline files beyond their first lines (computable, extraction, research-*).

## Contradictions between the sources
Twelve, listed in `baseline-requirements.md` section 4; two are resolved (GPU, duplicate ids).

## Constraints and risks found
- Eval material has labels that were set by one person (the owner) and the earlier suites are "starter-sized"; no holdout split exists yet (the agent-app workflow requires one for decisions).
- `unittest`-style tests, no pytest markers: the workflow's `trace_check.py` will warn for test-verified requirements without markers (conventions-agent.md, section 10).
- The SysML text of this repository has not been parsed by a SysML tool (`KNOWN_RISKS.md`).
- Baselines compare against the light model; a model change (the full model, or a new Gemma tag) needs a new baseline.

## Not investigated
The Godot project internals, the JavaScript chat modules beyond file names, `communicator.py` behaviour in detail, the real content of `calibration.txt` (persona, not in git), `data/runs` of real use, whether the full test suite passes today (814 tests were reported on 2026-10 by the README commit), the Tailscale path, the contents of the other baseline files.
