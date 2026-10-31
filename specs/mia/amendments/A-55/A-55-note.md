# A-55: the Workflow execution N-2.4 is integrated

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The three parts of N-2.4 are verified: N-2.4.1 Pipeline runner (Verified with findings), N-2.4.2 Tools and sandbox (Verified with findings, D-134), N-2.4.3 Run log (Verified with accepted deviations, D-148). The integration steps `tests/integration/N-2.4/step_01` to `step_03` skip because `tests/helpers/integration.py` (protected) does not list the nodes in `READY` (`need()`). Their real providers are in `tests/helpers/contract.py` already: IF-401 `_RunEventsAdapter` (A-29), IF-202 and IF-105 `_RunWorkflowAdapter` (A-31), IF-402 `_ToolCallsAdapter` (A-32). This is the pattern of A-02 (the Database N-3: `READY` got the four N-3 nodes).

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `tests/helpers/integration.py` | `specs/mia/contract-drafts/tests/helpers/integration.py` (the change on the file as of 9f79dab, for reading); `tools/apply_amendment_a55.sh` builds it from the installed file at install time | `READY` gets `N-2.4.3`, `N-2.4.2`, `N-2.4.1`, `N-2.4`; the comment names A-55 |

The script refuses when the `READY` line is not found exactly once, keeps every node already listed (another integration may have added one), and reports "unchanged" once installed.

Unchanged: `tests/helpers/contract.py` (no adapter is missing), the step files, `scenario.py`, the mocks, the contracts, `decomposition.yaml` (it has no field for "integrated"; the order N-2.4.3, N-2.4.2, N-2.4.1 is the one of the steps).

Effect on other steps: none. `need()` of N-2 `step_03` and later also needs N-2.5, N-2.3, N-2.2, N-2.1; N-0 `step_04`, `step_05` need N-1, N-4, N-2.

## What the steps then show, and what they do not
- step_01: the real run log (IF-401) with the runner, the tools and the model as mocks; step_02: the real door (IF-402) too; step_03: the real runner (IF-202, IF-105) too. Each real provider is the contract adapter in its own fresh folder: the scenario drives every part through its own interface, **not** the runner calling the door and writing the log. The wiring of the three real parts (as `web_app.py` does it) is tested outside the protected folders by `tests/test_workflow_execution_wired.py` (TC-N24-003, built at this step).
- The model of the scenario (IF-103) stays the mock in every step; the runner of step_03 uses the fake model of its adapter (`_FixtureModel`). Model-dependent criteria are decided by the eval suites, not here.

## Checked on a scratch copy (not installed)
A copy of `v1-n24-int` (HEAD with the two fixes of the step) with `bash tools/apply_amendment_a55.sh --do`: the four N-2.4 steps OK in the image (steps 1 to 3 run, none skipped); a second run reports "unchanged"; the built file equals the draft. The full comparison with the same copy without A-55 is in the step's record (`specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/implementation-log.md`).

Install (on goal/v1 after the merge of v1-n24-int): `bash tools/apply_amendment_a55.sh` (look), then `bash tools/apply_amendment_a55.sh --do`, commit as "plan: A-55 installed".
