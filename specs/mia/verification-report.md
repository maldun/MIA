# Verification report: MIA, goal G-V1 (first version)

**Goal:** G-V1 (iteration, no subgoals), supervised, accepted by Stefan Reiterer
**Branch:** goal/v1 @ 7091b62 (reviewed in the worktree branch `v1-verify`, equal to goal/v1)   **Parent line of work:** master   **Plan baselines:** `plan-baseline-it1` (4336393), `decomp-baseline` (fe819ca)
**Date:** 2026-11-01   **Reviewers:** Claude Sonnet 5.5 (AI, independent: never saw the implementation chat); human review: pending (the owner)
**Status of this report:** a proposal. I did not approve, merge, tag or install anything.

## Verdict (proposal)

**Verified with accepted deviations, conditional on the owner's decisions D-1 to D-9 below.** If the owner does not accept D-1 (NFR-8 is not met in the product) or D-2 (the red-team part of TC-MIA-006 is not held), the verdict is **Not verified**.

What is solid: 192 of 199 Python test files and all JS tests ran green or as known (details below), all 27 integration steps pass (N-0 step 05 is the planned skip), the protected material is explained by amendments except one unrecorded labelling step, goal check and decomposition check have 0 errors, the trace check has 46 error lines (baseline 47), no secret, no new dependency without approval.

What is not solid: one Must requirement (NFR-8, with CON-7) is not met in the running product, one root check (TC-MIA-006) is only held in part, the contract suites of three interfaces never ran against a real provider, no `test-requirements.md` exists, and the draft release documents contain claims that are wrong (F-01, F-05).

### Deviations the owner would have to accept
| # | Deviation | Why it is a candidate | Needs |
|---|---|---|---|
| D-1 | NFR-8 / AC-15 / TC-MIA-015 / CON-7: the running app keeps its state in the file backend; PostgreSQL runs but nothing reads it (F-01) | recorded at node level (D-139 (4), N-4.2 F3) but never at goal level; NFR-8 is "in" in goal.md without a "partly" row and without a TD record | decision + scope row or TD record; release notes corrected |
| D-2 | TC-MIA-006 / NFR-3: the red-team part ("0 failures over all red-team cases") is not held; the seven `rt_*` suites have 2 dev cases each and target kind `pending` (F-02) | no TD record, row is listed as kind B | decision + TD record (interim criterion = the deterministic injection and sandbox tests) |
| D-3 | Nine stage 4 checks deferred (TC-MIA-002, -003, -009, -011, -019, -022, -024, -025, -028 = TD-12 to TD-20, D-178/D-179) | owner's decision already; suites on the pinned model not run | recorded; owner confirms in this Verify |
| D-4 | N-5 Graph app and FR-22 out (D-177); N-0 step_05 stays a skip | owner's decision | recorded |
| D-5 | Contract suites IF-103, IF-404, IF-405 have only the mock side executed; IF-111 real side needs Godot; IF-102 on PostgreSQL not run here (F-03, F-04) | decomposition rule 3 asks for the suite on both sides | decision (accept for G-V1 or add TD records) |
| D-6 | Known failing files: `tests/test_amendment_report.py` (no git in the image), `tests/test_harness.py` (rt_edit 2 cases, wants 30), `tests/acceptance/test_benchmarks.py` (baseline never measured) | confirmed, causes confirmed (see Automated checks) | accept; the harness test is the same fact as D-2 |
| D-7 | Node verdicts "Verified with findings" of N-2.4.1 and N-2.4.2 (owner to accept in this Verify, merge request) | their findings are listed in their reports; not re-judged here | accept |
| D-8 | `sandbox_backend: none` in `deploy/setup_cfg.compose.json`: the script check is off in the deployed stack (F-15) | consistent with NFR-3 ("refused, not weakened") but THR-005's mitigation is then not active | accept + Phase 6 record |
| D-9 | No `test-requirements.md` at all (F-07) | M41/P24: no check has a TR; the table (a) cannot be filled | Plan amendment or acceptance as a project-wide deviation |

## Goal and scope
G-V1 scope: FR-1 to FR-33 except FR-22 (out), FR-34 and FR-35 (out, FB-01); NFR-1 to NFR-9; the partly/out rows of goal.md (REQ-RUN-*, REQ-GA-*, REQ-CHV-007/008, REQ-WFM-022, REQ-TLS-002/006 and others). `goal_check.py --tree`: 412 requirements in scope. Exit criterion VAL-001, VAL-003 to VAL-006 is field validation (Phase 7), VAL-002 moved on (D-134). The goal has no subgoals, no frozen requirements, no joint amendments, so the acceptance check F3 for unsupervised goals does not apply.

## Automated checks
All Python tests ran in the image (`localhost/mia:latest`, built 2026-10-31 22:53) with `bash tools/run_in_image.sh`-equivalent commands, one container per file (`podman run --rm --init --user 0 -v $PWD:/work:z -w /work localhost/mia:latest python <file>`), from the clean worktree of goal/v1, not from a `git archive` copy (deviation from the hand-over wording; the worktree has no untracked or modified tracked files before or after the runs, `git status --short` empty). Per-file results: `/home/maldun/.claude/jobs/1d092ebb/tmp/verify/py_results.txt`.

| Check | Command | Result |
|---|---|---|
| Python tests, all files | loop over `tests/test_*.py`, `tests/acceptance/test_*.py`, `tests/acceptance/contract/test_*.py` | 192 files run, **189 pass, 3 fail (the known three)**; 2254 tests, 119 skipped in the image; 7 files not run (podman stacks) |
| Python tests that skip in the image, re-run on the host | `python3 tests/test_sandbox.py`, `test_pdf_text.py`, `test_script_checks.py`, `acceptance/test_decide_guard.py` | 67 / 14 / 32 / 11 tests OK, 0 skipped (the host has bwrap and podman; the image has neither). 30 skips remain: IF-103 real 6, IF-404 real 5, IF-405 real 4, IF-101 2, IF-201 1, seed workflows 3 (T-10), storage_postgres 2, browser/podman tests 7 |
| Known failing files | same loop | `test_amendment_report.py`: `FileNotFoundError: git` (image has no git); `test_harness.py`: `2 not greater than or equal to 30 : rt_edit`; `acceptance/test_benchmarks.py`: `unexpectedly None : the baseline is measured at task T-06`. Causes confirmed as stated in the hand-over. `test_author_in_records.py` passed in this run. |
| Not run (podman stack, rule 3) | | `test_container_alone`, `test_container_alone_step`, `test_database_stack`, `test_delivery_on_stack`, `test_first_account_up`, `test_up_backup`, `test_up_fresh`; `tests/smoke/*` (3 files); `tools/container_alone.sh`; `tools/contract_postgres.sh` (also: no `psycopg` in the image or on the host) |
| JS tests | `node --test "tests/js/*.test.mjs"` | 161 tests, 161 pass, 0 fail, 0 skipped |
| JS contract suites | `node --test "tests/acceptance/contract/*.mjs"` | 36 tests, 23 pass, 0 fail, 13 skipped (IF-104 real 7: stale reason, see F-03; IF-111 real 6: Godot `test_bridge.gd`, D-155/A-73) |
| Integration steps | `python3 -I tools/run_integration_steps.py .` | 23 python + 4 JS steps: 25 OK, 2 "failed" on the host (N-2 step_05, N-0 step_04: no flask); both OK in the image (`python -m unittest -v tests/integration/N-2/step_05/test_step.py`, `N-0/step_04`); N-0 step_05: `skipped 'N-5 not integrated yet'` |
| Trace | `trace_check.py --spec-dir specs/mia --tests-dir tests` | 46 errors, 438 warnings (baseline 47; not higher). 26 errors are markers of the old feature specs (`IF-001..006`, `REQ-NUM/GATE/EVAL/STAB-*`, `NFR-BUD-001`) found in `tests/acceptance` that `specs/number-gate` owns; 20 are test-specs without `## Scenarios` (hand-over said 19); WARN: `no test requirements (M41)` |
| Goals | `goal_check.py --spec-dir specs/mia` | 0 errors, 0 warnings |
| Decomposition | `decomp_check.py --record specs/mia/decomposition.yaml --root .` | 0 errors, 7 warnings (N-1.1 tasks 8 vs plan 9; N-2.1 has 5 interfaces, exception stated) |
| Model ids | `python3 -I tools/check_sysml_model.py .` | OK, 30 acceptance criteria |
| SysML parse | `bash tools/check_sysml.sh` | 4 files, 0 errors, 0 warnings |
| Agent check | `agent_check.py --spec-dir specs/mia --eval-dir eval` | 2 errors, 640 warnings. Errors: A10 `SkillDigestStep` @TrustBoundary names no threat; A9 `SkillDigestStep` secondBudget 0.0 (an FB-01 item, out of G-V1, F-09). The tool reads the suite folders including `*.holdout`; I opened none and printed no holdout content |
| Quality | `quality_check.py --quality ... --requirements specs/mia/requirements.md` | 7 errors Q4 (ids live in node files). With all node `requirements.md` files passed: 0 errors, "All nine characteristics are covered". The stages.yaml step `quality` passes only the root file, so it fails (F-08) |
| Plausibility | `req_plausibility.py` with root + node requirements, `plausibility.yaml`, `deferred.md` | 19 errors (19 requirements without a record, F-14), 92 warnings; ratings 375 plausible, 40 questionable, 0 implausible |
| Refactor commits | `refactor_check.py --base plan-baseline-it1` | 1 error, 1 warning: `6ba63229` (F-10) |
| Agent config | `agent_config_diff.py --base plan-baseline-it1` | 0 errors; INFO `CLAUDE.md` (+2 -1) and `stages.yaml` (+31) for a person to read |
| Free and open | `python3 tools/check_free.py` | OK: GPL-3.0-or-later, no paid API in 2 requirement files |
| Test documentation | `test_doc_check.py --tests-dir tests` | 2649 findings in 159 files: T1 no docstring 1462, T2 no `Example:` 253, T3 no Given/When/Then 910, T4 23 (F-13) |
| Release check | `release_check.py --root .` | 3 errors (no CITATION.cff, no SBOM, no AI statement), 2 warnings (SPDX headers, README formats); only needed for outputs shared beyond the team (F-17) |
| Secrets scan | grep for key/token/password assignments, PEM, `ghp_`, `sk-`, `AKIA` over 1427 tracked non-binary files | no hit; no tracked `.env`, `.pem`, `.key`. (Known F-T06-1: the image contains `deploy/.env`, recorded D-139) |
| Dependencies | `git diff plan-baseline-it1 -- requirements*.txt`; AST scan of third-party imports | only change: `requirements-db.txt` (`psycopg[binary]>=3.2,<4`, approved D-54) and a comment line. Imports of `cv2`, `playsound` are the old local player (lazy, pre-existing). Browser image `selenium==4.25.0` is in `tests/browser/Containerfile`, approved D-141. The mia image installs only `requirements.txt` (F-01) |
| Static tools | ruff, bandit, vulture, pip-audit, semgrep, jscpd, import-linter | **not installed (host and image): not run** |
| Stage ladder | `run_stages.py` / CI | **not run**: no CI exists (`deploy/build.sh` missing). Equivalent coverage: stage 0-1 steps by hand above (model-ids, quality, decomposition, sysml-parse, js, unit by file, contract-js); stage 2 `acceptance`, `contract-real` by file; `integration` as above. Stage 3 steps `contract-postgres`, `container-alone`, `smoke` **not run** (hardware rule, no psycopg). No stage log, so `merge_gate.py` has nothing to read |
| Flakiness, benchmarks, statistical checks | | not run (stage 4 deferred; no repeated runs made). One run per file: no flake rate measured |
| Mutation testing | | not run by me; node reports claim mutants killed, with survivors named in nine of fifteen reports (plausible, not "all killed everywhere") |
| Documentation examples / clean-machine walkthrough | | not run (needs a fresh stack); `deploy/preflight.sh` run on this worktree: podman ok, 989 GB free, ports free, GPU devices ok, WARN missing untracked assets (character build, Kokoro, voice lines), WARN `sandbox_backend none`, FAIL model server not reachable (no Ollama running) |
| Usability evaluation with bad inputs | | not run (needs the stack and a browser; page tests exist). List for the owner |
| Deployable artifact builds | | not run (no build script; `deploy/Containerfile` exists; the image in use was built 2026-10-31 22:53 and is older than commits made on 2026-11-01, F-16) |

## Protected material against the baselines
`git diff --stat plan-baseline-it1 -- tests/acceptance tests/helpers tests/smoke tests/integration contracts benchmarks stages.yaml specs/mia/deferred.md specs/mia/decomposition.yaml specs/mia/plausibility.yaml eval/suites eval/baselines`: **148 files** (144 added, 4 modified). The tag `plan-baseline-it1` (2026-10-24) predates the decomposition Plan, so 52 of them are the decomposition Plan itself. Against `decomp-baseline` (2026-10-26, fe819ca): **97 files** (52 added, 45 modified). `specs/mia/test-requirements.md` does not exist (F-07); no `benchmarks/` change; `eval/baselines` unchanged (no `.jsonl` file exists).

| Group | Files | Mapped to |
|---|---|---|
| `contracts/IF-*.md` (17) | modified since decomp-baseline | amendments A-25, A-42 to A-68 etc. (commit subjects name them; per-file list in `/home/maldun/.claude/jobs/1d092ebb/tmp/verify/protmap2.txt`); the 6 interfaces first drafted in the decomposition Plan commits (IF-103, -105, -112, -203, -204, -405) are Plan-gate commits (`38aa847`, `110fe08`, `df132a8`, `46b9fc5`, `321e44c`) |
| `tests/helpers/**` mocks, `contract.py/.mjs`, `integration.py/.mjs` | modified | A-52 (IF-103 HTTP mock), A-54 to A-68, A-72 to A-81; new since decomp-baseline: `if_103_model_server_http.py` (A-52), `if_104_graph_api.mjs`, `real/if_112_voice_player.mjs` (amendments in the log) |
| `tests/acceptance/contract/*` (18) | modified | the matching IF amendments (suite, mock and spec change together) |
| `tests/acceptance/test_*.py` (8 new since decomp-baseline) | added | N-4.1/N-2.3/N-2.5 plan amendments (`check_baselines`, `decide_guard`, `eval_platform`, `judge_calibration`, `measure_latency`, `skill_path_doc`, `voice_synthesis`, `workflow_library`) |
| `tests/integration/**` (N-0 to N-4, 25 step files) | modified | A-02, A-55, A-72 to A-81 |
| `tests/smoke/*` | added `smoke_fresh_install.py`, `smoke_stack.py` | A-46, A-47 |
| `stages.yaml`, `deferred.md`, `plausibility.yaml`, `decomposition.yaml` | modified/added | A-59, A-64, A-83 to A-85 (stages, deferrals); decomposition via node amendments; `plausibility.yaml` and `deferred.md` were added after decomp-baseline by Plan commits |
| `eval/suites/hard_checks/cases.jsonl` | modified | A-40 (retire case `n-planted-figure`) |
| `eval/suites/rt_*` (7 + 7 holdout), `verdicts_injection`, `verdicts_wikidata` (+ holdouts): **36 files** | added in `271176c` "checked in drafts" (2026-10-26, author the owner) | **no amendment number and no review-log entry** (F-06). Most likely the labelling gate of `specs/mia/eval-drafts/redteam_mia.jsonl` (28 drafts, 14 dev / 14 holdout), which the eval-drafts README says is the owner's move into `eval/suites`. Not verified by me; I did not open the holdout files |

Skills and library (`git diff plan-baseline-it1 -- skills library`): 52 files, 51 added, 1 modified. `skills/chat.md` changed from version 1 to 2 (conversation on the runner, `personal: true`): **bump present**. All new library pipeline and node files are new immutable versions; none was edited after its first commit (checked with `git log` per file). New skills carry their own versions (memory_write 7, review_full 2, review_keywords 2, others 1) with pipelines `memory.write@5`, `review.*@1/2`, `verify.number_gate@1..5`. `verify_claim` stays on `verify.single@1` (D-159); `verify.number_gate@5` exists and is unused by default. Status in the manifests: pipelines 34 draft, 4 tested, 2 trusted (all `review.*` are draft); nodes 37 draft, 9 tested, 41 trusted, 2 retired.

## Verification matrix (in-scope FR / NFR / CON)
Result key: **Met** = tests that pass and can fail exist and ran green in this review; **Partly** = automated part met, rest named; **Deferred** = TD record, interim criterion state in "Open deferrals"; **Person** = needs a person or the target; **Not met**. TC-MIA rows: see the next table. "Plausible?" is checked against `plausibility.yaml`: no result is implausibly good (no stage 4 result exists; mutation claims name survivors).

| Requirement | Method | Evidence (this review) | Result |
|---|---|---|---|
| FR-1 Conversation | Test, Demonstration (phone checklist) | chat_backend, chat_service tests, `chat-page`, `chat.test.mjs`, N-1 integration steps 00-03, IF-101 suite (real, in the image) green | Partly: viewports, keyboard/screen reader, touch targets need browser/person (`tests/test_chat_views_browser.py` skipped in the image) |
| FR-2 Embodied character | Test, Demonstration | JS `character*.test.mjs` green; Godot tests (`ui/godot/tools/test_*.gd`) not run (no Godot) | Partly; Person (look, contact sheet) |
| FR-3 Voice | Test, Demonstration | speech_stream/speech_text/voice_effects tests, IF-112 JS suite, `voice-player.test.mjs` green; chat audio through IF-204 is TD-11 | Partly; Person (listening) |
| FR-4 Transparency | Test | run log, status line tests (TC-MIA-021 chain) green | Met |
| FR-5 User-shaped appearance, persona | Test | presets_api, persona prompt tests green; AC-8 check dialogues TD-10 | Partly |
| FR-6 Tasks as skills | Test | chat_tasks, extension_loader, skill_store tests green | Met |
| FR-7 Workflows as data | Test, property | graph_rules, graph_tables, workflow_library, IF-104/203/301 suites green; library folder TD-06 (REQ-GTB-004 partly) | Met, with TD-06 |
| FR-8 Model management | Test, Demonstration | model-turn/commands tests green; IF-103 only against the mock (F-03); real switch and GPU memory freed need a person | Partly; Person |
| FR-9, FR-10 Verify / Lookup | Eval | node tests (number gate, check-first claims) green; eval deferred TD-12 | Deferred |
| FR-11, FR-12 Review / Sources; NFR-4 | Eval | review_* tests green; review entry out; TD-13 | Deferred |
| FR-13 Method transfer | -- | off by default; REQ-WFM-022 out (D-173) | Out of the built scope (D-4 equivalent), not a failure |
| FR-14 Memory | Eval | memory_records/chat_memory tests green; TD-18 | Deferred |
| FR-15 Behaviour rules | Eval | chat_repair/speech_repair tests green; TD-19 | Deferred |
| FR-16 Traceability | Test | run_log, run_events, replay tests (`test_run_explain.py`, `test_run_log_*`) green; recorded-run replay not done (no recorded runs in the worktree) | Met |
| FR-17, FR-18 Measurable quality / learning | Eval | eval_platform tests green; REQ-RUN-004 out; TD-17 | Deferred |
| FR-19 Operable | Test, Smoke (target) | backup, shutdown, shutdown_database, config, runbook tests green; fresh-install and stack smoke not run | Partly; Person/Phase 6 |
| FR-20 Skill development path | Inspection | `test_skill_path_doc.py` green; the path walked by a person is VAL-005 | Deferred (TD-14) |
| FR-21 Accounts, login | Test | accounts, accounts_api, api_sessions, IF-101 throttle tests green; plain-HTTP/port scan on the target | Met; Person for the target part |
| FR-22 Graph app | -- | out (D-177); IF-104 routes and tables stay and pass | Out |
| FR-23, FR-24, FR-32 Mood, exchange, variant | Test, Demonstration | mood, presets, variant tests green (JS and Python); Godot not run | Partly; Person |
| FR-25 Persona from a file | Test | persona tests green; AC-8 TD-10 | Partly |
| FR-26, FR-30, FR-31 Spec/benchmark, context graph, voice lines | Test | workflow_library, context_graph, voice_lines tests green; recorded baselines for trusted workflows out (REQ-EVL-005 partly) | Met |
| FR-27 Feedback and points | Test | chat_answers, mood_score, converse_behaviours green; votes on reactions out (FB-05) | Met |
| FR-28 Tasks and memos | Test | chat_tasks, items_api, files_api green; the exact "50 odd records" scenario not found by name | Met (scenario not verified verbatim) |
| FR-29 Adaptation to negative feedback | Statistical | node tests green; TD-15 (signed off) | Deferred |
| FR-33 Workflow schedule | Statistical | workflow_library + IF-202/203 green; TD-20 | Deferred |
| NFR-1 Accessibility, devices | Test, Demonstration | JS page tests green; phone checklist, keyboard, screen reader | Person |
| NFR-2 Small-model strategies | Eval | TD-17 | Deferred |
| NFR-3 Untrusted input is data | Test, red team | sandbox 67 + pdf 14 + script_checks 32 tests green on the host; tool_calls_untrusted, injection tests green; red-team suites not runnable (F-02) | Partly (D-2) |
| NFR-5 Local-first privacy | Test | check_free OK, `no-outside-requests.test.mjs` green, web log tests green; browser request recording (`page_requests`, `character_requests`) skipped in the image | Met; browser run not seen |
| NFR-6 Secure access | Test | accounts, HTTPS front config tests green; Tailscale untried | Partly; Person |
| NFR-7 Efficient on the hardware | Benchmark | BM-MIA-001/-002 not measured; TD-16; budgets tested by `test_runner_budgets.py` (green) | Deferred |
| NFR-8 Shared state in a database | Test | storage + migrate + postgres backend tests exist; **the app uses `Storage(FileBackend(_db_dir))` (web_app.py:658)**, compose.yaml:22 says nothing reads `MIA_DATABASE_URL`, the mia image has no psycopg | **Not met in the product (D-1, F-01)** |
| NFR-9 Container per node | Smoke (target) | `test_compose_stack` (6, image) green; stack tests and smoke not run | Partly; Person/Phase 6 |
| CON-1 Free and open | Inspection | check_free OK; `test_system_inspection.py` green | Met |
| CON-2 Hardware | Benchmark | with NFR-7 | Deferred |
| CON-3 Technology | Test | `test_python_version`, `test_system_inspection` green | Met |
| CON-4 Secure context | Test | `secureChannel` JS tests green (29d5cdd adds the password dialog) | Met; Person on the tailnet |
| CON-5 Private network only | Test | compose binds loopback, https front (tests green); port scan from outside not done | Partly; Person |
| CON-6 Trusted users only | Test | accounts tests green | Met |
| CON-7 One shared database | Test | same as NFR-8 | **Not met (D-1)** |

### Root checks TC-MIA-001 to -029 (from `tc-mia-status.md`, judged here)
| TC-MIA | Kind (status file) | Held by (sample, from the status file) | Result of this review |
|---|---|---|---|
| 001 | B | 14 test files incl. chat-page, chat_backend, N-1 steps | Partly: automated part green; viewports/keyboard/touch need browser and person |
| 002, 003, 009, 011, 019, 022, 024, 025, 028 | C | none (stage 4) | **Deferred** (TD-12 to TD-20), not run |
| 004 | B | accounts_wiring, run_log_node, IF-202/401 | Met |
| 005 | B | check_free, no-outside-requests, page_requests, web log | Met (browser recording skipped here) |
| 006 | B | IF-101/402/404, tool_calls*, memory_write_skill | **Partly**: red-team half missing (F-02) |
| 007 | B | backup, first_account, runbook, shutdown_database; up_fresh/first_account_up/up_backup/smoke not run | Person/Phase 6 |
| 008 | D | persona mechanism only | Deferred (TD-10) |
| 010 | B | 22 files | Met |
| 012 | B | 10 files | Met |
| 013 | B | 12 files | Partly: listening is for a person |
| 014 | B | 17 files | Partly: the target part (HTTP from LAN, port scan) is for a person |
| 015 | B | 18 files | **Not met** for "state is in the PostgreSQL database" (F-01); round trip and backup tests pass |
| 016 | D | out (D-177) | Out |
| 017 | B | 21 files | Partly: contact sheet, second model, second device are a person's |
| 018 | B | 9 files | Met |
| 020 | A | `test_system_inspection.py` + `check_free.py` | Met (3 tests green) |
| 021 | B | 6 files | Met |
| 023 | B | 12 files | Partly: real model switch/GPU by a person; IF-103 mock only |
| 026 | D | FR-13 off | Out |
| 027 | B | 15 files | Met (property test seeds 1 to 1000 not located by name) |
| 029 | B | 9 files | Partly: stack not started by me |

The status file's own warning stands: it is an inventory by the coding agent, not a verification; I read the rows against the evidence above, not every scenario step by step.

## Test requirements (M41)
There is **no `test-requirements.md`** in `specs/mia/` or any node folder and no `TR-…` item anywhere in `specs/`. The table (a) of verify-phase cannot be filled; every check ran under conditions that no document demands (F-07). What exists in place of test requirements, as I found it:

| Condition | Where stated | Met in this review? |
|---|---|---|
| Fake and real pass the same contract suite | `decomposition.yaml` interface entries, `contracts/` | IF-101, 102 (files), 104 (Py), 105, 201, 202, 203, 204, 301, 302, 401, 402: yes. IF-103, 404, 405: real side skipped always. IF-102 on PostgreSQL, IF-111, IF-112 real: not run here |
| Pins digest, temperature, seed | `specs/mia/eval-spec.md` (draft), `tools/eval.py` PINS (MP-light only) | not checked on the host (no Ollama running); not approved |
| Holdout run by the verifier, repeats, power | `eval-spec.md` draft | n/a: no eval run, no baseline file |
| Statistical checks with fixed seeds (TC-MIA-011, -027) | `test-spec.md` | -027 seeds: not located; -011 deferred |

## Goal acceptance
| Item | Result |
|---|---|
| Requirements in scope verified | 412 in scope; node reports: 13 of 14 nodes "Verified with (accepted) deviations/findings" per the merge request, N-5 out; this review did not re-judge each node |
| Frozen requirements unchanged | none exist; `goal_check.py` 0/0 |
| Protected checks identical to baseline | no: changed, and explained by amendments except F-06 |
| Nothing outside the goal's parts touched | not applicable (no subgoals); `git diff --stat master...HEAD`: 87 files, 3169 insertions, 70 deletions |
| Every stop condition logged | not assessed in depth; review-log D-137 to D-179 read, no worked-around stop seen |
| Exit criterion met | field validation, Phase 7 |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | NFR-8 AC-15, CON-7 | app store is the file backend; PostgreSQL not wired; image lacks psycopg | Plan amendment (scope/TD) or Implement (F-01) |
| specified, not done | TC-MIA-006 red-team half | `rt_*` suites have target `pending`, 2 cases each | Plan amendment (TD) (F-02) |
| specified, not done | IF-104 real JS cases | skip text says "N-2 Backend does not serve the routes of IF-104 yet", but N-2.1 serves them (Python IF-104 real suite green, N-2 step_05 OK) | Plan amendment (stale skip, protected file) (F-03) |
| specified, not done | quality step in `stages.yaml` | command passes only root requirements: fails | Plan amendment (F-08) |
| specified, not done | quality.md row Q-ids | exist only in node files, consistent once passed | none |
| done, not specified | chat `react("shocked")` swallows any exception (`except Exception: pass`, chat_service.py) | the vote is kept (D-143); no requirement states that a failing reaction is silent and not logged | Backlog (low) |
| done, not specified | `web_app.py` composition root imports modules of 9 other nodes | architecture has no composition-root part (F-12) | Plan note |
| consistent | rate limit 10/60 s: IF-101 v12, REQ-API-004 AC-14, `chat_rate_per_minute` setting (web_app.py:695) | matches | none |
| consistent | password change only over a secure channel (29d5cdd) vs REQ-CLV-018 | test fails on old code by construction (docstring and Given/When/Then) | none |

Human review: the specification side lives in `review-log.md` (D-137 to D-179 read). I read code only for the sampled commits below.

## Code against the architecture
- **Modules and flows.** A script scanned the root `*.py` modules for imports of other modules and mapped modules to nodes with the `Touches:` lines of the leaf plans. 65 modules mapped, 33 root modules appear in no plan (unmapped, e.g. glue and old modules). With the interfaces of `decomposition.yaml` as the only allowed edges between nodes (ancestor/descendant and same-node allowed): **18 cross-node imports without an interface**: `web_app.py` (N-2.1) to `pipeline_model`, `checks`, `sandbox`, `scholar`, `web_tools`, `events`, `speech_stream`, `speech_text` (N-2.4.x, N-2.5), `config`, `shutdown` (N-4.2); `harness.py` to `behaviour`, `extraction` (N-2.2) and `metrics`; `reproduce.py` and `run_explain.py` to `pipeline`, `evidence`, `web_tools`, `config`; `speak.py` to `config`. Most are the composition root wiring real objects and mapping artefacts of `Touches` (e.g. `harness.py`), so this is a low-confidence finding (F-12); there are import tests for the IF-102 boundary (`test_api_storage_imports`, `test_chat_storage_imports`, `test_workflow_*_storage_imports`) which pass. No import-linter configured.
- **Interfaces sampled** (contract suite on the real side, executed in the image): IF-101, 102 (files), 104 (Py), 105, 201, 202, 203, 204, 301, 302, 401, 402 pass; IF-103/404/405 real skipped; IF-111/112 JS real: 112 real file exists (`tests/helpers/real/if_112_voice_player.mjs`) and passes, 111 real is Godot (not run). Spot reads against code: IF-101 `rate_limited` (contract line 114 vs chat_service.py:206), `chat_start`/events used by the page; no mismatch found in these two. I did not read every IF line by line.

## Task commits read against requirements (10 sampled across nodes)
| Commit | Node / requirement | Reading | Finding |
|---|---|---|---|
| 29d5cdd fix(chat) password over secure channel | N-1.1 REQ-CLV-018 | code, test (Given/When/Then), mock fix match the requirement | none; mixed commit (F7 + F8 + F9) |
| f8b85bc feat(chat) minus vote makes her shocked | N-2.2 REQ-CHV-006/CHA-015 | matches D-143/D-156; failing reaction swallowed silently | low: spec silent on logging |
| 63b1b16 fix(storage) raising subscriber | N-3.1 REQ-SLY-006 | test pair for files and postgres backends; postgres test skipped in the image | postgres evidence not re-run |
| 6ba63229 refactor(chat) categories from storage | N-2.2/N-3.1 D-162 | labelled refactor, adds a new test and changes the source of the categories | F-10 |
| d7d7578 fix(runner) connect timeout 10 s | N-2.4.1 REQ-RUN-003 | timeout in `communicator.model_client`, test added; no mismatch | none |
| 35a3597 feat(config) warn on missing options | N-4.2 REQ-OPR-003 | tests `test_missing_options`, `test_config` pass | none |
| d9d0ebc feat(operation) one file one command | N-4.2 REQ-OPR-001 | `test_up_fresh.py` (not run here, podman); README says db "starts" | NFR-8 deviation (F-01) |
| f451e38 feat(deploy) preflight | N-4.2/Deploy | `tests/test_preflight.py` green; commit has no `Requirements:`, mixes feature and docs | F-11 |
| aeea69f / 2ae1fc5 storage `categories()` | N-3.1 IF-102 v2 (A-59) | IF-102 suite green | none |
| 88f484d feat(character) shocked preset and voice line | N-1.2 REQ-CHV-006 | preset in `expressions.json`/library; JS tests green; Godot not run | look is for a person |
Commit format over the goal (`53c6766..HEAD`, 102 feat/fix/refactor commits): 96 carry `Requirements:`, 6 do not (F-11). Test-first order cannot be verified from single commits that contain test and code together; the tests I read carry docstring examples that fail on the old behaviour.

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap / not now |
|---|---|---|---|---|
| Functional suitability | FR-1 etc., AC-1..29, REQ-WFM-019 | 2254 Python tests, 161 + 23 JS tests, 27 integration steps | Met except F-01, F-02 | stage 4 quality of answers deferred (TD-12 to -20) |
| Performance efficiency | NFR-7, NFR-2, CON-2, REQ-WFM-031 | budgets tests only | Gap | measurement deferred (TD-16, TD-17); no timing run, no VRAM measure |
| Compatibility | FR-24, CON-3, contracts | contract suites, python_version test | Partly | IF-103/404/405/111 real sides not run |
| Interaction capability | NFR-1, FR-4, FR-23, REQ-CLV-023 | JS page tests; browser tests skipped in the image | Partly | accessibility, touch, phone: person (TD-01, TD-02 browser tests) |
| Reliability | NFR-4, FR-19, REQ-WFM-033 | shutdown/backup/runner tests | Partly | availability `not now` (Q-3); recovery on the target not tried |
| Security | NFR-3, 5, 6, FR-21, CON-4, 5, REQ-WFM-037 | sandbox (bwrap) tests on the host, tool-door tests, check_free, accounts tests, secrets scan | Partly | red-team suites unrunnable (F-02); sandbox off in the deployed config (F-15); image holds `deploy/.env` (D-139) |
| Maintainability | NFR-8, FR-20, REQ-WFM-039 | decomposition check 0 errors, import tests | Partly | NFR-8 not met (F-01); test docs findings (F-13); no static tools |
| Flexibility | FR-8, FR-32, REQ-WFM-035 | model/variant tests | Met | paid-model path untested |
| Safety | `not now` (Q-2) | n/a | n/a | owner decision |
`quality_check.py` with all requirement files and this report: 0 errors, all nine characteristics covered.

## Open deferrals (M26)
Interim criterion = "the node tests of the row pass" for TD-12 to TD-20; I ran those files (all green) except where noted. Target check state: "specified only" for all but TD-06 and TD-11 (skip with reason).

| TD | Requirement | Interim criterion verified? | Target check | Trigger |
|---|---|---|---|---|
| TD-01 | REQ-CLV-023 | yes: `taskcard.test.mjs` green (161 JS) | specified only | mock sends `task_status`, FB-01 Plan, or 2026-12-31 |
| TD-02 | REQ-CLV-024 | yes: `test_files_api.py`, IF-101 TC-30 green | specified only | as TD-01 |
| TD-03 | REQ-WFM-032 | yes (page text "Tokens (estimated)" not looked at) | specified only | first review at cap, 2026-12-31 |
| TD-04 | REQ-WFM-039 | yes (inspection test green) | specified only | fourth skill, 2026-12-31 |
| TD-06 | REQ-GTB-004 | yes | skip: `library/workflows` missing (`test_seed_workflows` 3 skips, TC-GTB-005) as expected | T-10, 2026-12-31 |
| TD-07 | REQ-EVL-003 | yes (calibration on fixtures green) | specified only | first judge, 2026-12-31 |
| TD-08 | REQ-EVL-011 | yes | specified only | FB-03 Plan, 2026-12-31 |
| TD-09 | REQ-CHA-005 | yes (`test_oldest_are_dropped_over_the_limit`); sign-off present | specified only | first delete request, 2026-12-31 |
| TD-10 | REQ-CHA-008 | yes (`test_persona_prompt.py`) | specified only | after the field test |
| TD-11 | REQ-VOI-001 | yes (IF-204, TC-VOI-001..003) | skip: IF-101/IF-201 `audio_chunk` cases (2 + 1 skips, as expected) | next Plan, 2026-12-31 |
| TD-12 to TD-20 | FR-9..FR-33 etc. | yes: node test files listed in each record ran green in this review; **the eval, benchmark and statistical checks themselves were not run (D-178)** | specified only | next Plan with approved eval-spec, or 2026-12-31 |
No strict xfail started passing. Trace check warns that TD-12 to TD-20 are not listed in the older node verification reports (expected, they pre-date the records). No TD-05 exists (unused number). The trigger date 2026-12-31 is 60 days away; no trigger has passed.

## Review findings
Severity: blocker / high / medium / low. Destination: Implement, Plan amendment, Backlog, Phase 7 note.

| # | Finding | Evidence | Severity | Destination |
|---|---|---|---|---|
| F-01 | **NFR-8 / CON-7 / TC-MIA-015 not met in the product; release documents say otherwise.** App uses the file backend; PostgreSQL only runs and is backed up; the mia image lacks psycopg (Containerfile installs `requirements.txt` only; `import psycopg` fails in `localhost/mia:latest`). Goal scope has NFR-8 as plain "in"; release-notes.md ("State in PostgreSQL behind one storage layer") and CHANGELOG.md ("PostgreSQL storage with backup and restore") overstate | `web_app.py:658`; `deploy/compose.yaml:22`; `deploy/Containerfile:8-9`; N-4.2 report F3 (accepted D-139 (4) at node level); `podman run localhost/mia:latest python -c "import psycopg"` fails | high | Plan amendment (scope row "partly" + TD record, or wire it) and correct the release notes; if kept as is, owner accepts D-1 |
| F-02 | **TC-MIA-006 / NFR-3: red-team half not held, no deferral record.** All 7 `rt_*` dev suites have 2 cases and target `pending`; `test_harness.py` fails on them; the root check demands 0 failures over all red-team cases; `tc-mia-status.md` lists the row as B without saying this | `wc -l eval/suites/rt_*/cases.jsonl`; `suite.json` `"kind": "pending"`; `specs/mia/test-spec.md:16`; test_harness failure above | high | Plan amendment (TD record with interim criterion) or Implement (targets) |
| F-03 | **Contract suites without a real side**: IF-103 (6 skips, REQ-RUN-011 out), IF-404 (5), IF-405 (4) always skip ("only used in stage 2"); IF-104 JS real cases skip with a stale reason although N-2.1 serves the routes; IF-111 real is Godot (not run) | skip lists above; `tests/acceptance/contract/test_if_104_graph_api.test.mjs` reason text | medium | Plan amendment (suites are protected; deferral records or stage-2 providers) |
| F-04 | IF-102 suite on a real PostgreSQL (`contract-postgres`, stage 3) and `test_storage_postgres` not run in this review: no psycopg in image or host | `tools/contract_postgres.sh` precheck; 2 skips | medium | Phase 6 / re-run where psycopg exists |
| F-05 | **Draft release documents contain wrong or stale claims.** merge-request.md: "40 commits ahead of master" (actual `git rev-list --count master..HEAD` = 47); "74 files" (actual 87, `git diff --stat master...HEAD`); "A-84 drafted" and "A-01 to A-84" (A-84 and A-85 are installed per the log); "47 error lines ... 19 test-specs" (46 and 20); open placeholders `<<...>>` (date, CI link, red-team and budget lines, redo trial merge); release-notes.md: PostgreSQL claim (F-01), "SMOKE-MIA-nnn per the verification report" (3 exist: 001, 003 and manual 002), `<<list Provisional ...>>` although none exist (validation-plan says none; I found none either); `deploy/build.sh` missing is stated correctly; "master is 3 commits ahead" is correct; known-failing list is correct | commands in the claims column | medium | Commit phase: correct before the merge |
| F-06 | 36 files in `eval/suites` (rt_*, verdicts_injection, verdicts_wikidata, with holdouts) were added by `271176c` "checked in drafts" with no A-nn and no review-log entry | `git log -- eval/suites/rt_edit` | medium | Phase 7 note / record the labelling gate in the review-log; owner confirms the labels are his |
| F-07 | **No `test-requirements.md`; no TR anywhere** (M41, P24). CLAUDE.md and the protected list name it | `trace_check` WARN; `find specs -name 'test-requirements*'` empty | high | Plan amendment (or accept D-9) |
| F-08 | stages.yaml step `quality` fails (7 Q4 errors) because it passes only the root requirements; with the node files: 0 errors | commands above | low | Plan amendment (stages.yaml protected) |
| F-09 | `agent_check`: 2 errors on `SkillDigestStep` (FB-01 item, outside G-V1: secondBudget 0.0, TrustBoundary without a threat); 640 warnings, mostly case `req:` tags naming `REQ-VER-*` that belong to `specs/number-gate`; all 15 @ModelStep entries carry `criterion = "none: set in Plan"`, tokenBudget is the context window, not a per-step budget; secondBudgets are "guesses" per the model comment; no `formal.yaml` exists so budgets were not checked with Z3 | `architecture.sysml:716-736` | low | Plan amendment / Phase 7 |
| F-10 | refactor commit `6ba63229` changes a check file (`tests/test_chat_answers.py`, +42 lines, new test) and moves the source of the vote categories; no `Before:` line | `refactor_check.py` R1/R4 | low | Backlog (owner decided D-162) |
| F-11 | 6 of 102 feat/fix/refactor commits lack `Requirements:` (`f451e38`, `1cff889`, `27972e9`, `4441df7`, `1a4fcbf`, `181d74f`); `f451e38` mixes code and drafts | git log scan | low | Backlog |
| F-12 | 18 cross-node imports without an interface in the model, mostly `web_app.py` as composition root; 33 root modules named in no plan; the model has no composition-root part; no import-linter | scan above | low | Plan note |
| F-13 | Test documentation: 2649 findings in 159 files (1462 without docstring, 253 without Example, 910 without Given/When/Then, 23 T4) | `test_doc_check.py` | low | Backlog |
| F-14 | 19 requirements added by amendments have no plausibility record (REQ-API-017, REQ-BE-077, REQ-CLV-022/023/024, REQ-FE-031, REQ-WFM-027 to -039); 40 rated questionable (accepted risks) | `req_plausibility.py` | low | Plan amendment |
| F-15 | `sandbox_backend` is `none` in the stack config: the script check is off in the deployed system; THR-005/TB-code mitigation inactive there (documented in deploy-plan) | `deploy/setup_cfg.compose.json:72`, preflight WARN | medium | Phase 6 record, owner accepts (D-8) |
| F-16 | Evidence gaps from the environment: no Godot (character tests, `test_bridge.gd`), Ollama not running (pins, VRAM, budgets not measured), no podman stack, the image was built 2026-10-31 22:53 (before later commits; the tests mount the checkout, so unaffected, but the image to ship needs a rebuild from the tag), no CI | tool checks above | medium | Phase 6 / owner |
| F-17 | `release_check.py`: no CITATION.cff, SBOM, AI-use statement, SPDX headers, README format statement | script output | low | Backlog (only needed if outputs are shared beyond the team) |
| F-18 | Goal record is stale: Phases table says Plan "A-01 to A-35", Implement "in progress ... N-1.3 waits for the owner's checks by ear; N-2.1 Verify: not verified yet"; the row for REQ-RUN-007 starts with a stray space; `eval-spec.md` still Draft and unapproved, `tools/eval.py` PINS holds MP-light only | `goal.md` | low | Commit phase (docs) |
| F-19 | Node report heads keep their first-round verdicts ("Not verified") with re-verification sections appended; the final verdict of each node is only in the last section and the merge-request table, which is hard to audit | e.g. N-1.1 report line 9 vs 166 | low | Backlog |

No blocker is raised on its own: F-01, F-02 and F-07 are the three items that decide between "Verified with accepted deviations" and "Not verified".

## Accepted deviations
Not accepted by anyone yet: the owner decides D-1 to D-9 above. Already decided by the owner (recorded): D-3 (D-178/D-179), D-4 (D-177), the partly/out scope rows of goal.md, TD-01 to TD-04, TD-06 to TD-11.

## Agent verification (agent-app-verify)

### Protected eval material and versions
| Check | Result |
|---|---|
| eval/suites, eval/baselines unchanged since plan-baseline (or approved amendments A-nn) | `hard_checks` changed by A-40; 36 files added without A-nn (F-06); `eval/baselines`: 9 `.md` files, no `.jsonl`, unchanged |
| threat-model.md, eval-spec.md unchanged (or amendments) | `threat-model.md` last changed 2026-10-28 (A-19 era); `eval-spec.md` is the 2026-10-31 draft (726dae1), not approved (D-179); both were new after it1 |
| Every changed prompt or pipeline has a new version | yes: `chat` 1 to 2; all other changes are new immutable versions (no file edited twice) |
| Pins on the host equal eval-spec.md | **not checked**: no Ollama on the host during this review (`curl :11434` refused); eval-spec digests MP-light `sha256:38044be4...`, equal to `tools/eval.py` PINS; MP-full only in the drafts |
| Sandbox backends available, features that depend on them on | host: bwrap and podman present, sandbox tests pass; image: none; deployed config: `none` (F-15) |

### Checks against their test requirements (M41)
No TR exists (F-07). Suites that exist but did not run: all eval suites (D-178). The fake model server is the mock of IF-103; its real side never ran (F-03).

### Eval criteria (decided on holdout)
**Agent check C (suites on the pinned model) was not done.** Reasons: the nine stage 4 checks are deferred by the owner (D-178, D-179: the drafts of the eval specs are not approved, there are no holdouts for the lookup, review and behaviour suites, no recorded baselines), and the hardware rule forbids heavy GPU jobs and the 26B model. No criterion is decided; "PASS/FAIL/NOT DECIDED" is empty for all, and no claim of better answers can be made from this review. Only the deterministic fake-model tests ran (the full Python suite above). I ran no `*.holdout` suite and did not set labels.

### Red-team cases
| RT | Threat | Dev | Holdout | Result |
|---|---|---|---|---|
| RT-001 to RT-006 | THR-001 to THR-003 (injection in web text, claims, oversize) | `verdicts_injection` 12 cases; not run | not run | not decided |
| RT-007 to RT-013 | THR-004 to THR-010 | 2 cases per suite, target `pending`, not runnable | not run | not decided (F-02) |
Deterministic mitigation tests passed: tool door (`tool_calls_untrusted`, `tool_calls_web_log`), sandbox, injection signal checks, PDF wall (`test_pdf_text` with bwrap).

### Threat conformance
| Model step | Tools in code = @ModelStep? | Boundary as declared? | Sandbox / limits | Result |
|---|---|---|---|---|
| all 15 @ModelStep entries (Chat, Plan, Extraction, Verdict, Synthesis, ScriptWriter, Expression, Dream, MemoryWrite, Review x5, SkillDigest) | all declare `tools = ""`; all 31 model nodes in `library/nodes` have only `plain, retries, schema, system, template` (no tools); the 3 tool nodes (`tool.fetch_page`, `tool.web_search` v1/v2) and 1 script node are separate nodes with `reads_web` / `runs_code` flags | UserMessage, FetchedPageText, PaperText, ChatHistory, GeneratedScript, WorkflowEdit declared in threat-model TB-user..TB-edit; one sampled view node (`view.review_abstract`) tells the model that the text is data | scripts only in the sandbox (script node `runs_code: true`, backend none in deployed config); web only through `tool.*` nodes | Met by reading and tests, with SkillDigestStep (A10) and F-15 |
I read the pipeline files and node bodies by script (counts above), not every prompt.

### Budgets
| Budget | Requirement | Measured (median, max) | Limit | Result |
|---|---|---|---|---|
| tokens per step | REQ-RUN-005 | not measured (no model) | num_ctx 8192 | not decided; refusal by estimate tested (`test_runner_budgets.py` green) |
| seconds per run | NFR-7 | not measured | 10 s first text | deferred TD-16 |
| VRAM (ollama ps) | CON-2 | not measured (no Ollama) | 16 GB, one 12B model | not decided |
No `formal.yaml`: the Z3 budget check was not re-run.

### Replay
| Run | Reproduced? | Divergence explained by |
|---|---|---|
| none | not done: no recorded runs in the clean worktree (`data/` is ignored) | the deterministic replay tests (`test_run_explain.py`, `test_run_log_node.py`, IF-401 suite) pass |

### Transcript review
**For a person (the owner, who did not implement):** F transcript review was not done and cannot be done by me. There are no eval runs to read; for validation the plan is `specs/mia/goals/G-V1/validation-plan.md` (20 sampled lookups by the owner).

### Prompts against the specification (agent reviewer, both directions)
| Step / prompt (version) | Specified but missing | Present but not specified | Destination |
|---|---|---|---|
| `chat` v2 + pipeline `chat` | none found (`personal: true` is new in v2; the 3-line diff matches D-173 (F4) / REQ-CHA-009 context, not re-checked line by line) | none found | none |
| `review_abstract` v1 / `view.review_abstract` | prompt text sampled only; relevance 0-3, eligibility include/maybe/exclude with reason codes, "only quote words in the text" | none found | review entry out of G-V1; quality TD-13 |
| other 13 skills, 34 draft pipelines | not read | not read | not assessed: limited by effort; marked in "did not do" |

### Acceptance check (unsupervised goal only)
Not applicable: G-V1 is supervised.

### Proposed cases from Implement
| Draft | Labelled by | Decision | Amendment |
|---|---|---|---|
| `specs/mia/eval-drafts/review_proposed_cases.jsonl` (48 lines), `memory_sample.jsonl`, `hard_checks_planted.jsonl`, `redteam_mia.jsonl` (28, some moved to suites by `271176c`) | label state not verified by me | not for this report: they enter suites through an amendment | none recorded for the moved red-team cases (F-06) |
I did not open them beyond the folder listing and README.

## Notes for Phase 7 (validation)
Use `specs/mia/goals/G-V1/validation-plan.md`; its claims that I checked are correct (`ui/CHECKLIST_CHAT_PHONE.md`, `tools/tag_smoke_cases.py`, `run_explain.py list/show/explain/cost/problems/reproduce`, `deploy/up.sh restore` saves the current state first). Things only people can judge, or only the target shows:
- The character: look of the presets and the shocked reaction, the contact sheet, the second `.vrm` model, expressions on a second device (Godot not run here).
- The voice: the anime effect, voice lines per mood, mute and stop (listening).
- Phone use inside the tailnet, HTTPS, keyboard and screen reader, touch targets (VAL-004, TC-MIA-001/014).
- The fresh-install walkthrough and the stack (`up.sh db`), kill-and-restart recovery, `tests/smoke/*`, the model digests against the pins (`ollama show`), VRAM with `ollama ps`, first-text time (BM-MIA-001/-002, deferred).
- The PostgreSQL decision (F-01): either wire it or tell users the state is in files.
- Release documents: correct the points of F-05 before the merge; rebuild the image from the tag.
- Provisional values: none found by `grep -rn Provisional`.
- Consent, retention and deletion date for the users' run logs (open in the validation plan).

## What I did not do, and why
- No eval, benchmark, holdout or red-team run; agent check C not done (D-178/D-179, hardware rule). No pins check (no Ollama running), no VRAM or timing measurement.
- No compose stack, no 26B model, no `test_container_alone*`, `test_up_fresh`, `test_first_account_up`, `test_up_backup`, `test_database_stack`, `test_delivery_on_stack`, no `tests/smoke/*`, no `container_alone.sh`, no `contract_postgres.sh` (also no psycopg). The browser image tests skipped in the image.
- No Godot tests (Godot not installed).
- No ruff, bandit, vulture, pip-audit, semgrep, import-linter, jscpd (not installed; I did not install anything). No mutation testing. No flake measurement (one run per file). No usability test with bad inputs. No docs-examples run.
- Tests ran from the clean worktree, not from a `git archive` copy.
- I did not read all code: 10 task commits and two interface lines in full, the pipeline files by script, one prompt by hand; the 15 skills and 34 draft pipelines were not read prompt by prompt. I did not re-judge each node report; the node and merge-request verdicts are taken as claims, checked for dates and counts only where listed.
- No transcript review (F), no holdout reading, no labels set, no suites or baselines edited, no amendment installed, nothing merged, tagged or approved.
