# Implementation log: Operation (N-4.2)

Goal G-V1 (line of work `goal/v1`). Method (owner's rule: test the existing code first, change only what fails).

## T-01 Report of missing options (2026-10-31, done at unit level; startup wiring open) – REQ-OPR-003

The existing code already reports missing options (`config.missing`, `python config.py [folder]`); the task added the test of TC-OPR-003 and completed the example file, which the test case assumes lists every option.

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-OPR-003 missing options reported | `config.missing(folder)` (unchanged): the options of `setup_cfg.example.json` that `setup_cfg.json` lacks, with the example's value; `config.py` as a command prints one line per option | `tests/test_missing_options.py` (3): two options removed from the real example give exactly these two, in `missing()` and in the printed report; none removed gives none |

Finding (existing failure of `tests/test_config.py`, `test_every_option_the_code_reads_is_in_the_example`): on `goal/v1` (f80c552) the scan of the code found 11 keys read by the code but not in `setup_cfg.example.json`, so the precondition of TC-OPR-003 ("the example lists every option") did not hold:
- 8 real options added by earlier tasks without the example: `files_dir`, `files_max_bytes`, `files_max_total_bytes`, `model_classes_file`, `review_answer_seconds`, `skill_options` (web_app.py), `workflow_speak`, `workflow_speak_tasks` (workflow_voice.py). Fixed: added to the example with the defaults of the code (1 GiB, 50 GiB, 1800 s, `{}` for the two maps, which the code treats like absent). No behaviour changes.
- 3 false positives of the scan, not options of the file: `MIA_PROXY_TRUST` (Flask `app.config` in accounts_api.py), `budget` and `model_pin` (`options` of a workflow run in run_workflow.py). Not fixed: the fix is in `tests/test_config.py` (`NOT_OPTIONS`), outside the task's bounds. The test still fails with these three.

The test file is new (`tests/test_missing_options.py`) instead of an extension of `tests/test_config.py` (plan note), so that the local model typed one whole file and no existing test was touched.

Local coder: `tests/test_missing_options.py` typed by the local model from an exact instruction (task `n42-t01-missing-options`, 1 attempt, 34 s); every instruction line found verbatim by script; verdict `ok`.

Tests reported green (feedback, not verification): `tests/test_missing_options.py` (3), `tests/test_config_local.py` (5), `tests/test_deploy.py` (16), `tests/test_requirements.py` (7); `tests/test_config.py` 13 of 14 (the 3 false positives above).

Open questions for the owner:
- Q1: add `MIA_PROXY_TRUST`, `budget`, `model_pin` to `NOT_OPTIONS` in `tests/test_config.py` (or narrow the scan to `cfg`)? Recommendation: add them to `NOT_OPTIONS` with a one-line reason each; a small follow-up in that test file.
- Q2: REQ-OPR-003 says "when MIA starts after an update"; nothing calls `config.missing` at start (`__main__.py`, `web_app.py` only call `ensure`). Wiring the report into the start touches `__main__.py`, outside T-01's files, and the wording of the start message is fixed by no requirement. Recommendation: one line in `__main__.py` after `ensure_config` that prints the report of `config.py` (same wording as the command), as an amendment of T-01's Touches; until then TC-OPR-003 (Unit) is met by the function and the command only.
- Q3: the 8 options added to the example are not described in README.md ("Configuration"), which the docstring of `config.py` promises. README.md is outside the task's files. Recommendation: describe them in the same follow-up as Q1.

### T-01 follow-up (2026-10-31, done) – owner's answers Q1 to Q3 (D-120: yes to all)
- Q1: `MIA_PROXY_TRUST`, `budget`, `model_pin` added to `NOT_OPTIONS` in `tests/test_config.py` with a one-line reason each; `test_config.py` is green (14 of 14).
- Q2: `config.warning(folder)` (new) returns the report as text ("Warning: setup_cfg.json lacks N option(s) of setup_cfg.example.json (the defaults apply until you add them; README.md describes them):" and one line per option) or None; `python config.py` prints it (else "has every option"), and `__main__.py` prints it right after `ensure_config` (only for `setup_cfg.json`, like `ensure`). The command's first line now starts with "Warning: "; otherwise the wording is unchanged. Tests (written by hand, two additions to `tests/test_missing_options.py`, red before: 1 failure, 1 error): `test_the_start_warning_names_both_and_no_others`, `test_mia_prints_the_warning_at_start` (a source check like `test_shutdown.MiaCodeUsesIt`: `__main__.py` imports at package level and starts the whole app, so it is not run in a unit test).
- Q3: README "Configuration" describes the 8 options (`files_dir`, `files_max_bytes`, `files_max_total_bytes`, `model_classes_file`, `review_answer_seconds`, `skill_options`, `workflow_speak`, `workflow_speak_tasks`), the count of options is 108, and the start warning is mentioned.
- Touches beyond the plan's list (approved by D-120): `tests/test_config.py`, `__main__.py`, `README.md`.
- Tests reported green (feedback, not verification), in the image: `test_missing_options` (5), `test_config` (14), `test_config_local`, `test_deploy`, `test_requirements`.
- Open for Verify: the warning ignores `setup_cfg.local.json` (an option set only in the local overlay is still reported missing); no requirement says whether the overlay counts.

## T-02 Orderly shutdown with the database (2026-10-31, done) – REQ-OPR-004

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-OPR-004 orderly shutdown, memory saved | `shutdown.close_database(storage)` (new): closes the backend when it has `close()` (PostgreSQL), nothing for the file backend or None; `__main__.py` runs it as the step "close the database" right after "save history" and before the helpers stop | `tests/test_shutdown_database.py` (5): close once / nothing to close; SIGTERM, Ctrl+C and /goodnight! on the harness each save the history and keep the memory record, identical on the next start, in the order history, database, proxy, speech; `tests/test_shutdown.py` `MiaCodeUsesIt` asserts the step in `__main__.py` after "save history" |

- `tests/shutdown_harness.py` (test support, not protected) takes an optional data folder: a history in memory saved to `memories.json` at shutdown and one memory record in a file database (`Storage(FileBackend)`, `MemoryRecords`), closed by `close_database`.
- /goodnight! is tested as the signal it ends in (SIGINT to MIA itself, after dreaming): `test_shutdown.test_commands_ask_for_an_orderly_shutdown` already shows that /goodnight! dreams and then requests the shutdown; dreaming needs the model and is not run here.
- Red first: the 5 new tests failed on the old `shutdown.py` (no `close_database`: 2 errors, 3 harness failures); the new assertion in `test_shutdown.py` fails on the old `__main__.py`.
- Touches beyond `shutdown.py` (trivial, logged): `__main__.py` (one import, one step), `README.md` ("Stopping MIA" names the database), `tests/test_shutdown.py`, `tests/shutdown_harness.py`.
- Local coder: `tests/test_shutdown_database.py` typed by the local model (task `n42-t02-shutdown-db`, 1 attempt, 59 s); fixture lines and every statement found verbatim by script; verdict `ok`.
- Tests reported green (feedback, not verification), in the image: `test_shutdown_database` (5), `test_storage` (12); `test_shutdown` 14 of 15 (the known failure `test_group_stop_also_ends_the_helpers_of_the_process`, also on master: in the container the killed `sleep` stays a zombie without an init, so `os.kill(pid, 0)` still finds it; checked: with `podman run --init` all 15 pass). Proposal: `--init` in `tools/run_in_image.sh` (outside this node; owner decides).
- Open for Verify: the app's database today is the file backend (`web_app._votes_store`); the PostgreSQL path of `close_database` is shown with a fake backend only. Requests of web threads that are still running after the close would fail (the web server has stopped accepting by then).

## T-03 Compose stack (2026-10-31, stopped before the first test: decisions needed) – REQ-OPR-007, -008, -010

State found: `deploy/compose.yaml` has `mia` (backend with the frontend), `https` (Caddy), `ollama` (profile), `db` (profile, N-3.1 T-08), `searxng`. `OLLAMA_MAX_LOADED_MODELS: "1"` is set in the base file and not overridden by the ROCm/NVIDIA overlays (TC-OPR-010 holds already). No test of TC-OPR-007/-008/-010 exists yet.

Open questions for the owner:
- T03-Q1 (TC-OPR-008 vs today's stack): "only the HTTPS front publishes a port", but `mia` publishes http 8585 on `MIA_BIND` (127.0.0.1 by default), which README and `up.sh` tell users to open. Drop the http port (the page only through https 8586), or keep it bound to 127.0.0.1 and read TC-OPR-008 as "only the HTTPS front publishes a port to the network"? Recommendation: keep 127.0.0.1:8585 for the local page and count only ports on non-loopback addresses (a test asserts every published port of every service except `https` binds to 127.0.0.1); needs the owner's reading written into TC-OPR-008.
- T03-Q2 (REQ-OPR-007 "one container per node, N-2 to N-5"): which containers exactly? Today N-2 = `mia`, N-3 = `db`; N-4 (evaluation) has no service, N-5 (graph app) is being built in another line of work. Recommendation: N-2 `mia`, N-3 `db`, N-5 `graph` added when N-5 delivers it, N-4 none (the eval harness runs from the `mia` image as a command); write that into REQ-OPR-007 or the node's test spec.
- T03-Q3 ("each container alone against the mocks of its neighbours", SMOKE-MIA-003): which mocks run as containers (a mock database? a mock backend for N-5?) and from which image? None exists; a mock service is a new part. Recommendation: the mocks of `tests/helpers/` run inside the `mia` image (`podman run localhost/mia:latest python -m ...`), so no new image; needs a decision and probably an amendment to the test spec.
- T03-Q4 (images): `ollama:latest`, `searxng:latest`, `caddy:2` float. Pin them by digest for the stack (and the retirement freeze of REQ-OPR-006)? Recommendation: yes, pinned in T-08's freeze step, not in T-03.
T-04 to T-08 not started (plan order; T-07 depends on T-03). Seen ahead: T-04 needs no new dependency (stdlib script: `LICENSE` is GPL-3 already, a list of banned paid-API packages, a host list for the web log).

## T-03 answers of the owner (2026-10-31, D-127) and amendment A-37
The owner answered T03-Q1 to Q4 with the recommendations: (1) 8585 stays on loopback, TC-OPR-008 reads "nothing except the HTTPS front publishes a port on a non-loopback address"; (2) containers `mia` (N-2), `db` (N-3), `graph` (N-5, once delivered), none for N-4; (3) the mocks of `tests/helpers` run inside the mia image for SMOKE-MIA-003 / TC-OPR-007; (4) image digests pinned in T-08. A-37 changes the wording of REQ-OPR-007, TC-OPR-007, TC-OPR-008 and SMOKE-MIA-003 (`specs/mia/test-spec.md`). T-03 can continue. The proposal `--init` in `tools/run_in_image.sh` is still open.

## T-03 Compose stack (2026-10-31, partly done: TC-OPR-008 and TC-OPR-010 green, TC-OPR-007 stopped) – REQ-OPR-007, -008, -010

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-OPR-008 private access only | `deploy/compose.yaml`: the port of `mia` is `127.0.0.1:${MIA_PORT:-8585}:8585`, no longer on `MIA_BIND`; only `https` follows `MIA_BIND`; no script calls `tailscale funnel` | `tests/test_compose_stack.py` (3 of 4): every published port of a service other than `https` starts with `127.0.0.1:` in all three variants; `https` and `mia` each publish one port; no shell or Python file outside tests/ and specs/ has `tailscale funnel` or the argument `"funnel"` in code |
| REQ-OPR-010 one model at a time | `OLLAMA_MAX_LOADED_MODELS: "1"` in the base file, not overridden by the ROCm/NVIDIA overlays (unchanged) | `tests/test_compose_stack.py` (1 of 4): the base environment merged with each overlay gives "1" |
| REQ-OPR-007 compose stack | not done (questions below) | – |

- Red first: `test_only_the_https_front_publishes_a_port_off_loopback` failed on the old `compose.yaml` (`mia publishes ${MIA_BIND:-127.0.0.1}:${MIA_PORT:-8585}:8585`); the other three hold on the old files (characterization of TC-OPR-008's script part and TC-OPR-010).
- Reading of A-37 (behaviour change, for the owner to confirm): TC-OPR-008 says nothing except the HTTPS front publishes on a non-loopback address. With the old file `MIA_BIND=0.0.0.0` (which README and `up.sh` recommend for other devices) also put http 8585 on all addresses. The port of `mia` is now fixed to loopback; `MIA_BIND` moves only the https port. `up.sh` prints http only for localhost and https for the other addresses; `deploy/README.md` says so (two sentences). `podman compose config` renders `127.0.0.1:8585:8585`.
- Touches beyond the plan's list (trivial, logged): `deploy/up.sh` (the printed addresses), `deploy/README.md`; new test file `tests/test_compose_stack.py`.
- Local coder: `tests/test_compose_stack.py` typed by the local model (task `n42-t03-compose-stack`, attempt 2 passed, 87 s in all); UNCHANGED block identical by difflib, every statement found by a membership check except one comment ("ollode" for "ollama"), fixed by hand; verdict `fixed`.
- Tests reported green (feedback, not verification), in the image: `test_compose_stack` (4), `test_deploy` (16).

Stopped at TC-OPR-007 (decisions needed; no new part built):
- T03-Q5 (the `graph` container): `graph_app/` is a static page (vis-network, opens a JSON file; IF-104 wiring is N-5 T-02 to T-03, and the backend serves no IF-104 route yet). Which server and which door? (a) a `graph` service from the mia image running `python -m http.server --directory graph_app`, reached through the https front under a path (Caddyfile route `/graph/` -> graph, same origin as the IF-104 calls later); (b) the same with `caddy:2` `file_server` (image already in the stack); (c) wait until N-5 T-03 wires IF-104 and add the service then. Recommendation: (a), same origin through the https front, no published port; the Caddyfile change is outside T-03's files and needs approval.
- T03-Q6 (the graph's contract suite alone): its suite is JavaScript (`tests/acceptance/contract/test_if_104_graph_api.test.mjs`, node); no image of the stack has node, and the mocks of `tests/helpers` are in-process objects, not services. Options: (a) run the JS suite on the host (node exists there) against the files the graph container serves, counting that as "graph alone"; (b) a node image (a new dependency); (c) narrow TC-OPR-007 for `graph` to "its page loads from the container". Recommendation: (a), written into TC-OPR-007 by an amendment.
- T03-Q7 (where the stage 3 test lives): TC-OPR-007 is SMOKE-MIA-003, and `tests/smoke/` is protected. Options: (a) an amendment draft `tests/smoke/smoke_stack.py` under `specs/mia/amendments/` with an install script, written by me, installed by the owner; (b) an unprotected `tests/test_compose_stack_system.py` (stage 3, skipped without podman). Recommendation: (a) for the smoke, plus the per-container contract runs that exist already (`run_in_image.sh` of the Python contract suites for `mia`; N-3.1's PostgreSQL suite for `db`).
- Next step for TC-OPR-007 after the answers: the `graph` service in `compose.yaml` (and Caddyfile route), then the smoke draft.

## T-04 Licence and dependency check (2026-10-31, done) – REQ-OPR-009

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-OPR-009 free and open | `tools/check_free.py` (new, stdlib only): `licence_problems` (LICENSE is the GPL v3 text, README.md grants "version 3 ... or (at your option) any later version"), `paid_packages` (requirement lines whose normalized name is in `PAID_PACKAGES`), `paid_hosts` (web log lines whose `url` host is in `PAID_HOSTS` or below one); `python tools/check_free.py [--repo DIR] [--log FILE ...]` exits 0 with "free and open ..." or 1 with one line per problem | `tests/test_check_free.py` (6): this repository's licence; an MIT LICENSE reported; `requirements.txt` and `requirements-db.txt` clean; `OpenAI>=1.0`, `anthropic[bedrock]==0.40`, `google_generativeai` found; two paid hosts in a web log found with their line numbers, a search query naming one is not; the command's exit codes |

- Red first: all 6 failed on the old tree (`ModuleNotFoundError: check_free`).
- The two lists (`PAID_PACKAGES`, 22 names; `PAID_HOSTS`, 20 hosts) are the one place where paid APIs are named (plan note); their content is my choice from the common paid LLM, speech, translation and search APIs. Open for the owner/Verify: review the lists (e.g. whether DeepL Free or Bing count).
- Not checked: the web log of a real session. The worktree has no `data/runs/web-*.jsonl`; the owner runs `python tools/check_free.py --repo <the checkout that MIA runs from>` (or `--log` on the volume's logs) once after a session. Without a log the command still checks the licence and the requirement files.
- No new dependency. Local coder: `tests/test_check_free.py` typed by the local model (task `n42-t04-check-free`, 1 attempt, 55 s); UNCHANGED block identical by difflib, every statement found by a membership check; verdict `ok`.
- Tests reported green (feedback, not verification), in the image: `test_check_free` (6); `python3 tools/check_free.py` on this checkout: free and open (2 requirement files, 0 web logs).

## T-05 Backup and restore of all data (2026-10-31, stopped before the first test: decisions needed) – REQ-OPR-005

State found: `tools/backup.sh` and `tools/restore.sh` exist (N-3.1 T-07, `61c7ed0`): one archive with `db.dump` (pg_dump of a named container) and `data.tar` (`--data DIR`, a host folder); `tests/test_backup.py` (TC-SLY-008) already does TC-OPR-005's setup (50 records with versions and a data folder, backup, wipe both, restore, same records and files). But the stack's own command, `deploy/up.sh backup|restore` (README), copies only the `mia-data` volume, not the `db` service's database, so in the stack with `db` "all data including the database" is not backed up by the documented command.

Open questions for the owner:
- T05-Q1 (the backup command of the stack): (a) `deploy/up.sh backup|restore` calls `tools/backup.sh`/`restore.sh` with the `db` container when that service exists (archive with `db.dump` + `data.tar`; restore also accepts the old data-only archive); (b) keep `up.sh backup` for the volume and document `tools/backup.sh --db-container mia_db_1` as a second step (a list of steps, which the plan note rules out); (c) the database part only once N-3.1 moves the app's store to PostgreSQL (today `web_app._votes_store` is the file backend in the volume, which `up.sh backup` covers). Recommendation: (a); it touches `deploy/up.sh` (T-06/T-07's file), so it needs the Touches widened, and a test that reads the archive of `up.sh backup` against a stack with `db` (stage 3).
- T05-Q2 (where the database tests run): `tests/test_backup.py` is skipped on this host: no venv under `~/prog/Python/venvs` has psycopg (host python 3.14, `mia312` lacks it), and the mia image has psycopg but no podman to start `postgres:16`. Options: (a) install `requirements-db.txt` (psycopg, already a declared project dependency) into the `mia312` venv; (b) run the test in the image against a `postgres:16` container started by a wrapper script on the host (a pod or `--network` shared); (c) leave it to Verify/CI. Recommendation: (a), the owner's approval for changing the venv; until then TC-SLY-008/TC-OPR-005 are unchecked here (and in my earlier N-3.1 knowledge only reported, not seen).
- T05-Q3 (trace): mark the TC-SLY-008 test in `tests/test_backup.py` also with `REQ-OPR-005` (the same test serves both test cases), or a separate test for the stack command of Q1? Recommendation: the stack test of Q1 carries REQ-OPR-005; `test_backup.py` stays with N-3.1.

T-06 to T-08 not started (plan order; T-07 depends on T-03 and T-05, T-08 on T-07).
