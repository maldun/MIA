# Deployment record: MIA v0.1.0 (TEMPLATE, filled where the repository knows the answer)

Blanks `<<...>>` are filled by the owner at the deployment. Template: `deploy-phase/assets/deployment-record.md` and `agent-app-deploy/assets/deployment-record-agent.md`.

| | |
|---|---|
| Version / tag | <<v0.1.0 or the tag the owner sets>> |
| Goal | G-V1 (iteration) |
| Artifact | image `mia` from `deploy/Containerfile`, sha256 <<digest>>, built <<by whom, where; no CI build script yet>> |
| Target | the owner's workstation (Fedora 43, podman), clients in the home network and tailnet |
| Date / by | <<date>> / Stefan Reiterer |
| Configuration | `deploy/.env` (not in git), `deploy/setup_cfg.compose.json` + `deploy/setup_cfg.local.json`; `accounts_enabled` <<true>>; `MIA_BIND` <<...>> |
| Previous version kept at | <<path/image>>; backup archive <<file>> |

## Preflight (`bash deploy/preflight.sh`)
<<paste the output>>

## Smoke results
| ID | Result | Notes |
|---|---|---|
| SMOKE-MIA-001 | green (2026-11-02) | fresh clone, one config file, page answers, offer printed once, 5 services, first account, chat answered by the real model |
| SMOKE-MIA-002 | <<>> | phone, tailnet |
| SMOKE-MIA-003 | green (2026-11-02) | mia alone 220 tests OK (18 skipped), db alone 26 OK, graph alone 14 (7 pass, 7 skipped, TD-23), all 5 services together |
| SMOKE-GATE-001, -002 | green (2026-11-02) | 5 cases on MP-light through the real server; header digest equals /api/tags |
| Recovery (kill and restart) | <<>> | |

## Agent section
| Item | Found |
|---|---|
| MP-light digest | `sha256:38044be4f923...` = pin (host Ollama 0.40.5, `deploy/preflight.sh` P3 PASS) (pin `sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3`) |
| MP-full digest | `sha256:001e5dafc3c7...` = pin (P3 PASS) (pin `sha256:001e5dafc3c77684c2307ebc6ab8e336e10c9b18eca52acf547d72fc83c3ca8c`) |
| Options in the config | `num_ctx` 8192; temperature and seed for evaluation only |
| Sandbox | `sandbox_backend` <<none>>: the `script` check is off |
| Search engine | SearXNG container <<up>> |
| Smoke eval | <<cases run; tolerance: the same outcome on every smoke case>> |
| VRAM after the run (`ollama ps`) | <<>> |
| Rollback tested | <<yes/no, date>>; old digests confirmed <<>> |

## Resolved feedback
None (FB-01 to FB-06 are triaged for the next iteration).

## Deviations from "install from the tag"
- Kokoro files were missing in the clone (untracked, RUNBOOK): `MIA_KOKORO_DIR` pointed at the main checkout's folder. Preflight check, `tools/fetch_kokoro.sh` and `deploy/up.sh voice` added afterwards (commit `ae9cba2`, REQ-OPR-001); the deployed tree is `v0.1.0` without that commit.
- Voice lines (`voice/expressions/*.wav`) are git-ignored and copied at image build: <<present in the install or MIA silent on mood lines>>.

## Known issues and open deferrals
See `release-notes.md`; TD-01 to TD-04, TD-06 to TD-22.

## Ready for validation
<<Yes/No>>. Versions and pins are frozen during validation.
