# MIA v0.2.1 (2026-11-20)

Iteration 2: G-V2 (skill rework, foundation) and G-V3 (skill run view, spoken-only chat). Not yet validated in the field. The tag v0.2.0 (pushed on commit `4a3a74c9`) has the same code but no CHANGELOG entry, release notes or D-358; v0.2.1 replaces it.

## New
- Skills are records (command, steps, knowledge); wrong records are refused with the reason. Workflow graphs and the skill set are stored as node and edge records (IF-302).
- Toolbox with trust status: a step from outside does not run until the owner allows it.
- Snapshots of the skill set with restore; the state before restoring is kept (IF-102 v7, IF-203 v2, IF-302 v13/v14).
- Five skills (research, plan_question, verify_claim, extract_claims, verify_computable) run on the graph path when an acceptance record exists (`tools/accept_conversion.py`).
- G-V3: Skill run view, spoken-only chat, report file per run (details in `CHANGELOG.md`).

## Changed
- `Core.run` takes the graph path only for a skill with a valid acceptance record in `conversion_dir` (default `data/conversion`); else the old runner.
- The state of skills and graphs lives in PostgreSQL where configured; the file backend stays for the transition.

## Resolved feedback
- FB-08 (report download).

## Goal
- G-V2: exit criterion OC-1 to OC-5 via AC-31, AC-32, AC-34, AC-38, AC-40; out of scope: goals B (skills window), C (context graphs), D (testbench, debates).
- Provisional values for Validate: VAL-007 (converted skill through the UI), V2-4 (speed difference).

## Agent changes
### Models
| Pin | Model | Digest | Change |
|---|---|---|---|
| MP-light | gemma4:12b-it-qat | sha256:38044be4f923... | unchanged |

### Skills and pipelines
| Skill / pipeline | Old | New | What changed |
|---|---|---|---|
| research, plan_question, verify_claim, extract_claims, verify_computable and their pipelines | unchanged since 2026-10-20 | same | now also run from records on the graph path |
| lookup, review, search | 1 | 2 | G-V3.REPORT (`run_report`) |
| digest step | | 8 | G-V3.CHAT, A-160 |

### Eval results (dev only, no holdout: TD-88)
| Suite | Criterion | Converted, dev (3 repeats) | Wording |
|---|---|---|---|
| EV-research | right >= 0.85 | 0.950 (n=20) | not worse on dev |
| EV-plans | >= 0.54 | 0.639 (n=36) | not worse on dev |
| EV-verdicts | >= 0.83 | 0.940 (n=50) | not worse on dev |
| EV-extraction | >= 0.59 | 0.667 (n=51) | not worse on dev |
| EV-computable | >= 0.87 | 0.974 (n=39) | not worse on dev |
Smoke subset on master 2026-11-20 (verdicts_wikidata, 3 cases x 3): 6 of 9, same outcome as the old baseline.

### Red-team and budgets
- No red-team run in this phase; THR-011 has no case (V2-6). Budgets not re-measured (TD-87).

### Baselines
Kept: the old-runner dev baselines of D-355 (owner decision 2026-11-20). No new baseline files.

## Known issues and open deferrals
- TD-86 live trust and lifecycle on the converted path; TD-87 budgets and stop on the converted path; TD-88 AC-34 on dev only; TD-89 research.escalate@3 (check) vs @1 (skill); TD-90 real half of the IF-103 contract suite skipped. Signed by the owner 2026-11-20 (D-355, D-356, D-357).
- V2-6 no red-team case for THR-011; D-309 MODEL deviations (context graph ID not read from the record, F-04); TD-81 to TD-85.
- `test_decide_guard.py` and `test_judge_calibration.py` fail on master (`behaviour.FUNCTIONS`), not G-V2.
- No current-state deployment record exists (`specs/mia/deployment/current-state.md`); none created without the owner.

## Also in this release
- TD-11 option B (speak again through the voice route, verified 2026-11-08) and all of G-V3: see `CHANGELOG.md`, section 0.2.1. Open deferrals of G-V3: TD-82 to TD-85 (signed).

## Statuses at the tag
- Goal G-V2 and its five subgoals: Verified. Requirements REQ-RUN-030 to 035, REQ-WFM-057 to 060, 069, 110 to 115 are still Draft (owner approval open); all other G-V2 requirements are Verified.
- Open paperwork: V2-8 (TC-WFM-110 to 114 in no test-spec table), V2-3 (stale docstring in `skill_converter.py`, Implement), V2-1 (scope wording `REQ-WFM-143`).

## For deployment (Phase 6)
- Artifact: built from tag v0.2.1 by `deploy/build.sh` in CI. **`deploy/build.sh` does not exist: gap for Deploy; no build on the laptop.**
- Target: the reference host (Fedora, RX 7800 XT 16 GB, podman, Ollama).
- Pull model by digest: `gemma4:12b-it-qat` (`sha256:38044be4f923...`); `num_ctx` 8192.
- Services: PostgreSQL, sandbox, search as in the compose stack. The stack starts from a fresh copy (SMOKE-MIA-001 green 2026-11-20).
- Skills with an acceptance record run on the graph path: `conversion_dir` `data/conversion`, records written by the owner with `tools/accept_conversion.py`.
- Smoke eval: cases tagged `smoke` in `verdicts_wikidata`.
