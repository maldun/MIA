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
