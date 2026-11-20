## G-V2: Skill rework, foundation (iteration goal, goal A; version v0.2.0 together with G-V3)

**Goal:** G-V2 (iteration, supervised)   **Branch:** none. STORE, MODEL, TOOLBOX, CONVERT and SNAPSHOT are all already in `master`; there is no `goal/v2` branch. So the update of the branch, the range-diff and the history cleaning (commit-phase steps 1 to 3) have nothing to act on. This record documents what is already merged.
**Accepted by:** Stefan Reiterer (owner); he tags
**HLS:** `specs/mia/high-level-spec.md`   **Goal record:** `specs/mia/goals/G-V2/goal.md`
**Verification report:** `specs/mia/goals/G-V2/verification-report.md` (Verified with accepted deviations, owner 2026-11-20)
**Subgoals:** G-V2.STORE, G-V2.MODEL, G-V2.TOOLBOX, G-V2.CONVERT, G-V2.SNAPSHOT (each with its own report and log)

### What changes for the user
- A skill is one description (record): command, steps and knowledge; a wrong description is refused with the reason (OC-2).
- Skills with an acceptance record run on the workflow graph path; all others stay on the old runner (OC-1).
- Steps that arrive from outside are untrusted: they do not run until the owner allows them (OC-3, toolbox).
- Snapshots of the skill set: go back to a named moment; the state before going back is kept (OC-4).
- A fresh copy starts with one config file and one command (OC-5, SMOKE-MIA-001 green on 2026-11-20).

### Checks on the integration candidate (2026-11-20, clean worktree `/home/maldun/prog/Python/MIA-commit-g-v2-work` of master `7c1bb4bc`)
Master differs from the verified commit `740d7fa3` only by three docs commits (verification report, hand-over), no code, test or suite.
| Check | Result | Reference of the report |
|---|---|---|
| Unit suite in six pieces | 678, 513, 596, 427, 20, 269 = 2503, all OK (skips and expected failures as recorded) | 2503 |
| JS | 186 of 186 | 186 |
| `check_sysml_model.py` | OK | OK |
| `trace_check` | 563 errors | 563 |
| `goal_check` | 8 errors (GL1, 5 x GL3, GL4) | 8 |
| `agent_check` | 2 errors, both THR-011 | 2 |
Not re-run here (no change since the verified run, same code): acceptance and contract scripts, PostgreSQL tests, `check_sysml.sh`, smoke test. The stage 4 long checks are unchanged.

### Quick eval subset (cases tagged `smoke`, dev split)
Only `verdicts_wikidata` has smoke cases (3). Run: MP-light, `verify.single@1`, 3 repeats, not saved. Result 6 of 9 right: `river-length-false` 3/3, `tower-height-true` 3/3, `bridge-year-true` (Q110994774) 0/3. The old-runner baseline (`eval/baselines/verdicts_wikidata__single__devsample.jsonl`) fails the same case (`fail`), so the outcome is unchanged. Stability over repeats 100 %. 9 calls, 13.4 s.

### Agent changes
| Suite | Requirement (AC-34) | Dev decision, converted vs baseline | Holdout | Skill / pipeline versions | Run file (git-ignored, `data/eval/`) |
|---|---|---|---|---|---|
| EV-research | right >= 0.85, n=20 | PASS, 0.950 | none (TD-88) | `research.escalate@1`, unchanged since 2026-10-20 | `research__converted__20261120-111026.jsonl` |
| EV-plans | right >= 0.54, n=36 | PASS, 0.639 | none | `plan.free`, unchanged | `plans__converted__20261120-111505.jsonl` |
| EV-verdicts | right >= 0.83, n=50 | PASS, 0.940 | none | `verify.single`, unchanged | `verdicts__converted__20261120-111801.jsonl` |
| EV-extraction | right >= 0.59, n=51 | PASS, 0.667 | none | extraction, unchanged | `extraction__converted__20261120-112131.jsonl` |
| EV-computable | right >= 0.87, n=39 | PASS, 0.974 | none | `verify.computable`, unchanged | `computable__converted__20261120-112720.jsonl` |
- Pins: MP-light `gemma4:12b-it-qat`, digest `sha256:38044be4f923...`, unchanged; `num_ctx` 8192.
- Records of the five accepted skills: `data/conversion/{research,plan_question,verify_claim,extract_claims,verify_computable}.json` (git-ignored).
- Wording: dev runs are feedback by the plan's own words: "not worse on dev", not "better" (no holdout, no sign test).
- Red-team: no case run in this phase; THR-011 has no case (V2-6, accepted).
- Budgets: no change measured (not re-measured; TD-87).

### Requirements
G-V2 requirements Implemented: statuses to Verified after the owner confirms (see Decisions). Frozen requirements: no subgoal merge in this phase.

### Known issues / accepted deviations (carried into the release notes)
TD-86 (live trust and lifecycle on the converted path), TD-87 (budgets and stop), TD-88 (AC-34 on dev only), TD-89 (`research.escalate@3` in the check, `@1` in the skill), TD-90 (real half of the IF-103 contract suite skipped): all DRAFT until the owner signs. V2-6 (no red-team case for THR-011), MODEL deviations of D-309, TD-81 to TD-85. V2-4 (converted runs 2 to 10 times faster than baseline runs) goes to Validate.

### Paperwork still open
V2-1 (scope wording `REQ-WFM-143`), V2-7 (SNAPSHOT agreement row, CONVERT Phases row), V2-8 (TC-WFM-110 to 114 in no test-spec table); V2-3 (stale docstring in `skill_converter.py`) goes to Implement. Not done here without the owner: statuses, goal status, Phases rows.

### Decisions for the owner
1. **Baselines.** `eval/baselines/` holds the old-runner dev runs of 2026-11-15 (D-355). The skill says baselines come from holdout and verified runs, never dev only; no holdout exists (TD-88). Recommended: keep these baselines, record the converted dev runs only in the release notes. Baselines are protected; nothing is written.
2. **Statuses**: G-V2 requirements Implemented → Verified (except those with deferrals), Phases rows, goal Proposed → Verified.
3. **Signing** TD-86 to TD-90, the D-358 row.
4. **Tag** `v0.2.0` (below).

### Merge, tag, push (the owner; nothing was done by the agent)
Everything is on master. After the status commit (on branch `commit/g-v2`, own worktree `/home/maldun/prog/Python/MIA-commit-g-v2-work`):
```
cd /home/maldun/prog/Python/MIA && git status --short   # only the untracked files of other sessions
git merge --ff-only commit/g-v2
git tag -a v0.2.0 -m "MIA v0.2.0: G-V2 skill rework foundation, G-V3 skill run view"
git push origin master v0.2.0
```
`deploy/build.sh` does not exist: the release artifact cannot be built from the tag yet (gap for Deploy).
