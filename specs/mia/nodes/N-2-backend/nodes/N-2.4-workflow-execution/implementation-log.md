# Implementation log: Workflow execution (N-2.4)

## Integration step: N-2.4.3, N-2.4.2, N-2.4.1 real (2026-10-31, T-01 to T-04 of plan.md)
Branch `v1-n24-int` from goal/v1 9f79dab; fresh context; tests in the image `localhost/mia:latest` (`--init --network none`), no model server (fake models), no compose stack. Feedback, not verification.

### What ran
| Run | step_00 | step_01 (N-2.4.3) | step_02 (+ N-2.4.2) | step_03 (+ N-2.4.1) |
|---|---|---|---|---|
| goal/v1 9f79dab as installed | OK | skipped (`need`: not in `READY`) | skipped | skipped |
| scratch copy, `READY` + N-2.4.1, N-2.4.2, N-2.4.3, N-2.4, the real adapters of `contract.py` (A-29, A-31, A-32) | OK | OK | OK | OK |
| scratch copy of `v1-n24-int` with `tools/apply_amendment_a55.sh --do` | OK | OK | OK | OK |

The steps passed at once on the real parts: no adapter was missing (the three real providers were drafted with the parts and installed). What the steps prove is limited: each port is its own real provider in its own folder, so the scenario drives the log, the door and the runner each through its own interface; the real runner of step_03 (`_RunWorkflowAdapter`) has no door and no IF-401 log of the scenario, and the scenario's model (IF-103) stays the mock. The wiring of the three parts as the app builds it (`web_app.py`: `Runner(tool_calls=build_tool_calls(...), door_tools=..., run_events=RunEvents(...))`) was not tested anywhere; this step adds that test (below) and found one defect with it.

### Defects fixed (test-first, one commit each)
1. **N-6 of the N-2.4.2 re-verification: the runner counted a call the door refused** (`731a407`, REQ-RUN-012, REQ-WFX-019). The runner reserved a door tool call against the run's budget before IF-402 answered and kept it when the door refused the call (`bad_arguments`, `unknown_tool`, `budget`), though the door counts nothing then (IF-402). Observable: with `on_error: skip` a refused search used up `search_calls: 1`, and the next valid search ended the run as `budget`, "missing search_calls", with the door at 0 calls. Fix in `pipeline.Runner._do_tool`: the reservation stays (a budget key can be shared by several tools; map items run in parallel), the call is given back on such a refusal, and `budget_spent` is emitted only for a call the door counted (after the call; for other tools as before). Tests: `tests/test_runner_interfaces.py::test_a_call_the_door_refuses_is_not_counted_by_the_runner` (mock of IF-402) and `tests/test_workflow_execution_wired.py` (the real runner, door and run events, wired as in `web_app.py`; 3 tests, of which `test_a_call_the_real_door_refuses_uses_no_budget` is the N-6 case): the two N-6 tests red on 9f79dab's `pipeline.py`, green after; the other wired tests pass on both. The wired test caught a variant the mock missed: the real door raises `bad_arguments` chained `from` a `TypeError`, so a first version of the fix that looked at `__cause__` passed the mock and failed on the real door.
2. **REQ-WFX-022 (AC-15) for the whole node, D-138 (2), D-147** (`eef5ecb`): `tests/test_workflow_execution_storage_imports.py` (TC-N24-001, 3 tests): the modules of the three parts and every local module they import (22) use no database driver except `library.py`'s `sqlite3` index, which the owner allows as a cache (D-147); the index comes back equal after it is deleted; no code outside the tests writes the index's `cases` table (`Library.add_case`), the one part the library files cannot rebuild. Green at once (an inspection that decides the requirement, not a defect).

### Amendment A-55 (draft, for the owner)
`specs/mia/amendments/A-55/A-55-note.md`, `specs/mia/contract-drafts/tests/helpers/integration.py`, `tools/apply_amendment_a55.sh`: `READY` of `tests/helpers/integration.py` gets N-2.4.3, N-2.4.2, N-2.4.1, N-2.4; built from the installed file at install time; nothing else protected changes. Scratch test (two copies of `v1-n24-int` at `eef5ecb`, one with `apply_amendment_a55.sh --do`, each run in one container, every file on its own): look-only shows the one-line diff; `--do` installs it and the four N-2.4 steps pass; a second run says "unchanged"; the built file equals the draft. All 163 `tests/test_*.py`, 15 contract suites and 23 Python integration steps: on both copies only the known failures, the same on both (`test_amendment_report` FromGit: no git in the image; `test_harness` `test_every_shipped_suite_is_valid`: suite `rt_edit` has 2 cases); with A-55 the three N-2.4 steps run instead of skipping, nothing else changes. JavaScript (`tests/js`, the JS contract suites and integration steps, on the host): 168 tests, 149 pass, 19 skipped, 0 fail on both.

### Still skipped, and why
- Nothing of N-2.4 after A-55. N-2 `step_03` to `step_05` and N-0 `step_04`, `step_05` keep skipping: they also need N-2.5, N-2.3, N-2.2, N-2.1, N-1, N-4 in `READY`.
- Contract suites: the real sides of IF-103 (the model server, stage 2), IF-404 and IF-405 (gap G-3 of N-2.4.2: no stage-2 provider for the real web and scholarly APIs) still skip; no network in these runs.

### Decided at this step
- REQ-WFX-022: met for the node with the cache exception of D-147 (test above).
- REQ-WFX-019 and REQ-RUN-012 with the real parts wired: met after fix 1 (budget per tool, what is missing named, tool calls only through the door, every call in IF-401 with its trust).
- The other requirements of TC-N24-001 to -003 hold as far as the scenario checks them; model-dependent and statistical criteria stay with the eval suites (not run).

### Findings for the owner
1. **G-4 (REQ-TLS-001 / REQ-WFX-005 AC-2: "in the run log the code checks precede the first model call of each claim")** is not checked by any test: the scenario only asserts that the model mock was not called, and the order depends on the workflow, not on the door. Open question 1 of the coordinator's report.
2. **The protected step_03 runs the parts side by side, not wired** (above). The wired test now lives outside the protected folders; whether the scenario should get a wired port (an adapter that hands the real door and log to the real runner) is open question 2.
3. **The `cases` table of `library.sqlite` is not a cache**: `Library.add_case` writes rows nothing else holds. No code uses it today (pinned by the test); if a later workflow records cases there, D-147's "a cache that can be rebuilt" no longer holds and the cases belong behind IF-102.
4. **G-1, G-2, G-3** of N-2.4.2 (REQ-TLS-002 measurement, the red-team part RT-001..003, the real sides of IF-404 and IF-405) need eval runs or stage-2 providers: not part of this step, unchanged; G-1 still has no decision (D-134 sends the gaps to this step and the next iteration).
5. N-6 is fixed (above); F-2 of N-2.4.2 (the app's door without trust sources) was fixed in 70a6f35 and is covered by the wired path only through `build_tool_calls`, which the wired test does not use (it needs `web_tools`, `scholar` and the trust table; no network).

### The owner's answers (D-152, 2026-10-31) and what was done
1. **G-4 tested** (`ab3bdeb`, `tests/test_claim_pipelines_check_first.py`, TC-N24-002, REQ-WFX-005, REQ-TLS-001 AC-2): every shipped claim pipeline (`library/pipelines/verify.*`, latest version, through the skills `verify_claim` and `verify_computable`) on the real runner, the real run log (`RunLog`, read back from its files) and the real run events (IF-401), fake model. A code check is a `check.*` node or a `check_run` event, a model call a `model_call` event.
   - Holds: `verify.number_gate@5`, for a claim with a number and one without (check.number before the first judge).
   - **Findings (pipelines unchanged; a change needs an eval run), kept as expected failures:** `verify.single@1` (the pipeline of the shipped skill `verify_claim`), `verify.consistency@1`, `verify.jury@1`, `verify.cops@1`, `verify.trial@1` call the model with no code check before it (they are meant for "a claim no hard check can decide", but nothing in the pipeline or the skill runs the hard check first); `verify.computable@2` lets the model write the check script before `check.script` runs it (the check is model-written by design). For the owner: either the claim reaches these styles only after the gate (route `verify_claim` through `verify.number_gate`, or put a hard-check node first; an eval run either way), or REQ-TLS-001 AC-2 names the gate as the place where it holds.
   - Seen on the way: for a claim without a number the gate's `check.number` node is in the run record but writes no `check_run` to IF-401, so the order is visible in `RunLog`, not in IF-401.
2. **step_03 accepted as side by side for G-V1**: the wired test (`tests/test_workflow_execution_wired.py`) covers the wiring; a wired IF-202 adapter in the protected helpers comes in the next iteration.
3. **The `cases` table guard stays**; the cases move behind IF-102 when they are first used.
4. **G-1 (the measurement of REQ-TLS-002) is out of G-V1**; its scope row is `partly`.
