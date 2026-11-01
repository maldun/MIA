# A-43: IF-202 v1 names what the provider already returns (D-113, finding F8 of the N-2.4.1 verification)

- Change: `contracts/IF-202-run-workflow.md` only (text). A run can end `stopped` or `error` (with a plain `error`), and a pin the server does not hold is `pin_unavailable`. `run_workflow.WorkflowRuns` returns all three since N-2.4.1 T-01 (2026-10-30); the IF-202 contract suite passes against the real provider and is not changed (it tests none of the three; a case for them can follow with the next amendment of the suite).
- No code, mock or test changes.
