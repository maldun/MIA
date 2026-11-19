# A-162 (DRAFT 2026-11-19): the eval target `digest` runs the step as the app runs it

Number: A-160 and A-161 are taken; check A-162 against the parent's range before applying. Goal: G-V3.CHAT (follow-up of A-160; the eval harness belongs to N-4.1). Nothing in this draft is applied: requirements are Draft, no code is changed for them.

## Finding (2026-11-19, feedback run 8 of EV-skill_turns, `data/eval/skill_turns_long__default__20261119-083601.jsonl`)
1. `Harness._digest` (`harness.py`) builds `SkillDigestStep(call, persona=text)` without `with_options=True`, and `call` passes only the seed and the temperature of the pin. The step's own options (`OPTIONS = {"num_predict": 1024}`, REQ-CHA-073, since step version 8) are never sent. The app's `LiveDigest` sends them with every call.
2. Effect measured on the one long case (81 884 characters): 16 calls, 149 123 characters received (about 9 300 per call, above what 1024 tokens allow), 608 s (about 38 s per call; the app measured 2.5 to 12.9 s per call). The run does not show how the app behaves on a long result.
3. Not an effect on the earlier decisions: up to step version 7 the step had no options at all, so the dev runs of 2026-11-14 to 15 and the holdout of 2026-11-16 ran the step as the app ran it. The dev runs of version 8 on the 24 short and medium cases of 2026-11-19 are unaffected in practice (no output of 1024 tokens or more), but they were not run with the cap either.
4. The docstring cites `REQ-EVAL-003`; there is no such id (the harness requirements are REQ-EVL-001 to 011). The traceability of the digest target is therefore weak: no requirement says that the target runs the step as production does.
5. To check (not proven): `_digest` passes `model=pin["name"]` and the options seed and temperature, but no `num_ctx`. `OllamaModel.resolve` gives the base options of a model only when it is the current model of the app (`self._current()[0] == model`). If the current model is another one, the call has no `num_ctx` 8192 from the pin and runs with the server default. The eval header says `num_ctx=8192` for MP-light.

## Changes
1. **New REQ-EVL-012, the target `digest` runs the step as the app does** (N-4.1 Evaluation, subject Evaluation, group EV, Must, Test): the Evaluation shall run the digest target with the options of the step in every model call, merged with the seed and the temperature of the pin, so that an eval run of the step and a run of the app send the same options to the model server. Acceptance criterion (exact): with a scripted model the options of every call of a `summary`, a `failed` and a `stopped` case hold `num_predict` 1024, the seed and the temperature of the pin, and the step's own options win nothing over the pin for seed and temperature.
2. **Code (after approval, test first):** `harness.py` `_digest`: `call(messages, options=None)` merges `{**(options or {}), seed, temperature}` and the step is built with `with_options=True`; the docstring cites REQ-EVL-012. No change to `skill_digest.py`; no change to the prompt, so the step version stays 8 and the labels apply.
3. **Open question for the owner: `num_ctx`.** If finding 5 is true, a second requirement (or a clause of REQ-EVL-012) says that the pin's `num_ctx` reaches every call of the target. First step after approval: a test that records the options of a call with a current model that is not the pin.
4. **Optional, separable (owner decides): case input by reference** (new REQ-EVL-013, Should): a case may hold `input.result_ref` with the SHA-256, the length and a local path instead of the text, for long inputs of real runs that must not go into a public repository; the harness reads the file and stops with a clear error if the hash differs or the file is missing. It makes the proposed case `prop-run2-1` (`specs/mia/goals/G-V3.CHAT/proposed-cases-run2.jsonl`) runnable. A new part of the harness: not built without the owner's approval.

## Checks (red first, after approval)
- TC-EVL-012 (REQ-EVL-012): fake model that records the keyword arguments of every call; one case each of kind summary (long enough for pieces), failed and stopped; the options of all calls are as stated. Fails on the current code (mutation: remove `with_options=True`).
- TC-EVL-013 (REQ-EVL-013, only if change 4 is approved): hash matches, hash differs, file missing.
- Protected files: a new acceptance test in `tests/acceptance/` is protected: patch plus apply script, as for A-158 and A-160 (the owner applies it). Test requirement: Applies to: line of the test requirement that covers the harness targets; to be decided in the plan gate.

## Eval material (agent-app)
- No suite, label or baseline changes. After the fix a feedback run of the long case (scratch suite, `MIA_SUITES`) shows what the app does on a long result; a person labels its summary (the faithful label needs a reading of a summary against the result; the hard checks compare numbers and quoted names).
- The 24 dev cases need no re-run for this change (their outputs are far below 1024 tokens); a re-run of `skill_turns` as feedback is optional.

## Not part of this amendment
- The long summary that lists every work one by one (a prompt matter; `skill_turns` labels accept it as faithful; a prompt change needs an eval case and the owner's approval first).
- A time budget for the end message of a long result (owner decision B of A-160: none).

## Plan after approval (small, in this order)
1. Plan gate: the owner rates REQ-EVL-012 (and REQ-EVL-013 if wanted) as plausible.
2. Patch and apply script for the protected test, review-log rows, plausibility entries, the model mirror if the Evaluation part has a behaviour entry for the targets, traceability.
3. Red test, then the change of `_digest`; full unit suite; feedback run of the long case.
