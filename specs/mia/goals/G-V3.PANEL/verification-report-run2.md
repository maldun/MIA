# Verification report: G-V3.PANEL (the Skill run view), second run

**Goal:** G-V3.PANEL (subgoal of G-V3), supervised
**Branch:** goal/v3 @ `dc41b43` (clean checkout by `git archive`; tag baseline `plan-baseline-it2-panel`)   **Date:** 2026-11-14   **Reviewer:** Claude Sonnet 5.5 (AI, fresh context, no memory of earlier sessions); the human reviewer has not yet read the marked items.
First run: `verification-report.md` (Not verified, F-01 to F-12). Finding ids continue at F-13.

## Verdict
**Not verified.** (Verified with accepted deviations once F-13 is fixed or accepted by a person.)

Exact remaining reasons:
1. F-13: a chat link `#run=<id>` of a run that is not found (deleted, or another account's) leaves the strip empty after the load although the backend names a shown run (REQ-CLV-038). Browser probe below. Low, but a defect of the text of REQ-CLV-038 and the same symptom as F-03, so it is not settled by the fix of F-03.
2. F-14 to F-17 are low and need a decision (fix, backlog or accept) by a person; none is accepted yet.
3. F-10 is backlogged by the owner as TD-81 (D-331, signed off 2026-11-13): an accepted deviation. Its two `trace_check` errors (REQ-CLV-034 lacks `Relaxed: TD-81` and `Target`) are known and left by the owner.

All eleven other findings of the first run are fixed (table below). No regression of the fix round was found in the deadlock, `RLock`, `read_manifest` and `runOfHash` places named in the brief; the weak places are F-14 and F-13.

## Automated checks (clean checkout of HEAD, venv `mia312`, Python 3.12)
| Check | Result |
|---|---|
| Full unit suite (`unittest discover -s tests`, 501 s, run alone) | 2075 tests, 1 error (`test_tailscale`, known), 5 skipped, 1 expected failure |
| Contract suites | `test_if_101_chat_api` 78 OK (2 documented skips); `test_if_302_record_tables` 16 OK; `test_if_102_storage` 24 OK; `tools/contract_postgres.sh` 12 OK (throwaway postgres:16); `tests/test_storage_postgres.py` 26 OK |
| Goal tests | `test_skill_runs` 8, `test_skill_run_observer` 1, `test_skill_run_gaps` 7, `test_skill_runs_race` 1, `test_emit_status_storage_error` 1, `test_extension_loader` 9: all OK |
| Browser (podman, `localhost/mia` + `localhost/mia-browser`) | `test_skill_run_view_browser` 12 OK, three runs, no flip; `test_skill_run_view_restart` 1 OK |
| JavaScript | `node --test "tests/js/*.test.mjs"`: 164 pass, 0 fail |
| `check_sysml_model.py` | OK, no problems (F-07 fixed) |
| `tools/check_sysml.sh` | 4 files, 0 errors, 0 warnings |
| `req_graph.py` | 26 errors, REQ-FE-032 gone (as expected) |
| `trace_check.py` | 547 errors vs 545 at the tag; the sorted lists differ only by the two TD-81 lines on REQ-CLV-034 (known, owner's choice); no other new error; no error for a PANEL id |
| `goal_check.py --parent-ref plan-baseline-it2-panel` (run in the worktree) | GL1 (D-271) and GL11 (G-V3.CHAT) only; no GL5: frozen requirements unchanged |
| `req_lint.py`, `req_plausibility.py` | plausibility 40 errors as at the tag; lint findings of PANEL items are L1-SUBJECT warnings as in the first run |
| `req_review.py status` | changed since review: TC-WFM-047, TR-MODEL-003 (G-V2.MODEL, not PANEL); rows for REQ-WFM-135, TC-WFM-135, TC-CLV-030 exist in `review-log.md` |
| `test_doc_check.py` | 2658 errors vs 2659 at the tag: no new error (`TestReviewPhases` is clean; the TC-IF-101-39 T3 error is gone) |
| `agent_check.py` | only EV-skill_turns / THR-012 items (CHAT's) |

### Protected material against the baseline
`git diff plan-baseline-it2-panel HEAD` was reproduced in a scratch copy: baseline plus `git apply` of `contract-change-3`, `-5`, `-6`, `-7` (in that order) gives, byte for byte, the files `tests/helpers/contract.py`, `tests/helpers/mocks/if_101_chat_api.py`, `tests/acceptance/**`, `contracts/*`, `specs/mia/plausibility.yaml`. Differences that are not in a payload:
- `specs/mia/deferred.md`: TD-81 added, signed off (D-331).
- `tests/browser/skill_run_view.py`: four lines, `#srv-full` to `#srv-full-body` (A-146, approved; the file is not in a protected folder of CLAUDE.md, but the first brief called it protected: stated in A-146's "Done").
- `tests/browser/skill_run_restart.py`, `tests/smoke/`, `tests/integration/`, `benchmarks/`, `eval/`, `test-requirements.md`, `decomposition.yaml`: unchanged.
Nothing else changed. Brief said "the owner's two installs": the real installs are four payloads (3, 5, 6, 7); payloads 6 and 7 are the renumbering and the Given/When/Then comments.

## Closing of the first run's findings
| Id | Probe (rerun) | Result |
|---|---|---|
| F-01 | real `Storage` on the file backend, 60 answers from one thread + 60 reports from another: 60 answers, last figures kept; plus answers, files, phases, reports from four threads: 40 and 40; 20 rounds of answer/end/history delete in three threads: no deadlock (dump timer 60 s not hit); `subscribe` on `skill_runs` that reads `record` inside the callback: no re-entry problem | fixed. Two recorders on one storage still lose half the answers (60 of 120): the lock is per recorder. `ChatService` builds exactly one (`web_app.py:685` is the only construction), so not reachable today; see F-16 |
| F-02 | `record` raising `OSError`: plain status goes out (`test_emit_status_storage_error`); mutants S01, S02 killed | fixed, but see F-14 |
| F-03 | browser, reload with `#run=%E0%A4%A`: header shows the shown run (`review`, 10:00), the empty text is hidden; click on such a link calls `open(null)`, no throw, a failure notice | fixed for the broken escape; the same symptom for an unknown id is F-13 |
| F-04 | A-145: TC-IF-101-40 passes on mock and real; mutant "mock `skill_run` without account check" killed, "mock `shown_run` without account filter" killed, M10 (`record` ignores the account) and M10b (`shown` ignores it) killed | fixed |
| F-05 | A-146: with the CSS limit `34 * 1.6 dvh` the browser tests of TC-CLV-036 and TC-CLV-045 fail (4 failures, light and dark) | fixed (the test-spec wording of TC-CLV-036 was not changed, F-17) |
| F-06 | M02, M04, M11, M12, M20, M21, M22 all killed by `test_skill_run_gaps.py` | fixed |
| F-07 | `check_sysml_model.py` clean; `skillRunStore` is `built` with `skill_runs.py` and `skill_run_observer.py`; the chat views part lists the three `skill-run*.js` files | fixed |
| F-08 | one history record deleted: only the run with that id goes, same account's other run and other accounts' runs stay (TC-WFM-135, TC-IF-101-39); mutants M08, M09b (delete by author again), killed; probe: another account's history delete with the id of anna's run removes anna's run (accepted by A-144, see F-15) | fixed |
| F-09 | manifest `phases`: `"searching"`, `5`, `None`, `{"a":1}`, `["a",""]`, `["a",1]` refused; `[]`, `["a","b"]` and missing accepted; the three shipped manifests (lookup, search, review) still load | fixed |
| F-10 | not fixed by decision | accepted deviation, TD-81 |
| F-11 | `req_graph` 26 errors, no REQ-FE-032 | fixed |
| F-12 | `test_doc_check`: no error for `TestReviewPhases` | fixed |

## New code, the places named in the brief
| Place | Judgement |
|---|---|
| lock in `skill_runs.py`: `_emit` and `TaskMonitor` called inside it | the callbacks are `ChatService._emit_status` (reads the record without the lock, same thread, `RLock`) and the chat emit; no storage lock is held while subscribers run (`Storage._tell` dispatches after the write lock; the Postgres listener calls the callback outside the connection lock): no lock inversion found, 20 rounds with three threads finished. A slow `emit` (socket) would hold the recorder lock; harmless today |
| `report` outside the lock around `monitor.update` | a `report` after `end` raises `KeyError` (logged by the observer), unchanged and harmless |
| `_emit_status` `except Exception` | hides every error, including a programming error, without a log line, and sends a status without `skill`, `started`, `phases`, `state`: F-14 |
| `runOfHash` returning `null` | for a broken escape the view shows the backend's shown run, which is what REQ-CLV-038 wants; for the click on such a link the page asks for run `null` and shows a failure notice (acceptable). The unknown-id case is F-13 |
| `read_manifest` | refuses only wrong types; nothing that loaded before (shipped three) is refused |
| `_history_changed` by id | any delete of a history record with the id of a run, whatever its author, removes that run (accepted by A-144). Nothing in the product writes or deletes the table `history` (no hit outside `record_tables.py`, `skill_runs.py`; `items_api` kinds are tasks, memos, memory): the subscription is dead code in production and the id mapping (history id = run id) is tested only by the acceptance tests: F-15 |

## Mutants (scratch copy `git archive` of HEAD)
Killed: recorder M01, M02, M03, M04, M05, M07, M08, M09b, M10, M10b, M06 with both sites dropped; lock removed, lock removed only in `answer`, only in `_keep_figures` (L01 to L03, `test_skill_runs_race`); observer M11, M12; service S01, S02 (`_emit_status` except removed or narrowed to `KeyError`), M13, M16, M17, M20, M21, M23; route M22; manifest E01, E02; JS J01, J02 (`runOfHash` without try, raw id on error), M24 to M27; mock `skill_run` without the account check, mock `shown_run` without the filter; CSS `.srv-full-body` limit x1.6 (browser).
Survivors:
| Mutant | Reason | Proposed test |
|---|---|---|
| M06 (elements dropped only in `end`) and M06b (only in `_keep_figures`) | equivalent: both sites store `elements`; dropping both is killed | none |
| M09c (history delete of an id that is no run is not skipped) | equivalent in effect: `storage.delete` raises `not_found`, the storage logs and swallows it; only the log line and the early return differ | assert that no `skill_run_changed` is sent and no exception is logged for a history id that is no run |
| mock `delete_history` without its account check (`tests/helpers/mocks`) | test adapter code that no test pins | one mock self-test: `delete_history("ben", run_of_anna)` changes nothing (F-17) |
Not re-run (killed in the first run, code unchanged since): M28, M28b (innerHTML), M29 to M32, shares and review stage mutants; the browser file passed three times.

## Amendments A-144 to A-148
| Amendment | Note vs what was done |
|---|---|
| A-144 | text of REQ-WFM-135 in `requirements.md`, the SysML doc, `test-spec.md` (TC-WFM-135) and `run-recorder-interface.md` agree (a history record deleted removes the run with its id and no other, event names the id, files stay); `git diff ad454f6 HEAD` shows no other requirement text changed |
| A-145 | as noted; TC-IF-101-40 in payload 5 |
| A-146 | first text said payload and a test-spec change; done: three measurements in the non-protected browser file; the test-spec text of TC-CLV-036 ("its height at most 306 px") was left, which is consistent with the new measurement, but the note announced a rewording (F-17) |
| A-147 | `architecture.sysml`: chat part lists the three new JS files, `skillRunStore` built with its modules; the note says no new part was added and that the manifest check is not listed |
| A-148 | corrected mechanism: REQ-FE-032 added to Verifies of TC-CLV-030 in the N-1.1 `test-spec.md`; `req_graph` count 26 confirms |
Still needs the owner: review-log rows exist for REQ-WFM-135, TC-WFM-135 and TC-CLV-030 and `req_review.py status` lists none of them (nothing open); D-331 covers A-144 to A-148 (one D-number for all five, recorded 2026-11-13; no further D-number needed unless the owner wants one per amendment); TD-81 is signed off, trigger "Validate of G-V3 or 2026-12-31"; the two `trace_check` errors of TD-81 remain until the requirement change (`Relaxed: TD-81`, `Target`) is approved; `tools/check_d_numbers.py` still lists the old D-304 to D-309 as collisions on the unrenamed line `goal/v3.chat` (known).

## Review findings
| # | Commit | file:line | Requirement | Problem | Severity | Destination | Direction | Proposed failing test |
|---|---|---|---|---|---|---|---|---|
| F-13 | `19d8b43`, `92075cb` | `templates/static/chat/skill-run.js:127-132` (`start`) | REQ-CLV-038 (also -037) | Reload with `#run=gone` (a run that is deleted, or belongs to another account, so `skillRun` answers 404): `open()` fails and `start()` does not fall back to `refresh()`; the strip says "No skill has run yet" although the backend names a shown run. Browser probe (stub server, shown run r7): `#run=r7` shows `review`, `#run=%E0%A4%A` shows `review`, `#run=` shows `review`, `#run=gone` shows an empty header and the empty text | low | Implement fix (if `open` fails at load, call `refresh`) | specified-not-done | browser check: load with `#run=gone` shows the shown run |
| F-14 | `92075cb` | `chat_service.py:316-319` (`_emit_status`) | REQ-WFM-136 | The `except Exception` leaves no log line (the observer logs the same kind of error), covers `payload["id"]` too, and the plain status has no `state`, `skill`, `phases`, `started`: a `failed` or `stopped` end then shows as `done` and the phases disappear in the view until the next `skill_run_changed` refreshes it (it follows after `end`, so it heals unless the storage keeps failing) | low | Implement fix (log the exception; keep the plain status) | done-not-specified | storage raising on the end status: a log record is written |
| F-15 | `90823b9` | `skill_runs.py:114-123`, `chat_service.py` | REQ-WFM-135, A-144 | Nothing in the product writes or deletes the table `history` (the chat log is not in the storage), so the subscription cannot fire in production; the mapping history id = run id is tested only by the acceptance tests. Another account's delete of a record with a run's id removes that run (accepted by A-144) | low | backlog (state it as a fact in A-144's follow-up: the link becomes real when the chat log moves to IF-102) | done-not-specified | none until the chat log writes `history` |
| F-16 | `92075cb` | `skill_runs.py:30` | REQ-WFM-133 | The lock is per recorder and per process: two recorders on one storage (a second instance on one shared database) still lose answers (60 of 120 in the probe). Not reachable today (one `ChatService`, shared-state plan is postponed) | low | backlog (note in the shared-state plan, `deploy/REQUIREMENTS_DB.md`) | done-not-specified | two recorders, one storage, concurrent answers (fails until the write is atomic, e.g. `expected_version` with retry) |
| F-17 | `a02fd5f`, `48b386a` | `tests/helpers/mocks/if_101_chat_api.py` `delete_history`; `test-spec.md` TC-CLV-036 | test quality | The account check of the mock's `delete_history` is not pinned (mutant survives); A-146 announced a reworded TC-CLV-036 ("the height of the opened part") that was not made | low | Plan amendment / backlog | done-not-specified | see survivor table |

## Quality evidence per characteristic (M32)
| Characteristic | Evidence | Result | Gap |
|---|---|---|---|
| Functional suitability | acceptance, contract, browser x3, restart, full suite | green | F-13 |
| Reliability | race test, 20 rounds with three threads, storage-error test | fixed | F-14, F-16, TD-81 |
| Security | other account's run 404 (real and mock, mutants killed); texts via `textContent` unchanged since run 1 | met | F-15 (deletion by id) |
| Maintainability | model check clean, doc check no new error | met | F-17 |

## Facts, not findings
- `trace_check` 547 errors: two more than the tag, both TD-81 (owner's choice). `check_d_numbers.py` lists the old D-304 to D-309 for the line `goal/v3.chat`. The branch has not merged master; `goal/v3.chat` is a separate line; the character look in the changed box is VAL-012.
- The full unit suite and the browser runs were done one after the other, never two suites at once.

## Not run
- Mutants M28 to M32 of the first run (page innerHTML, shares, review stages) were not re-run; the browser file is unchanged for them and passed three times.
- No two-instance run on a shared database.

## Accepted deviations
F-10 (TD-81, owner, D-331, 2026-11-13). Nothing else.
