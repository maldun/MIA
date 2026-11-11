# Verification report: G-V3.PANEL (the Skill run view), first run

**Goal:** G-V3.PANEL (subgoal of G-V3), supervised
**Branch:** goal/v3 @ `7556624` (code state `8531be9`; the head commit only adds `verify-brief.md`)   **Parent line of work:** master (not merged into the branch yet)   **Plan baseline:** tag `plan-baseline-it2-panel` (`756b142`)
**Date:** 2026-11-12   **Reviewers:** Claude Sonnet 5.5 (AI, fresh context, no memory of the implementation); the human reviewer has not yet read the marked items.

## Verdict
**Not verified.**

Exact remaining reasons:
1. F-01 (lost updates in the run record between the answer thread and the skill thread), F-02 (a failing storage read inside `task_status` enrichment propagates into the skill's thread) and F-03 (a chat link with a malformed `%` sequence leaves the strip empty after the load): each is a defect of the code against REQ-WFM-133 / -136 and REQ-CLV-037 / -038 and each has a failing probe (below). They go to Implement.
2. F-04 (no test fixes that another account's run is a 404 on the route; mutant M10 survives) and F-07 (`architecture.sysml` lists the removed `task-card*.js`, so `tools/check_sysml_model.py` reports PROBLEMS, and has no part for the recorder) go to Plan amendments. F-04 is a security property.
3. Everything else is low and can be settled as listed in the findings table.

All automated checks of the goal are green (details below); the verdict is held back by the findings, not by red tests.

## Automated checks (clean checkout of HEAD by `git archive`, venv `mia312`, Python 3.12)
| Check | Result |
|---|---|
| Stage log | no CI run; the checks were run by hand in the order of the brief |
| Full unit suite (`unittest discover -s tests`, clean checkout, 560 s) | 2069 tests, 1 error (`test_tailscale` timeout, known, not PANEL), 4 skipped, 1 expected failure |
| Acceptance, contract, goal tests | `test_if_101_chat_api` 76 OK (2 documented skips: character variant, expression event); `test_if_302_record_tables` 16 OK; `test_if_102_storage` 24 OK; `test_skill_runs` 8 OK; `test_skill_run_observer` 1 OK; `test_skill_runs_table` 1 OK; `tools/contract_postgres.sh` 12 OK on a throwaway postgres:16; `tests/test_storage_postgres.py` 26 OK, not skipped |
| Browser (podman, `localhost/mia` + `localhost/mia-browser`) | `test_skill_run_view_browser` 12 OK, run three times in total, no flip; `test_skill_run_view_restart` 1 OK; `test_task_files_browser` 2 OK; `test_chat_views_browser` 12 OK; `test_speak_again_browser` 2 OK; `test_page_requests` 6 OK |
| Harness of TR-PANEL-001 | `chromium --version` = 156.0.8078.73; `fc-match sans-serif` = DejaVu Sans; light and dark themes run by the driver |
| JavaScript | `node --test "tests/js/*.test.mjs"`: 163 pass, 0 fail |
| Statistical checks, benchmarks, flakiness | not applicable (no random input, no benchmark in the goal); the browser file was run 3 times without a flip |
| Protected material vs. baseline | `git diff plan-baseline-it2-panel HEAD` is empty for `tests/acceptance/`, `tests/smoke/`, `tests/integration/`, `contracts/`, `benchmarks/`, `eval/`, `plausibility.yaml`, `deferred.md`, `test-requirements.md`, `decomposition.yaml`. `tests/helpers/contract.py` changed only by commit `edf0534`; its `+/-` lines are identical to `specs/mia/goals/G-V3/contract-change-3/contract.patch`. `tests/browser/skill_run_view.py` and `skill_run_restart.py` unchanged |
| Traceability (`trace_check.py`) | 545 errors at HEAD and at the tag, the sorted lists are identical; none for a G-V3 or PANEL id. One new warning: `REQ-CLV-023 verified by test, but no marker` (superseded requirement, expected). TC-CLV-023 "no test requirement applies" as expected |
| `goal_check.py --spec-dir specs/mia --parent-ref plan-baseline-it2-panel` | GL1 (G-V2 and G-V3 both open, D-271) and GL11 (G-V3.CHAT) only; no GL5, so the frozen requirements are unchanged |
| `req_graph.py` | 27 errors, identical to the tag. `REQ-FE-032` is among them (G7, no verification): F-11 |
| `req_lint.py` | the same findings as the tag, except `REQ-RTB-001` L1-LENGTH 41 to 51 words (reworded text). Known leftovers REQ-CHA-008/014 and REQ-WFM-030..039 (Group missing, length) are not PANEL text defects. PANEL items only have L1-SUBJECT warnings (subject not named) |
| `req_plausibility.py` | 40 errors, none for a PANEL id. Note: `plausibility.yaml` DOES hold the PANEL ratings (REQ-CLV-030.. are in it, line 4068 ff.); the note of the brief that they were not applied is out of date |
| `req_review.py status` | changed since review: TC-WFM-047, TR-MODEL-003 (G-V2.MODEL, not PANEL). REQ-RTB-001 is not listed because `review-log.md` has the owner's row of 2026-11-08 for its new fingerprint `eca9b984ca9a` |
| `test_doc_check.py` | 2660 errors, 2659 at the tag; the one new: `tests/test_review_chat.py` `test_every_phase_the_review_sends_is_declared_in_its_manifest` has no `Example:` line (F-12) |
| `agent_check.py` | only EV-skill_turns / THR-012 items, which belong to CHAT |
| `check_sysml_model.py` | **PROBLEMS: files not found in repo: task-card-model.js, task-card.js** (F-07). Passes at the tag |
| `tools/check_sysml.sh` | 4 files, 0 errors, 0 warnings |

## Verification matrix
| Requirement | Method | Evidence | Result | Result plausible? |
|---|---|---|---|---|
| REQ-FE-032 | refined by CLV-030..047 | no check of its own (G7 error, same at the tag) | no direct check (F-11) | rated in plausibility.yaml |
| REQ-CLV-024 | browser + Test | `test_task_files_browser` (files), TC-CLV-024; probe of hostile file names: hrefs built with `encodeURIComponent`, no `a href=javascript:` | Met | yes |
| REQ-CLV-030, 031, 032, 035 | browser (light, dark; 360, 1440) | `test_skill_run_view_browser` header, meters, reason | Met | yes |
| REQ-CLV-033 | browser + JS | pause, resume, stop once each; mutants M25, M24 killed | Met | yes |
| REQ-CLV-034, 038 | browser, restart | `test_skill_run_view_restart` (real backend twice on one folder) | Met, except F-03 for a malformed link and F-10 for a run left `running` after a crash | yes |
| REQ-CLV-036 | browser | 12 OK, but the check measures `details#srv-full` (summary only, 18.8 px). My probe measures the floating `.srv-full-body`: 257 px at default (34 % of the 757 px inner height of the headless window) and 189 px at 25 %, both at the CSS maximum, so the limit holds; the check itself cannot fail on the part (F-05) | Met by probe, check weak | yes |
| REQ-CLV-037 | browser | link opens the Full run part and the view lies in the viewport (wide, phone); click and load probe for `#run=r1`, `#run=a%20b` OK; `#run=` falls back to the shown run | Met, except F-03 | yes |
| REQ-CLV-039 | browser | empty view text, no control | Met | yes |
| REQ-CLV-040, 041, 042 | browser (1440 x 900, 1920 x 1080, 360 x 800) | layout, size, phone checks green; no 820 px switch of the chat mode is the owner's ruling (2026-11-11); the look of the character is VAL-012 | Met at the three sizes | yes |
| REQ-CLV-043 | browser + probe | all five hostile strings: probe over reason, result, answers, material, files, elements, phase names, skill name: no `script`, `img`, `link`, `iframe` or `style` node inside the view, no alert, hrefs only `/api/files/<encoded>`; mutants M28, M28b (innerHTML) killed | Met | yes |
| REQ-CLV-044 | browser | elements as dt/dd beside the common figures | Met | yes |
| REQ-CLV-045, 046 | browser + probe | range 12..40 and 20..60 refused outside, revert on change; `"20"` OK, `"20.5"`, `""`, `"11"`, `"41"` refused; `"2e1"` is accepted as 20 (harmless); storage that throws: `persist` check with blocked storage OK; mutants M29, M30, M31 killed | Met | yes |
| REQ-CLV-047 | browser | `scroll` check | Met | yes |
| REQ-WFM-031 | unit | `test_task_monitor`, IF-101 task_status; max twice per second unchanged (`min_interval` 0.5) | Met; but see F-02 for the enrichment | yes |
| REQ-WFM-036 | contract | marker and link in `chat_done`, failure text with link; the summary of at most 1200 characters and its wording belong to CHAT (G-V3.CHAT) | PANEL part met (link, failure message) | yes |
| REQ-WFM-038 | unit | `test_review_chain`: files in the run record, no `Files:` suffix | Met | yes |
| REQ-WFM-039 | unit + inspection | manifest field `phases`; no loader or chat-service change needed for a new skill | Met; F-09 (no type check) | yes |
| REQ-WFM-130, 131, 132 | acceptance | `test_skill_runs` (8) and mutants M01, M03, M06, M07 killed | Met; F-06 survivors M02, M04 | yes |
| REQ-WFM-133 | acceptance | order and time of the answers (M05 killed) | **Not met under concurrency** (F-01) | yes |
| REQ-WFM-134 | acceptance | ties, two accounts (probe: anna r3, bob r2, nobody None) | Met | yes |
| REQ-WFM-135 | acceptance + probe | deleting history deletes the account's records, keeps others (M08, M09 killed); see F-08 for what "deleted" covers | Met as tested, F-08 | yes |
| REQ-WFM-136 | acceptance + inspection | `grep` over `extensions/` and the registered tasks: no skill file or manifest names the view or the recorder | Met; F-06 (phase filter untested) and F-02 | yes |
| REQ-WFM-137 | acceptance + probe | 6000-character result stored unchanged; hostile strings stored as text | Met | yes |
| REQ-WFM-138 | acceptance | elements in `task_status` and the record (M06, M06b killed) | Met | yes |
| REQ-RTB-001 (reworded) | unit | TC-RTB-001: `test_record_tables` names 15 tables and the deletable set of five; `record_tables.py` and the IF-302 contract agree | Met, status can go back to Verified | yes |
| REQ-RTB-007 | contract | TC-IF-302-01, -08, TC-IF-102-12 on mock, file backend and PostgreSQL | Met | yes |
| REQ-API-015 (PANEL side) | contract | TC-IF-101-30, -31, -34..-39 on the real provider with the installed helper patch | Met; F-04 and F-06 for what the tests do not pin | yes |

TC-WFM-136 inspection part: confirmed by `grep -rniE "skill.?run|recorder|observer|skill_run_changed|srv-" extensions/` (no hit).

## Test requirements (M41)
| Test requirement | Kind | Verified by | Met? |
|---|---|---|---|
| TR-PANEL-001 (reference environment) | browser harness | image versions confirmed above; light and dark | Met (trace_check WARN: aspect name `reference environment` is not in its list, same at the tag) |
| TR-PANEL-002..005 | fakes, fixed clock, hostile strings (TR-PANEL-005 five strings) | `test_skill_runs`, browser `hostile` check, my DOM probe | Met |
| TR-PANEL-006 (known-answer), TR-PANEL-007 | contract and restart | contract run, `test_skill_run_view_restart` | Met (same WARN on the aspect name) |
| VAL-012 | person looks at the character in the changed box | not for this phase | open for Validate |

## Goal acceptance
| Item | Result |
|---|---|
| Requirements in scope verified | 45 of 47 listed ids have a passing check; REQ-FE-032 has none of its own (F-11); REQ-WFM-133 passes its test but fails under concurrency (F-01) |
| Frozen requirements unchanged vs. parent | yes (`goal_check --parent-ref`: no GL5) |
| Protected checks identical to baseline | yes, except the owner's helper patch, byte-equal to the patch |
| Nothing outside the goal's parts touched | yes. Changed outside code: `CHANGELOG.md`, `ui/README.md`, `ui/tools/*` (stubs), review log row, handover note |
| Every stop condition logged | yes (T-05 helper patch, T-01 requirement conflict) |
| Exit criterion | checked in Validate (VAL-012) for the character look |

## Changes to tests that existed before (task 4)
| File | Reason | Weakened? |
|---|---|---|
| `tests/test_review_chain.py` | A-140: no `Files:` suffix; now asserts the run link at the end and the files in the run record and in `chat_done` | no (asserts more: the link, the record, the done files) |
| `tests/test_review_chat.py` | `update(... elements=None)` signature; the phase is a declared stage (`searching`) and the detail is an element; new class `TestReviewPhases` | no (owner's decision on the stage names) |
| `tests/test_review_run_mode.py` | signature of the monitor fake only | no |
| `tests/test_record_tables.py` | 15 tables and a deletable set of five (REQ-RTB-001 reworded, owner's ruling) | no |
| `tests/test_task_files_browser.py`, `tests/browser/task_files.py` | the three card tests and the card scenario retired with the card (A-131, REQ-CLV-023 superseded); the files test waits for the Skill run view instead of a card | covered by TC-CLV-033 / -036 in the new browser file; pause/resume/stop-once and late-status-after-done are in TC-CLV-032/033 |
| `tests/js/page-wiring.test.mjs`, `tests/js/taskcard.test.mjs` (deleted) | card section and 7 card tests retired | same |
| `ui/tools/skill_run_stub_server.py`, `real_backend_stub.py` | endpoints re-pointed, route parameter name, allowed origins of the container address (test harness only; the real origin guard of `web_app` is untouched) | do not hide a defect of the page |

## Specification vs. code (task 2 decisions of the implementer)
| Item | Judgement |
|---|---|
| strip fixed at the bottom, `--strip-h` moves the panel | harmless, implied by REQ-CLV-040 / 041 |
| Full run part floats above the strip with its own share | harmless; limit holds (probe above); the protected check cannot see it (F-05) |
| local time hours and minutes | harmless; REQ-CLV-030 names a start time without a format |
| buttons always present, disabled by state | harmless (needed for the 44 px check) |
| shares built in T-08 | in requirements (CLV-045 / 046), order of tasks only |
| `ChatService` builds its own recorder from `votes` | harmless; documented. Without `subscribe` on the storage it falls back to the old texts |
| recorder's own `TaskMonitor`, only `skill_run_changed` forwarded | harmless; no double `task_status` |
| record state never `paused` | in IF-101 v16 (`task_status` says paused) |
| running phase takes `failed`/`stopped` | in IF-101 v16 text; tested (M07 killed) |
| failed text `The /<task> run failed: <reason>` plus link | in IF-101 v16; wording is CHAT's |
| ties by id | gap in REQ-WFM-134, harmless; untested (M02 survives) |
| account `page` without accounts | consistent with `chat_ops_api.account()` |
| observer swallows recorder errors | by design, but the enrichment in `_emit_status` does not (F-02) |
| nothing marks a run left `running` by a crash | F-10 |

## Review findings
| # | Commit | file:line | Requirement | Problem | Severity | Destination | Direction | Proposed failing test |
|---|---|---|---|---|---|---|---|---|
| F-01 | `8890dc2` / `4a895b8` | `skill_runs.py:53` (`answer`), `:117` (`_keep_figures`), `report`, `file`, `end` | REQ-WFM-133, -131 | Every recorder method loads the whole document, changes it and puts it back without a lock; the answer arrives on the HTTP thread while the skill thread reports figures. Probe (`vp/probe2.py`): 60 answers from one thread and 60 `report` calls from another on the file backend leave 0 of 60 answers (60 without the reporting thread). | medium | Implement fix (one lock per recorder around load-modify-save) | specified-not-done | `test_answers_survive_concurrent_reports`: two threads, assert all N answers in order |
| F-02 | `8890dc2` | `chat_service.py:314-320` (`_emit_status`) | REQ-WFM-136 (a record must not take the run away; observer docstring) | `_emit_status` reads the record on every `task_status`; a storage error is raised through `TaskMonitor._send` into the skill's `monitor.update` and into `monitor.finish()` at the end of `_do_chat`. Probe (`vp/probe3.py`): `OSError` propagates. The observer swallows the same error. | medium | Implement fix (catch, log, send the plain status) | specified-not-done | `test_task_status_survives_a_failing_record_read` |
| F-03 | `19d8b43` | `templates/static/chat/skill-run.js:106,129` (`runOfHash`, `start`) | REQ-CLV-038, -037 | `decodeURIComponent` throws on `#run=%E0%A4%A`; `start()` rejects before `refresh()`, so after the load the strip shows "no skill has run yet" although the backend names a shown run. Browser probe (`vp/probe_driver.py`, `probe_hash`): header empty, `srv-empty` visible. A click on such a link throws after `preventDefault`. | low | Implement fix (try/catch, fall back to the shown run) | specified-not-done | browser or JS test: load with `#run=%E0%A4%A` shows the shown run |
| F-04 | `8890dc2` | contract `test_if_101_chat_api.py` (protected), `chat_service.py:skill_run`, `skill_runs.py:84` | REQ-API-015 (IF-101 v16), security | No check makes `GET /api/skill-runs/<id>` of another account a 404. Mutant M10 (`record` ignores the account) survives all tests of the goal. The code is correct today (`chat_ops_api.py` passes `g.account`). | medium | Plan amendment (new protected test: two sessions, 404 for the other) | done-not-specified (test gap) | session B asks for A's run id: 404 `not_found`, A gets 200 |
| F-05 | `ca255bb`..`9bcddec` | `tests/browser/skill_run_view.py:227,230` (protected) | REQ-CLV-036 | The check measures `details#srv-full`, i.e. the summary (18.8 px), not `.srv-full-body` (257 px at 34 %); it cannot fail on the limit. Implementation is within the limit (probe). | low | Plan amendment (measure `#srv-full-body`) | specified-not-done (test) | the same scenario measuring `#srv-full-body` |
| F-06 | | `skill_run_observer.py:21`, `chat_service.py:314`, `chat_ops_api.py:55`, `skill_runs.py:98,95` | REQ-WFM-136, -131, -134, REQ-API-015 | Survivors of the mutants: M11 / M12 (undeclared phase accepted, declared phase ignored: nothing checks the phase filter or the phase progress through the observer), M20 (`paused` state lost in `task_status`), M21 (`reason` sent for `done`), M22 (`204` replaced by `200 null`: the real adapter does not pin the wire code), M04 (reason stored for `done`), M02 (ties reversed; tie rule unspecified). | low | Plan amendment (add checks) / backlog | done-not-specified (test gap) | one check per survivor, see names in the mutant list |
| F-07 | `8531be9` | `specs/mia/architecture.sysml:232`, `:775`, `:910` | architecture, REQ-WFM-130, REQ-FE-032 | The module list of the chat page still names `task-card.js`, `task-card-model.js` (removed) and lacks `skill-run.js`, `skill-run-model.js`, `skill-run-shares.js`; `tools/check_sysml_model.py` reports "files not found in repo". No part carries `skill_runs.py` or `skill_run_observer.py`; the existing part `skillRuns : SkillRunSource` describes the CHAT skill-turn relay, not the recorder. | medium | Plan amendment (model) | done-not-specified | `check_sysml_model.py` gives no PROBLEMS |
| F-08 | `4a895b8` | `skill_runs.py:106` (`_history_changed`) | REQ-WFM-135 | The notice names the author of the delete, not the owner of the history record, and fires for a single record: deleting one history record deletes ALL run records of that author (probe P9: two runs of carl gone after one `history` delete). A delete by another user would remove the wrong account's runs. Today nothing in production deletes history records, so only the acceptance test shows it. | low | Plan amendment (say what "history records of an account deleted" means) | done-not-specified | two history records, delete one: expected runs kept or deleted per the decided rule |
| F-09 | `ca255bb` | `extension_loader.py:47` | REQ-WFM-039 | `phases` from a manifest is not checked: a string becomes a tuple of characters (probe P12), `None`/`5` raise `TypeError` and the skill is skipped with that text. | low | backlog | done-not-specified | manifest with `"phases": "searching"` is a problem, not five letters |
| F-10 | `4a895b8` | `skill_runs.py:98` (`shown`) | REQ-WFM-134, REQ-CLV-038 | A run record left `running` by a crash or restart is never closed; `shown` prefers running runs, so the strip shows it as running after every restart and later ended runs are hidden until a new run starts. | low | Plan amendment (rule for a stale run) | done-not-specified | recorder rebuilt on a store with a `running` record: shown is not that run as running |
| F-11 | plan | `nodes/N-1-web-frontend/requirements.md:381` | REQ-FE-032 | no check lists it (`req_graph` G7 error, already at the tag); the CLV children verify it | low | Plan amendment (Verified by the CLV checks) | specified-not-done | none |
| F-12 | `ca255bb` | `tests/test_review_chat.py` `TestReviewPhases` | test conventions | docstring has no `Example:` line (test_doc_check T2) | low | Implement fix | done-not-specified | n/a |

Mutants run in a scratch copy (killed / survived): recorder M01, M03, M05, M06, M06b, M07, M08, M09 killed; M02, M04, M10 survived. Observer/service M13..M19 (marker on the question and on `chat_done`, link, link without id, `Files:` kept, stopped reason, end mapping) killed; M11, M12, M20, M21 survived. Routes M23 killed, M22 survived. JS model M24..M27 killed. Page M28, M28b (innerHTML) killed. Shares M29, M30, M31 killed. Review stages M32 killed.

## Quality evidence per characteristic (M32)
| Characteristic | Evidence | Result | Gap |
|---|---|---|---|
| Functional suitability | acceptance, contract, browser | green | F-01, F-03 |
| Performance efficiency | status at most twice per second unchanged; `shown` scans all records of the table on each call | fine for the size of the table | `shown` is O(runs) per page load, backlog |
| Compatibility | IF-101 v16/v17, IF-302 v8/v9, IF-102 v4 field by field: routes, 204/404/401, `skill_run_changed`, marker, link form, `elements` | match | wire `204` not pinned (F-06) |
| Interaction capability | 44 px targets at 360 px, disabled states, text as text | met | the character look is VAL-012 |
| Reliability | run end, restart, delete | | F-01, F-02, F-10 |
| Security | CSP unchanged and strict (`script-src 'self'`); no `innerHTML`, `insertAdjacentHTML`, `outerHTML`, `document.write` in `skill-run*.js`; texts via `textContent`; file links `encodeURIComponent`; account from `g.account`; no secrets, subprocess or file deletion added; `app.js` builds with no `task-card` reference | met | F-04 (test), F-08 |
| Maintainability | | | F-07, F-12 |

## Open deferrals (M26)
`deferred.md` TD-01 still names REQ-CLV-023 (superseded); the move to REQ-CLV-038 needs the owner (fact, not a finding).

## Facts, not findings
- `CHANGELOG.md` has an `[Unreleased]` section that will collide with master's at the merge.
- The branch has not merged master (STORE, MODEL, TD-11 are on master).
- The branches `goal/v3.panel` and `goal/v3.chat` named in the plans do not exist; the work was on `goal/v3`.
- `plausibility.yaml` holds the PANEL ratings already (differs from the brief).
- The look of the character in the changed box is not checked here (VAL-012).
- CHAT items (IF-201 v3 skill_turn variants, `test_chat_skill_turns`, `test_digest_score`, `test_run_end_to_end`, EV-skill_turns) are out of scope and were not run as gates.

## Not run or only partly run
- No exhaustive cross product of the five hostile strings over every text field; one probe covered eight fields with the five strings spread over them (reason, result, answers, material, files, elements, phase names, skill name).
- "A run that ends while the history is deleted" was not run as a race; only the sequential delete and the lost-update race (F-01) were.
- The wire code `204` was checked by reading `chat_ops_api.py`, not by a request against a running web application.
- The statistical rule does not apply; the human batch review of the marked code items (F-01, F-02, F-08) is open.

## Accepted deviations
None.

## Notes for Phase 7 (validation)
- VAL-012: look at the character in the changed box (`character=0` in all browser checks), at 600 to 820 px landscape where the old chat switch keeps the panel (owner's ruling).
- Watch a real review: the stage names (`choosing keywords`, `searching`, `screening`, `reading full texts`, `writing the report`) and the `Now` element.
- Probes and scratch copies: `/tmp/claude-1000/-home-maldun-prog-Python-MIA/cad505ab-8fd6-492b-9090-0cb8ca6b10ce/scratchpad/vp/` (`probe1.py`, `probe2.py`, `probe3.py`, `probe_driver.py`, `mutate.py`).
