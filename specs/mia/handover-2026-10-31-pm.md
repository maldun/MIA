# Hand-over for the next session (written 2026-10-31, afternoon): G-V1, N-2.4.1 verified with findings, N-2.4.2 in re-verification, N-4.2 T-03 running

The newest hand-over. It continues `handover-2026-10-31-late.md` (read its "How to work" and "Later the same evening"). Then read `CLAUDE.md`, `specs/mia/goals/G-V1/goal.md`, `specs/mia/review-log.md` (**D-120 to D-132**) and the `implementation-log.md` and `verification-report.md` of the node you work on.

## Owner's rules (new today, keep them)
- **Decisions as a questionnaire, then the steps** (also in the dev-workflow skill): ask every open decision at once with a question tool, each question standing alone with a recommended option first; after the answers, list the steps by which each answer is applied, then do them.
- **Full absolute paths** for every report or artifact you name.
- **Privacy is a non-issue for now** (D-131): personal use, trusted users, controlled environment. Untrusted content (web pages, papers, model output) stays untrusted.
- A person merges (dev-workflow, M27): check a merge in a throwaway worktree, run the suites on the result, give the owner the commands. The owner installs amendments with their scripts; commit the installed files if the owner did not.

## State of `goal/v1`
Next free ids: **D-137, A-48, FB-04** (A-47 is reserved for the N-4.2 agent if T-07/T-08 need a protected change).

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

## Afternoon, 15:10 to 15:30 (owner away; agent worked alone)
- N-2.4.2 re-verification: **Verified with findings** proposed (report committed `086b814`). Built since: N-1 `number_check` with evidence as one string (`ad9f482`); the node log written (`ad3ed0e`); A-44 drafted (IF-402 v4 text: what leaves the host, `result` of `run_script`).
- N-2.4.1 low findings built: F14 empty digest (`cea4d62`), F13 model part (`a2e2df0` area), F16 markers and comments (`b268743` area), F11 run-level tool wins over the door (`520626d` area), F17 shared mount label `:z` (`7f89a82` area, reproduced: 3 of 4 parallel runs failed with `:Z`), A-43 drafted (IF-202 v1). Open: F7 (`started_by` default, a decision), F10 (note), the Scenarios section of the node's test-spec (specification).
- N-4.2 on branch `v1-n42-ops2` (`41ea5c2`): T-03 partly (`042a784`: http 8585 always on loopback, `tests/test_compose_stack.py`), T-04 done (`56ebee1`: `tools/check_free.py`), stopped at T-05 with 7 questions (its log). Trial merge into goal/v1: clean, suites as on goal/v1.
- Full run on goal/v1 at 15:23: all `tests/test_*.py` fail only in `test_amendment_report` and `test_harness` (rt_edit count; `n-planted-figure` until A-40); contract, integration, JS all pass.

## Questions for the owner on return (ask as one questionnaire)
1. Merge `v1-n42-ops2` (clean); install A-40, A-43, A-44 with their scripts.
2. N-4.2 Q1 http 8585 on loopback even with `MIA_BIND=0.0.0.0` (recommend keep); Q2 how `graph` is served (recommend the mia image behind a Caddy route `/graph/`); Q3 "graph alone" = the JS suite on the host against the served files (amend TC-OPR-007); Q4 the TC-OPR-007 test as an amendment draft (tests/smoke protected); Q5 `up.sh backup` calls `tools/backup.sh` incl. `db`; Q6 the database tests: install `requirements-db.txt` into the `mia312` venv; Q7 review the paid-API lists in `tools/check_free.py`.
3. N-2.4.2: N-2 (wrong argument types: refuse as `bad_arguments` before counting?), N-3 (mock `result` and `failed`: an amendment), N-6 (the runner counts a call the door refuses), the flows of `toolDoor`, THR-001 and the planted figure, gaps G-1 to G-4 (accept as deviations or plan).
4. N-2.4.1 F7: make `started_by="message"` the default (every command path names itself), or accept "command" as default.
5. The `number_check` rule (D-132 conflict) when it is built.

## Evening, 16:00 to 17:40
- Decisions D-133 to D-136: merges and installs; N-4.2's seven recommendations; F7 default "message"; N-2 type checks; VAL-002 moved to the next goal (G-V1's exit criterion is VAL-001, VAL-003 to VAL-006); N-2.4.2 **Verified with findings**; N-5 T-02 waits for FB-02 (REQ-GA-002, -003 out); N-4.2 T-06/T-07 answers.
- Merged by the owner: `v1-n42-ops2` (twice), `v1-f7-n2`. Installed: A-40, A-43, A-44, A-45, A-46 (all committed by the agent, each equal to its draft).
- **Run the stack smoke with the venv's Python:** `/home/maldun/prog/Python/venvs/mia312/bin/python tests/smoke/smoke_stack.py` (psycopg 3.3.6 is only there; with another python its db part skips, which counts as red). It needs the host's Ollama running (`podman start ollama`).
- Running at 17:40: the N-4.2 agent on `v1-n42-ops2` for T-06 to T-08 (until 20:00 at most); its new commits need another merge.
- Open: the `number_check` rule (D-132 conflict); N-2.4.2's N-3, N-6, flows of `toolDoor`, THR-001, G-1 to G-4; N-2.4.1 F10 (note) and the Scenarios sections; the nodes N-2.1, N-2.2, N-2.3, N-2.4.3, N-4.1, N-1 and their Verifies; the integration steps (N-2.4 first, after N-2.4.3 is verified); then Verify, Commit, Deploy, Validate of G-V1.
