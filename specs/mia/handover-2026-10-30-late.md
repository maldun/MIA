# Hand-over for the next session (written 2026-10-30, late): IF-401 v1, FB-01 up to Plan, N-2.4.1 T-01

The newest hand-over. It continues `handover-2026-10-30.md` (read its sections "Rules the owner gave", "Pitfalls" and the open items 1, 2, 5, 6; they still hold) and folds in the work of the **two sessions** of this evening: this one (A-30, FB-01 triage, N-2.4.1 T-01, A-31) and the parallel FB-01 Explore session (`handover-fb-01-plan.md`, D-114). Then read `CLAUDE.md`, `specs/mia/review-log.md` (**D-110 to D-114** are new) and the `implementation-log.md` of the node you work on.

## State of the repository (master `fd4f2c9`)
- Everything below is merged into master and installed: **A-30** (`058588d`) and **A-31** (`9cfa556`). Nothing tracked is uncommitted.
- Next free ids (check again on master right before you write one, two sessions ran in parallel and collided once): **D-115**, **A-32**, **FB-02**.
- Branches not to merge: `mock-server-config`, `t11b-backup` (as before), `worktree-chat-c5` (`ca36518`, 2026-10-18, chat settings C5: old, never merged; ask the owner whether it is still wanted before touching it). Old worktrees `fb-01-skills-panel`, `n241-t01`, `a30-if401-errors` are merged and can be removed.
- Tests: `bash tools/run_in_image.sh tests/test_x.py`. All `tests/test_*.py` in the image fail only as on master: `test_config`, `test_shutdown`, `test_harness` (suite `rt_edit` has 2 cases, the test wants 30), `test_amendment_report` (no `git` in the image). All 15 contract suites green; skips only where the provider is not built (IF-101 3, IF-201 2, IF-103, IF-104, IF-402, IF-404, IF-405).

## What was done this evening
1. **A-30, IF-401 v1** (D-110): the contract lists `invalid_run` (a run id that is not a plain name, any operation), `invalid_payload`, `invalid_user` and the order of the checks of `emit`; mock in step; TC-IF-401-05. No code change.
2. **FB-01, the skills panel** (owner's live test): triaged (`specs/mia/feedback/FB-01.md`, D-111), **Explore done by the parallel session** (HLS iteration 1: FR-34 skills panel, FR-35 skill turns in the chat, AC-30, boundary TB-result, architecture 5.3; `research-fb-01.md`; D-114). D-114 **revised** two of the owner's first answers: the **chat model** (not the skill) words the status messages and the summary in persona, a long result is digested in pieces (`SkillDigestStep`); 1200 characters is in the prompt only, nothing cuts. **Waiting: the owner's HLS gate for iteration 1**, then Plan with `specs/mia/handover-fb-01-plan.md` (start prompt, gate question, decided and open points are there).
3. **N-2.4.1 T-01, IF-202 and IF-105** (D-112, D-113, A-31). Owner's decision D-112 ("reference + sync"): a workflow of the library (IF-203) names its `skill` and may pin a `pipeline` (`id@version`); its process nodes carry the pipeline's node ids. Built:
   - `pipeline.py`: budgets of model **calls** and **tokens** (Ollama's `prompt_eval_count`/`eval_count` via `OllamaModel.chat_with_usage`, else 4 characters a token), `RunResult.missing` and `.cost`; `model_call` events carry `tokens_in`/`tokens_out`.
   - `run_workflow.py` (`WorkflowRuns`): `run` (refused over the estimate, `budget_exhausted` with the outputs so far, also `stopped` and `error`), `costs`/`node_costs` (median per top node from the run log, calls inside map/branch included), IF-105 `workflows`, `run_case` (pins `{id: {name, digest}}` checked against `held()`), `events`; `sync_skills`.
   - `tools/sync_workflows.py` (dry run unless `--do`): one IF-203 workflow per skill; all 15 skills sync; the review draft is kept.
   - A-31: the real adapters of IF-202 and IF-105 in `tests/helpers/contract.py` (fixtures `lookup` "42", `drifting` 2 -> 4 calls); 18 contract tests green.
   - Log: `specs/mia/nodes/N-2-backend/nodes/N-2.4-workflow-execution/nodes/N-2.4.1-pipeline-runner/implementation-log.md`.

## Nodes still to build (from the node plans and logs)
| Node | Open |
|---|---|
| N-2.4.2 Tools and sandbox | not started (0 of 7); code exists (`sandbox.py`, checks, web tools): map requirements to code, run the IF-402 suite on the real side, change only what fails; the real adapter is an amendment |
| N-2.4.1 Pipeline runner | T-02 one model at a time, chat before background; T-03 model switch, server unreachable, IF-103; T-04 internet only on command; T-05 context share, calls, learning; T-06 first text in 10 s (stage 4); T-07 interfaces only (events through IF-401 `RunEvents`, the review through the runner) |
| N-2.4.3 Run log | done except the wiring that comes with N-2.4.1 T-07 (runner writes through `RunEvents`; chat `account` linked to IF-401) |
| N-4.2 Operation | not started (0 of 8) |
| N-5 Graph app | not started (0 of 6); holds D-108 (context graph content) and "one executable library" (option 3 of D-112) |
| N-2.1 API and accounts | T-03 rest (`audio_chunk`, REST codes), T-04 IF-104, T-05 |
| N-2.2 Chat agent | T-01 rest (`stop` of a waiting answer); T-04 waits for its Verify on the holdout (`verify-handover-t04.md`) |
| N-2.3 Workflow management | T-08 method transfer not logged; FB-01 changes REQ-WFM-031/-036/-038/-039 |
| N-4.1 Evaluation | T-07 proof of concept (needs the N-2 steps) |
| N-1 Web Frontend | the deferred character variants (REQ-CHV-007, -008), counters view, `due` input; FB-01 adds the panel |
| Root | T-10 example workflows, T-12 root integration |
Done: N-3 Database, N-2.5 Voice synthesis.

## Open items, in the order I would take them
1. **Owner:** the HLS gate of FB-01 iteration 1 (questions in `handover-fb-01-plan.md`), then the Plan session for FB-01 in a fresh chat.
2. **N-2.4.2 Tools and sandbox** (completes N-2.4 together with the rest of N-2.4.1); then N-2.4.1 T-07 (wiring through IF-401, the two event formats) and T-02, T-03.
3. **Wire `WorkflowRuns` into the app and the harness**: nothing calls it yet (chat and extensions call `Core.run`); pins from `eval-spec.md`, `held` from `ollama list`, when to run the sync (start of the app or by hand: an owner decision).
4. **An amendment of IF-202/IF-203** for what the provider does beyond v0: statuses `stopped` and `error`, `pin_unavailable` on `run`, the keys `skill` and `pipeline` of a workflow document.
5. Older owner decisions still waiting (from `handover-2026-10-30.md`): TD-01 to TD-05, the A-23 HLS wording, RVP-001 labels; the `/review` hand test results.
6. Verify phase for the usability work (REQ-WFM-029 to -039, REQ-CLV-023/-024 still `Draft`; FB-01 will change several of them, so verify after its Plan or exclude them).

## Two sessions in parallel: rules learned tonight
- Read the newest D-, A-, TC-ids **on master at the moment you write one**, and again before the merge; append rows to `review-log.md`, never reorder; on a conflict keep both rows.
- Shared files: `review-log.md`, `high-level-spec.md`, `architecture.sysml`, `decomposition.yaml`, `tests/helpers/contract.py` (its draft under `specs/mia/contract-drafts/` must be rebased on the installed file before a new amendment).
- FB-01's skill turns go through the chat path, not `run_workflow.py`; a Plan session for FB-01 that needs the runner stops and reports.

## Pitfalls met
- `tools/run_in_image.sh` prints only the summary of a module; for the failing test names run `podman run --rm --user 0 -v "$PWD:/work:Z" -w /work localhost/mia:latest python tests/test_x.py`.
- A skill's runs need a `skill` (budget, model, prompts) and a `pipeline`; a library workflow without `skill` (the review draft, `implemented_by`) cannot run through IF-202.
- Equal runs compared event by event (TC-IF-105-03) need a still clock: the run_end and model_call payloads carry seconds.
