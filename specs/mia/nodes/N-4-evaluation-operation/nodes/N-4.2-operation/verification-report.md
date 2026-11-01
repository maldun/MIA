# Verification report: Operation (N-4.2)

**Goal:** G-V1 (iteration), node N-4.2 (leaf), supervised
**Branch:** goal/v1 @ 0568820   **Parent line of work:** master   **Node commits:** 27c1936, 35a3597, 32338f3, 042a784, 56ebee1, 9c78385, b6427d8, bfbd327, d9d0ebc, c681c0b, ae54227, 8435c44, c3471ea (merges 95e9927, 6e2468c); amendments installed 2ae13de (A-46), 113108f (A-47)
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 as independent reviewer (AI; never saw the implementation chat)

## Verdict
Proposed: **Verified with accepted deviations, after F1 is fixed** (a small Phase 3 fix with a regression test) and the owner has decided F2. Every requirement has a test that can fail and runs green; the remaining findings are low (documentation, architecture model, usability edges). REQ-OPR-006 (walkthrough) and the outside port scan of REQ-OPR-008 stay with the owner (Phase 6).

## Automated checks (local runs of the reviewer, no CI)
| Check | Result |
|---|---|
| Stage log | No CI run for this node; the reviewer's own runs below count as the evidence. |
| Tests in the image (`bash tools/run_in_image.sh`) | `test_missing_options` 5, `test_config` 14, `test_config_local` 5, `test_shutdown` 15, `test_shutdown_database` 5, `test_compose_stack` 6, `test_check_free` 6, `test_first_account` 7, `test_deploy` 16, `test_requirements` 7, `test_storage` 12: all OK |
| Tests on the host (stub podman/compose/curl) | `test_up_backup` 5, `test_first_account_up` 4, `test_up_fresh` 4, `test_runbook` 6, `test_compose_stack` 6, `test_deploy` 16, `test_check_free` 6: all OK |
| Database test (venv `mia312`) | `tests/test_backup.py` (TC-SLY-008, the tools under `deploy/up.sh backup`): 3 OK, its own `postgres:16` on loopback, removed afterwards |
| Smoke tests SMOKE-MIA-001 / -003 | Not run by the reviewer (instruction: they start the whole stack). Evidence: commit messages of 2ae13de (A-46: mia alone, graph alone, all together ok; db alone re-run with the venv, 17 OK) and 113108f (A-47 green on the merged state); implementation log lines 122, 173. No file under `deploy/`, `first_account.py`, `__main__.py`, `config.py` or `shutdown.py` changed after the merge 6e2468c, so the A-47 run covers the current deploy files. Code reviewed below. |
| Mutation (scratch copy, removed) | 8 mutants, all killed: marker of up.sh not written (3 failures); backup ignores the db (1); secret only when `.env` is missing (1); mia port on `MIA_BIND` (1); `OLLAMA_MAX_LOADED_MODELS: "2"` in the NVIDIA overlay (1); `close_database` does not close (1); marker of `first_account.py` not written (3); `config.missing` drops all but one option (3) |
| Protected material | N-4.2's task commits touch no protected path. `tests/smoke/smoke_stack.py` and `smoke_fresh_install.py` are byte-identical to their drafts in `specs/mia/contract-drafts/tests/smoke/` (A-46, A-47, installed by the owner). |
| Traceability (`trace_check.py`) | No error or warning for REQ-OPR-001 to -010 (the 93 errors of the run belong to other parts of the spec). Markers: OPR-001 7, -002 15, -003 6, -004 7, -005 6, -006 7, -007 4, -008 4, -009 7, -010 2. |
| Model consistency (`check_sysml_model.py`) | OK |
| Image pins (`podman image inspect`, no pull) | All six digests in `deploy/compose.yaml`, `compose.rocm.yaml` and `Containerfile` equal `.Digest` of the local images: caddy:2 173b2630…, ollama:latest 40c61dbf…, ollama:rocm 33134349…, searxng:latest 2fc7a1ee…, postgres:16 f9d1e581…, python:3.12-slim 2b4f19da… |
| Published ports | Only `mia` (`127.0.0.1:${MIA_PORT}:8585`) and `https` (`${MIA_BIND}:${MIA_HTTPS_PORT}:8586`) publish; `graph`, `db`, `ollama`, `searxng` publish nothing; the overlays add no port. |
| `tools/check_free.py` on this checkout | "free and open: GPL-3.0-or-later, 2 requirement file(s) and 0 web log(s)", exit 0 |
| Static / security | No linter configured (CLAUDE.md). Manual: no shell built from user input (`up.sh owner` validates the name; `first_account` passes a list to `subprocess.run`). Recorded, not judged again: the secret in the image (F-T06-1, D-139 (1)). |
| Usability (bad inputs) | `up.sh owner "bad name"` refused with usage; `up.sh restore` of a missing file "not a readable .tar.gz"; a db archive without `db` refused with the command to run. Gaps: F1, F5, F6. |

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-OPR-001 one file, one command | Test, Demonstration | `test_up_fresh.py` (4; mutant killed); SMOKE-MIA-001 (A-47) green per 113108f; code of the smoke reviewed | Pass, with deviation F3 (the database runs, MIA does not use it; D-139 (4)) | yes |
| REQ-OPR-002 first account | Test | `test_first_account_up.py` (4, pty for the terminal case), `test_first_account.py` (7); smoke part "offer once" | Pass (F5 low) | yes |
| REQ-OPR-003 missing options | Test | `test_missing_options.py` (5): exactly the two removed options, in `missing()`, the command and the start warning; source check of `__main__.py` | Pass at unit level; F2 (the stack warns about 31 options at every start) | yes |
| REQ-OPR-004 orderly shutdown | Test | `test_shutdown_database.py` (5: SIGTERM, Ctrl+C, /goodnight! via SIGINT on the harness; history and memory record identical on the next start; order history, database, helpers); `test_shutdown.py` 15 | Pass. Note: the app's store is the file backend; the PostgreSQL close is shown with a fake (log T-02) | yes |
| REQ-OPR-005 backup and restore | Test | `test_up_backup.py` (5, stub podman and tools); `test_backup.py` (TC-SLY-008, real PostgreSQL, 50 records with versions, wipe, restore) | Pass for the parts; the stack command against a real stack with `db` was never run (log line 137) → manual check M3; F1 | yes |
| REQ-OPR-006 runbook | Inspection | `deploy/RUNBOOK.md` read against the requirement: start ✓, update of the model pins ✓, backup and restore of the database ✓, retirement ending in the freeze with image and model digests ✓; `test_runbook.py` (6) | Pass by inspection; F4 (three wrong or stale details); walkthrough TC-OPR-006 = owner, Phase 6 | – |
| REQ-OPR-007 compose stack | Test, Demonstration | `test_compose_stack.py` (graph service, Caddy route); SMOKE-MIA-003 (A-46) per 2ae13de | Pass (F9 low) | yes |
| REQ-OPR-008 private access | Inspection, Test | `test_compose_stack.py` (3; mutant killed); own inspection of all compose files; no `tailscale funnel` in code | Pass for the files; outside port scan SMOKE-MIA-002 = owner (M2) | yes |
| REQ-OPR-009 free and open | Inspection | `test_check_free.py` (6); `tools/check_free.py` run; LICENSE GPL v3 and "or later" in README | Pass for licence and dependencies; no real web log checked yet (M4) | yes |
| REQ-OPR-010 one model at a time | Inspection | `test_compose_stack.py` (base merged with each overlay; mutant killed); own read of the three files | Pass | yes |

## Test requirements (M41)
`specs/mia/test-requirements.md` does not exist; the node's test spec fixes stage and tolerance per test case. Deviations from it: TC-OPR-002 (Integration, stage 3) and TC-OPR-005 (Component, stage 3) are checked with stub podman at stage 1 plus the real tools (TC-SLY-008) and the fresh-install smoke (first start only); the second start and `deploy/up.sh backup|restore` were never run against a real stack (M3).

## Goal acceptance (node part)
| Item | Result |
|---|---|
| Requirements of N-4.2 verified | 10 of 10 have passing evidence; REQ-OPR-006 and the scan part of REQ-OPR-008 need the owner (Phase 6) |
| Protected checks | unchanged except the approved installs A-46, A-47 (identical to the drafts) |
| Outside the task bounds | `__main__.py`, `README.md`, `tests/test_config.py`, `tests/test_shutdown.py`, `tests/shutdown_harness.py`, `first_account.py`, `tools/backup.sh` (comment), Caddyfile: each logged and approved (D-120, D-133, D-136) or trivial |
| Stop conditions logged | yes (T-03, T-05, T-06, T-07, T-08 questions, answered by D-127, D-133, D-136, D-139) |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-OPR-001 "with its database" | the `db` service starts and is backed up, but no code reads `MIA_DATABASE_URL`; MIA keeps the file store (F3) | accepted deviation (D-139 (4)) |
| specified, not done | REQ-OPR-003 "after an update" | in the stack the warning is permanent (F2) | owner decision |
| done, not specified | `first_account.py` hint line, marker file `data/first_account_offered`, `MIA_FIRST_ACCOUNT_OFFERED` in `.env` | all decided by D-136 / D-139 | – |
| done, not specified | `MIA_IMAGE` variable in compose | logged in T-03, test support | – |
| architecture | `first_account.py`, `tools/check_free.py`, `deploy/RUNBOOK.md` are in no part of `OperationLayer`; `composeStack` doc names neither `graph` nor `db` (`architecture.sysml:588-612`) (F8) | Phase 2 doc amendment |

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap |
|---|---|---|---|---|
| Functional suitability | OPR-001…007 | tests above, smokes | pass | F2, F3 |
| Performance efficiency | – | – | – | not now (no budget for operation) |
| Compatibility | OPR-007, -010 | compose variants CPU/ROCm/NVIDIA | pass | docker path of backup with db (F7) |
| Interaction capability | OPR-002, -003 | prompts and printed commands | pass | F2 noise, F5 |
| Reliability | OPR-004, -005 | shutdown and backup tests | pass | F1 (MIA left stopped after a failed backup) |
| Security | OPR-008, -009 | port inspection and tests, pins by digest | pass | secret in the image recorded (D-139 (1), D-131); port scan M2 |
| Maintainability | OPR-006 | runbook, pins | pass | F4, F8 |
| Flexibility | – | `MIA_PROJECT`, `MIA_IMAGE` | – | not now |
| Safety | – | – | – | not applicable |

## Open deferrals (M26)
None for N-4.2 in `specs/mia/deferred.md`.

## Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | `deploy/up.sh:182-192` (and `:207-208` for a restore of an old archive): `set -e` plus a failing `tools/backup.sh` (pg_dump of an unhealthy `db`, wrong user ...) ends the script after `podman stop` of MIA: MIA stays stopped and the temporary copy of the data volume (histories, account hashes) stays in `/tmp`. Reproduced on a scratch copy with the stubs of `test_up_backup.py` and a `backup.sh` that exits 1: exit 1, no `podman start`, tmp folder left. The db restore path (`:205`) handles the same failure. Introduced by b6427d8. | Medium | Needs test, Phase 3: regression test in `tests/test_up_backup.py` (failing backup tool → `podman start mia1` is called, no tmp folder left, exit ≠ 0), then start MIA again and remove the folder on failure (a trap or `||` as at `:205`). |
| F2 | REQ-OPR-003 in the stack: `__main__.py:42-44` warns about every option of `setup_cfg.example.json` that the mounted `setup_cfg.json` lacks. The stack mounts `deploy/setup_cfg.compose.json`, which lacks 31 of 108 options on purpose (defaults), and `config.missing` (`config.py:80-88`) ignores `setup_cfg.local.json` (e.g. `accounts_enabled`). Computed with `config.warning` on a copy: "lacks 31 option(s)" plus 31 lines at every start of the mia container, so the report no longer means "after an update". Open for Verify in the log (line 34). | Medium | Owner decision. Proposal: complete `setup_cfg.compose.json` with every option (the example's values or the defaults) plus a test in `tests/test_deploy.py` that it lists every option of the example, and let `config.missing` count the local overlay; alternative: accept the noise as a deviation. |
| F3 | REQ-OPR-001 "with its database": nothing reads `MIA_DATABASE_URL`; `deploy/compose.yaml:21` says "the storage option picks the database", but no such option exists. | Low | Accepted deviation per D-139 (4) (until the store moves to PostgreSQL); fix the comment. |
| F4 | `deploy/RUNBOOK.md`: (a) `:13-16` names `ui/godot/assets/mia.vrm` as the missing character file, but the stack mounts `ui/godot/build/web`, installed with `deploy/up.sh character ZIP` (deploy/README "The 3D character"), which the runbook does not mention; (b) `:23` lists three pinned images, `postgres:16` and `python:3.12-slim` (D-139 (6)) are missing; (c) `:20` `curl http://127.0.0.1:11434/api/tags` and `podman exec ollama` work only for a host Ollama, the stack's own `ollama` publishes no port and its container is `mia_ollama_1`. Also stale: `deploy/README.md` "Four containers" and the header of `compose.yaml:1-5`. | Low | Fix in the runbook (with a test line for `build/web` / `up.sh character` in `test_runbook.py`); the owner's walkthrough TC-OPR-006 would find them. |
| F5 | `first_account.py:33`: Ctrl+D at the terminal prompt raises `EOFError` and stops `python -m MIA` at start (up.sh handles it with `|| name=""`); `:35-37` ignores the result of `accounts_cli.py create` and prints the login hint even when the account was not made (password mismatch); the marker is already written, so no second offer. | Low | Needs test, Phase 3: EOF counts as "later"; on a failed create print the command instead of the hint. |
| F6 | `deploy/up.sh:113` and `:244` append to `.env` without the last-newline check of `:18`, which runs only when the secret is missing: a hand-edited `.env` without its last newline gets a merged line (`OLLAMA_URL=...MIA_FIRST_ACCOUNT_OFFERED=1`). | Low | Needs test, Phase 3: do the newline check once before any append. |
| F7 | `tools/backup.sh:22`, `tools/restore.sh:57,61` call `podman` directly, while `up.sh` supports docker (`ENGINE`): `up.sh backup` with `db` fails under docker. | Low | Owner decision: podman only (say so in deploy/README) or pass the engine. |
| F8 | Architecture model: `first_account.py`, `tools/check_free.py`, `deploy/RUNBOOK.md` belong to no part of `OperationLayer`; `composeStack` names "MIA, Ollama, SearXNG and Caddy" only (`architecture.sysml:588-612`). | Low | Phase 2 doc amendment (module lists and doc). |
| F9 | `tests/smoke/smoke_stack.py:30`: "graph alone" compares 4 files, not `graph_app/vendor/`; TC-OPR-007 says every served file. The IF-104 JS suite passes with 5 of 10 skipped (log line 122), the real halves waiting for the backend route. | Low | Protected: an amendment if the owner wants the vendor files compared; the skips are expected until N-5 wires IF-104. |
| F10 | `__main__.py:49-57`: the offer reads `accounts_dir` from `setup_cfg.json` only (plain `json.load`), the web app with the local overlay (`web_app.py:103`); an `accounts_dir` set only in `setup_cfg.local.json` makes the offer count the wrong folder. | Low | Record; fix with F2 if the overlay is counted there. |

## Accepted deviations (candidates, for the owner)
| Deviation | Reason | Accepted by |
|---|---|---|
| F3: `deploy/up.sh db` starts PostgreSQL, MIA uses the file store | D-139 (4) | owner (D-139) |
| Secret and database password in the image (F-T06-1) | D-139 (1), D-131 | owner (D-139) |
| TC-OPR-002 and -005 at stage 1 with stubs instead of stage 3 | the real parts are covered by TC-SLY-008 and SMOKE-MIA-001 | owner (to confirm) |

## Manual checks for the owner
- M1 TC-OPR-006: walk through `deploy/RUNBOOK.md` once on a clean machine (watch F4).
- M2 SMOKE-MIA-002: a port scan from outside the home network; only 8586 reachable inside the LAN with `MIA_BIND=0.0.0.0`, nothing from outside.
- M3 TC-OPR-005 in the stack: `deploy/up.sh db`, `deploy/up.sh backup x.tar.gz` (archive holds `db.dump` and `data.tar`), wipe, `deploy/up.sh restore x.tar.gz`, same data. Never run against a real stack so far.
- M4 TC-OPR-009: `python tools/check_free.py --log <the web logs of the volume>` after a session; review the lists `PAID_PACKAGES` / `PAID_HOSTS` (D-133 (7)).
- M5 index digests of the images at the next pin update (D-139 (6)).

## Notes for Phase 7 (validation)
- Two offers of the first account in the stack (terminal of `up.sh` and the container log, D-139 (2)): watch whether users are confused.
- The start warning of F2 may train users to ignore warnings.
- `podman stop` gives MIA 10 s (no `stop_grace_period`); history and database come first in the shutdown, so only the helpers may be killed.

## Re-verification (2026-10-31)
**State:** goal/v1 @ f4da817 (fixes: branch v1-n42-ops3, merged in c893a7e: 84b3176, 3135c0b, 28b57ed, 5c4e7e4, 311d3df, d90b792, c13f91b; model change 3b41371). **Reviewer:** Claude Opus 5.5, fresh context (AI), never saw the implementation or fix chat. **Decisions read:** D-139, D-144, D-145, D-146. No file under `deploy/`, `config.py`, `first_account.py`, `__main__.py`, `tools/backup.sh`, `tools/restore.sh` or the node's tests changed between c893a7e and f4da817.

### Findings of the first verification
"Red before" = the new test run on a scratch copy of f4da817 with the source files of c893a7e^1 (`deploy/up.sh`, `config.py`, `first_account.py`, `deploy/setup_cfg.compose.json`, `deploy/RUNBOOK.md`) put back; removed afterwards.

| # | State | Evidence |
|---|---|---|
| F1 | **Fixed** | `deploy/up.sh:183-193,209`: `make_backup` removes its mktemp copy whatever the tools do and returns their result; both callers start MIA again (and the restore path removes `$TMP`) and exit 1. Tests `test_a_failing_backup_starts_mia_again_and_leaves_no_copy`, `test_a_failing_backup_before_a_restore_starts_mia_again_and_leaves_no_copy` (`tests/test_up_backup.py`): red before (2 failures), green now (7 OK). Mutants on a scratch copy, all killed: copy removed only on success (2 failures), restore folder kept on failure (1), failed backup exits 0 (1). Left as stated in the log: a partial archive a failing tool may write is not removed (info, see N4). |
| F2 | **Fixed; the tracked `"accounts_enabled": false` decided and applied (D-146)** | `deploy/setup_cfg.compose.json` lists the 108 options of the example, no extra key; `config.missing` (`config.py:87`) reads with `config.load`, so the local file counts. Computed on a copy of the stack layout (compose config as `setup_cfg.json`, example, `{}` local): `config.warning` → None. Tests `test_the_config_of_the_stack_lists_every_option_of_the_example` (`tests/test_deploy.py`) and `test_an_option_of_the_local_file_counts_as_present` (`tests/test_missing_options.py`): red before, green now. The changed assertion of `test_the_settings_of_one_machine_are_a_local_file_that_is_not_in_git` (now `false` instead of absent) matches D-146. I checked every added value against the code's default: equal except `scholar_cache_dir` (no cache → `data/cache/scholar`) and `source_trust_file` (not read → `data/source_trust.json`), as the log says; see N1 for these two. |
| F3 | **Fixed (comment)** | `deploy/compose.yaml:22` now says nothing reads `MIA_DATABASE_URL`; `grep` confirms no code reads it. No test needed (no behaviour). The deviation itself stays accepted (D-139 (4)). |
| F4 | **Fixed** | `deploy/RUNBOOK.md:13-24`: `ui/godot/build/web` with `deploy/up.sh character`, both kinds of Ollama (`deploy/up.sh exec ollama ...` passes through to `compose exec`, `up.sh:275-276`; not run, no stack started), all six pinned images. Tests `test_the_runbook_names_the_character_folder_the_stack_mounts`, `test_the_pin_update_names_every_pinned_image_and_both_kinds_of_ollama`: red before (2 failures), green now (8 OK). `deploy/README.md:3` and `compose.yaml:1-2` list the containers. Left over: the top-level `README.md:60` still says "three containers" (N2). |
| F5 | **Fixed** | `first_account.py:33-45`: EOFError is "later"; a non-zero return code of `accounts_cli.py create` prints the command instead of the login hint. Tests `test_ctrl_d_at_the_prompt_counts_as_later`, `test_a_failed_create_prints_the_command_instead_of_the_login_hint`: red before (1 error, 1 failure, in the image), green now (9 OK). Mutant "return code ignored" killed (1 failure). |
| F6 | **Fixed** | `deploy/up.sh:17`: the last-newline check runs once before every append. Tests `test_the_marker_of_the_offer_gets_a_line_of_its_own`, `test_the_database_password_gets_a_line_of_its_own` (`tests/test_up_fresh.py`): red before (2 failures), green now (6 OK). |
| F7 | **Recorded (D-145)** | podman only in `tools/backup.sh` / `tools/restore.sh`; not changed. deploy/README does not say "podman only" for `up.sh backup` with `db` (stays a known limitation). |
| F8 | **Fixed (model, D-145)** | 3b41371: `launcher` names `first_account.py`, `composeStack` names graph, db, pins, runbook and the backup tools, new part `freeCheck` (`tools/check_free.py`). `check_sysml.sh` 4 files 0 errors; `check_sysml_model.py` OK with the note "part operation.freeCheck carries no requirement" (N3). |
| F9 | **Recorded (D-145)** | protected smoke unchanged; the skips of the IF-104 suite wait for N-5. |
| F10 | **Recorded (D-145)** | `__main__.py:57-58` still reads `accounts_dir` from `setup_cfg.json` alone (`json.load`, `__main__.py:46-47`). |

### New findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| N1 | The complete stack config turns on two things the stack did not do before, and the operation docs do not say so. (a) `deploy/setup_cfg.compose.json:84` `scholar_cache_dir`: scholarly API answers (URL with the research query, body) are cached as JSON files in the volume `mia-data`; `ResponseCache` (`scholar.py:336-363`) ignores entries older than 7 days but never deletes them, so the folder only grows and every backup archive carries it. Safety checked: the Semantic Scholar key goes in a header and is not part of the cache key (`scholar.py:701`); `scholar_email` is null in the stack (otherwise it would appear in the cached URLs as `mailto`); write errors are swallowed; only MIA writes the volume. (b) `:89` `source_trust_file`: the stack now reads `data/source_trust.json`, which `POST /api/trust` writes (`web_app.py:668`, `trust_persona_api.py:55-71`); with `accounts_enabled` false that route has no login, so with `MIA_BIND=0.0.0.0` any device in the LAN can change the trust classes that the stack's literature reviews now use. Before the fix such edits were written but ignored by the stack. Within D-131 (trusted users, controlled environment), and the same as on the development machine, so not a blocker. `deploy/README.md:31` (`data/`: "histories, presets, logs, token") and `deploy/RUNBOOK.md:27` mention neither. | Low | Owner decision (keep both on), then a doc line; a test only if pruning is wanted | Keep both (README describes them as defaults of the example); add "scholar cache, trust overrides" to `deploy/README.md:31`; owner decides whether expired cache files should be pruned at start (then a test in `tests/test_scholar.py` first) or excluded from the backup. |
| N2 | `README.md:60` still says "MIA, Ollama and SearXNG as three containers"; F4 fixed `deploy/README.md` and the compose header only. | Low | Doc fix, no test | Name the six containers or point to `deploy/README.md`. |
| N3 | `specs/mia/architecture.sysml:614` new part `freeCheck` has no requirement allocated or satisfied (REQ-OPR-009 is satisfied by `mia.operation` as a whole); `check_sysml_model.py` prints a note, not an error. | Info | Phase 2 doc amendment, optional | `allocate r_req_opr_009 to mia.operation.freeCheck;` with the next model change. |
| N4 | `deploy/up.sh:192`: after a failed backup a partial archive at the requested path may remain while the message says only "the backup failed"; the log states it is the tool's business. | Info | – | Optionally name the path in the message ("do not use <file>"). |
| N5 | Listing the defaults in the tracked stack config freezes them: a later change of a code default (e.g. `DEFAULT_BUDGET`, `review_answer_seconds`) no longer reaches the stack, and a removed `review_budget` key would make `Budget` raise "unknown limit" (`extensions/review/review_request.py:44-46`). The completeness test guards new options, not changed defaults. | Info | – | Note for the runbook's update step: compare `setup_cfg.compose.json` with the example after an update. |

### Checks (reviewer's own runs, no CI)
| Check | Result |
|---|---|
| Tests in the image (`bash tools/run_in_image.sh`, image `localhost/mia:latest`, checkout mounted) | `test_missing_options` 6, `test_config` 14, `test_config_local` 5, `test_shutdown` 15, `test_shutdown_database` 5, `test_compose_stack` 6, `test_check_free` 6, `test_first_account` 9, `test_deploy` 17, `test_requirements` 7, `test_storage` 12, `test_runbook` 8: all OK, exit 0 |
| Tests on the host (stubs) | `test_up_backup` 7, `test_first_account_up` 4, `test_up_fresh` 6, `test_runbook` 8, `test_compose_stack` 6, `test_deploy` 17, `test_check_free` 6: all OK |
| Database test (venv `mia312`) | `tests/test_backup.py` 3 OK (own `postgres:16` on loopback, removed by the test) |
| Red before / mutation | 11 new tests all red on the pre-fix sources; 4 mutants of the fixes all killed (above). Scratch copies removed. |
| Protected material | `git diff c893a7e^1 c893a7e` touches no path under `tests/acceptance`, `tests/helpers`, `tests/smoke`, `tests/integration`, `contracts`, `benchmarks`, `eval/suites`, `eval/baselines`. |
| SysML | `bash tools/check_sysml.sh`: 4 files, 0 errors, 0 warnings; `python3 -I tools/check_sysml_model.py .`: OK (notes: `verifier.toolDoor`, `operation.freeCheck` carry no requirement) |
| `trace_check.py` | exit 1 with 93 errors and 250 warnings, as in the first verification (93); the N-4.2 lines: ERROR "test-spec.md: 10 check(s) but no '## Scenarios' section" (M39, plan-level, unchanged since Plan, also N-4.1 and N-4), WARN TD-01…TD-04 "open deferral not listed" (none of them belongs to N-4.2: TD-01…03 UI, TD-04 REQ-WFM-039; listed here to answer the check). No error for REQ-OPR-001…010. |
| `test_doc_check.py` (node's test files) | 0 errors in the new or changed tests (`test_up_backup`, `test_up_fresh`, `test_runbook`, `test_missing_options`, `test_first_account`, `test_first_account_up`, `test_compose_stack`, `test_check_free`, `test_shutdown_database`). Older files keep their earlier T1/T2 errors (`test_deploy` 19, the same 19 before the fixes; `test_config` 21, `test_shutdown` 20, `test_storage` 23, `test_requirements` 10, `test_config_local` 5, `test_backup` 5): not from this fix branch. |
| Smoke tests, stack | Not run (instruction). No deploy file changed after the fixes besides those reviewed above; the A-46/A-47 smoke runs predate the fixes, so the second start and the stack config with the cache are unrun in a real stack (M3, M6). |
| Known failures | `test_amendment_report`, `test_harness` (rt_edit): not run here, not part of the node. |

### Remaining manual checks for the owner
- M1 TC-OPR-006 walkthrough of `deploy/RUNBOOK.md` on a clean machine (now including `deploy/up.sh character` and `deploy/up.sh exec ollama ollama list`).
- M2 SMOKE-MIA-002 outside port scan.
- M3 TC-OPR-005 in a real stack: `deploy/up.sh db`, `backup`, wipe, `restore`; once also with `db` stopped to see F1's message and MIA started again.
- M4 `tools/check_free.py --log` on a real web log; review `PAID_PACKAGES` / `PAID_HOSTS`.
- M5 index digests at the next pin update.
- M6 one start of the stack with the new config: no "lacks N option(s)" warning in `podman logs mia_mia_1`; after one literature review, `data/cache/scholar` exists in the volume (N1).
- Decide N1 (pruning / docs) and N2.

### Proposed status
**Verified with accepted deviations.** F1 to F6 are fixed, each with tests that fail on the old code and pass now (mutants killed); F2's tracked `"accounts_enabled": false` is the owner's choice (D-146); F8 is fixed in the model and F7, F9, F10 are recorded (D-145); F3 stays an accepted deviation (D-139 (4)). The new findings are low (N1 docs and an unpruned cache inside D-131's trust assumption, N2 one stale README line) or info, none blocks. REQ-OPR-006 (walkthrough) and the scan part of REQ-OPR-008 stay with the owner in Phase 6.
