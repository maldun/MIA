# Hand-over for the next session (written 2026-10-31, late): G-V1, N-2.4.1 T-07 done, A-34 installed, Verify of N-2.4.1 running

The newest hand-over. It continues `handover-2026-10-31.md` ("How to work" and the rules there still hold). Then read `CLAUDE.md`, `specs/mia/goals/G-V1/goal.md`, `specs/mia/review-log.md` (**D-120 to D-125** are new) and the `implementation-log.md` of the node you work on.

## State of `goal/v1` (HEAD `99d185a`)
Line of work: branch `goal/v1`, worktree `.claude/worktrees/goal-v1`; master is still at `53c6766`. Next free ids: **D-126, A-36, FB-03** (check `goal/v1` and master before you write one).

| Commit | What |
|---|---|
| `2c53841` | `pipeline_model.UNREACHABLE` is the owner's wording "Can't reach my brain right now beep" (D-120), pinned by a test |
| `11150e7` | FB-02: networkx graphs of objects and vis.js, for the **next iteration** (D-121, D-122) |
| `356f90b` | N-2.4.1 T-07: tools through IF-402 (`Runner(tool_calls=, door_tools=)`), events also through IF-401 (`run_events=`, beside the run log), `WorkflowRuns` reads IF-203 `estimate` (not `check_budget`), the chat's privacy rule moved to `core.keep_texts`, `ToolCalls.fetch_page`, wiring in `web_app.py` |
| `93733dd`, `cca40c8` | A-34 drafted and installed by the owner: IF-402 v2 with `fetch_page` (TC-IF-402-06) |
| `c04b041`, `99d185a` | T-07 log; A-35 approved: N-2.4.1 **T-08** "the review as a workflow of the library" (REQ-RUN-013, AC-9); REQ-RUN-007 out of G-V1 |
| `5735d1c` | D-124: N-5 continues with a vis.js mockup |

| Node | State | Open |
|---|---|---|
| N-2.4.1 Pipeline runner | T-01 to T-05, T-07 done; T-06 deferred (REQ-RUN-007 out, D-125) | **Verify started 2026-10-31 late** by an independent agent; its report is `.../N-2.4.1-pipeline-runner/verification-report.md`, **uncommitted** until the owner has read it. T-08 waits for its eval criterion and suite (fixed before the task starts) and perhaps for FB-02 |
| N-2.4.2 Tools and sandbox | T-01 to T-06; `tool_calls.py` got `fetch_page` (A-34) | its Verify (fresh context) |
| N-4.2 Operation | T-01 (agent); owner said yes to Q1 to Q3 (D-120) | the agent continues: `NOT_OPTIONS` += `MIA_PROXY_TRUST`, `budget`, `model_pin`; `config.missing` at startup in `__main__.py`; README describes the 8 options; then T-02 to T-08 |
| N-5 Graph app | T-01 (agent, plain SVG) | vis.js (vis-network) mockup (D-124; vendored file, licence, version to name and approve: a new dependency); Q-3 protected JS mock of IF-104 before T-02 (yes, D-122); **Q-2 open** (JS copy of `graph_rules.py`) |

## Decisions of today, second session (review-log)
- D-120: N-4.2 Q1 to Q3 yes; unreachable wording; T-06 deferred; T-07 choices (IF-402 door, IF-401 beside the run log, review split out).
- D-121: graph direction networkx + vis.js, to be planned. D-122: finish G-V1 on the current design, redesign next iteration (FB-02); `fetch_page` into IF-402; IF-104 JS mock yes.
- D-123: numbering A-34 (IF-402 v2) and A-35 (T-08). D-124: N-5 vis.js mockup. D-125: A-34 installed, A-35 approved, REQ-RUN-007 out.

## Open for Verify of N-2.4.1 (from the T-07 log)
- `tests/test_content_store.py` now takes `core.keep_texts` (the privacy rule moved out of the runner): a move, not a weakening?
- Still outside IF-402: script nodes (sandbox directly), `checks.build_web_checks` (web functions directly), `library_select`/`library_describe` (Core's tools).
- `ToolCalls._used` grows per run id for the life of the app.
- The stricter default `started_by="message"` (T-04 proposal) is not done.

## Waiting for the owner
1. Read the verification report of N-2.4.1 (when the agent is done), decide its findings, commit it.
2. T-08: name the eval criterion and suite (review benchmark, TC-MIA-003?), and whether T-08 waits for FB-02.
3. N-5 Q-2; approve the vis-network file the N-5 agent proposes.
4. Branch cleanup: 61 branches merged into master and `goal/v1` (55 with a worktree). Script: `remove-branches.sh` in the scratchpad of the session of 2026-10-31 late (`/tmp/claude-1000/-home-maldun-prog-Python-MIA/1251f948-2f8f-400a-acca-407c0b962dbf/scratchpad/`; /tmp may be gone after a reboot: regenerate with `git branch --merged master` and `git worktree list`). Keep `master`, `goal/v1`, `v1-n5`, `v1-n42-t01` (agents still working) and the three **unmerged** `mock-server-config`, `t11b-backup`, `worktree-chat-c5` (look first). `.claude/worktrees/godot-ui` holds an untracked `memories.json`.
5. Older items of `handover-2026-10-31.md`: number_check planted figure (item 4), eval criteria and `eval-spec.md` with pins (item 5), FB-01 HLS gate, `WorkflowRuns` wiring into the harness, TD-01 to TD-05.

## How to work (adds)
- Local coder: a `--forbid 'class Runner'` matched `class RunnerInterfaceTests` and failed a good draft twice: forbid `class X(` and `class X:`. Compare every draft with the instruction by script (difflib on the fixture, a membership check per statement): it lengthened two hex digests this time.
- The shell can drop back to the master checkout after a `cd` into the scratchpad: use absolute paths or `cd` into the worktree in the same command.
- Ollama runs in the podman container `ollama`; start it only for delegations and stop it afterwards.

## Start prompt for the next session
> Continue G-V1 on branch goal/v1 (worktree .claude/worktrees/goal-v1). Load dev-workflow, agent-app and the phase skills you need, and local-coder. Read CLAUDE.md, specs/mia/handover-2026-10-31-late.md, goals/G-V1/goal.md and the N-2.4.1 verification report. First go through the findings of the report with me, then ask me the open points of "Waiting for the owner" 2 and 3, then start the Verify of N-2.4.2 in a fresh context.
