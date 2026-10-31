# Hand-over for the next session (written 2026-10-31, afternoon): G-V1, N-2.4.1 verified with findings, N-2.4.2 in re-verification, N-4.2 T-03 running

The newest hand-over. It continues `handover-2026-10-31-late.md` (read its "How to work" and "Later the same evening"). Then read `CLAUDE.md`, `specs/mia/goals/G-V1/goal.md`, `specs/mia/review-log.md` (**D-120 to D-132**) and the `implementation-log.md` and `verification-report.md` of the node you work on.

## Owner's rules (new today, keep them)
- **Decisions as a questionnaire, then the steps** (also in the dev-workflow skill): ask every open decision at once with a question tool, each question standing alone with a recommended option first; after the answers, list the steps by which each answer is applied, then do them.
- **Full absolute paths** for every report or artifact you name.
- **Privacy is a non-issue for now** (D-131): personal use, trusted users, controlled environment. Untrusted content (web pages, papers, model output) stays untrusted.
- A person merges (dev-workflow, M27): check a merge in a throwaway worktree, run the suites on the result, give the owner the commands. The owner installs amendments with their scripts; commit the installed files if the owner did not.

## State of `goal/v1`
Next free ids: **D-133, A-43, FB-04** (A-40 is the retirement of `n-planted-figure`, drafted; A-41, A-42 used).

| Node | State | Open |
|---|---|---|
| N-2.4.1 Pipeline runner | **Verified with findings** (re-verification 2, `verification-report.md`); T-06 out (REQ-RUN-007), T-08 deferred to the next iteration (A-35, D-128); scope rows `partly` for REQ-RUN-005, -009, -013 (D-130) | open low findings F7, F8, F10, F11, F13, F14, F16, F17; the edge: an empty command list sends `/light!` without asking (log) |
| N-2.4.2 Tools and sandbox | fixes of findings 6, 7, 8, 10 (`191a8f3`), A-41 (REQ-TLS-007 wording), A-42 installed (IF-402 v3, `toolDoor` in SysML); **re-verification running** (started 15:10) | finding 1: A-40 draft (retire the case) for the owner; the `number_check` rule (below); findings 3, 4 in FB-03 |
| N-4.2 Operation | T-01, T-02 merged (`95e9927`); A-37 (D-127); **T-03 to T-08 running** on branch `v1-n42-ops2` (worktree `.claude/worktrees/v1-n42-ops2`), the agent stops at decisions | its questions |
| N-5 Graph app | vis-network 10.1.2 mockup merged (`798c2e6`), A-36 installed (IF-104 HTTP wire, JS mock) | Q-2 (a JS copy of `graph_rules.py`) blocks T-02 |
| eval-spec | `specs/mia/eval-spec.md` merged as a **draft** (`ee8abbb`) | its decisions in the next iteration's Plan (no lookup or review suite has a holdout) |

Tests in the image (`tools/run_in_image.sh`, now with `--init`): all `tests/test_*.py` fail only in `test_amendment_report` (no git in the image) and `test_harness` (suite `rt_edit` has 2 cases, wants 30; and `n-planted-figure` until A-40 is installed). Contract suites, integration steps and JS tests: all pass.

## Waiting for the owner
1. Install A-40: `bash tools/apply_amendment_a40.sh --do` in the goal-v1 worktree, commit "plan: A-40 installed".
2. The `number_check` rule for conflicting values (D-132): `open` (inconclusive) was chosen, but the planted figure is labelled `fail`. Options when it is built: drop the sentences flagged by `web_tools.injection_signals` before comparing (gives `fail`), or keep `open` and expect inconclusive. Then the unit test and the IF-402 contract case of the planted figure, and a re-measure on the dev sample of the number-gate verdict suites (light model, about 30 min).
3. N-5 Q-2.
4. The results of the two running agents (N-2.4.2 re-verification, N-4.2 T-03 to T-08) and their questions.
5. Older items: `handover-2026-10-31.md` items 5 and 6, FB-01 HLS gate, TD-01 to TD-05.

## Next iteration (after Validate of G-V1)
FB-02 (networkx graphs of objects, vis.js), FB-03 (re-specify how workflow pipelines are built; with it T-08, the paths around the tool door, IF-402 trust and sandbox tier), the eval-spec decisions.

## Lessons of today
- An amendment draft that copies a whole shared file (`specs/mia/test-spec.md`) goes stale when another branch merges first: the A-42 install put back the old SMOKE-MIA-003 row of A-37 (fixed in `0f5050d`). Copy only the changed lines, or redo the copy right before the install.
- The local coder slips on brackets (extra `)` at the end of an assert line, a dropped `});`): rule 11 of its model guide. Compare every draft with the instruction by script.
- `git commit --amend` changes the hash: fix references in the log (N6 of the re-verification).
