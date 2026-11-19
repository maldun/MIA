# A-162 (DRAFT 2026-11-19, reworked after the owner's answers of the same day): the eval target `digest` runs the step as the app runs it

Number: A-160 and A-161 are taken; check A-162 against the parent's range before applying. Goal: G-V3.CHAT (follow-up of A-160; the eval harness belongs to N-4.1). Nothing in this draft is applied: requirements are Draft, no code is changed for them.

## Finding (2026-11-19, feedback run 8 of EV-skill_turns, `data/eval/skill_turns_long__default__20261119-083601.jsonl`)
1. `Harness._digest` (`harness.py`) builds `SkillDigestStep(call, persona=text)` without `with_options=True`, and `call` passes only the seed and the temperature of the pin. The step's own options (`OPTIONS = {"num_predict": 1024}`, REQ-CHA-073, since step version 8) are never sent. The app's `LiveDigest` sends them with every call.
2. Effect measured on the one long case (81 884 characters): 16 calls, 149 123 characters received (about 9 300 per call, above what 1024 tokens allow), 608 s (about 38 s per call; the app measured 2.5 to 12.9 s per call). The run does not show how the app behaves on a long result.
3. Not an effect on the earlier decisions: up to step version 7 the step had no options at all, so the dev runs of 2026-11-14 to 15 and the holdout of 2026-11-16 ran the step as the app ran it. The dev runs of version 8 on the 24 short and medium cases of 2026-11-19 are unaffected in practice (no output of 1024 tokens or more), but they were not run with the cap either.
4. The docstring cites `REQ-EVAL-003`; there is no such id (the harness requirements are REQ-EVL-001 to 011). The traceability of the digest target is therefore weak: no requirement says that the target runs the step as production does.
5. Confirmed by reading the code (not by a run): `_digest` passes `model=pin["name"]` and the options seed and temperature, but no `num_ctx`. `OllamaModel.resolve` gives the base options of a model only when it is the current model of the app (`self._current()[0] == model`). `PINS` in `tools/eval.py` has no `num_ctx` for MP-light at all, and `build_core` makes the current model the `light` or the `full` profile by `default_profile`; so with the full model as current model the call has no `num_ctx` from anywhere and runs with the server default. The eval header says `num_ctx=8192` for MP-light.

## Owner's answers of 2026-11-19
1. REQ-EVL-012 wording right, with the `num_ctx` clause (now its own requirement, REQ-EVL-013, to keep each requirement atomic).
2. Case input by reference now (REQ-EVL-014 and REQ-EVL-015).
3. No hand plausibility rating (the plan-phase skill has none now): the gate is the review in small batches (`req_review.py`), scenarios before test code, test requirements, and the automated checks.

## Changes
Four new requirements in `specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/requirements.md`, all Draft. `req_lint.py` on the four blocks: no error of their own and no warning (the file has one old L0-GROUP error: it has no `## Groups` table; not caused by this amendment).

### REQ-EVL-012 – The digest target sends the options of the step
- Level: low   Subject: Evaluation
- Text: When running a digest case, the Evaluation shall send the options of the digest step, merged with the seed and temperature of the model pin, in every model call.
- Rationale: refines REQ-CHA-073; an eval run that leaves out the options (num_predict 1024) does not show how the app runs the step (A-162, run 8 of 2026-11-19: 16 calls, 608 s)
- Parent: REQ-CHA-073, REQ-OPS-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: with a scripted model, every call of a summary case that needs pieces, of a failed case and of a stopped case carries num_predict 1024, the seed and the temperature of the pin (exact)
- Verified by: TC-EVL-012
- Status: Draft
- History: A-162 (proposed 2026-11-19), new

### REQ-EVL-013 – The digest target sends the context length of the pin
- Level: low   Subject: Evaluation
- Text: When running a digest case, the Evaluation shall send the context length of the model pin in every model call, whichever model is the current model of the app.
- Rationale: refines REQ-EVL-004; the pin names num_ctx 8192 (eval-spec.md) but the harness has no num_ctx in the pin and resolves the base options of a model only when it is the current model of the app (A-162, finding 5)
- Parent: REQ-EVL-004, REQ-OPS-001
- Priority: Must
- Verification method: Test
- Acceptance criterion: AC-22: with a scripted model and an app whose current model is not the pin, every call of a digest case carries num_ctx 8192 (exact)
- Verified by: TC-EVL-013
- Status: Draft
- History: A-162 (proposed 2026-11-19), new

### REQ-EVL-014 – A case may hold its input text by reference
- Level: low   Subject: Evaluation
- Text: Where a case holds a reference to its input text with a local file path and a SHA-256, the Evaluation shall read the input text from that file.
- Rationale: refines REQ-EVL-001; the result of a real run must not go into a public repository, but the case must stay reproducible (A-162, case prop-run2-1)
- Parent: REQ-EVL-001
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-22: a case with a reference to a file of 5 000 characters is run with exactly the text of the file as its input (exact)
- Verified by: TC-EVL-014
- Status: Draft
- History: A-162 (proposed 2026-11-19), new

### REQ-EVL-015 – A reference that does not match stops the run
- Level: low   Subject: Evaluation
- Text: If the file of an input reference is missing or its SHA-256 differs from the reference, then the Evaluation shall stop the run with an error that names the case.
- Rationale: refines REQ-EVL-014; a run on another text than the one that was labelled is worse than no run
- Parent: REQ-EVL-014
- Priority: Should
- Verification method: Test
- Acceptance criterion: AC-22: with a missing file and with a file that has one changed character, the run stops before the first model call and the error names the case id (exact)
- Verified by: TC-EVL-015
- Status: Draft
- History: A-162 (proposed 2026-11-19), new

**Code (after the plan gate, test first):** `tools/eval.py` `PINS["MP-light"]` gets `num_ctx` 8192 (the value of `eval-spec.md`; a change of a pin is an amendment there first, so this is the check that the two agree); `harness.py` `_digest`: `call(messages, options=None)` sends `{**(options or {}), seed, temperature, num_ctx}`, the step is built with `with_options=True`, the docstring cites REQ-EVL-012 (not the non-existent REQ-EVAL-003); a case with `input.result_ref` is read (path, SHA-256) before the first call. No change to `skill_digest.py` or its prompt, so the step version stays 8 and the labels apply. The reference form: `"result_ref": {"path": "data/eval-external/proposed/prop-run2-1.result.txt", "sha256": "...", "chars": 81884}` in place of `result` (path relative to the repository, under the ignored `data/`).

## Scenarios (for `test-spec.md` of N-4.1, protected; to be placed at the gate)
- **TC-EVL-012** Verifies: REQ-EVL-012. Given: a scripted model that records the keyword arguments of every call, a pin with seed 7 and temperature 0, and three digest cases (a summary of 20 000 characters that needs pieces, a failed and a stopped case). When: the harness runs the three cases. Then: every recorded call carries `num_predict` 1024, `seed` 7 and `temperature` 0; the number of calls of the first case is more than one.
- **TC-EVL-013** Verifies: REQ-EVL-013. Given: the same scripted model, an app whose current model is another model than the pin. When: the harness runs one digest case. Then: every recorded call carries `num_ctx` 8192.
- **TC-EVL-014** Verifies: REQ-EVL-014. Given: a file of 5 000 characters of known text and a case that holds its path and SHA-256 and no `result`. When: the harness runs the case. Then: the step receives exactly the text of the file (compared character by character).
- **TC-EVL-015** Verifies: REQ-EVL-015. Given: the case of TC-EVL-014 once with the file removed and once with one character of the file changed. When: the harness runs it. Then: the run stops with an error that holds the case id, and the scripted model has recorded no call.

## Test requirements (to `test-requirements.md`, protected)
- **TR-EVL-001** (setup kind, credibility aspect: stand-in fidelity; applies to TC-EVL-012 to 015): the scripted model shall take the same arguments as `OllamaModel.chat` (messages, schema, model, profile, options) and fail on an unknown argument, so that a change of that signature breaks these tests; Verified by: a signature check in the test itself.

## Checks (red first, after the gate)
New acceptance tests in the protected `tests/acceptance/`: patch plus apply script, applied by the owner, as for A-158 and A-160. Mutation checks by the reviewer in Verify: remove `with_options=True` (TC-EVL-012 fails), drop `num_ctx` (TC-EVL-013), skip the hash check (TC-EVL-015).

## Eval material (agent-app)
- No suite, label or baseline changes. After the code, a feedback run of the long case through the reference (a scratch suite with `MIA_SUITES`, or the suite once the owner takes the case in) shows what the app does on a long result; a person labels its summary.
- The 24 dev cases need no re-run for this change (their outputs are far below 1024 tokens).
- The case `prop-run2-1` (`/home/maldun/prog/Python/MIA/specs/mia/goals/G-V3.CHAT/proposed-cases-run2.jsonl`) changes from `result_ref` as a note to the reference form above once REQ-EVL-014 is built; it enters `eval/suites/` only by the owner.

## Not part of this amendment
- The long summary that lists every work one by one (a prompt matter; the labels of `skill_turns` accept it as faithful; a prompt change needs an eval case and the owner's approval first).
- A time budget for the end message of a long result (owner decision B of A-160: none).

## Plan after approval (small, in this order)
1. Review in small batches (`req_review.py next`, then `mark`): goal and scope (G-V3.CHAT follow-up, N-4.1), the four requirements, then the four scenarios with TR-EVL-001; the owner decides; the review log records each item. No plausibility rating.
2. Place the requirements, scenarios and TR-EVL-001 in their files, run `req_lint.py`, `trace_check.py` and `check_sysml_model.py` (mirror), review-log rows (next free D id; check before appending).
3. Patch and apply script of the protected tests, red tests, then the code in `harness.py` and `tools/eval.py`; full unit suite; feedback run of the long case.
