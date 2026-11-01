# Integration log: Backend (N-2)

| Step | Node | Amendment | Result | Notes |
|---|---|---|---|---|
| 01 | N-2.5 Voice synthesis | A-77 (proposed) | step_01 runs with the real `SpeechService` as IF-204; IF-204 suite and the node's 8 test files green | No finding. IF-204 is not wired into the chat (TD-11, D-173); the step shows the provider only. |
| 02 | N-2.3 Workflow management | A-78 (proposed) | step_02 runs with the real `WorkflowLibrary` as IF-203; IF-203 suite 8 and the node's 15 test files green | No finding. No holdout touched. Model-dependent criteria are decided by the eval suites, not here. |
| 03 | N-2.4 Workflow execution | none | runs and passes since A-77 and A-78 made N-2.5 and N-2.3 ready (A-55 listed N-2.4) | No amendment needed; recorded here. |
| 04 | N-2.2 Chat agent | A-79 (proposed) | step_04 runs with the real `ChatService` as IF-201; IF-201 suite 16 (1 skip, TD-11); the node's tests and 16 other chat test files green | No finding. `audio_chunk` and `expression` events not built (TD-11, D-173). |
