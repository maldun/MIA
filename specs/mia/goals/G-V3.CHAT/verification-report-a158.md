# Verification report A-158 (live status line of a skill run)

Reviewer: independent agent session (did not implement). Scope: commits `7e03715b..HEAD` (HEAD = `97122a8a`). No code, test or spec was changed; only this file was written. Mutations ran in a scratch copy (`.../scratchpad/verify-copy`).

## Verdict: PASS WITH FINDINGS

All in-scope checks are green, the requirements are met by code, and 7 of 9 mutations are caught. Two trust/interface properties (no HTML in the line text, the encoded href) have no test (F-01, F-02). The remaining findings are low. None blocks the merge on its own. Each should become a failing test first.

Findings by severity: 0 blocker, 0 high, 2 medium, 4 low, 2 info.

## 1. Checks run (venv python `/home/maldun/prog/Python/venvs/mia312/bin/python`)

| Check | Result |
|---|---|
| tests/test_skill_turn.py | 4 tests OK |
| tests/test_skill_history.py | 5 OK |
| tests/test_chat_verify_fixes.py | 46 OK |
| tests/test_skill_digest.py | 5 OK |
| tests/test_run_line_wiring.py | 3 OK |
| tests/acceptance/test_chat_skill_turns.py (incl. class LiveLine, TC-CHA-073..075) | 26 OK |
| tests/integration/G-V3/test_run_end_to_end.py (TC-CHA-068) | 1 OK |
| `node --test "tests/js/*.test.mjs"` | 178 tests, 174 pass, 4 fail; all 4 known and out of scope: TC-CLV-021, TC-CLV-049 (2), TC-CLV-052. run-line.test.mjs and run-line-page.test.mjs: 5/5 pass. |
| tests/test_run_line_browser.py (podman, headless Chromium on the stub) | 2 tests OK (20.5 s) |
| `python3 -I tools/check_sysml_model.py .` | OK (notes only: parts without requirement; "acceptance criteria: 40") |
| `bash tools/check_sysml.sh specs/mia/architecture.sysml` | ok, 0 errors, 0 warnings |
| trace_check, lines for CHA-068..071, CLV-053/054, TC-CHA-073..075, TC-CLV-053 | only one line: `WARN REQ-CHA-071 verified by test, but no @pytest.mark.req marker found` (see F-08) |

Known and out of scope (not counted): TC-CLV-049 (2), TC-CLV-052 node tests, tests/test_task_files_browser.py (not run), TC-CLV-021 (needs the owner's contract text of IF-101-change.md), accounts_enabled (the stub patch of `MIA.config.load` is older than `7e03715b`, not in this diff and limited to `ui/tools/chat_stub_server.py`).

Working tree: at the start of this review `tests/integration/G-V3/test_run_end_to_end.py` was modified and not committed (matches `amendment-a158/protected-integration-tc-cha-068.patch`). During the review it was committed as `97122a8a plan: A-158 integration check TC-CHA-068 follows A-156 and A-158`; the tree is now clean for it. Still untracked and unrelated: `eval/baselines/verdicts_*devsample.jsonl`, `templates/UI/`, a G-V2.CONVERT handover.

Protected files changed in range: `tests/acceptance/test_chat_skill_turns.py` (TC-CHA-075 now compares only status and message events, patch `protected-fix-tc-cha-075.patch`, commit `be60bf2a`) and the integration check (patch `protected-integration-tc-cha-068.patch`). Both have patches and apply scripts in `amendment-a158/` and a plan commit message. I could not verify from the repo who approved them outside the session (named approver of these two patches is not in the commits; the A-158 review-log draft names the owner for the amendment as a whole). See F-07.

## 2. Matrix (requirement, test, code, both directions)

| Requirement | Test | Code | Result |
|---|---|---|---|
| REQ-CHA-041 phase in status, no chat message, repeat once | TC-CHA-073 (`test_the_status_line_follows_...`), SkillTurns phase tests, TC-CHA-068 | `skill_turn` returns `{"id": None}` for phase; `_phase_line` dedupes `self._lines.get(run) == payload`; observer also dedupes | met; mutation M5 (no dedupe) caught |
| REQ-CHA-055 no status message for a run without phases (to the chat log) | TC-CHA-073 (lookup gives `working`, no message), wiring test | `start` with no declared phases gives `GENERIC_LINE` event only | met |
| REQ-CHA-068 line = phase name or `working`, repeat once | TC-CHA-073, TC-CHA-068, wiring | `_phase_line` | met; undeclared phase gives no line (tested) |
| REQ-CHA-069 clear before end message for done, failed, stopped | TC-CHA-074 (3 kinds), TC-CHA-068, wiring (failing run, no phases) | `skill_turn` clears before `post_assistant`; `_do_chat` clears before the end text | met; M1, M1b caught (see section 4) |
| REQ-CHA-070 `waiting for your answer` after the question, phase line again after the answer | TC-CHA-075, wiring | `skill_turn(question)` emits after `post_assistant`; `ask` calls `answered` | met for the answered path; the unanswered path is open (F-03) |
| REQ-CHA-071 line not in log, model history, speech | TC-CHA-073 (texts, spoken, model_history), TC-CHA-068 | `_phase_line` only `_emit`s | met; M2 (line posted to log) caught by 3 test files |
| REQ-CLV-053 line last element, replaced in place | run-line.test.mjs, run-line-page.test.mjs, browser test (TC-CLV-053) | `insertBefore(..., runLineEl)`, `list.append`, `runLineState` | met; M3 caught |
| REQ-CLV-054 removed when cleared | TC-CLV-053 (page, browser) | `runLineEl.remove()` on `text == null` | met |

Behaviour in code that no requirement states (gap in the specification, Phase 2 amendment or remove):
- `_clear_line` is also sent for a run that never had a line (code comment says so; it is harmless and makes a lost line impossible). No requirement and no test states it (the TC-CHA-074 example contains a line first). Info, F-06.
- The turn kind `answered` and the fallback `setdefault(run, "working")` when `answered` comes without a prior line (also for a run with declared phases that has not entered one). IF-201 v4 names the kinds (plan T-07), but no requirement says what a phase-run shows in that case. F-06.
- `_lines` bookkeeping (dedupe state, popped on clear). Needed for REQ-CHA-068 "once"; fine, not a record.
- Page: `runLineLabel` translates exactly the two English texts `working` and `waiting for your answer`; a manifest phase literally named `working` would be shown as "Arbeitet". Negligible. REQ-CLV-053 does not state the translation (the i18n text is in `en.json`/`de.json` and tested at T-08). F-06.
- Page keeps one line for all runs (`runLine` is a single value): the event of another run replaces the shown line, a clear of another run leaves it (tested, TC-CLV-053). Two runs at once are not required; also the service has one `_observer` (older limit).

Requirements the code does not meet: none found.

Edge cases (by reading; where a test exists it is named):
- Run fails before any phase: the clear is sent in `_do_chat` (wiring test "failing run clears the line too"). OK.
- Stopped run while a question waits: status `stopped`, so `_clear_line` runs before the end message. The line does not stay. Not covered by a test that combines wait and stop (the TC-CHA-074 stop case starts from a phase line). F-05.
- Question that gets no answer (timeout, `ask` returns `None`): no `answered`, so `waiting for your answer` stays on the page while the skill carries on, until a different phase or the end (the dedupe suppresses the same phase again). F-03.
- Reload during a run: the page forgets the line and the server does not resend it; the line comes back only with the next event (or never if the run is in one long phase). No requirement covers it. F-04.
- `answered` without `start`: `setdefault` shows `working` (see above).
- Phase declared and repeated after a different one (collect, rank, collect): shown each time; consecutive repeat once. OK.
- Exceptions: the observer wraps `on_phase` in `_call` (try/except). The other call sites do not: `_phase_line(..., "start")` in `_do_chat`, `_phase_line(..., "answered")` in `ask` (after the reply was taken from the queue, so a raise would lose the answer), `_clear_line` before the end message. They only raise if `_emit` or `_phases_of` raises; `_emit` is the raw socket emit, the same exposure as every other emit in the file. F-02-adjacent, low: F-05.
- Thread safety: `_lines` is a plain dict, check-then-set-then-emit is not under a lock. `phase` events come from the run thread, `question`/`done` from the run thread too, but `skill_turn` is also the public IF-201 method (API thread). A race could reorder an emit after a clear. Low, F-05.
- A `question` that arrives after the run ended (race) would leave a `waiting` line with nothing to clear it. F-05.

## 3. Trust and interface rules

- Text, not HTML: `chat.js` builds the line with `el('span', 'run-line-text', text)` which sets `textContent`; the phase name comes from the manifest through `runLineLabel`. Code is safe. No test would catch a change to `innerHTML` (mutation M7 survived). F-01.
- href: `withRunLine` builds `#run=${encodeURIComponent(run)}`; the click handler `a[href^="#run="]` uses `runOfHash`, which decodes with `decodeURIComponent` and returns null on a broken escape. Compatible. No test uses a run id that needs encoding (mutation M8 survived). F-02.
- New event: `chat_run_status` is named in `amendment-a158/IF-101-change.md`, `plan.md`, handover and the code docstring. It is not in a live IF-101 contract text (waiting for the owner's text; TC-CLV-021 known) and not in `architecture.sysml`. Not counted.
- Stub: the A-158 change in `ui/tools/chat_stub_server.py` is a `scripted_run` triggered by the user text "run" and a `_declared_phases` lambda on the stub's own service; it touches nothing outside the stub. The scripted run uses the account `anna` and a daemon thread. OK.
- Untrusted text: the line holds only manifest phase names or two fixed texts; no model output, no result text. Phase names are filtered by `phases` (declared only). OK.

## 4. Quality of the checks: mutations (scratch copy, real tree untouched)

| # | Mutation | Caught by |
|---|---|---|
| M1 | clear after the end message in `skill_turn` | TC-CHA-074 (3 subtests fail). Integration, wiring and JS pass (they take the `_do_chat` path). |
| M1b | no clear in `_do_chat` | TC-CHA-068 integration (1 fail) and 3 wiring tests. Acceptance passes (it only uses `skill_turn`). |
| M2 | post each line also to the chat log | 8 acceptance failures, integration, wiring |
| M3 | page: line no longer kept last (`insertBefore(..., null)`) | run-line-page TC-CLV-053 (1 fail) |
| M4 | page: clear of another run clears the line | run-line-page TC-CLV-053 (1 fail) |
| M5 | no dedupe of a repeated phase | TC-CHA-073 |
| M6 | waiting line sent before the question message | TC-CHA-075 |
| M7 | `innerHTML` instead of `textContent` for the line text | NOT caught (node 5/5 pass; browser test not run for this mutation) |
| M8 | no `encodeURIComponent` in the href | NOT caught |
| M9 | `answered` does not re-emit the phase line | TC-CHA-075, wiring |

The double clear (`_do_chat` and `skill_turn`) is redundant for a run, but each path is needed (the API turn kinds are called directly by tests and by IF-201 clients).

## 5. Findings

| ID | Sev | Where | What | Evidence | Suggested fix (test first) |
|---|---|---|---|---|---|
| F-01 | medium | tests/js/run-line-page.test.mjs, chat.js line render | No test that a phase name with markup is shown as text | Mutation M7 (`innerHTML`) survives all run-line tests | Node page test: line text `<img src=x onerror=...>` gives a text node, no element child |
| F-02 | medium | chat-model.js `withRunLine`, tests | No test of the encoded href and its round trip with `runOfHash` | Mutation M8 survives | Test with a run id `a b/c#d`: href is `#run=a%20b%2Fc%23d` and `runOfHash(href)` returns the id |
| F-03 | low | chat_service.py `ask` and `skill_turn(question)` | After a question times out (`reply is None`) the line `waiting for your answer` stays while the skill continues in the same phase (same-phase dedupe suppresses the old line) | read: `answered` only when `reply is not None`; `_lines` still holds the phase so `_phase_line("phase", same)` returns | Scripted test: question, timeout, same phase again; expect the phase line again (or a requirement saying it stays). Needs an owner decision, Phase 2 if the requirement should say it |
| F-04 | low | server and page | A reload during a run loses the line until the next event; no requirement, no resend on connect | read: `_lines` is never sent on connect; the page keeps `runLine` in memory | Decide in Plan: requirement or "not now"; then a test (reconnect gives the current line of a running run) |
| F-05 | low | chat_service.py `_phase_line`, `_clear_line`, `skill_turn(question)` | (a) start, answered and clear call sites are not wrapped in try (an `_emit` error loses the answer in `ask`); (b) `_lines` check-then-emit is not locked; (c) a question after the end leaves a waiting line; (d) no test for stop while a question waits | read | Tests: emit that raises does not lose the reply or the end message; stop while waiting clears before the end message; question after done gives no line |
| F-06 | low | spec gap | Behaviour in code with no requirement: clear sent when no line was shown; kind `answered` and its `working` fallback; translation of exactly two texts | read, section 2 | Amend (REQ-CHA-069/070, REQ-CLV-053) or remove; add one test each |
| F-07 | info | amendment record | The two protected-file patches name no approver in the commits; the owner decision is in the amendment review-log draft (a draft with `D-??`) | `git log`, review-log-draft.md | A person confirms the approver of both patches in `review-log.md` before the merge (P9) |
| F-08 | info | trace_check | `WARN REQ-CHA-071 ... no marker found` although `@mark.req("REQ-CHA-068", "REQ-CHA-071")` exists in test_chat_skill_turns.py:410 and the integration test | trace_check output; grep | Tooling question: the marker with two ids may not be parsed for the second id; check the script, not the tests |

## 6. Not checked, and why

- Quality evidence per characteristic (quality.md), deferrals, bandit/semgrep and licence checks, mutation of the browser test: not run, out of the stated scope of this review.
- The browser test with mutation M7/M8 was not run (cost); the page node tests did not catch them, so I did not claim browser coverage either.
- `tests/test_task_files_browser.py`: known out of scope, not run.
- Who approved the two protected-test patches: cannot be seen from the repo (F-07).
- Plausibility (req_plausibility), usability evaluation with bad inputs of the stub server: not done.
- No eval suites are touched by A-158; the agent-app eval checks do not apply (no prompt, skill, pipeline or pin change in the diff; the digest step is unchanged).
