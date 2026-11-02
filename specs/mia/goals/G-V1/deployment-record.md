# Deployment record: MIA v0.1.0

Filled 2026-11-02 from the owner's outputs. Template: `deploy-phase/assets/deployment-record.md` and `agent-app-deploy/assets/deployment-record-agent.md`.

| | |
|---|---|
| Version / tag | v0.1.0 (clone `~/tmp/mia-v0.1.0` of the tag, `git describe` = `v0.1.0`) |
| Goal | G-V1 (iteration) |
| Artifact | image `mia` from `deploy/Containerfile`, `localhost/mia:latest` = `localhost/mia:v0.1.0`, image id `8217ecd0ccf8cd644fd09ecbf66b99f75b77a2feb2b3210523e497911021861f`, built 2026-11-02 21:53 UTC by `deploy/up.sh` on the target itself (no CI, no `deploy/build.sh`: the "never build on the target" rule is not kept here, accepted for a personal workstation) |
| Target | the owner's workstation (Fedora 43, podman), clients in the home network and tailnet |
| Date / by | 2026-11-02 / Stefan Reiterer |
| Configuration | `deploy/.env` (not in git), `deploy/setup_cfg.compose.json` + `deploy/setup_cfg.local.json`; `accounts_enabled` false (compose default, `setup_cfg.local.json` is `{}`); `MIA_BIND` 127.0.0.1 (default); `OLLAMA_URL=http://host.containers.internal:11434` (host Ollama 0.40.5, container `ollama`, rocm image); Kokoro files fetched into the clone's `voice/models/kokoro` |
| Previous version kept at | image `localhost/mia:pre-v0.1.0` (`e37a87782beb`, built 2026-10-31); backup archive `~/tmp/mia-v0.1.0/mia-backup-20261102-2303.tar.gz` |

## Preflight (`bash deploy/preflight.sh`)
```
ok:   podman 5.7.1 | ok: 989 GB free | ok: deploy/.env exists | ok: GPU devices /dev/kfd and /dev/dri
WARN: sandbox_backend is 'none' (the script check is off)
| P1 | server | Ollama 0.40.5 at http://127.0.0.1:11434 | PASS |
| P3 | MP-full | gemma4:26b digest 001e5dafc3c7 = pin | PASS |
| P3 | MP-light | gemma4:12b-it-qat digest 38044be4f923 = pin | PASS |
| P4 | gemma4:12b-it-qat | loaded, 8.0 GB in VRAM, context 8192 | INFO |
Preflight OK
```
Run on the host before the install (the ports 8585/8586 were free then) and again after the rollback (P3 PASS). The Kokoro check (`ae9cba2`) came after the first install.

## Smoke results
| ID | Result | Notes |
|---|---|---|
| SMOKE-MIA-001 | green (2026-11-02) | fresh clone, one config file, page answers, offer printed once, 5 services, first account, chat answered by the real model |
| SMOKE-MIA-002 | **not run** (deferred, TD-26, D-184) | owner's decision 2026-11-02: Tailscale is not installed on the workstation (never tried against a real tailnet, baseline OP-4). NFR-6 / CON-5 evidence by this smoke test is missing; the loopback binding is shown by `ss` (`127.0.0.1:8585`, `:8586`) |
| SMOKE-MIA-003 | green (2026-11-02) | mia alone 220 tests OK (18 skipped), db alone 26 OK, graph alone 14 (7 pass, 7 skipped, TD-23), all 5 services together |
| SMOKE-GATE-001, -002 | green (2026-11-02) | 5 cases on MP-light through the real server; header digest equals /api/tags |
| Recovery (kill and restart) | green (2026-11-02) | `tools/recovery_check.sh` (`1652ddd`): SIGKILL of `mia` while an answer streamed, restart, page back, marker stored, 1004 files with content intact, database answers, new message answered. Note: the check looked at `data/` files only (history is still file-based, TD-21) |

## Agent section
| Item | Found |
|---|---|
| MP-light digest | `sha256:38044be4f923...` = pin (host Ollama 0.40.5, `deploy/preflight.sh` P3 PASS) (pin `sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3`) |
| MP-full digest | `sha256:001e5dafc3c7...` = pin (P3 PASS) (pin `sha256:001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c`) |
| Options in the config | `num_ctx` 8192; temperature and seed for evaluation only |
| Sandbox | `sandbox_backend` none: the `script` check is off |
| Search engine | SearXNG container up (`mia_searxng_1`) |
| Smoke eval | SMOKE-GATE-001/-002: the 5 `smoke` cases (3 Wikidata, 2 VitaminC) green. **Gap:** the other suites have no `smoke` tag (the eval spec asks for 2 per lookup suite and 2 of the review suite); nothing else was run on the target. Seconds per case were not recorded |
| VRAM after the run (`ollama ps`) | preflight: 12B model 8.0 GB loaded at context 8192; no `ollama ps` after the smoke run was taken |
| Rollback tested | yes, 2026-11-02: `localhost/mia:pre-v0.1.0` (`e37a87782beb`) retagged as `latest`, `mia` and `graph` recreated with `--no-build`, container ran image `e37a87782beb`; then forward again to `8217ecd0ccf8` (confirmed by `podman inspect`). `MIA_IMAGE` alone did not recreate the container under podman-compose (RUNBOOK, "Rollback to the previous image"). Old model digests: unchanged host Ollama, preflight P3 after the rollback: both digests equal the pins (PASS) |

## Resolved feedback
None (FB-01 to FB-06 are triaged for the next iteration).

## Deviations from "install from the tag"
- Kokoro files were missing in the clone (untracked, RUNBOOK): `MIA_KOKORO_DIR` pointed at the main checkout's folder. Preflight check, `tools/fetch_kokoro.sh` and `deploy/up.sh voice` added afterwards (commit `ae9cba2`, REQ-OPR-001); the deployed tree is `v0.1.0` without that commit.
- Voice lines (`voice/expressions/*.wav`) are git-ignored and copied at image build: none in the clone or the image (0 files): the faces show and MIA stays silent on mood lines (D-167, D-171); `python tools/make_voice_lines.py` and a rebuild would add them.
- `mia_ollama_1` (the stack's own Ollama) is running idle next to the host Ollama: `ollama list` in it is empty, so no unchecked model is in use; MIA uses the host Ollama through `OLLAMA_URL`. `podman rm -f mia_ollama_1` frees it.
- Preflight, `tools/fetch_kokoro.sh`, `deploy/up.sh voice` and `tools/recovery_check.sh` were added during this deployment (`ae9cba2`, `1652ddd`); the deployed tree is `v0.1.0` without them.

## Known issues and open deferrals
See `release-notes.md`; TD-01 to TD-04, TD-06 to TD-22.

## Ready for validation
Yes, except SMOKE-MIA-002 (skipped by the owner, 2026-11-02; the owner confirms the hand-over). Versions and pins are frozen during validation.
