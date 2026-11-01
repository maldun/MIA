# Deploy plan: G-V1 (DRAFT of 2026-11-01)

Prepared by the coding agent while the goal Verify is still to be done. Nothing here is run; the owner runs it on the workstation after the tag exists. Phase 6 skills: `deploy-phase`, `agent-app-deploy`. Operating details: `deploy/RUNBOOK.md`, `deploy/README.md`.

## Target and who does what
| | |
|---|---|
| Target | the owner's workstation (Fedora 43, Ryzen 9 5900X, RX 7800 XT 16 GB, 62 GB RAM, podman); clients: phones and computers in the home network and the tailnet |
| Who runs it | the owner (a personal system, but the machine has an open hardware problem, see "Risks"); the coding agent prepares and assists, uses no credentials |
| When | days before the first users depend on it, not the night before |
| Artifact | the `mia` image built from the **tag** (`deploy/Containerfile`; `deploy/build.sh` does not exist: decide how CI or the owner builds it, never on a laptop for a release) |
| Models | pulled by digest: MP-light `gemma4:12b-it-qat` `sha256:38044be4f923...`, MP-full `gemma4:26b` `sha256:001e5dafc3c7...` (drafts `specs/mia/eval-spec.md`, `specs/number-gate/eval-spec.md`); `deploy/setup_cfg.compose.json` names the same two |

## Steps
1. **Before anything:** `deploy/up.sh backup` (the archive holds the database and the data folder, REQ-OPR-005); keep the previous image and do not `ollama rm` any model.
2. **Preflight:** `bash deploy/preflight.sh` (new in this draft; tested by `tests/test_preflight.py`). It checks podman, free space, ports, GPU devices, what a fresh checkout lacks, the sandbox backend, and the model server against the pins (`deploy/preflight_agent.py`). FAIL stops; a moved digest is a model change (amendment), never an install detail.
3. **Install from the tag:** check out the tag in a new folder, copy `deploy/.env`, run `deploy/up.sh db` (AMD: `deploy/up.sh rocm db`). The first start adds the SearXNG secret and the database password and offers the owner account once.
4. **Smoke tests on the target** (below). Red: roll back or fix; never hand a failing deployment to validation.
5. **Record:** fill `deployment-record.md` (this folder); set the FB items resolved to *Deployed* (none in this release).
6. **Freeze for validation:** no pulls, no skill or prompt edits on the target during validation; urgent fixes go through the loop as a patch version.

## Smoke tests (`tests/smoke/`) and what they cover
| ID | Where | What | Run by |
|---|---|---|---|
| SMOKE-MIA-001 | `python tests/smoke/smoke_fresh_install.py` | fresh clone of the committed HEAD, one config file, one command, the page answers, the first-account offer appears once (REQ-OPR-001, -002) | owner |
| SMOKE-MIA-002 | by hand, phone outside the home network | Tailscale + HTTPS: the page loads, a message is answered, no public port (NFR-6, CON-5) | owner |
| SMOKE-MIA-003 | `python tests/smoke/smoke_stack.py` | each container alone against the mocks, then all together, the https front answers on `/` and `/graph/` (NFR-9) | owner |
| SMOKE-GATE-001, -002 | `python tests/smoke/smoke_gate.py` | the 5 smoke cases of the number gate through the real server on MP-light (3 Wikidata cases must answer unclear) | owner |

- **Smoke eval for the other suites:** the draft eval spec asks for 2 cases per lookup suite and 2 of the review suite chosen by the owner; only the 3 Wikidata cases are tagged `smoke` today (`tools/tag_smoke_cases.py`). Choose and tag the rest before the release or record the gap in the deployment record.
- **Qualities only the target shows:** installability (the script without manual fixes), recovery (kill the `mia` container mid-answer, restart, check history and data), timing on the target (BM-MIA-001/-002 are deferred, TD-16; record first-text time anyway).

## Rollback
- The previous release's folder and image stay; the data volume and the database are saved by step 1.
- Back: `deploy/up.sh db down`, start the previous folder's `deploy/up.sh db`, and if data changed, `deploy/up.sh restore <archive>` (it first saves the current state).
- Check afterwards that the models in use are the old digests (`bash deploy/preflight.sh` on the old checkout). Test the rollback once before the users depend on this release.

## Risks and known limitations to record
- **Hardware:** identical fatal CPU machine checks (CPU 18, bank 5) on every reboot since 2026-10-17, at MIA shutdown. An update that stops the stack can end in a reboot: back up first, do not start it under load, and do not run the full stack and the 26B model together with other heavy jobs.
- `sandbox_backend` is `none` in the compose config: the `script` check is off (known limitation; red-team cases for scripts are not exercised by this deployment).
- Login is off by default (`accounts_enabled: false`): turn it on before other people use it (RUNBOOK, "The login").
- Files a fresh checkout lacks (RUNBOOK): character page, VRM model, Kokoro models, voice lines. Without them MIA answers but has no character and no voice.
- The Graph app is the T-01 mockup behind `/graph/` (D-177).
- No `deploy/build.sh`, no CI log: `merge_gate.py` and the stage log have nothing to read yet.

## Open deferrals that go with the release
TD-01 to TD-04, TD-06 to TD-11, TD-12 to TD-22 (`specs/mia/deferred.md`); listed in the release notes.

## Hand-over to Validate
The validation plan is `validation-plan.md` in this folder. Give the users the URL, their accounts, the release notes and the feedback channel.
