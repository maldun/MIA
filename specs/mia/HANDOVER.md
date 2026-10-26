# Hand-over: where MIA stands (2026-10-27, late)

For a fresh session. Read this, then `CLAUDE.md` (rules), `specs/mia/plan.md` (tasks), `specs/mia/review-log.md` (decisions D-45 to D-76, the newest at the end) and the `implementation-log.md` of the node you work on. The agent memory holds the owner's working rules: give scripts not step lists, end every branch job with the merge commands, scripts show the diff (`tools/amendment_lib.sh`), reuse existing code, **delegate simple tasks to the local coder model (skill `local-coder`, see "How to work")**.

Everything below is **merged into master** (last merge `d89d253`) unless it says otherwise. Start a new job from a worktree and check first that it branched from current master (`git log --oneline -1`, then `git merge --ff-only master`).

## State by node
- **Plan phase: approved** (tag `decomp-baseline`); about 426 requirements `Approved`; protected material: `tests/helpers`, `tests/acceptance/contract`, `tests/integration`, `contracts/`, `eval/suites`, `eval/baselines`; model in `specs/mia/architecture.sysml`. Protected files change **by amendment only** (A-01 to A-08 installed, A-09 and A-10 drafted (table below)).
- **N-3 Database: done** (`storage*.py`, `accounts.py`, `graph_*`, `record_tables.py` now with 12 tables incl. `cases` and `behaviours`, `migrate.py`, `tools/backup.sh`, `deploy/db/`).
- **N-1 Web Frontend: done** except the deferred parts (character model selection and variants in Godot: REQ-CHV-007, -008, after the first human tests). The page has no view for the adaptation counters yet.
- **N-4.1 Evaluation: T-01 to T-06 done** (`eval_platform.py`, `metrics.case_table`, `tools/decide_guard.py`, `tools/check_baselines.py`, `tools/measure_latency.py` ...). Not done: T-07 (proof of concept, waits for N-2 and N-3 steps), TC-EVL-009 (agent check on the suites), the live latency number (needs `websocket-client` in the image: a dependency for the owner to approve). N-4.2 not started.
- **N-2.1 API and accounts**: T-01, T-02 done (`api_sessions.py`, `accounts_api.py`, `internal_auth.py`, `tools/accounts_cli.py`; `accounts_enabled` is **off by default** in `setup_cfg.json`). T-03 routes done (see below). Not done: `audio_chunk` (N-2.5), REST codes, T-04 (IF-104), T-05.
- **N-2.2 Chat agent**: T-02, T-03, T-06, T-07 done, T-05 done in a way that satisfies the owner's decision, **T-04 not built** (needs a design). Map of requirement to code:

| Requirement | Code | Test |
|---|---|---|
| REQ-CHA-006 regenerate, speak again | `ChatService.regenerate` / `speak_again` | `tests/test_chat_regenerate_speak.py`, `test_chat_answers.py` |
| REQ-CHA-007 voice lines | `voice_lines.py`, `library/voice_lines.json` (only `annoyed` has a clip, the rest `silent`; **nothing plays them yet**) | `tests/test_voice_lines.py` |
| REQ-CHA-008 persona | `persona.py`; `Communicator.persona_message()` is the system message of EVERY call (read from `data/persona.json` each time, not stored in the history, default address "master"); `calibration.txt` is the fallback | `tests/test_persona_prompt.py` |
| REQ-CHA-009 mood in 7 situations | `moods.json` section `situations`, `MoodTracker.enter()`; wired only for `error` | `tests/test_moods_situations.py` |
| REQ-CHA-010 score shifts mood | `MoodTracker.set_score`, offset in `status()['offset']`, set after every vote | `tests/test_mood_score.py` |
| REQ-CHA-014 silent repair | `ChatService(repair=...)`, `settled()`: the page only gets the settled, repaired part; the whole answer is repaired at the end; `/lookup` answers are never repaired | `tests/test_chat_repair.py` (all 67 texts of `eval/suites/behaviour`) |
| REQ-CHA-015 votes | `ChatService.vote`, table `votes`, one record per user, category, subject | `tests/test_chat_answers.py` |
| REQ-CHA-016 case on a minus | `is_fact` (a source with trust >= `reputable_trust`, 0.6), `_open_case` -> table `cases`; lookup answers keep `sources` with trust (`note_sources`) | `tests/test_chat_behaviour.py`, `test_evidence.py` |
| REQ-CHA-017/018 adaptation, counters | `show_chance` (0.2 % from a net of -5), `counters`, `reset_counter`, `show_behaviour` (**nothing calls it yet**), list in `library/behaviours.json` | `tests/test_chat_behaviour.py`, `test_chat_ops_api.py` |
| REQ-CHA-019 recite | `recite`, `recite_all` (commands `/tasks`, `/memos`), `recite_due` (called first in `time_update`) | `tests/test_chat_recitation.py` |
| REQ-CHA-020 storage only via IF-102 | inspection | `tests/test_chat_storage_imports.py` |

- **Routes of the Backend** (all read the account from `g.account`, "page" without accounts): `chat_ops_api.py` (vote, score, regenerate, speak_again, account, counters, reset_counter), `items_api.py` (tasks, memos, memory + `item_changed`), `trust_persona_api.py` (trust = override file `source_trust_file`, persona = `data/persona.json`; events `trust_changed`, `persona_changed`). `web_app.py` gives them one shared `Storage` (`_votes_store`, folder `accounts_dir`, default `data/db`). `ui/tools/chat_mock_server.py` imports the real `web_app` and **re-points** the endpoints of `chat_ops_api.*`, `items_api.*`, `trust_persona_api.*` to the mock views; `counters` and `reset_counter` are re-pointed too (`tests/test_chat_mock_server.py`).
- **Not started:** N-4.2, N-2.2 T-04, N-2.3 to N-2.5, N-5 Graph app, the example workflows (root task T-10), root integration (T-12). Order in `specs/mia/decomposition.yaml`.

## Amendments (all installed; the owner runs `bash tools/apply_amendment_aNN.sh` in the MAIN checkout, it shows the diff, `--do` installs)
| Amendment | What |
|---|---|
| A-01 to A-04 | root order; real Database providers; IF-101 v1; IF-111 keeps the current expression, IF-101 v2 logout |
| A-05 | IF-101 v3; real provider of IF-101 login/session/logout |
| A-06 | IF-101 v4 (`series` per ISO week); IF-201 v1 (regenerate, speak_again, account, vote, score) |
| A-07 | real providers of IF-101 and IF-201 in `tests/helpers/contract.py`; the suites forward `make` options. Skips left: IF-101 3, IF-201 2 (expression/`audio_chunk` N-2.5, `stop` of a waiting answer N-2.2 T-01, the character variant REQ-CHV-008) |
| A-08 | IF-101 v5 (`counters`, `reset_counter`, `counters_changed`, `invalid_vote` rule `subject`), IF-201 v2, IF-302 v1 (tables `cases`, `behaviours`); five accounts in the suites (anna, ben, carl, dora, emil) |
| A-09 | IF-101 v6: optional `due` (tasks only) in `save_item`, shown by `items`; `invalid_item` rule `due` (D-77). Drafted and tested on a scratch copy; **install: `bash tools/apply_amendment_a09.sh --do` in the main checkout** |
| A-10 | IF-302 v2: optional `kind`, `status`, `subject`, `updated` of a memory record (D-79). Drafted, tested on a scratch copy; **install: `bash tools/apply_amendment_a10.sh --do`** (after A-09) |

## Decisions the owner still has to make
1. **T-04 structured memory (REQ-CHA-011 to -013).** 011 is an eval criterion ("at least as good as today's dreaming at equal or lower token cost"): it needs a people-labelled memory test set and a store design (facts, preferences, commitments linked to a source; the `memory` table has only `text` and `source`). 012 (no memory from web or file text) has nothing to guard until a structured writer exists. 013 (inspect, correct, delete with source) already works through `items_api`.
2. ~~A `due` field for tasks~~ decided and drafted as A-09 (D-77); the page has no `due` input yet.
3. **AC-8 (persona) and AC-25 (detector precision and recall)** are eval criteria: **postponed by the owner to the first iteration after the field test** (not run by the agent).
4. The judgement calls of D-76 (0.2 % instead of 1 %, a step instead of a curve, a reset at the same second, a case is not removed by a later plus) and `moods.json` `situations` (greeting = happy, error = embarrassed).
5. Older ones: REQ-EVL-011 (old harness targets still call the in-process core until the N-2 integration); FR-20 (the idea date is stored nowhere, N-2.3 may need a field); legacy stores (chat log, memory, presets ...) need a loader and a writer each (D-67), the Tasks/Memos/Memory tabs of the page start empty; no session timeout, accounts only from the CLI.

## Plan material waiting for the owner
- **Threat model** `specs/mia/threat-model.md` and the **step budgets** (`secondBudget`, three are guesses) are drafts. `bash tools/check_agent.sh --errors` (with `EVAL_DIR=/home/maldun/prog/Python/MIA/eval`) showed 7 errors: no red-team case for THR-004 to THR-010; the 28 promoted cases (RT-007 to RT-013) are **untracked** in the main checkout (`eval/suites/rt_*`): commit them there and re-run the check.
- Dev/holdout split of the 10 suites (agent check A6) and the mapping of the `REQ-VER-*` ids (A7): the owner's, with labelled truth. `library/baselines.json` does not exist (`python3 tools/check_baselines.py`). `formal.yaml` (Z3 check of the budgets) is not written.

## Suggested next steps
1. ~~Re-point `counters` / `reset_counter` in the mock server~~ done.
2. T-04: literature plus a checked sample of 30 (D-78): the owner approves `eval-drafts/memory-design.md`, checks `memory_sample.jsonl`; A-10 drafted, model-free parts built (`memory_records.py`, D-80). Next: the writer step (model step, dev cases only), wiring, the reworded REQ-CHA-011. Install A-09 and A-10.
3. Wired since: the speech streamer speaks the settled, repaired text (`SpeechStreamer(repair, settle)`, `tests/test_speech_repair.py`); `converse` asks `show_behaviour` before a gesture (`tests/test_converse_behaviours.py`). Decided and built after that: every mood has a voice line entry (empty = silent) and the first gesture says its line; the sender is named in the prompt as `[name]` (`tests/test_chat_sender.py`). Still open: `MoodTracker.enter` (`idle` would clear the emotion of an answer; nothing triggers `waiting` or `greeting`). Original list: play the voice lines (`VoiceExpressor` plays one clip per expression), call `show_behaviour` where the character picks a gesture, `MoodTracker.enter` for thinking/speaking/waiting/greeting, name the sender in the prompt, let the speech streamer speak the repaired text (it still gets the raw text).
4. The counters view on the page (N-1, REQ-CLV) and a `due` input.
5. Legacy stores into the tables (D-67); `ChatService.account` only echoes `pipeline` events kept in the log record, the link to the run log (IF-401) is open; the chat log is still a file (`chat_log.py`), not the history table.
6. Then N-2.3 to N-2.5, N-4.2, T-07 of N-4.1 once the N-2 steps exist.

## How to work
- **Tests:** `node --test "tests/js/*.test.mjs"` (98 pass). Python: anything that imports flask or the app runs in the image: `bash tools/run_in_image.sh tests/test_a.py tests/test_b.py` (the host python is 3.14, the project is 3.12 and lacks the packages); stdlib-only tests also run with `python3 tests/test_x.py`. Contract suites: `bash tools/run_in_image.sh tests/acceptance/contract/test_if_101_chat_api.py ...`. Godot: `bash ui/tools/run_godot_tests.sh`. PostgreSQL tests start a `postgres:16` container. Plan checks: `python3 -I tools/check_sysml_model.py .`, `bash tools/check_sysml.sh`, `bash tools/check_agent.sh`.
- **Delegation to the local coder model (owner's rule since 2026-10-27, to save tokens):** use the skill `local-coder` (`~/.claude/skills/local-coder`, model `xentriom/gemma-4-12B-coder-fable5-composer2.5-v1:latest` in Ollama, container `ollama`). Flow: `lc.py add` (needs a real check: `--contains`, `--forbid`, `--min-tests`, `--run`, `--check`; attaches `model-guide.md`), `lc.py run`, **read every result**, `lc.py verdict ID ok|fixed|rejected`, `lc.py lesson`, `lc.py report`. Lessons so far: paste the exact fixture into the instruction, forbid fake copies of the class under test, `--forbid 'REQ-CH-'` (it shortens requirement ids), it forgets imports, tests of more than about 80 lines with a long fixture failed 2 of 4 times (write those yourself), and a failed task deletes its file. For MIA tests use the image (`--check 'bash tools/run_in_image.sh ...'`). Results so far: 7 test tasks, review 0 ok / 4 fixed / 3 rejected; the effect of the guide is not measured yet (five reviewed tasks with and without it are needed). Never delegate design, bug causes, security code, amendments or protected files.
- **Try it by hand:** `bash tools/start_testing.sh` lists the stages; `restart chat-with-login` is the chat page on the IF-101 mock (anna / pw-anna, ben / pw-ben, carl / pw-carl). The container mounts the checkout the script is in: start it from the checkout you want to see.
- **The real backend:** `"accounts_enabled": true` in `setup_cfg.json`, `python3 tools/accounts_cli.py create NAME`, `source ~/prog/Python/venvs/mia312/bin/activate`, `cd ~/prog/Python`, `python -m MIA` (from the PARENT folder), page on `http://localhost:8585/`. Votes made with old code stay in `data/db/votes` (delete the folder for a clean score). `/light!` in the chat saves GPU memory. Check with the real model: `bash tools/check_accounts_real.sh`.
- **Generators:** `tools/gen_node_requirements_model.py` (after every change of a requirement file), `tools/gen_integration_drafts.py`, `tools/gen_plausibility_draft.py`. Amendments: draft the new files under `specs/mia/amendments/A-NN/` and `specs/mia/contract-drafts/`, test them on a scratch copy of the repo, write `tools/apply_amendment_aNN.sh` with `tools/amendment_lib.sh`, add a decision to `review-log.md`.

## Pitfalls met
- In a worktree session, shell commands that mix `git`, `$(...)`, variables (`$S`, `$P`), heredocs, `python3 - <<EOF` with git, `git -C`, `sed` with a backslash or `git reset --hard` are refused: use Write/Edit, literal paths, or a script file (the jobs folder `$CLAUDE_JOB_DIR/tmp` is for scratch scripts).
- Writing over protected files (`tests/helpers`, `contracts/`, `eval/suites`) is refused to the agent: draft on `specs/mia/contract-drafts/` and test on a scratch copy.
- Containers of the image need `--user 0` and `-v checkout:/work:Z` (`tools/run_in_image.sh` does it). `pkill` of a browser is refused; kill your own processes by PID.
- A new worktree may branch from an OLD commit: compare with master first. Commit EVERY edited file before telling the owner to merge (`git status --short`).
- `ui/tools/chat_mock_server.py` imports the real `web_app`: a route added to `web_app.py` shadows the mock's route of the same path; re-point it in the mock server.
- The page must keep working with today's old backend (tolerant acknowledgement and history in `chat.js`); accounts are opt-in. The trust table of the web tools is loaded at start: a trust edit on the page reaches the `sources` of lookup answers at once, the web tools after a restart.
- A passed check of a delegated file proves only its structure: run delegated tests red against the real code, and fix typos by hand.
- **Hardware:** fatal CPU machine checks happened when MIA shut down under load (memory note `crash-fatal-mce-cpu`). Do not run the full compose stack or the 26B model for tests; loading one 12B model unloads the other (16 GB VRAM).
