# Verify hand-over: T-04 structured memory (REQ-CHA-011 to -013), 2026-10-27

For a **fresh, independent session** (skills `verify-phase` and `agent-app-verify`). The implementer (the session that built it) has seen all dev cases and tuned the prompt against them, so it must not run the holdout. This file is everything the verifier needs; the implementer's chat is not needed.

## What was built (merged into master)
- `memory_records.py`: records (kind, text, source = message id, subject, status, times), `add` / `remember` (the source must be exactly `"user"`, checked BEFORE the writer is asked), `retrieve` (shared words + recency, abstains without a match, token budget), `memory_hooks`.
- Skill `skills/memory_write.md` **v6** (profile light, `options: {temperature: 0.2}`), pipeline `memory.write@5`, node `view.memory_write@5`. Versions 1 to 5 are kept (they have recorded dev runs).
- Wiring: `ChatService(remember=...)` after a plain chat turn that ended `done`; `Communicator.memory_provider` puts the matching records into the system message; option `structured_memory` (default **false**) and `memory_budget_tokens` (400) in `setup_cfg.json`.
- Plan changes: A-10 (IF-302 v2), A-11 (agent view `MemoryWriteStep`), A-12 (REQ-CHA-011 reworded, AC-24). Check with the owner that A-12 is installed (`bash tools/apply_amendment_a12.sh` shows no difference when it is).
- Decisions and runs: `specs/mia/review-log.md` D-77 to D-85; `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/implementation-log.md` (dev runs 1 to 8 with versions, model digest and findings); design and literature: `specs/mia/eval-drafts/memory-design.md`.

## What to verify
1. **AC-24 (a), the decision run on the holdout** (the only place the holdout may be opened, by you):
   ```
   ~/prog/Python/venvs/mia312/bin/python tools/memory_dev_run.py --split holdout --verifier --repeats 3 --log <a file outside the repository>
   ```
   Needs Ollama with the light model `gemma4:12b-it-qat` loaded (digest recorded in the log: `38044be4f923`; compare with `ollama list` first, a mismatch is a stop condition). The script prints the cases right (majority of 3 repeats), the Wilson 95 % lower bound and **PASS or FAIL** for the rule of A-12: at least 9 of 11 cases right and a lower bound of 0.5 (exact error rates for a good rate of 0.95 and a bad rate of 0.5 with the re-run: false alarm 0.0002, miss 0.064). A FAIL is **re-run once** with fresh repeats and only the second result counts; never more; do not change repeats, rule, seeds or the temperature to get a PASS.
   - The holdout is 11 cases (`"split": "holdout"` in `specs/mia/eval-drafts/memory_sample.jsonl`). Do not copy their text into prompts, cases or the implementer's notes. A failing holdout case goes back as a **description** (category and what went wrong), not as text.
   - The matcher of the score is English-only and rough (kind equal, at least half of the wanted words); read the stored texts of every case that is wrong in the log and say whether the matcher or the model is at fault. A wrong match is a finding about the script, not a PASS.
2. **AC-24 (b)**: `python3 -I tools/memory_cost.py --history memories.json --db <a copy of data/db> --questions <the last 20 user messages>` (the owner's data stays local; print counts only). It must say "not higher than dreaming"; with few records it proves little, say so. The budget cap is tested exactly in `tests/test_memory_records.py`.
3. **REQ-CHA-012 (exact)**: `bash tools/run_in_image.sh tests/test_memory_records.py tests/test_chat_memory.py tests/test_memory_write_skill.py` and read `test_text_from_the_web_a_file_a_tool_or_an_unknown_source_never_becomes_a_record` and `test_remember_does_not_even_ask_the_model_about_text_that_is_not_the_users`. Then check by reading that the ONLY caller of `remember` is the plain-chat branch of `ChatService._do_chat` (not `/lookup`, `/search`, files, pages, regenerate) and that no flow in `specs/mia/architecture.sysml` carries page text to `memoryWriter`.
4. **REQ-CHA-013** (inspect, correct, delete with the source): `tests/test_items_api.py` and the Memory tab; records written by the writer show their `source` (a message id).
5. **Red-team**: the threat model names four draft cases for THR-006 (RT-009) in `specs/mia/eval-drafts/redteam_mia.jsonl`; when the implementer last looked the file was empty and `eval/suites/rt_memory` has 2 cases. Do not label or write cases; report what exists and that the memory writer's only protection against poisoned text is the code rule of item 3 (the cases `untrusted` in the sample are refused before the model).
6. **Protected material unchanged** except by approved amendments: `git diff decomp-baseline..HEAD --stat -- tests/helpers tests/acceptance contracts eval/suites eval/baselines` and compare with A-01 to A-12; this task changed no eval suite and no baseline.
7. **Static checks**: `bash tools/check_sysml.sh`, `python3 -I tools/check_sysml_model.py .`, `bash tools/check_agent.sh --errors` (with `EVAL_DIR`), `python tools/library.py validate`, and the traceability check of `CLAUDE.md` (27 known errors: the number-gate markers).

## Things the implementer could not settle (look at them)
- The dev result (100 % recall on 21 dev cases) is feedback on cases the prompt was tuned against; expect the holdout to be lower. The records of one statement are sometimes stored twice (a fact and a derived preference); the owner labelled one record per statement, so these count as extras but do not make a case wrong in the script. Judge whether that is acceptable.
- The language rule (always English) was fixed by the prompt and the temperature; check on the holdout log that no record is German or French.
- `structured_memory` is off by default and was tried by hand by the owner once; nothing runs it under load. The memory call uses the light profile; with the full model as the chat they unload each other on the 16 GB card.
- The suite `EV-memory` and a harness target do not exist (A-12 says so); do not invent a formal `Eval criterion:` line.
- Pre-existing and not from this task: `tests/test_harness.py::test_every_shipped_suite_is_valid` (the `rt_*` suites have 2 cases each) and `tests/test_shutdown.py::test_group_stop_also_ends_the_helpers_of_the_process` (process groups in the container).

## Report
Write `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/verification-report.md` (verify-phase template): per requirement the evidence and the verdict, the holdout run with versions, digest, repeats, PASS or FAIL and the cases wrong (as descriptions), findings with severity, and what goes back to the implementer. Do not edit the memory code, the skill or the sample; findings become failing tests or draft cases for the owner.

## Start prompt for the fresh session
> Verify T-04 of MIA (structured memory). Read `CLAUDE.md` and `specs/mia/verify-handover-t04.md`, load `verify-phase` and `agent-app-verify`, work in a worktree that branched from current master. You are the independent verifier: run the holdout once as the hand-over says, never tune anything, write the verification report.
