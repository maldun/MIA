# Integration log: Backend (N-2)

| Step | Node | Amendment | Result | Notes |
|---|---|---|---|---|
| 01 | N-2.5 Voice synthesis | A-77 (proposed) | step_01 runs with the real `SpeechService` as IF-204; IF-204 suite and the node's 8 test files green | No finding. IF-204 is not wired into the chat (TD-11, D-173); the step shows the provider only. |
| 02 | N-2.3 Workflow management | A-78 (proposed) | step_02 runs with the real `WorkflowLibrary` as IF-203; IF-203 suite 8 and the node's 15 test files green | No finding. No holdout touched. Model-dependent criteria are decided by the eval suites, not here. |
