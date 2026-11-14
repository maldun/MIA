# Verification report: G-V3.PANEL (the Skill run view), third run

**Goal:** G-V3.PANEL (subgoal of G-V3), supervised
**Branch:** goal/v3 @ `f9f8536` (clean checkout by `git archive`; code identical to `404dcc7`; tag baseline `plan-baseline-it2-panel`)   **Date:** 2026-11-14   **Reviewer:** Claude Sonnet 5.5 (AI, fresh context, no memory of earlier sessions); the human reviewer has not yet read the marked items.
Earlier runs: `verification-report.md` (F-01 to F-12), `verification-report-run2.md` (F-13 to F-17). Finding ids continue at F-18. Narrow run, as in `verify-brief-run3.md`.

## Verdict
**Not verified**, formally, for paperwork and two low findings only; no defect of the product remains open.

Exact remaining reasons:
1. F-15, F-16 and F-17 are deferred by the owner's wish as TD-82, TD-83 and TD-84, but are **not accepted by an approval row**: the decision row (next free D-number: D-338, not used anywhere in `specs/` except the hand-over and the brief) and the sign-offs of TD-81 to TD-84 (all four say "Sign-off: pending" except TD-81, which is signed) are missing. 'Verified with accepted deviations' needs that row and those sign-offs. TD-81 itself is signed off (D-331).
2. F-18 and F-19 (new, low) need a decision (fix, backlog or accept) by a person.
3. The eight new `trace_check` errors (TD-81 two, TD-82 to TD-84 six) stay until the owner links the drafts in one amendment (his choice of 2026-11-14).

Closed in this run: F-13 and F-14 (own probes below, not only the new tests). No other regression was found.

## Closing of F-13 and F-14
| Id | Probe (own) | Result |
|---|---|---|
| F-13 | Browser (Chromium of `localhost/mia-browser`, stub server, shown run r7, runs r2 and r7 known), page loaded with `#run=r7`, `#run=r2`, `#run=%E0%A4%A`, `#run=`, `#run=gone`, `#run=other%2Fid`: every load shows the header `review · 10:00 AM`, state `done`, the empty text hidden, no toast. Linked runs (r7, r2) also open the Full run part; the five other links leave it closed. Probe `vp/probe_f13.py` | fixed. (r2 and r7 look the same in the DOM because the stub records share their start; the choice between them is pinned by the JS unit test) |
| F-13, fake DOM | `vp/p13.mjs`: load with a live link shows r2; a reconnect with a link that still opens keeps r2; a reconnect with a link that is gone shows the backend's r7 without a note; both `skillRun` and `shownRun` failing keeps r2; broken, empty, missing and absent hash show r7 with no note; link gone and no shown run (204) leaves the strip empty | all as wanted |
| F-14 | Recorder raising `OSError` on the end status (`vp/p14.py`): the plain status goes out unchanged; one `logger.error` line per event: `The run record for the status of r1 could not be read: disk read failed ...`; the payload's `result` text ("CONFIDENTIAL RESULT") is not in the log; no exception reaches the caller | fixed |

## Review of the diff of `404dcc7` (the places named in the brief)
| Place | Judgement |
|---|---|
| `start()` on every socket `connect` | after a reconnect a link that no longer opens now shows the backend's shown run (before: the view stayed). The no-link reconnect already did the same (`refresh()` replaces `view` by `shownModel`), so the two cases are now alike. REQ-CLV-037 speaks of a click, REQ-CLV-038 of the load: neither says what a reconnect keeps. Acceptable, but note: a transient error of `skillRun` (not a 404) at a reconnect also replaces the linked run by the shown one (low, observation, no finding). A reconnect with a link that does open keeps the linked run (probe) |
| order inside `open` | `view` is assigned only after `await api.skillRun(id)` succeeded; a failed `open` leaves `view` untouched (probe: view stays r2) |
| other callers of `open` | the click handler calls `open(id)` without the option, so it still notifies on failure (probe: one note on a dead link, none on a live one, view kept); `app.js` only calls `initSkillRunView`. But no test pins it: F-19 |
| `refresh()` with both calls failing | the strip keeps what it shows (probe) |
| `_emit_status`, `payload.get("id")` | for a payload that is not a dict the old code sent it on unchanged (the `TypeError` of `payload["id"]` was swallowed); the new `.get` in the handler raises `AttributeError` out of `_emit_status`. `TaskMonitor` always builds a dict, so it cannot happen today: F-18 (low) |
| log flood | the monitor emits at most every 0.5 s while a run works and once at the end; with a storage that keeps failing, that is up to two error lines a second for one run (5 events gave 5 lines + the end). Reported, not failed (as the brief says) |
| log content | the line holds the run id and the exception text; the status payload (result, answers, elements) is never put in it. A storage exception text could in principle name a record, not run content, in the shipped backends |

## Mutants (scratch copy of HEAD; the tests run were `skill-run-start`, `skill-run-model` (JS) and `test_emit_status_storage_error`)
Killed: `start()` without the fallback (M1); `open` returning `undefined` on success (M2); `open` returning `true` on failure (M2b); `logger.error` removed (M4); log without the cause (M6); log level `info` (M7); a second log line (M8).
Survivors:
| Mutant | Reason | Proposed test |
|---|---|---|
| M3 `open` notifies while quiet (`if (!quiet)` dropped) | gap: the JS test checks the shown run, not that no note appears at load | in `skill-run-start.test.mjs`: after `#run=gone` at load, `notes` is empty |
| M3c `start()` calls `open(linked)` without `{ quiet: true }` | same gap | same test |
| M3b `open` never notifies (note removed) | gap: no test of the click handler on a link that cannot be opened (browser `link` scenario only follows a live link) | JS test with the `click` handler of the fake DOM on `#run=gone`: one note, view kept |
| M5 log call moved before the `try` | gap: the test only asserts the count on a failing recorder; nothing says a healthy recorder writes no line | `test_emit_status`: a recorder that works logs nothing (`log.error.call_count == 0`) |
All five are low. They are test gaps of the fix, not product defects. Not re-run: the mutants of the earlier runs (code of those places unchanged since the second run, the browser file passed three times).

## Automated checks (clean checkout of HEAD, venv `mia312`, Python 3.12)
| Check | Result |
|---|---|
| Full unit suite (`unittest discover -s tests`, 454 s, alone) | 2076 tests, 1 error (`test_tailscale`, known), 5 skipped, 1 expected failure. The brief expected 2081; the second run had 2075 and the fix adds one Python test (`test_the_error_is_logged`), so 2076 is right and 2081 was a miscount in the brief (fact, not a finding) |
| JavaScript | `node --test "tests/js/*.test.mjs"`: 166 pass, 0 fail (164 + the 2 of `skill-run-start.test.mjs`) |
| Contract suites | `test_if_101_chat_api` 78 OK (2 skips, as documented); `test_if_302_record_tables` 16 OK; `test_if_102_storage` 24 OK; `tools/contract_postgres.sh` 12 OK (throwaway postgres:16); `tests/test_storage_postgres.py` 26 OK |
| Goal acceptance tests | `test_skill_runs` 8, `test_skill_run_observer` 1, `test_skill_runs_table` 1: OK; `test_skill_runs_race`, `test_skill_run_gaps` 7, `test_emit_status_storage_error` 2: OK |
| Browser (podman) | `test_skill_run_view_browser` 12 OK, three runs, no flip (46 to 48 s each); `test_skill_run_view_restart` 1 OK |
| `check_sysml_model.py` | OK, no problems; `tools/check_sysml.sh`: 4 files, 0 errors, 0 warnings |
| `req_graph.py` | 26 errors, as in the second run |
| `trace_check.py` | **553 errors**, as the brief says: the 547 of the second run plus six for TD-82 to TD-84 (`REQ-WFM-135`, `REQ-WFM-133`, `REQ-CLV-036`: no `Relaxed: TD-nn`, no `Target`); no error for a PANEL id other than these |
| `test_doc_check.py` | 2658 errors, same as the second run: the two new tests add none |
| `goal_check.py --parent-ref plan-baseline-it2-panel` | GL1 (D-271) and GL11 (G-V3.CHAT) only; no GL5 |
| `check_d_numbers.py` | lists the old D-304 to D-309 for `goal/v3.chat` (known, not yet merged) |

### Protected material against the baseline
`git diff 3791b27 HEAD` (second report to now) touches no protected path: only `chat_service.py`, `templates/static/chat/skill-run.js`, `specs/mia/deferred.md` (TD-82 to TD-84), the two new test files, and the brief. `tests/helpers/`, `tests/acceptance/`, `tests/smoke/`, `tests/integration/`, `contracts/`, `benchmarks/`, `eval/`, `test-requirements.md`, `decomposition.yaml`, `plausibility.yaml` are therefore as in the second run (installs of contract-change-3, 5, 6, 7 and the A-146 change of `tests/browser/skill_run_view.py`, byte for byte checked there). The `git diff plan-baseline-it2-panel HEAD` file list is the same set as then plus `deferred.md`. No new test or protected file changed with the drafts.

## The drafts TD-82 to TD-84 (`deferred.md`, commit `e037c7a`)
| Entry | Requirement | Finding | Trigger | Judgement |
|---|---|---|---|---|
| TD-82 | REQ-WFM-135 (A-144) | F-15 | the chat log moves to the storage (IF-102), or the Plan of the shared-state database, whichever first | right requirement, finding and trigger (second report: "the link becomes real when the chat log moves to IF-102"); the interim criterion and the risk are as the report found them (nothing writes `history`) |
| TD-83 | REQ-WFM-133 | F-16 | the Plan of the shared-state database, before a second instance uses one database | matches the report (lock per recorder, 60 of 120 lost answers; backlog note in the shared-state plan). The text says "30 of 30 answers kept" for `test_skill_runs_race`, while the report spoke of 60 answers in its own probe: both are only examples, not a mismatch of requirement |
| TD-84 | REQ-CLV-036 and REQ-WFM-135 | F-17 | next plan amendment or contract change that touches `tests/helpers/` or the IF-101 contract test, or the Validate of G-V3 | matches F-17 (protected helper change or Validate); both halves (mock account check, TC-CLV-036 wording of A-146) are named |
All three are marked DRAFT, Decision "pending", Sign-off "pending (owner)". The diff of `e037c7a` is 45 added lines in `deferred.md` only: no requirement text, test or protected file changed with them. `deferred.md` is on the protected list of the first brief; the change is the owner's own drafting and the same kind of change as TD-81 (fact, not a finding).

## Review findings
| # | Commit | file:line | Requirement | Problem | Severity | Destination | Direction | Proposed failing test |
|---|---|---|---|---|---|---|---|---|
| F-18 | `404dcc7` | `chat_service.py:319` (`_emit_status`) | REQ-WFM-136 | The new log line calls `payload.get("id")` inside the `except`, outside the `try`: a payload that is not a dict now raises `AttributeError` out of `_emit_status` (before the fix the `TypeError` was swallowed and the payload went out). Not reachable today (`TaskMonitor.state()` always returns a dict) | low | Implement fix (read the id once inside the `try`, or `isinstance`) or accept | done-not-specified | `_emit_status(probe, "task_status", None)` sends the payload on and raises nothing |
| F-19 | `404dcc7` | `tests/js/skill-run-start.test.mjs`, `tests/test_emit_status_storage_error.py` | REQ-CLV-037, 038, WFM-136 | The tests of the fix leave four mutants alive (M3, M3b, M3c, M5, see the table): "no note at load for a dead link", "the click on a dead link still notifies", "a healthy recorder logs nothing" are not pinned | low | Implement fix (add the assertions) | specified-not-done | the four tests of the survivor table |

## Quality evidence per characteristic (M32)
| Characteristic | Evidence | Result | Gap |
|---|---|---|---|
| Functional suitability | acceptance, contract, browser x3, restart, own browser probe of six links, JS probe of reconnects | green | F-19 |
| Reliability | `_emit_status` probes (storage error, missing id, non-dict payload), log count | met | F-18 (unreachable), log flood (fact) |
| Security | log line holds no run content; texts via `textContent` unchanged since run 1 | met | |
| Maintainability | model check clean, doc check no new error | met | TD-82 to TD-84 open |

## Facts, not findings
- `trace_check` has 553 errors (545 at the tag): two TD-81, six TD-82 to TD-84, linked later in one amendment by the owner's choice. The sign-offs of TD-82 to TD-84 and their decision row (D-338) are pending.
- The branch has not merged master; `goal/v3.chat` is a separate line and renumbered (D-332 to D-337, A-149); `check_d_numbers.py` lists old numbers for it until it is merged. The look of the character in the changed box is VAL-012.
- The full unit suite and the browser runs were done one after the other, never two suites at once; the suite ran in a `git archive` copy, so `test_checkout_untouched` was not at risk.
- Probe scripts: `vp/p13.mjs`, `vp/p14.py`, `vp/probe_f13.py`, `vp/run_probe.sh` in the reviewer's scratchpad (not in the worktree).

## Not run
- The mutants of the first and second run were not repeated (code unchanged since).
- No two-instance run on a shared database.

## Accepted deviations
F-10 (TD-81, owner, D-331, 2026-11-13). F-15 to F-17 are deferred by the owner's wish but not accepted until D-338 and the sign-offs exist.
