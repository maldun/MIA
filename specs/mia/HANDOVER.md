# Hand-over: where MIA stands (2026-10-27)

For a fresh session. Read this, then `specs/mia/plan.md` (tasks), `specs/mia/review-log.md` (decisions D-45 to D-73, the newest at the end) and the `implementation-log.md` of the node you work on. Rules: `CLAUDE.md`; the agent memory has the owner's working rules (give scripts not step lists, give the merge commands, scripts show the diff, reuse existing code).

## State
- **Plan phase: approved and merged** (tag `decomp-baseline`). 422 requirements `Approved` at the gate, plus the four of the logout (REQ-FE-031, REQ-CLV-022, REQ-BE-077, REQ-API-017; not recounted); protected tests in `tests/helpers`, `tests/acceptance/contract`, `tests/integration`; model in `specs/mia/architecture.sysml`.
- **N-3 Database: implemented and merged** (`storage*.py`, `accounts.py`, `graph_*`, `record_tables.py`, `migrate.py`, `tools/backup.sh`, `deploy/db/`).
- **N-1 Web Frontend: implemented and merged** except the deferred parts. Since the last note: the **logout** is an item of the menu next to Account (`account.js`, `api.js`, mock server route); the old stage `chat-with-login` restarts with `bash tools/start_testing.sh restart chat-with-login`.
- **N-4.1 Evaluation: T-01 to T-06 built and merged** (`eval_platform.py` + `Harness(platform=)` for IF-105, `metrics.case_table`, `require_same_cases`, `tools/decide_guard.py`, judge calibration `mark_judge_verdicts`, `tools/check_baselines.py`, `tools/measure_latency.py`, `tools/measure_fps.mjs`, `docs/skill-path.md`). Log: `specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/implementation-log.md`. **Not done:** T-07 (proof of concept, waits for N-2 and N-3 steps), TC-EVL-009 (agent check on the suites, see Plan material below), the per-case table is not printed in the report, the live mode of the latency tool has not run against a server. N-4.2 (operation) not started.
- **N-2.1 API and accounts: T-01 and T-02 built and merged as a first slice**, `accounts_enabled` is **off by default** in `setup_cfg.json`. `api_sessions.py` (login, throttling, whoami, change_password, logout), `accounts_api.py` (routes, cookie `mia_session`, the guard of every request, origin and secure-channel checks, change log, sockets), `internal_auth.py` (secret between MIA's own processes), `tools/accounts_cli.py` (accounts are made on the machine, never by a request). The account goes into the records: `updated_by` on presets and gestures, `sender` on chat messages. Log with findings: `specs/mia/nodes/N-2-backend/nodes/N-2.1-api-and-accounts/implementation-log.md`. Checked with the real model: `bash tools/check_accounts_real.sh` (one answer of the light model; starts and stops the Ollama container). **Not done in N-2.1:** T-03 (chat events and streaming as IF-101, the operations regenerate, speak again, votes, score, records, trust, persona, account of an answer, variant), T-04 (IF-104), T-05; the other nodes N-2.2 to N-2.5, N-2.4.x.
- **Not started:** N-4.2, N-2.2 to N-2.5, N-5 Graph app, the example workflows (root task T-10), root integration (T-12). Order in `specs/mia/decomposition.yaml`.

## Amendments (protected files change by amendment only; the owner runs the apply scripts in the MAIN checkout; each script shows the compared files and the diff, `--do` installs)
| Amendment | What | State |
|---|---|---|
| A-01 to A-04 | root order; real Database providers; IF-101 v1; IF-111 keeps the current expression and IF-101 v2 `logout` | installed |
| **A-05** | IF-101 v3 (`403 bad_origin`, `403 insecure_channel`) and the real provider of IF-101 in `contract.py` (login, throttling, whoami, change_password, logout and the 401 without a session run against `api_sessions.py`) | **not installed yet:** `bash tools/apply_amendment_a05.sh`, then `--do`, then commit |

## Plan material waiting for the owner
- **Threat model** `specs/mia/threat-model.md` (6 boundaries, 10 threats) and the **step budgets** in the agent view (`secondBudget` per call: from the skill files, three are guesses) are drafts to review. `bash tools/check_agent.sh --errors` (use `EVAL_DIR=/home/maldun/prog/Python/MIA/eval` for the untracked injection suites) shows 7 errors: no red-team case for THR-004 to THR-010.
- **28 draft red-team cases** `specs/mia/eval-drafts/redteam_mia.jsonl` (RT-007 to RT-013, unlabelled). The owner labels them with `python3 tools/review_drafts.py FILE` (keep adds `label:people`, drops `source:draft`), then `python3 tools/promote_labelled.py FILE --do` moves them into `eval/suites/<suite>/` and `.holdout/`. Many are really code tests (validator, intake, sandbox): the README next to the file says which; do not move those into the suites.
- **Dev/holdout split of the 10 suites** (agent check A6: no holdout, most cases without `split:` tag) and the mapping of the `REQ-VER-*` ids of the verdict cases to `specs/mia` (A7): the owner's, with labelled truth.
- **`library/baselines.json`** (which suite and variant is the baseline of each of the 5 tested/trusted workflows) does not exist; `python3 tools/check_baselines.py` names the 5 that lack a baseline. The baselines in `eval/baselines/` are `.md` reports; the `.jsonl` baselines are made by recorded runs.
- `formal.yaml` (Z3 check of the budgets) is not written.

## Open decisions (owner)
1. Score "over time" (REQ-CLV-010): IF-101 votes by time or a series.
2. IF-201 (API to chat agent) probably needs the v1 operations too: draft as **A-06**, with N-2.1 and N-2.2 tasks.
3. Character model selection and variants in Godot (REQ-CHV-007, -008): after the first human tests.
4. REQ-EVL-011 (the harness reaches the platform only through IF-105): the old harness targets (checks, pipeline, research ...) still call the in-process core; kept side by side until the N-2 integration (owner agreed 2026-10-27).
5. FR-20 wants the time from idea to promotion on record: the library stores creation and promotion times, the idea date is stored nowhere (N-2.3 may need a field).
6. Legacy stores (chat log, memory, presets ...) need a loader and a writer each for the migration (D-67): part of the N-2 tasks. Decided 2026-10-27: no session timeout; accounts only from the CLI.

## How to work
- **Tests:** `node --test "tests/js/*.test.mjs"`; Python: `python3 tests/test_<name>.py` for stdlib-only tests; anything that imports flask or the app runs in the image: `bash tools/run_in_image.sh tests/test_a.py tests/test_b.py` (the host python lacks the packages). Godot: `bash ui/tools/run_godot_tests.sh`. PostgreSQL tests start a `postgres:16` container through podman.
- **Plan checks:** `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh`, `bash tools/check_agent.sh`, the decomposition and plan scripts from the skills, `python3 -I tools/run_integration_steps.py .`.
- **Try it by hand:** `bash tools/start_testing.sh` lists the stages; `restart chat-with-login` is the chat page on the IF-101 mock (anna / pw-anna, ben / pw-ben, carl / pw-carl; open the link without `?character=0` to see the character). **The container mounts the checkout the script is in**: start it from the checkout you want to see.
- **The real backend with accounts:** set `"accounts_enabled": true` in `setup_cfg.json`, `python3 tools/accounts_cli.py create NAME`, restart MIA.
- **Generators:** `tools/gen_node_requirements_model.py` (run after every change of a requirement file), `tools/gen_integration_drafts.py`, `tools/gen_plausibility_draft.py`.

## Pitfalls met
- In a worktree session, shell commands that mix `git`, `$(...)`, variables or heredocs in one line are refused (and so is any command line with `eval` as an argument, e.g. `agent_check.py --eval-dir eval`): split them, use literal paths, or put the logic in a script file (`tools/check_agent.sh`).
- Writing over protected files (`tests/helpers`, `contracts/`, `eval/suites`) is refused to the agent, also by `cp` in a script: test drafts on a scratch copy of the repo instead (symlink the files, copy `tests/`).
- Containers of the image need `--user 0` (and `-v checkout:/work:Z`); `tools/run_in_image.sh` does it. `pkill` of a browser is refused; kill your own processes by PID.
- Python 3.12 is the only supported version (HLS amendment 10); the host `python3` is 3.14.
- The page must keep working with today's old backend (tolerant acknowledgement and history in `chat.js`); the accounts are therefore opt-in.
- **Hardware:** the machine had fatal CPU machine checks when MIA shut down under load (memory note). Do not run the full compose stack or the big model for tests; the light model through `tools/check_accounts_real.sh`, which unloads it and stops Ollama again, was fine.

## Suggested next steps
1. Install A-05 (`tools/apply_amendment_a05.sh`), then N-2.1 T-03 so the skipped real contract tests start to run.
2. Label the red-team drafts and decide the code tests versus model evals (Plan material above).
3. Small N-4.1 gaps (per-case table in the report, live latency run), then N-4.2 and T-07 once the N-2 steps exist.
