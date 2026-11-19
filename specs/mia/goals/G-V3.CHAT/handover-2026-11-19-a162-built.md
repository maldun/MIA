# Hand-over G-V3.CHAT (2026-11-19, fifth): A-162 built, reviewed and fed back; next is the Verify of A-162 and its status update

Read `CLAUDE.md`, then this file, then `amendments/A-162-draft-eval-digest-target-runs-the-step-as-production.md` and the last lines of `implementation-log.md` (runs 8 and 9). The earlier hand-overs (`handover-2026-11-18-a160-built.md` and before) still hold for the traps. A-156, A-158 and A-160 are verified and their paperwork is done (see the merge request).

## State
- **A-162 (the eval target `digest` runs the step as the app does), all in `master`:**
  - Requirements **REQ-EVL-012 to 015** in `specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/requirements.md`: the options of the step with the pin's seed and temperature (012), the pin's `num_ctx` (013), an input text by reference with path and SHA-256 (014), a missing file or a differing hash stops the run and names the case (015). **Approved by the owner on 2026-11-19 (review-log D-353), status still Draft** until the Commit phase.
  - Checks TC-EVL-012 to 015 (`test-spec.md` of N-4.1) and TR-CHAT-012 (`specs/mia/test-requirements.md`), installed by `tools/apply_amendment_a162.sh`. Review-log row D-352.
  - Red tests installed by the owner: `/home/maldun/prog/Python/MIA/tests/acceptance/test_eval_digest_production.py` (commit `3dadf6ff`; staging copy in `specs/mia/goals/G-V3.CHAT/red-tests-a162/`, script `tools/apply_red_tests_a162.sh`).
  - Code: `harness.py` (`_digest` with `with_options=True` and `{**options, seed, temperature, num_ctx}`; `read_reference`; `InputReferenceError`, a `SuiteError` that `_run_case` re-raises and `run()` raises before the first call; the run header holds the pin's `num_ctx`), `tools/eval.py` (`PINS["MP-light"]["num_ctx"] = 8192`). Commit `76708761`. Extra test `tests/test_harness_reference.py` (`57fafaec`). Digest step stays version 8, no label changes.
  - Mutations found by me: removing `with_options=True`, dropping `num_ctx` and skipping the hash check each fail a test. The reviewer should repeat them.
- **Feedback run 9** (`/home/maldun/prog/Python/MIA/data/eval/skill_turns_long__default__20261119-133812.jsonl`, local): the long result of the first real `/review` (81 884 characters, by reference) took 201 s, 10 calls, 46 222 characters received; run 8 without the production options took 608 s, 16 calls. Status fail by the hard check `names`; unlabelled. Not part of any decision.
- **The long case `prop-run2-1` is dropped as an eval case** (owner, 2026-11-19): its output cannot be labelled, because the run record clips the output at 3000 characters (`MAX_OUTPUT_CHARS`) and a label keys on case plus SHA-1 of the full text. Improving the skills (long summaries that list the works one by one) belongs to another goal.
- Dev runs of the digest step version 8 (2026-11-19) are labelled and rescored (72/72 faithful and persona, 18/18 resisted); the form tool reports nothing left to label.
- Last full unit suite (worktree on `57fafaec`): 2476 tests, 2 failures (`test_task_files_browser`), fixed afterwards by master commit `b2385e41` (re-run green).

## Next, in this order
1. **Verify A-162** by a fresh reviewer (`verify-phase`, `agent-app-verify`): the author of code and tests is the same, so read the plan package and the code, not the chat. Points: the `fixed` options of the pin win over the step's options (seed, temperature, `num_ctx`); a pin without `num_ctx` sends none (existing test `test_digest_score.py` relies on it); the reference path is absolute or relative to the folder of `harness.py`; the scorer gets a copy of the case with the referenced text (`dict(case, input=data)`); the pre-check in `run()` covers all selected cases. Report: `verification-report-a162.md` next to this file, matrix per requirement, mutations repeated.
2. **Set REQ-EVL-012 to 015 to Verified** in the node file, add a follow-up line to `merge-request.md` and `goal.md` (as done for A-156/158/160).
3. Nothing is open for the eval material of this amendment: no suite, label or baseline changes.

## Known gaps and decisions
- The REQ-EVL-015 error is a `SuiteError` subclass, not a result record: the whole run stops, not only the case.
- The `result_ref` form (`path`, `sha256`, `chars`) is documented only in the A-162 draft; `proposed-cases-run2.jsonl` still holds the older note form with `local_copy`, which the harness does not read.
- A slower call than in the app (20 s per call in run 9, 2.5 to 12.9 s measured by the app) is not explained; another model test on the shared Ollama server may have contributed.
- The full 84 KB result text went public in commit `35f2156e`; the owner rebased and pushed, GitHub's cached copies remain until a support request purges them (not sent). The local copy is `data/eval-external/proposed/prop-run2-1.result.txt` and the branch `backup/before-rebase-bcc1177e`; both may be deleted now that the case is dropped.

## Traps (new today)
- **A removed worktree turns `cd <worktree> && ...` into a silent run in the main checkout** when the command is chained with `;` or when only the `cd` fails inside a heredoc script. Another process fast-forwards `master` and deletes merged branches and worktrees (twice today). Always `git worktree list` first, and name full paths.
- Installing into `tests/acceptance/` (`--do` of a red-test script) and writing `test-spec.md` or `test-requirements.md` from a script were refused by the auto-mode classifier; do not work around it. Stage the files and give the owner the script.
- The suite loader accepts only the keys `id, tags, claim, input, truth, expect, note, gold` and `expect` of `pass, fail, open, not_applicable`; a scratch suite with extra keys is refused. `MIA_SUITES=<folder>` points the tool to a scratch suites folder.
- The `## Groups` table of `specs/mia/test-requirements.md` has repeated rows (two lines "Fakes (CHAT)" etc.); the apply script edits the line that carries TR-CHAT-009.
- A stored eval output is a string clipped at 3000 characters; `make_digest_label_form.py` reads an output only if it is a dict with `output`.
- Review-log ids: D-352 (A-162 amendment) and D-353 (A-162 review); check the next free id before appending.
- Untracked and not ours: `eval/baselines/verdicts_*`, `specs/mia/goals/G-V2.CONVERT/handover-2026-11-16-convert-complete.md`, `specs/mia/goals/G-V2.CONVERT/verification-report.md`, `templates/UI/`.
- Real model runs: look at `ListAgents`, message a running session first (done today for `requirement-mode-c6`), release it afterwards.
