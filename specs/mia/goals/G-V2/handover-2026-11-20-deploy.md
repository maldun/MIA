# Hand-over G-V2 (2026-11-20): the Deploy phase of release v0.2.1 in a fresh session

Start with `/home/maldun/prog/Python/MIA/CLAUDE.md`, then this file, then `/home/maldun/prog/Python/MIA/specs/mia/goals/G-V2/release-notes.md` (the "For deployment" block) and `/home/maldun/prog/Python/MIA/deploy/RUNBOOK.md`. Load `dev-workflow`, `deploy-phase`, `agent-app` and `agent-app-deploy`. G-V2 is closed (owner, 2026-11-20); what is left of it is in `remainder-for-next-goal.md` and belongs to a new goal, not to this phase.

## State
- Release: tag `v0.2.1` on `6f44b59c` (pushed 2026-11-20), the iteration-2 release with G-V2 and G-V3. `v0.2.0` (pushed early on `4a3a74c9`) has the same code and no CHANGELOG or release notes; do not deploy it.
- Verified with accepted deviations (D-358 for G-V2, D-354 for G-V3). Checks at the tag: unit suite 2503, JS 186, smoke SMOKE-MIA-001 green 2026-11-20 (fresh clone, one config file, one command, 5 services, chat answered).
- Not yet validated in the field; Validate is a later phase.

## What the phase has to do
1. **Artifact.** `deploy/build.sh` does not exist; the release says "built from the tag in CI". **Gap, decide with the owner:** write `deploy/build.sh` (a Plan item, it needs a task) or deploy from the tagged checkout with the compose stack as in v0.1.0. Do not build on the laptop without the owner saying so.
2. **Preflight on the target** (`deploy/preflight.sh`, and `python deploy/preflight_agent.py --pins specs/mia/eval-spec.md --ollama <url>`): the pin MP-light `gemma4:12b-it-qat`, digest `sha256:38044be4f923e5a55264ed7df4eaac2676651a905f735197c504045140c02bd3`, `num_ctx` 8192, temperature 0, seed 7; GPU access, free VRAM (16 GB RX 7800 XT), PostgreSQL, sandbox backend, search engine. A digest mismatch stops the phase (a model change needs an amendment). The full model `gemma4:26b` is not a pin of this release.
3. **Install** from the tag: `deploy/up.sh rocm db` (AMD, see RUNBOOK). The `deploy/.env` is the machine's own file and is not in git.
4. **Smoke tests** on the target: `tests/smoke/smoke_fresh_install.py` (SMOKE-MIA-001), `smoke_stack.py`, `smoke_gate.py`; they are protected, never edit them.
5. **Smoke eval:** cases tagged `smoke` (only `verdicts_wikidata` has them: 3 cases). Reference run on master 2026-11-20 (3 repeats, MP-light, `verify.single@1`): 6 of 9, `bridge-year-true` (Q110994774) fails 3 of 3, as in the old-runner baseline. A different outcome is a finding. Real model run: `ListAgents` first, tell a running session, release it afterwards.
6. **Acceptance records and the graph path.** `conversion_dir` `data/conversion` is git-ignored. The five records (`research`, `plan_question`, `verify_claim`, `extract_claims`, `verify_computable`) exist on the owner's laptop only; on the target `bound_checks` finds none, so every skill runs on the old runner until the owner writes records with `tools/accept_conversion.py` (needs the run files in `data/eval/`, also git-ignored). Decide with the owner whether the target gets the records; record which skills run on which path in the deployment record.
7. **Rollback:** previous image or checkout (`v0.1.0` or the last deployed state), the previous model digests (do not `ollama rm`), the skill and pipeline versions (versions of the five skills and pipelines are unchanged since 2026-10-20; `lookup`, `review`, `search` are at 2 now, the digest step at 8). Test the rollback once.
8. **Deployment record** `specs/mia/deployment/deployment-record.md` from the skill's assets, with the agent section: pins found, preflight output, smoke eval table, sandbox status, rollback test. **Current-state deployment:** `specs/mia/deployment/current-state.md` does not exist; creating it is the owner's decision (M51), ask.
9. **Freeze the pins for Validate** (no pulls, no skill edits on the target); note the run-log settings (what is stored, retention, feedback controls).

## Known limitations to carry into the record
TD-86 to TD-90 (converted path: no live trust and lifecycle, no budgets and stop, dev-only decision, `research.escalate@3` vs `@1`, IF-103 real half skipped), V2-6 (no red-team case for THR-011), TD-81 to TD-85, the script check in the deployed stack may be off (`sandbox_backend: none`, TD-24 of v0.1.0: check the setting). Two acceptance scripts fail on master (`test_decide_guard.py`, `test_judge_calibration.py`, `behaviour.FUNCTIONS`), not a deploy problem. Speed difference of the converted and the old runner (V2-4) goes to Validate: if you time one skill on both paths on the target, note it.

## Traps
- Facts about the machine come from the machine (`fastfetch`, driver files, `ollama show`), not from documents.
- Worktrees vanish: another process deletes merged branches and worktrees. `git worktree list` before every `cd <worktree> && ...`; full absolute paths.
- Own worktree: `cd /home/maldun/prog/Python/MIA && git worktree add ../MIA-deploy-v021 -b deploy/v0.2.1 v0.2.1`; never create a venv, interpreter `/home/maldun/prog/Python/venvs/mia312/bin/python`.
- Name the paths in every `git add`; never `git add -A` in the main checkout (untracked there, not ours: `eval/baselines/verdicts_*__devsample.jsonl`, `specs/mia/goals/G-V2.CONVERT/handover-2026-11-16-convert-complete.md`, `specs/mia/goals/G-V2.CONVERT/verification-report.md`, `templates/UI/`).
- Protected paths (deny rules): `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `benchmarks/`, `eval/suites/`, `eval/baselines/`, `deferred.md`, `stages.yaml`. A change there is a patch in `specs/mia/amendments/` for the owner with a script in `tools/` that shows the diff before `--do`.
- Do not tag, push or merge; the owner does. A running stack on the laptop may hold the Ollama server: look before a real model run.

## Owner items outside this phase
The decision on `deploy/build.sh`, `current-state.md`, the records for the target, the new goal for the remainder, approval of the Draft requirements, cleaning old worktrees and branches (including `/home/maldun/prog/Python/MIA-commit-g-v2-work`, branch `close/g-v2`).

## Start prompt for the next session (paste it)
> Deploy phase of release v0.2.1 (G-V2 and G-V3). Read `/home/maldun/prog/Python/MIA/CLAUDE.md`, then `/home/maldun/prog/Python/MIA/specs/mia/goals/G-V2/handover-2026-11-20-deploy.md`, the release notes next to it and `/home/maldun/prog/Python/MIA/deploy/RUNBOOK.md`. Load `dev-workflow`, `deploy-phase`, `agent-app` and `agent-app-deploy`; work in your own worktree from the tag; change no code, tests, suites or baselines. Start with the preflight and ask me by questionnaire about the build gap (`deploy/build.sh`), the records for the target and `current-state.md`. Do not tag or push.
