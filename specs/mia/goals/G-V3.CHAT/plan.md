# Plan: G-V3.CHAT (the spoken-only chat and the digest step)

**Goal:** specs/mia/goals/G-V3.CHAT/goal.md   **Requirements:** REQ-BE-078 (N-2), REQ-CHA-040..063, REQ-CHA-008 and 014 (rev B), REQ-WFM-036 (N-2.2, N-2.3), IF-201 v3 (A-142), THR-012, `SkillDigestStep` in `architecture.sysml`   **Test specs:** `nodes/N-2-backend/nodes/N-2.2-chat-agent/test-spec.md` (TC-CHA-040..063, EV-skill_turns), `eval-spec.md`, `test-requirements.md` (TR-CHAT-001..007)   **Status:** Approved (owner maldun, 2026-11-08, task by task in two batches, D-308)

Line of work `goal/v3.chat`; supervised throughout (no unsupervised prompt-tuning subgoal, owner Q-10). The red tests were written first in a session of their own (Step 4, commit `f7953ca`) and installed by the owner; the implementing sessions never edit `tests/acceptance/`, `tests/helpers/`, `contracts/`, `eval/suites/`, `eval/baselines/`, red-team cases or `test-requirements.md`, never set truth labels, and never read, run or tune on the holdout (TR-CHAT-002). CHAT works against the mock of IF-101 v16 and the recorder of PANEL only through the interfaces; the real hook-up is an integration step after both subgoals are merged (T-06).

## Interface fixed by the red tests
The stubs carry the interface the installed tests expect; the tasks replace the stubs and keep these signatures.
- `skill_digest.py` (root, N-2.2): `SkillDigestStep(model, persona="", input_tokens=4096, count_tokens=None)` with `status(phase)`, `failure(reason)`, `stopped(reason)`, `summary(full_result)` and the attributes `tools` (an empty tuple) and `prompt` (names `1200 characters`); `model(messages)` takes `[{"role": "system" | "user", "content": str}]` and returns text; a long result is cut into consecutive pieces (every character in exactly one piece), each digested by one call in the user role, the last call gets only the digests and its text is returned uncut. Note: `specs/mia/goals/G-V3.CHAT/digest-step-interface.md`.
- `ChatService(..., digest=None, declared_phases=None)` with `skill_turn(account, run, kind, payload)` (IF-201 v3: kinds question, phase, done, failed, stopped; returns `{"id"}` or `{"id": None}`; the link ` [Open in the Skill run view](#run=<run>)` is added by code at the end of done, failed and stopped, a link in the model text is cut off; `repair` is applied before show, speech and storage; the text without the link goes to `speak` once) and `model_history()` (questions, answers, end summary, the last status message of a run; never the full result).
- `tests/helpers/fake_model.py`: `FakeModel(replies)` with the recorder of every call (TR-CHAT-006).

## Task list
| Task | Implements | Green when | Depends on |
|---|---|---|---|
| T-01 The digest step | REQ-CHA-048, 050, 051, 052, 061, 062, 063 (mechanics of 049) | TC-CHA-048, 050, 051, 052, 061, 062, 063 | red tests installed |
| T-02 Skill turns in the chat service | REQ-BE-078, REQ-CHA-040..045, 047, 055..058, 060, REQ-CHA-008 and 014 (rev B), REQ-WFM-036 | TC-CHA-040..045, 047, 055..058, 060; TC-IF-201-09..12 on the real provider | T-01 |
| T-03 History for the chat model | REQ-CHA-046, 059 | TC-CHA-046, 059 | T-02 |
| T-04 Harness target and scorer of EV-skill_turns (spike, tests, code) | REQ-CHA-049, 053, 054 (the means to decide them) | the tests of the scorer (Step 4b) and `python tools/eval.py list` shows a runnable suite | T-01 |
| T-05 Dev runs and prompt tuning | REQ-CHA-049, 053, 054 (feedback only, the criteria are decided in Verify) | dev-split runs logged with versions and the pin; every bad output proposed as an eval case | T-04 |
| T-06 Hook-up to the Workflow management (integration, after both subgoals are merged) | REQ-BE-078, AC-39 end to end | the integration check of AC-39 (Step 4b) | T-02, T-03; G-V3.PANEL T-04 and T-05 merged |

## Tasks

### T-01: The digest step
- Implements: REQ-CHA-048, 050, 051, 052, 061, 062, 063 (the mechanics that REQ-CHA-049 relies on: result and pieces only in the user role)
- Tests to turn green: TC-CHA-048, 050, 051, 052, 061, 062, 063 (`tests/acceptance/test_chat_skill_turns.py`)
- Touches: `skill_digest.py` (replace the stub); the prompt text lives in the step (version bump rule: the step carries a version string that changes with every change of prompt, schema, tools, budget or graph); `architecture.sysml` only for the budget of `SkillDigestStep` if a measured value replaces a proposal (not in this task)
- Must not touch: protected material, `communicator.py`, the library pipelines
- Depends on: red tests installed
- Done when: the listed tests are green, all other tests unchanged
- Notes: the prompt asks for at most 1200 characters and says nothing else about length (the 1200 are in the prompt only, REQ-CHA-052); the step has no tool (REQ-CHA-048); `secondBudget = 20.0` s in the model is not measured, T-05 measures it; the system prompt never contains text of a result (TB-result, THR-012)

### T-02: Skill turns in the chat service
- Implements: REQ-BE-078, REQ-CHA-040, 041, 042, 043, 044, 045, 047, 055, 056, 057, 058, 060; REQ-CHA-008 and 014 rev B (persona and speech repair of the new texts); REQ-WFM-036 (the end summary and the failure message of a run)
- Tests to turn green: TC-CHA-040, 041, 042, 043, 044, 045, 047, 055, 056, 057, 058, 060 (same file); the real variants of TC-IF-201-09, -10, -11, -12 (`test_if_201_chat_turn.py`)
- Touches: `chat_service.py` (`skill_turn`, the constructor arguments), `chat_log.py` only if the fields `skill_run` and `kind` need a place in a record
- Must not touch: protected material, `communicator.py`, `chat_api.py` (the wire is G-V3.PANEL T-05), the contracts and the IF-201 mock
- Depends on: T-01
- Done when: the listed tests are green, `tests/test_chat_*.py` and all other tests unchanged
- Notes: the real adapter of IF-201 in `tests/helpers/contract.py` must accept the mock option `phases`; that file is protected: if the real variant needs a change there, stop and report (plan amendment)

### T-03: History for the chat model
- Implements: REQ-CHA-046, REQ-CHA-059
- Tests to turn green: TC-CHA-046, TC-CHA-059
- Touches: `chat_service.py` (`model_history`); the one call in `communicator.py` that takes the messages of a run from `model_history()` (outside the service; **the owner gave the go-ahead for this one call on 2026-11-08, D-308**; any other change there stops and reports)
- Must not touch: protected material, the memory and summary logic of `communicator.py` beyond that call
- Depends on: T-02
- Done when: the listed tests are green, `tests/test_chat_memory.py` and all other tests unchanged
- Notes: per run the questions, the users' answers, the end summary and the last status message; the full result and the other status messages never

### T-04: Harness target and scorer of EV-skill_turns
- Implements: the means to decide REQ-CHA-049, 053, 054 (not the requirements themselves)
- Tests to turn green: TC-CHA-064 to 067 (`tests/acceptance/test_digest_score.py`, written in Step 4 and installed, commit `a6884aa`); then `python tools/eval.py list` shows `skill_turns` with a target other than `pending`
- Touches: `harness.py` (`Harness._digest`, replacing the stub), a new `digest_score.py` (replacing the stub), a generator and an apply script for the label form in `tools/`, `tools/eval.py`; the scorer is: ( the hard checks of TR-CHAT-004 (every number and quoted name occurs in the full result, no table or log line, a link only from code) and the people's labels for `faithful` and `persona`, `pass` for the injected-instruction cases), `tools/eval.py`
- Must not touch: protected material, `eval/suites/` (the suite target in `suite.json` is the owner's to change), `eval/baselines/`, the decision rules
- Depends on: T-01
- Done when: the scorer's tests are green; a dry run on the dev split with a scripted model runs end to end; nothing of the holdout is run
- Notes: the note `eval-target-note.md` is approved (2026-11-08): a target `digest` on the production step, hard checks of TR-CHAT-004 plus the owner's labels in `eval/labels/` (set only by the owner; key: case and SHA-1 of the output); an unlabelled injection case is `open`; the rule `both` of REQ-CHA-053 and 054 needs a baseline file with outputs: the empty baseline of D-304 gives NOT DECIDED or FAIL in `eval_decide.py`, which the owner decides (change of the rule or acceptance); no threshold, repeat, seed or n is changed to get a PASS

### T-05: Dev runs and prompt tuning
- Implements: REQ-CHA-049, 053, 054 as feedback (the holdout decides in Verify)
- Tests to turn green: none; the measure is the dev-split result of `python tools/eval.py run skill_turns --pin MP-light --repeats 3` (temperature 0, seed 7 of TR-CHAT-001), logged with the versions of the step and the pin
- Touches: the prompt and version string of `skill_digest.py`; `eval-spec.md` rows only for measured numbers (the budget `secondBudget` of the step) with the owner's approval
- Must not touch: protected material, `eval/suites/`, `eval/baselines/`, the holdout in any way, repeats, seeds, thresholds and decision rules
- Depends on: T-04
- Done when: dev runs are logged; every bad output is a proposed eval case in the log (labelled by the owner) before the prompt changes; a criterion that looks unreachable on the pinned model is reported, not worked around
- Notes: Ollama must be running with `gemma4:12b-it-qat`; results that flip between repeats more than `eval-spec.md` allows are a stop condition; your runs are feedback, not verification

### T-06: Hook-up to the Workflow management (integration)
- Implements: REQ-BE-078 and AC-39 end to end: the recorder of G-V3.PANEL calls `skill_turn` for the questions, the declared phases and the end of a run
- Tests to turn green: the integration check of AC-39 (written first, Step 4b, in `tests/integration/`), run on the merged line of work
- Touches: the adapter of G-V3.PANEL T-04 (one call), `chat_service.py` wiring in `web_app.py` (digest step and `declared_phases` from the manifest, REQ-WFM-039)
- Must not touch: protected material, the skills
- Depends on: T-02, T-03; G-V3.PANEL T-04 and T-05 merged
- Done when: the integration check is green, all other tests unchanged
- Notes: until this task the two subgoals meet only through the contracts and their mocks (the cost of the split, recorded in G-V3)

## Split check
6 tasks, within the usual 8; T-04 and T-05 are the model-dependent half and need Ollama; T-01 to T-03 need none (fake model). **Decided by the owner (2026-11-08, D-308): keep one plan.** `goal_check` warns GL11 (29 requirements in scope, no subgoals) since the scope rows were added; the goal's Split check already says keep together, and no row is added to the approved goal (the warning stays as a known one).

## Open before Implement starts
1. The integration check of AC-39 (T-06) is written outside the implementing session (Step 4b), before T-06 starts; it is not needed for T-01 to T-05.
2. After T-04 the owner sets `"target": {"kind": "digest"}` in the two `suite.json` of `skill_turns` (one-line command, no case text) and creates `eval/labels/`; the labelling of dev outputs is the owner's work for T-05.
(Closed on 2026-11-08: the harness target and scorer note, the `starter` flag, the rule `both` kept (D-306), the one call in `communicator.py` allowed.)
