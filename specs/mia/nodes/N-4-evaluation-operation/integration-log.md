# Integration log: Evaluation and operation (N-4)

| Step | Node | Amendment | Result | Notes |
|---|---|---|---|---|
| 01 | N-4.1 Evaluation | A-75 (proposed) | step_01 runs; the node's tests green (IF-105 suite 8, eval_platform 17, decide_guard 11, judge_calibration 7, check_baselines 3, eval_cli 8) | No finding. The scenario never calls the harness, so the step adds no coverage (see the N-4.1 verification, D-176 for the same case in N-1.1). |
| 02 | N-4.2 Operation (and N-4) | A-76 (proposed) | step_02 runs; no skip left in N-4; stage 1 tests of the node green (13 files) | No finding. The scenario never starts the stack, so no coverage added. `N-4` added to READY; no N-0 step wakes (they need N-1). |
