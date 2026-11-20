# Deployment record: MIA v0.2.1 → reference host (maldun's workstation)

**Kind:** release   **Commit:** 6f44b59c (tag v0.2.1) + dc63f056 (`deploy/build.sh`, branch `deploy/v0.2.1`, files not in the image)   **Date:** 2026-11-20   **Known gaps:** see Known issues
**How to reach it:** http://127.0.0.1:8585, https://127.0.0.1:8586 (self-signed)
**Goal:** G-V2 + G-V3 (iteration 2)   **Deployed by:** Claude session mia-aa, owner approved each step
**Artifact:** image `localhost/mia:v0.2.1`, id `439429d0b8d5cf859f44ceb49cea6911d8900a08438a17ef9f64220dc8eef626`, saved as `dist/mia-v0.2.1.tar` (SHA-256 `8670ca0b60c2fc9faa08a143bef7193c64600667466bbe5b0083e02216a8ab16`, untracked), base `python:3.12-slim@sha256:2b4f19da...`. Built **on the target** with `deploy/build.sh v0.2.1` (no CI exists; accepted for a personal workstation as for v0.1.0, amendment note A-BUILD).
**Target:** Fedora (kernel 6.18), podman 5.7.1, RX 7800 XT 16 GB, host Ollama 0.40.5 (podman container `ollama`, port 11434), loopback only.
**Configuration:** `deploy/.env` (machine's own, not in git): `OLLAMA_URL=http://host.containers.internal:11434` + generated secrets; `deploy/setup_cfg.compose.json` of the tag. Start: `deploy/up.sh rocm db up -d --no-build`.

## Preflight
| Check | Result |
|---|---|
| `deploy/preflight.sh` | OK; warnings: no character page, no Kokoro voice, no voice lines, `sandbox_backend: none` |
| `preflight_agent.py` | P3 MP-light and MP-full digests = pins; PASS |
| GPU devices, ports 8585/8586, disk | ok (980 GB free) |

## Smoke tests
| Test | Result |
|---|---|
| SMOKE-MIA-001 `smoke_fresh_install.py` | green |
| SMOKE-MIA-003 `smoke_stack.py` (mia/db/graph alone, 5 services together) | green |
| SMOKE-GATE `smoke_gate.py` | **not run: red by environment**, suite `verdicts_vitaminc` is git-ignored and absent in the tag checkout (see Known issues) |
| Running stack: page 200, 5 services up | ok |

## Rollback
Previous image `localhost/mia:pre-v0.2.1` (id `c58b66d1...`, built 2026-11-07). Command: `podman tag localhost/mia:pre-v0.2.1 localhost/mia:latest; deploy/up.sh rocm db down; deploy/up.sh rocm db up -d --no-build`. **Tested 2026-11-20:** old image ran, page 200, model digests unchanged (PASS), then rolled forward to v0.2.1 (image id checked). Data volumes untouched. Note: `podman rm` of a single container fails on dependants; use `down` then `up --no-build`.

## Known issues
- **F-1 build context:** there is no `.dockerignore`. `deploy/up.sh` (default `--build`) baked `deploy/.env` (secrets) and the 1 GB `dist/` tar into a rebuilt image. Found, removed (image deleted, stack runs the clean `v0.2.1` image, checked: no `.env`, no `dist/` inside). Never start with the default `--build` after `build.sh SAVE=1`; use `--no-build`. Fix = Plan task (`.dockerignore`), not done here.
- **F-2 smoke gate:** `verdicts_vitaminc` is git-ignored; the gate needs it (2 of its 5 cases). Open: owner supplies the suite from the laptop or the gate is run there.
- **F-3 records:** `data/conversion` (five acceptance records) is not on the target yet: all five skills run on the **old runner**. Owner decided to copy them; source path still to be given. Update this record when done.
- Carried from the handover: TD-86 to TD-90, V2-6, TD-81 to TD-85, `sandbox_backend: none` (script check off, TD-24), failing master acceptance scripts `test_decide_guard.py`, `test_judge_calibration.py`.
- Not installed: character page, Kokoro voice, voice lines (MIA answers in text).

## Open deferrals and shortcuts
- `deploy/build.sh` is a new script without a requirement id; Plan assigns one (A-BUILD note).

## Validation hand-over
Ready for validation: **not yet**, after F-2 and F-3 are settled. Version frozen during validation: v0.2.1 image `439429d0b8d5`.

## Agent deployment

**Target:** reference host, RX 7800 XT 16 GB, ROCm, Ollama 0.40.5   **Release:** v0.2.1   **Date:** 2026-11-20

### Pins on the target
| Pin | Model | Digest expected | Digest found | Options in the config | Result |
|---|---|---|---|---|---|
| MP-light | gemma4:12b-it-qat | 38044be4f923... | 38044be4f923 | num_ctx=8192 (loaded), temperature 0, seed 7 per eval-spec | PASS |
| (not a pin) | gemma4:26b | 001e5dafc3c7 | 001e5dafc3c7 | | present |

### Preflight
Ollama 0.40.5; MP-light loaded, 8.0 GB VRAM of 16, 100 % GPU, context 8192.

| Check | Result |
|---|---|
| GPU access, driver | `/dev/kfd`, `/dev/dri` present |
| Free VRAM | 8.0 GB used by the loaded model; other residents not measured |
| Sandbox backends | `sandbox_backend: none`: the `script` check is off (known limitation) |
| Search engine | `mia_searxng_1` up (a second, older `mia-searxng` runs on 8590, not ours) |
| Ports, certificates | 8585, 8586; self-signed |

### Smoke eval (cases tagged smoke, dev split)
Run: `python tools/eval.py run verdicts_wikidata --tag smoke --pipeline verify.single@1 --pin MP-light --repeats 3` (old runner), saved as `data/eval/verdicts_wikidata__default__20261120-130831.jsonl` (git-ignored).
| Suite | Cases × repeats | Same outcome as reference | Changed cases | Seconds per case | Result |
|---|---|---|---|---|---|
| verdicts_wikidata | 3 × 3 | yes: 6 of 9; `bridge-year-true` 0 of 3, others 3 of 3, stable | none | 1.62 s per run (14.6 s total) | PASS (as reference of 2026-11-20 on master) |
No `eval_decide` against the baseline file (it is not part of the tag checkout's reference run); verdicts_vitaminc smoke cases not run (F-2).

### Rollback
Previous image `pre-v0.2.1`; model digests unchanged (no pin change, nothing pulled or removed). Tested 2026-11-20: PASS (see above).

### Frozen during validation
Pins and skill versions to be frozen from the day F-2 and F-3 are settled; no pulls, no skill edits on the target. Run logs: in the data volume `mia_mia-data` (histories, logs); retention and feedback controls as in v0.1.0 (not changed).
