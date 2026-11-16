# Hand-over G-V2.CONVERT (written 2026-11-16, later): T-CV-04 done, extract_claims and verify_claim pass their dev criteria, next is plan_question and the acceptance record

Read `CLAUDE.md`, then this file, then `plan.md` and `implementation-log.md` of this folder. The older hand-over `handover-2026-11-16-convert-t-cv-04.md` has the design paragraph (Stage call, thin entries, descriptors) and the working rules of the owner; where it differs from this file, this file is newer.

Worktree `/home/maldun/prog/Python/MIA/.claude/worktrees/goal-v2-convert`, branch `goal/v2.convert`, HEAD `7c5c1da`, clean (only untracked `data/eval/` run files, git-ignored), 74 commits ahead of master `5825d1b`, not pushed (push and merge are the owner's). Master (with G-V3.CHAT and its status update) was merged in at `af1187b`; the one conflict, `plausibility.yaml` (a protected file, both sides appended references), was resolved by the owner's `sed`, both sets kept.

## Done in this session
| Task | Commit | What |
|---|---|---|
| T-CV-04 `run_converted` | `850f9aa` | `skill_converter.run_converted` converts the pipeline in memory, binds it, runs it on a throwaway `WorkflowLibrary` seeded from `library/nodes`, returns a `ConvertedRun` (`status`, `answer`, `values`, `named`, `error`, `events`). Settings reach thin entries: `Toolbox.run(tid, args, settings=None)` passes the settings node to a `run` that takes a second parameter, the shipped code of kind code is `run(args, settings=None)` (D-254, owner's choice, option 1). `resolve_model` gives options `None` where the skill sets none (the old runner does). TC-WFM-058 green for plan_question, verify_claim, extract_claims |
| T-CV-08 part | `1a23a62` | `compare_outputs`; TC-WFM-115 green (the 51 outputs of extract_claims_rules are equal, old against converted, no model) |
| T-CV-09 part | `94f6082`, `b18d406` | harness variant `converted` (D-255): `Harness._run_skill`, `_PinnedChat` (pin name, seed, temperature, no profile), targets `extraction` and `pipeline`; `tools/eval.py run ... --converted` |
| dev runs (feedback) | `ad59774`, `7c5c1da` | see below; both in the "Eval runs" part of `implementation-log.md` |

Unit tests added (all red first): `tests/test_run_converted.py` (4), `tests/test_harness_converted.py` (3), `tests/test_eval_cli_converted.py` (2). Decisions D-254 and D-255 are in `review-log.md` (CONVERT range D-240 to D-259; D-255 is the last used).

## Dev runs (MP-light gemma4:12b-it-qat, digest `sha256:38044be4f923` checked before each run, 3 repeats, seed 7, temperature 0; feedback, not verification)
| Skill | Criterion | Result | Run file (git-ignored, `data/eval/` of this worktree) |
|---|---|---|---|
| extract_claims (REQ-WFM-114, EV-extraction, 51 cases) | min 0.59 | PASS, 34 of 51, 0.667 (0.530 to 0.780), stability 1.00 | `extraction__converted__20261116-144402.jsonl` |
| verify_claim (REQ-WFM-112, EV-verdicts, 50 cases) | min 0.83 | PASS, 47 of 50, 0.940 (0.838 to 0.979), stability 1.00 | `verdicts__converted__20261116-152122.jsonl` |
The recorded runs of the old runner (0.68 and 0.94, `data/eval/*__20261115-*` in the main checkout) are the references; **the baseline files are still not in `eval/baselines/`** (owner), so no run claims "not worse", only the threshold. To read before accepting: the cases wrong in all repeats (extract_claims: cite-in-brackets, cite-with-quote, para-eiffel, para-meeting, para-python, para-water, none-page-number; verify_claim: num-eiffel-wrong, num-moon-wrong, num-sun-wrong). The model server is the host Ollama on `127.0.0.1:11434` (`localhost` did not answer from the shell).

## Tests today (own runs, `/home/maldun/prog/Python/venvs/mia312/bin/python`)
Green: `test_call_recording`, `test_skill_binding`, `test_common_operations`, `test_pipeline_graph`, `test_graph_order`, `test_graph_run_stages`, `test_graph_run`, `test_toolbox` (acceptance and unit), `test_harness` (30, 1 expected failure), `test_eval_cli`, and the three new modules. `tests/acceptance/test_skill_conversion.py`: 4 errors, all expected: research and verify_computable need `control.map` / `control.branch` (not in the toolbox). `test_skill_snapshots`: 8 red (T-CV-05, waits for contracts). Never run `unittest discover` over the whole tests folder: run named modules.

## Next, in the order I suggest
1. **plan_question dev run (REQ-WFM-111, EV-plans, 36 cases, min 0.54, 3 repeats):** needs the harness `plan` target to take `variant["converted"]` too (`_plan`, line about 452 of `harness.py`; use `_run_skill`, test first as in `ConvertedPipelineTarget`), then `python tools/eval.py run plans --pin MP-light --repeats 3 --skill plan_question --variant converted --converted --quiet`, decide with `eval_decide.py` against the recorded run `plans__free__20261115-173323`. The plan groups plan_question with research in T-CV-06 (REQ-WFM-110, 111); plan_question alone needs no controller, research does, so it is split off here.
2. **The acceptance record (owner question, short questionnaire):** `SkillConverter.mark_converted` keeps the state in memory only; nothing persists "extract_claims and verify_claim are converted" and nothing makes the app run them on the graph path. Where the record lives (the skill record of IF-203/IF-301, a file under `data/`) and how `checks` is fed from `decide_acceptance` is open (T-CV-09, REQ-WFM-057/059/060). Until it exists the two passing skills stay on the old runner.
3. **The `control.*` controllers** (`control.map`, `control.branch`, `control.loop`; the construct JSON is the settings node; stop rules as in the old runner) for verify_computable and research: needs a design questionnaire first (see "Wiring found before the conversions" in `plan.md`). T-CV-06a (tool budgets and trust labels of tool results, IF-402 door; research) and T-CV-07a (bind `script_check` to the sandbox; it runs model-written scripts, the owner must look at it) come before those two skills.
4. T-CV-09 rest: stage 4 steps and the per-suite check runner (`bash` run of stage 4 with `--dry-run` lists five steps).
5. T-CV-05 snapshots: waits for the parent session (contract text IF-203 v2, IF-302 v12 `current_versions`, IF-102 v7).
6. Owner items: place the five baseline files in `eval/baselines/` as `<suite>__<variant>__baseline.jsonl` (`research__escalate`, `plans__free`, `verdicts__single`, `computable__computable2`, `extraction__llm`); `test-requirements.md` lacks test requirements for TC-WFM-116 to 134 and TC-RUN-030 to 035 (protected; `trace_check` flags them); TC-WFM-059 criterion copy says min 0.82, REQ-WFM-110 says 0.85 since A-122.

## Things to know
- Open small points (unchanged): two input edges with one `as` are not refused; converter `order-<step>` node IDs could clash with a variable named alike; `seed_shipped` skips existing entries, so a persisted toolbox keeps the old `run(args)` text of `code.pick_field` (it fails with no path) until re-seeded.
- `model_step` still has no budget, token estimate or run events; the converted path therefore has `events = []` and no cost counting (T-CV-06a decides for tools; the harness counts model calls through the core's counting model).
- The converted harness path hands the core's `CountingModel` to `run_converted`, so the cost line of a run counts converted calls too.
- Protected files cannot be edited by the agent (deny rules): `plausibility.yaml`, `eval/baselines/`, `eval/suites/`, `tests/acceptance/`, `tests/helpers/`, `contracts/`. A merge conflict in one of them goes to the owner as a command. `git commit` during a merge cannot take `-- <path>`; stage with `git add` and commit plainly.
- Used one `git stash push -u -m cvtmp ... ; git stash pop` once (path-limited, popped at once, stack checked empty): do not repeat, use a WIP commit.
- Checks to run before a merge request (see the older hand-over): `goal_check.py`, `req_graph.py`, `trace_check.py`, `agent_check.py`, `req_plausibility.py`, `tools/check_sysml.sh`, `check_sysml_model.py`, `check_d_numbers.py` (the two D-182 collisions exist in master too). Not run after T-CV-04 to T-CV-08 except `check_sysml_model.py` and `check_d_numbers.py` after the merge.
- Merge commands for the owner come at the end of the goal, not now. Never `git add -A`; name the paths; commit messages end with the Co-Authored-By line.
