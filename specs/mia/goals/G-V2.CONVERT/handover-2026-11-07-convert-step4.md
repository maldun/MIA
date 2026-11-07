# Hand-over G-V2.CONVERT (written 2026-11-07, after the Step 4 session): red tests committed, tag `plan-baseline-it2-convert`, next is the owner's list, then the contract suites

Read `CLAUDE.md`, then this file, then `goals/G-V2/parallel-work.md` and `plan.md` of this folder. The earlier hand-over `handover-2026-11-07-convert.md` describes Plan steps 0 to 5; this one starts where it ended. Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-convert`, branch `goal/v2.convert`. Not pushed; the push and the merge are the owner's. One session at a time in this worktree (two sessions wrote here once before).

## Where things stand
- Commits, newest first: `0c62dbb` (merge of master: IF-301 v2 draft of MODEL, D-262 to D-264; conflicts in `architecture.sysml`, `plausibility.yaml`, `test-spec.md` resolved by the rules of `parallel-work.md`), `b818c1a` (A-121), `e02f9b5` (red tests).
- Tag `plan-baseline-it2-convert` on `e02f9b5` (local). The single tag `plan-baseline-it2` is the owner's, set on master after every subgoal has its red tests (`parallel-work.md`). A tag of that name was set by mistake and deleted again; do not recreate it.
- Step 4 of the plan is done for the stage 2 checks: TC-WFM-057 to 066, 069, 115. TC-WFM-110 to 114 are stage 4 eval runs and have no unit tests; do not write any and do not run any suite (never the holdout).

## What exists (all in the repo now)
| Path | What |
|---|---|
| `tests/helpers/call_recording.py` | T-CV-01: `Recording`, `RecordingModel`, `RecordingTool`, `Replay` (answers by order, not by prompt), `first_difference`, `ScriptedModel`, `schema_reply`. Replay registers every tool of the old run, also those never called |
| `tests/helpers/snapshot_lab.py` | `LibraryLab` (in-memory IF-203 v1 as far as snapshots need it), `AccountsLab`, `standard_state` (the 8-item state of TC-WFM-061) |
| `tests/acceptance/test_call_recording.py` | self-test of the helper, 5 tests, green |
| `tests/acceptance/test_skill_conversion.py` | 057 (2 tests), 058 (2, five skills each as subtests), 059 (3), 060, 069, 115 (2): 11 tests, 19 failures with subtests |
| `tests/acceptance/test_skill_snapshots.py` | 061 to 066: 6 tests |
| `skill_converter.py`, `snapshot_store.py` | stubs of the parts `skillConverter` and `snapshotStore`; they return wrong values and never raise, so every test fails on an assertion |
| `specs/mia/amendments/A-121-note.md` | proposal: IF-203 v1 snapshot section (not applied, not reviewed) |

Run: `python tests/acceptance/test_<name>.py` for each of the three modules. Expected today: `call_recording` OK, `skill_snapshots` FAILED (failures=6), `skill_conversion` FAILED (failures=19). **If an acceptance test passes before the product code exists, something is wrong; stop and report.** The tests use `from markers import mark` and `mark.req("REQ-WFM-nnn")` (the repo pattern, accepted by `trace_check`), not `pytest.mark`.

How the red tests were proven satisfiable: a throwaway reference implementation (not delivered) turned all green except TC-WFM-060. Hand-checked value of TC-WFM-059: limit 0.92 - 0.10 = 0.82, 17 of 20 = 0.85 passes, 16 of 20 = 0.80 and 15 of 20 = 0.75 fail; the real `eval_decide.py` gives 0.850, interval 0.640 to 0.948. The scripted run files need 3 repeats per case (the criterion asks `repeats=3`), otherwise `eval_decide.py` says NOT DECIDED.

How TC-WFM-058 works: the old run is the real `Core` (`core.run(skill, inputs, started_by="command")`) on a scripted model and scripted tools, recorded; the converted path `skill_converter.run_converted(...)` is then run on a `Replay` and the two lists of model calls compared with `first_difference`. No model and no suite is needed; all five model skills (research, plan_question, verify_claim, verify_computable, extract_claims) end `done` on schema-derived replies. The converted path is a function the implementer writes (`run_converted(name, inputs, model, tools, skills_dir, library_dir, runs_dir, skill_changes)`); `skill_changes` merges into the skill record so the test can plant `temperature 0.2`.

## Assumptions the tests encode (the owner has not confirmed all of them)
1. **Snapshot interface** (signatures in `snapshot_store.py`; A-90 names only `snapshot`, `list_snapshots`, `restore_snapshot`). The library operations `read_snapshot`, `get_trust`, `get_lifecycle`, `pins()` and `restore(kind, id, version, author)` are not in A-90.
2. **REQ-WFM-064: decided A by the owner (2026-11-07)**: a restore makes the stored version the item's *current* version; nothing is created or deleted. This needs a "current version" concept in the storage interface (not in v0 or IF-102): new work for the contract owner, noted in A-121 O1.
3. **TC-WFM-060 reason of the nine skills**: the test accepts "user interface" plus "later goal" or "another goal". `goal.md`, `eval-spec.md` and the test-spec agree on that wording; `handover-2026-11-07-convert.md` says "own later subgoal, closer integration" and "no suite of their own" and is the odd one out. Open: which wording is the exact text.
4. **Owner**: `accounts.is_owner(account)` is assumed; `accounts.py` has no owner concept (REQ-WFM-066: the account that creates accounts). Only the test double has it.
5. **TC-WFM-115 uses all 51 cases** of `eval/suites/extraction`, because the `split:dev` tags do not exist yet (A-120).
6. **A-90 asks `set_lifecycle` to take named evidence**; the lab has no `evidence` argument (a restore would pass "restore of <name>").
7. **Criterion copy in TC-WFM-059**: the line of REQ-WFM-110 (min 0.82) is copied into the test. REQ-WFM-110 to 114 are held until the baseline probe; if the margin 0.10 changes, test and numbers are amended together.

## The owner's list (blocks Implement)
- Apply A-120 (`split:dev` on the cases of EV-research, EV-plans, EV-verdicts, EV-computable, EV-extraction); record baselines as run files (dev, 3 repeats, MP-light, per skill and variant); rate the ten proposed plausibility items (`plausibility-proposal.yaml`); judge the margin 0.10 and approve REQ-WFM-110 to 114.
- Read A-121 and answer O2 to O5 (trust on restore, name rules, failure in the middle of a restore, bounds), plus assumptions 3, 4 and 6 above. After approval the parent session applies the text to `contracts/` (not this session).
- Merge order STORE, MODEL, TOOLBOX before CONVERT's Implement (P1). The IF-301 v2 draft `specs/mia/amendments/A-90-draft-IF-301-v2.md` is the MODEL session's and still waits for approval as a whole.
- Re-add the deny rules for `tests/acceptance/**`, `tests/helpers/**`, `tests/smoke/**` in `.claude/settings.json` if they are still lifted (they were lifted to install the red tests).

## What a next session can do
1. Nothing in `tests/acceptance/`, `tests/helpers/`, `tests/smoke/` or `benchmarks/` without the owner's go and the deny rules lifted; a protected test that seems wrong: stop and report (amendment).
2. After A-121 is approved: write the contract suite of IF-203 v1 (`tests/acceptance/contract/`, protected, owner's go); after the MODEL line's text is approved: IF-301 v2. Use the existing mocks as the pattern (`tests/helpers/mocks/`); do not edit the v0 mocks.
3. After A-120: narrow TC-WFM-115 to the `split:dev` cases (an amendment of a protected test).
4. Implement (separate session, `implement-phase` + `agent-app-implement`) only when P1 to P6 of `plan.md` are met. T-CV-02 (settings) has no dependency on STORE beyond P1; T-CV-05 (snapshots) needs the STORE merge.
5. Do not set baselines, `split:dev` tags or plausibility ratings; they are the owner's.

## Gaps and traps
- `stages.yaml` still has no stage 4 steps for TC-WFM-110 to 114 (T-CV-09 adds them). `required_for_merge` stays 1 to 3.
- The two stubs are in the repo root, not in `tests/`; the implementer replaces their bodies and may change signatures only through an approved amendment.
- Check results after the merge: `goal_check` no findings; `trace_check` lost the 12 "no marker" warnings for REQ-WFM-057 to 066, 069, 115 (067 and 068 are TOOLBOX scope and still warn); `req_graph` and `agent_check` unchanged (the known errors of other subgoals). `req_plausibility` prints warnings about `REQ-WFX-…` records of unknown requirements; not compared with the state before the merge.
- The scratch material of the Step 4 session (staged copies, patch) lived in a job folder that is deleted with the job; everything of value is in the commits above.

## Checks (run after every change)
```bash
P=~/.claude/skills
python3 $P/dev-workflow/scripts/goal_check.py --spec-dir specs/mia
python3 $P/plan-phase/scripts/req_graph.py --spec-dir specs/mia --tests-dir tests
python3 $P/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests
python3 $P/agent-app/scripts/agent_check.py --spec-dir specs/mia --eval-dir eval
python3 $P/plan-phase/scripts/req_plausibility.py --requirements specs/mia/requirements.md specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md --plausibility specs/mia/plausibility.yaml
bash tools/check_sysml.sh specs/mia/architecture.sysml
```
Host: model server on port 11434, MP-light (12B), keep runs short. The holdout is never run or opened by an agent. Never `git add -A`; name the paths; commit messages end with the Co-Authored-By line.
