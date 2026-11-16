# Hand-over G-V2.CONVERT (written 2026-11-07): Plan steps 0 to 5 done, next is Step 4 (red tests) in a dedicated session

Read `CLAUDE.md`, then this file, then `goals/G-V2/parallel-work.md` (ID ranges and shared-file rules). Skills: `dev-workflow`, `plan-phase`, `agent-app`, `agent-app-plan`, `decomposition` (the last three are not registered with the Skill tool: read their `SKILL.md` under `~/.claude/skills/`). Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-convert`, branch `goal/v2.convert`, master merged in (last merge at `b5bed0f` and `bb9b66f`). Not pushed; the push and the merge are the owner's.

## Where things stand
- Commits of this line, newest first: `2e981ca` (115 approved), `e18b59e` (059, 062, 063, 066 approved), `6bbc7c1` (plan.md), `95d8bbf` (stages.yaml comment), `ef946ce` (review edits), `4351963` (plausibility), `71c3d5d` (merge of master), `2798e2a` (Step 3 material, IDs in own ranges).
- Scope: REQ-WFM-057 to 066, 069 and the per-skill criteria **REQ-WFM-110 to 115** (REQ-WFM-059 was split per skill because its placeholder `Eval criterion` did not parse, `agent_check` A2). Checks: TC-WFM-057 to 066, 069, 110 to 115. Test requirements `TR-CONVERT-001..` in `specs/mia/test-requirements.md`. Amendment note `specs/mia/amendments/A-120-note.md` (proposed, not applied). Eval spec section "G-V2.CONVERT" at the end of `specs/mia/eval-spec.md` (skill-to-suite table, criteria, error rates, baselines).
- Review log: **approved** 057, 058, 059, 060, 061 to 066, 069, 115. **Held in Draft:** 110 to 114 (rated questionable with a probe; approved only after the baseline probe, owner decision of 2026-11-07). 068 and 070 are TOOLBOX scope, not ours.
- Plan for the implementation: `goals/G-V2.CONVERT/plan.md` (tasks T-CV-01 to 09, preconditions P1 to P6).

## Decisions of the owner this session (all in the files; D-260 is in `review-log.md` on master)
- Per-suite criteria (110 to 114) instead of one criterion in 059; 115 is a Test (output equality) for the rule-based `extract_claims_rules`.
- Nine skills stay on the old runner with a recorded reason (chat, check_speech, memory_write, summarize: "own later subgoal, closer integration"; the five review skills: no suite of their own, EV-review_toy has 7 cases). Open: whether the review skills get a suite in that later work.
- REQ-WFM-062 is Must; REQ-WFM-063 criterion names the automatic snapshot "before restore of <name>" with the owner as author; REQ-WFM-066 defines "owner" as the account that creates accounts (D-260 B).
- Plausibility (D-260): 066 plausible; 059 and 110 to 114 questionable with the probe "record the baselines on MP-light in Plan Step 4 (results only), then judge the margin 0.10"; 058 basis: model replies and tool results both scripted from a recording of the old run. Records written in `specs/mia/plausibility.yaml`; **proposals** for 057, 058, 060 to 065, 069, 115 sit in `specs/mia/plausibility-proposal.yaml` and wait for the owner's rating. No records for FR-36/37/38/40/45/47 (the owner rates those).

## What the next session does
1. **Step 4, red tests (dedicated session, not the implementing one).** Folders `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `benchmarks/` are protected and do not exist for G-V2 yet; the task of this session is to create them from `test-spec.md` and `test-requirements.md` for TC-WFM-057 to 066, 069, 115 (stage 2) and the helper for recording and replaying the old run (T-CV-01). Use `@pytest.mark.req("REQ-WFM-nnn")` and the TC id in the docstring; tests must fail for the right reason (assertion, not ImportError); recalculate one expected value by hand and show it. Commit as `test: acceptance tests for G-V2.CONVERT (red)`, tag `plan-baseline-it2`. The contract suites for IF-301 v2 and IF-203 v1 only after the owner reviews the contract text (D-188). Needs the owner's go to touch the protected folders.
2. **Owner tasks that block Implement** (also in plan.md): apply A-120 (tag `split:dev` on the cases of EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction); record the baselines as run files (dev, 3 repeats, MP-light, per skill and variant; today only `.md` summaries exist in `eval/baselines/`, three of five from one run); rate the ten proposed plausibility items; judge the margin 0.10 against the recorded baselines and then approve 110 to 114.
3. **Not before:** G-V2.STORE, MODEL and TOOLBOX merged (merge order STORE, MODEL, TOOLBOX, CONVERT).

## Gaps and traps
- `stages.yaml` has no stage 4 step for TC-WFM-110 to 114 yet; T-CV-09 adds them once the converted runner and the `split:dev` tags exist. `required_for_merge` stays 1 to 3.
- The 2 s per plan in the eval budget of EV-plans is an estimate, not a measured baseline.
- Q-5 in `quality.md` says "same outcomes", the criteria allow a starting margin of 0.10 below the v0.1.0 reference: a small tension, left to the owner.
- Open `agent_check.py` errors are not ours (THR-011 A8, SkillDigestStep A9 and A10). `req_graph.py` G7 errors on WFM-040 to 056, 067, 068, 070, REQ-RUN-016 to 018 and FR-36 to 47 are other subgoals or the parent session. `trace_check.py` warns "no @pytest.mark.req marker" until Step 4.
- **Two sessions wrote into this worktree at the same time** on 2026-11-07 and produced different edits to the same files; check `git status` and the newest `mtime` before editing, and never run two sessions on one worktree.
- Rules of `parallel-work.md`: own ID ranges only (REQ-WFM 110 to 129, REQ-RUN 030 to 039, D-240 to 259, A-120 to 129, TD-50 to 59, SC-40 to 49, TR-CONVERT-, VAL-007 and VAL-011); `review-log.md` is append-only; the SysML requirement block is generated (`python3 -I tools/gen_node_requirements_model.py .` then `bash tools/check_sysml.sh`); `requirements.md` (root), `goals/G-V2/goal.md`, `contracts/`, `tests/acceptance/` are for the parent session or protected. Never `git add -A`; name the paths. Commit messages end with the Co-Authored-By line.

## Checks (run after every change)
```bash
P=~/.claude/skills
python3 $P/dev-workflow/scripts/goal_check.py --spec-dir specs/mia
python3 $P/plan-phase/scripts/req_lint.py specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md --glossary specs/mia/glossary.md
python3 $P/plan-phase/scripts/req_graph.py --spec-dir specs/mia --tests-dir tests
python3 $P/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests
python3 $P/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval
python3 $P/plan-phase/scripts/req_plausibility.py --requirements specs/mia/requirements.md specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md --plausibility specs/mia/plausibility.yaml
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 $P/dev-workflow/scripts/run_stages.py --stages stages.yaml --upto 4 --dry-run
```
Host: model server on port 11434, use the 12B (MP-light), keep runs short. The holdout is never run or opened by an agent.
