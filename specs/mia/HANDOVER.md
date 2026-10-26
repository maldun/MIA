# Hand-over: where MIA stands (2026-10-26)

For a fresh session. Read this, then `specs/mia/plan.md` (tasks), `specs/mia/review-log.md` (decisions D-45 to D-70, the newest at the end) and the `implementation-log.md` of the node you work on. Rules: `CLAUDE.md`; the agent memory has the owner's working rules.

## State
- **Plan phase: approved and merged** (tag `decomp-baseline`). 422 requirements `Approved`; protected tests in `tests/helpers`, `tests/acceptance/contract`, `tests/integration`; model in `specs/mia/architecture.sysml` (checks: see below).
- **N-3 Database: implemented** (branch `impl/n-3-database`, merged). `graph_rules.py`, `graph_tables.py`, `record_tables.py`, `storage.py`, `storage_files.py`, `storage_postgres.py`, `accounts.py`, `storage_copy.py`, `migrate.py`, `tools/backup.sh`, `tools/restore.sh`, `deploy/db/`, compose service `db`.
- **N-1 Web Frontend: implemented except the deferred parts.** N-1.3 voice player (`VoicePlayer` in `sound.js`), N-1.2 page side of the character (`character.js`, reduced motion in Godot), N-1.1 login, senders, queue places and the ten views of IF-101 v1 (`api.js`, `workspace.js`, `account.js`, `panels-model.js`, answer actions in `chat.js`). Branch `impl/n-1-1-views` (to merge). Logs: `specs/mia/nodes/N-1-web-frontend/nodes/*/implementation-log.md`.
- **Not started:** N-4 Evaluation and operation, N-2 Backend (with N-2.1 to N-2.5, N-2.4.1 to N-2.4.3), N-5 Graph app, the example workflows (root task T-10), root integration (T-12). Order in `specs/mia/decomposition.yaml` (amendment A-01: N-1 before N-4).

## Amendments (protected files change by amendment only; the owner runs the apply scripts in the MAIN checkout)
| Amendment | What | Script |
|---|---|---|
| A-01 | root order: N-1 before N-4 (steps 2 and 3 of N-0 swapped) | `tools/apply_amendment_a01.sh --do` |
| A-02 | real providers of the Database in `contract.py` and `integration.py` | `tools/apply_amendment_a02.sh --do` |
| A-03 | IF-101 v1: spec (`specs/mia/amendments/A-03/`), mock and suite (`contract-drafts/`) | `tools/apply_amendment_a03.sh --do` |
The installed files of A-01 to A-03 must be **committed on `master`** (they were applied but uncommitted when this was written; a worktree then still sees the old mock).

## Open decisions (owner)
1. **IF-111:** an unknown expression name: fall back to `neutral` (contract draft, TC-IF-111-02) or keep the current expression (Godot bridge and backend code, with tests)? One of them needs an amendment. No answer yet.
2. Score "over time" (REQ-CLV-010): IF-101 v2 with votes by time or a series.
3. IF-201 (API to chat agent) probably needs the v1 operations too: draft as A-04, with N-2.1 and N-2.2 tasks.
4. Character model selection and variants in Godot (REQ-CHV-007, -008): after the first human tests.
5. Plausibility: 37 open items were decided; the record is `specs/mia/plausibility.yaml` (the owner's name). Validation notes VN-1 to VN-8: `specs/mia/validation-notes.md`.
6. Legacy stores (chat log, memory, presets ...) need a loader and a writer each for the migration (owner decision D-67): part of the N-2 tasks.

## How to work
- **Tests:** `node --test "tests/js/*.test.mjs"`; Python: `python tests/test_<name>.py` (stdlib ones) or the MIA virtualenv for those that import `flask` (`test_chat_page.py`, `test_chat_mock_server.py`, `test_character_stack.py`); Godot: `bash ui/tools/run_godot_tests.sh` (needs `ui/godot/assets/mia.vrm`, git-ignored: copy it from the main checkout, then `godot --headless --path ui/godot --import` once). PostgreSQL tests start a `postgres:16` container through podman and need `psycopg` (`requirements-db.txt`).
- **Plan checks:** `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh`, the decomposition and plan scripts from the skills (`decomp_check.py`, `req_graph.py`, `req_lint.py`), `python3 -I tools/run_integration_steps.py .` for the integration steps.
- **Try it by hand:** `bash tools/start_testing.sh` lists the stages; `start chat-with-login` is the chat page on the IF-101 v1 mock (anna / pw-anna, ben / pw-ben, carl / pw-carl), `chat-on-stub` the old backend with a fake model, `database` the PostgreSQL container. Stages run as containers of the image `localhost/mia:latest` with the checkout mounted.
- **Real browser:** `ui/tools/cdp_eval.py` drives a headless Chromium with a debugging port (the header says how); `ui/tools/chat_login_e2e.js` and `ui/tools/chat_views_e2e.js` are the click-throughs.
- **Generators:** `tools/gen_integration_drafts.py` (steps from `decomposition.yaml`), `tools/gen_node_requirements_model.py` (the generated block of `architecture.sysml`; run it after every change of a requirement file), `tools/gen_plausibility_draft.py`.

## Pitfalls met
- In a worktree session, shell commands that mix `git`, `$(...)` or variables in one line are refused; split them into plain commands or put the logic in a script file.
- `pkill` of a browser is refused by the permission classifier; kill your own processes by PID.
- Python 3.12 is the only supported version (HLS amendment 10); the host `python3` is 3.14, so use a 3.12 virtualenv for anything that imports the app.
- The page must keep working with today's old backend until N-2 replaces it (tolerant acknowledgement and history in `chat.js`).
