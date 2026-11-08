# Verification report, TD-11 option B (A-132, A-133): proposal

- Phase 4 (Verify), written 2026-11-08 by an independent Verify session that did not write the code and did not use the implementation log or earlier runs as evidence.
- Object: master commits `c17ec52` to `36acda3`, checked out as `3c6c388` (clean worktree, branch `verify-a132`). Handover: `specs/mia/amendments/A-132-handover-verify.md`.
- Python: `/home/maldun/prog/Python/venvs/mia312/bin/python`. No model, no GPU. Every run below is local, not CI: it is evidence for the matrix and nothing more.
- **Verdict proposal (updated after the fixes, section 7b): Verified except two open points of the owner.** The first run found F1, F2 and F7 as blockers; all three are fixed and re-verified (sections 7a, 7b). What keeps the report from a plain "Verified": (1) TC-CHA-035, the hand check on the host, has to be repeated after the fixes and written down per step (TR-VOICE-002); (2) the wording of REQ-CHA-033 AC-1 against two error lines in the app (section 7b). With both closed, or accepted as deviations by the owner, the verdict is Verified.
- The text below this line up to section 7 is the first run (before the fixes) and is kept as it was found.

## 1. Matrix (requirement, check, result, evidence)

All dates 2026-11-08, from the worktree root.

| Requirement | Check | Result | Evidence (command) |
|---|---|---|---|
| REQ-CHA-030 voice route per sentence | TC-CHA-030, TC-CHA-031 | pass | `python tests/test_chat_speak_again.py`: 8 tests OK; also inside `-p "test_chat_*.py"` (166 OK) and two full runs |
| REQ-CHA-030 on the real engine | TC-CHA-035 (hand check, TR-VOICE-002) | **evidence incomplete** | `A-132-hand-check-result.md`: failed at step 3, then "it works now"; per-step results, browser and audio device not recorded (open question 1) |
| REQ-CHA-031 order | TC-CHA-030, TC-CHA-036 | pass | `python tests/test_sound_server_handover.py`: 2 OK (real `SoundServer`, fake sink) |
| REQ-CHA-032 stop ends repeat | TC-CHA-032 (2 tests), TC-CHA-036 (cancel on close), TC-CHA-035 | pass, hand check incomplete | same commands; stop of a repeat that waits behind a blocked one is in TC-CHA-037 |
| REQ-CHA-033 failing route | TC-CHA-033 | pass with a fake, **not met with the real route (F1)** | test file above; probe `probe_route.py` (section 4) |
| REQ-CHA-034 one at a time | TC-CHA-034, TC-CHA-036 | pass | same commands |
| REQ-CHA-035 busy and speaking | TC-CHA-037 (a), TC-CHA-035 | pass for a repeat alone, **not met while an answer runs (F2)**, hand check incomplete | test file; `probe_status.py` |
| REQ-CHA-036 status returns | TC-CHA-037 (b) | pass for a repeat alone; wrong after an overlap (F2) | same |
| REQ-VPB-006 speak again within 3 s of a stop | TC-VPB-006 (node, 2 tests), TC-VPB-007 (browser, 2 tests) | pass | `node --test "tests/js/*.test.mjs"`: 163 pass; `python tests/test_speak_again_browser.py`: 2 OK in 16 s, not skipped (podman and both images present) |

Wider runs (this session):
- `node --test "tests/js/*.test.mjs"`: 163 of 163, 0 skipped.
- `python tests/test_chat_views_browser.py`: 12 OK in 46 s (the wire check TC-CLV-021 stays green).
- `-p "test_chat_*.py"`: 166 OK. `-p "test_speech*.py"`: 36 OK. `tests/acceptance/contract/test_if_201_chat_turn.py`: 16 OK.
- Whole unit suite twice (`python -m unittest discover -s tests`): both runs 2066 tests, 1 error, 4 skipped, 1 expected failure. The one error is `test_tailscale.ScriptTest.test_without_tailscale_it_says_how_to_install` (F10, not TD-11).
- `run_stages.py --upto 2 --keep-going`: model-ids, contract-js, js, quality, sysml-parse, contract-real, integration pass; `unit` fails (F10 only); `decomposition` fails (F7); `contract-mocks` and `acceptance` were skipped by `needs`, so I ran them by hand: contract-mocks 110 OK; acceptance 14 of 16 files OK, `test_graph_model.py` and `test_graph_run.py` fail (G-V2.MODEL red tests, F10).
- `sysml-parse` (`bash tools/check_sysml.sh specs/mia/architecture.sysml`): ok, 0 errors, 0 warnings. `python3 -I tools/check_sysml_model.py .`: OK.
- `trace_check.py`: 540 errors; none names a TD-11 id (grep for REQ-CHA-030..036, REQ-VPB-006, TC-CHA-03x, TC-VPB-006/7, TR-VOICE returns nothing). `goal_check.py`: 6 goals, 0 errors. `req_graph.py`: 26 errors, 46 warnings (as before). `req_plausibility.py`: one TD-11 item, the known REQ-VPB-006 warning (no claim for its 3 s). `test_doc_check.py`: 0 findings in the new Python files.
- Not done: bandit, semgrep, vulture, ruff or a dependency audit (none configured; no dependency was added). No mutation run beyond section 5.

## 2. Protected material and approved text

- `git diff --stat 43f2988 HEAD -- contracts tests/acceptance tests/helpers tests/smoke benchmarks stages.yaml`: empty. Contracts IF-101, IF-201, IF-204 are unchanged, as intended.
- Requirement text: Draft became Approved with History lines only (D-285, D-283). One approved text changed: REQ-CHA-033 AC-1 and TC-CHA-033 (A-133, "no event but audio_chunk and chat_status"), confirmed by the owner (D-284). Nothing else.
- New tests are plain files in `tests/` (not protected by the deny rules); the placement is open question 2.
- The same diff range also holds non-TD-11 commits (FR-42 samples, `tools/fetch_benchmarks.py`, `tests/test_fetch_benchmarks.py`); I did not review them.
- Process note: REQ-CHA-030..034 were implemented (`7e5f91a` to `d9d656c`) while Draft and were approved afterwards (D-285). REQ-CHA-035/036 were approved (D-283) before their fix `62a32d0`.

## 3. Code against the model

- `bash tools/check_sysml.sh` and `check_sysml_model.py` pass; REQ-CHA-035/036 have definition, usage, `satisfy`, `allocate` and `dependency`.
- **F6:** the model does not say that `mia.conversation` does this. `ConversationCore` lists `communicator.py`, `expressor.py`, `behaviourRules` and others; `chat_service.py` is the module of `WebApplication.chatService` (architecture.sysml line 282). REQ-CHA-030..036 are satisfied by and allocated to `mia.conversation`, as all older REQ-CHA are. No `interface` or `flow` connects the web app's chat service to the voice side (`audio` is bound to `voice.audio` only), so the new call chain ChatService, `speak_answer`, `SpeechStreamer`, sound server has no model element. The new `from .mia_logger import logger` import is not modelled either (trivial).

## 4. Findings

Severity: B blocks Verified; M merge or process; L low (trusted users, privacy-only items would rank lowest).

**F1 (B, Phase 3 or 2): REQ-CHA-033 is not met by the real route.** `web_app.speak_answer` makes one `SpeechStreamer` per sentence. `SpeechStreamer` catches `OSError` itself, logs "Sound server not reachable", and returns; it never raises. So `ChatService._play_again` sees no exception and does not drop the rest. With no sound server, 5 sentences gave 0 exceptions to the chat service and **5 error lines**, not one (probe `probe_route.py`: a copy of the body of `speak_answer` with the real `SpeechStreamer` on a closed port; I did not import `web_app`, which starts the whole app). TC-CHA-033 passes only because the fake raises `OSError`, which the real route never does: a fidelity gap of TR-VOICE-001 (its "Verified by" is TC-CHA-036, which does not cover the route). Proposal: a test of the real `speak_answer` with a closed port; then either let the route raise or amend AC-1 to "one line per sentence".

**F2 (B, Phase 2 then 3): the status is wrong when a repeat and an answer overlap.** Probe `probe_status.py` (real `ChatService`, fake blocking voice, answers on threads):
- an answer runs, a repeat is requested: status `(busy true, activity thinking)`, not speaking (REQ-CHA-035 says speaking, with no exception);
- that answer ends while the repeat still plays: `(true, idle)`: the page offers no Stop (it needs busy and speaking) while the voice is audible; same when a repeat runs and an answer starts and ends. After stop: `(false, idle)`.
No test covers it; mutants removing the `not self._running` guards (M12, M13) survive. Decision needed: what is the status and who owns the stop button in an overlap (handover decision 5 is only in the code).

**F3 (L, Phase 2): `stop()` now returns True when it ended only a repeat.** IF-201 edge says "`stop()` with nothing running is `{"stopped": false}`" and IF-101 "ends the running or next answer"; contracts were left unchanged on purpose. The page does not read the flag (`web_app.py:291` only returns it). Mutant M8 (return only `running`) survives, so no test pins it. Owner: widen the contract wording, or return False.

**F4 (L, Phase 2): `/api/speak_again` has no rate limit and no cap on waiting repeats.** `send` has both; `speak_again` spawns a thread per request that waits on the lock, and now plays on the host's speakers for any account (or "page" without accounts) (`chat_ops_api.py`). Trusted users today, so low.

**F5 (L, Phase 2): behaviour that only the code decides (the handover's five).** (1) stop result, see F3; (2) a stop ends every repeat that runs or waits, and a repeat requested after the stop is spoken (generation counter; TC-CHA-032 second test covers it); (3) any `Exception` is logged once and drops the rest of that request (covered for `OSError` only; see F1 for what the route really raises); (4) one connection per sentence (D-280); (5) status in an overlap, see F2. Also found: a stop that arrives while a repeat waits in the sound server's backlog makes the client close before sending a line; the real `SoundServer` then prints a traceback (27 stderr lines in `probe_empty.py`) and keeps serving the next client (it played "Alive."). Noise, not a failure.

**F6 (L, Phase 2): model allocation and missing flow**, section 3.

**F7 (M, Phase 2): stage-1 step `decomposition` is red, and A-133 made it worse.** `decomp_check.py`: 65 errors now, 63 at `43f2988`; the eight TD-11 ids (REQ-CHA-030..036, REQ-VPB-006) are the only REQ-CHA or REQ-VPB ids with "no parent one level up": their `Parent` is a requirement of the same node (REQ-CHA-006, -004, -032, -035; REQ-VPB-002). Six were red at the plan gate, REQ-CHA-035 and 036 were added by A-133. `stages.yaml` requires stage 1 for merge, so the gate would refuse.

**F8 (L): TC-CHA-037 relies on `time.sleep(0.2)`** to get the second request in line before the stop. If that thread were later than 0.2 s the second request would be spoken after the stop and the test would end at its 1 s check (a false red, no false green). Measured: 0 failures in 30 idle runs and 0 in 60 runs with 48 busy processes (`flake.sh`). Judged stable enough; a poll on the pending count would remove the race.

**F9 (L): no test for a repeat requested while an answer runs** (the `not self._running` guard), as the handover says. See F2 and mutants M12, M13.

**F10 (info, not TD-11): the stage ladder is red on this host for other reasons.** (a) `test_tailscale.test_without_tailscale_it_says_how_to_install` times out after 30 s in all three full runs and alone: `/usr/bin/tailscale` is installed, so the test runs the real `tailscale up`; neither `ui/tools/remote.sh` nor the test changed in the TD-11 range. (b) Stage-2 acceptance: `tests/acceptance/test_graph_model.py` and `test_graph_run.py` fail (red tests of G-V2.MODEL, installed in `97146b4`; another goal). The flake the handover names, `tests/test_chat_review.py::test_the_status_says_waiting_while_a_question_is_open`, did not recur: 0 errors in two full runs and 0 of 60 runs under load.

## 5. Can the controls and characterization fail? Yes

Mutations in a scratch copy of the tree (`git archive` to the job's tmp folder; the repository is untouched). Each turned the named test red:
- TC-VPB-006: `speakAgain()` made empty: test 1 fails. Drop window removed: the control (test 2) fails.
- TC-VPB-007 (browser): `onSpeakAgain()` call removed in `chat.js`: the button test fails; drop window removed: the control fails.
- TC-CHA-036: cancel on closed connection removed in `speak.py`: the cancel test fails; `SoundServer` made threaded: the order and no-overlap test fails.
- `chat_service.py`: no lock (M1), stop ignored (M2, M9), no stop check between sentences (M3), no speech filter (M4), route error not caught (M5), status not restored (M6), busy not reported (M7), pending not decremented (M10), reversed order (M11): all caught. **Survivors: M8, M12, M13** (F3, F2, F9).

## 6. Test requirements

| TR | Met | Note |
|---|---|---|
| TR-VOICE-001 fake records, blocks, raises `OSError` | yes, but the fake is unfaithful for failure | F1: the real route never raises |
| TR-VOICE-002 hand check on the host, result in this report | **no, evidence incomplete** | open question 1 |
| TR-VOICE-003 sentences written by hand | yes | read in the tests |
| TR-VOICE-004 real server, real TCP, fake sink | yes | mutations above |
| TR-VOICE-005 real `sound.js` and real page; mock sends `audio_reload` with `url`, `serial`, `message` | yes | one difference: the mock emits to every session of the token, `AudioRouter.announce` only to the owner page |

## 7. Open questions for the owner (not decided here)

1. TC-CHA-035: please give per step 1 to 4 the result, the browser, the audio device and the code state of the passing run. Until then the evidence is incomplete.
2. Where do the new tests belong: stay in `tests/`, or move into `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`?
3. REQ-VPB-006's 3 s is the constant `STOP_DROP_MS`: accept the plausibility warning, or give it a reference?
4. F1: should the real route raise so that one line is logged and the rest dropped, or should REQ-CHA-033 say one line per sentence?
5. F2: what is the status and the Stop button during an overlap of a repeat and an answer?
6. F3: widen the contract wording of `stopped`, or return False when no answer was stopped?
7. F4: a rate limit or a cap on waiting repeats for `/api/speak_again`, or accept as is?
8. F7: change the `Parent` of the eight requirements, or relax the decomposition rule?
9. TD-61 (not in scope): the sound server's handler ends only after the client closes; `SpeechStreamer.wait` always closes, so today's route is not hit. Per-sentence connections lose the rendering ahead of the engine (D-280): please listen to a long answer spoken again on the host (not in the hand check).
10. Overlap with `goal/v3` (A-132 section 9): I did not diff that branch; it may change `chat_service.py`, `sound.js` and `chat.js` too.

## 7a. Decisions of the owner (2026-11-08, answered in the Verify session; the Verify session decided none of them)

Questions 1 to 8 of section 7 are answered; 9 and 10 are tasks. The verdict does not change until the fixes below are verified.

| Question | Decision | Steps | Who |
|---|---|---|---|
| F1 (4) | The route raises | failing test of the real `speak_answer` on a closed port (raise; `_play_again` logs once and drops the rest); make `speak_answer` / `SpeechStreamer` raise on a failed connection; re-run TC-CHA-033 and the new test | Phase 3 |
| F2 (5) | Status is busy and speaking while any repeat runs or waits, also over a running answer; the former activity returns when the last one ends | amendment of REQ-CHA-035/036; failing overlap tests for both orders (repeat then answer, answer then repeat); fix `chat_service.py`; mutants M12 and M13 must then turn red | owner approves the amendment, then Phase 3 |
| F7 (8) | Change the `Parent` of the eight requirements | amendment: parent one level up for REQ-CHA-030..036 and REQ-VPB-006, the sibling stays as a `dependency`; re-run `check_sysml.sh` and `decomp_check.py` (expected 65 to 57 errors); update trace links | owner approves, then Phase 2 |
| F3 (6) | `stop()` returns True only when an answer was stopped; it still ends a repeat | test that pins the value; change the return to `running`; contracts stay unchanged | Phase 3 |
| TC-CHA-035 (1) | Repeat the hand check after the F1 and F2 fixes | record per step 1 to 4 the result, the browser, the audio device and the commit; the evidence stays incomplete until then | owner |
| Test place (2) | New tests stay in `tests/` | none; the F1 to F3 fixes can edit them without an amendment | none |
| 3 s claim (3) | Accept the plausibility warning | add REQ-VPB-006 to `plausibility.yaml` as accepted risk (maldun), like the other 40 | owner approves, then Phase 2 |
| F4 limits (7) | Accept as is | known limitation, to revisit with TD-61 | none |

**F7 applied (A-134, D-286, 2026-11-08):** the owner approved the proposed parents; the eight `Parent:` lines and the model `dependency` lines are changed. After the change: `decomp_check.py` 57 errors (was 65), none of TD-11; `check_sysml.sh` ok; `check_sysml_model.py` OK; `trace_check.py` 540 errors, none of TD-11; `req_graph.py` 26 errors and 46 warnings as before. F7 is closed; the `decomposition` stage step stays red only for the 57 older errors of the plan backlog, which are not TD-11.

Still open as tasks (not decisions): listen to a long answer spoken again on the host (together with the hand-check repeat; question 9), and diff `goal/v3` against the TD-11 files before the merge (question 10).

## 7b. Fixes and re-verification (2026-11-08)

The fixes were written by a separate implementer agent (it wrote the code; this session did not), test first, one commit per finding; this session then re-verified them from a fresh detached checkout of the agent's branch. Commits on `verify-a132` (cherry-picked unchanged, `git diff` against the agent's branch is empty): `4cb7156` F3, `32b30b9` F2, `1c9405f` F1; the specification part is `8a3a8b0` (A-134, F7).

| Finding | Result | Evidence (this session, 2026-11-08) |
|---|---|---|
| F3 `stop()` | fixed | `tests/test_chat_stop_result.py` 1 OK; red on the pre-fix code (`a91ed8c`), red when the fix is mutated back (N3, N6) |
| F2 overlap status | fixed | `tests/test_chat_speak_overlap.py` 2 OK (both orders, real threads); red on the pre-fix code (2 failures), red under mutation (N1, N2); my own probe `probe_status.py` on the fixed code: `(true, speaking)` at every step of both orders, `(false, idle)` after the stop (was `thinking` and `idle`) |
| F1 route | fixed, with one wording point (below) | `tests/test_speech_route_failure.py` 2 OK with the real `SpeechStreamer` on a closed port; red on the pre-fix code (1 failure, 1 error), red under mutation (N4, N5); my probe `probe_route_fix.py`: ChatService with the real `speak_text`, 5 sentences, nothing listening: **1 connection attempt** (was 5), the status back to `(false, idle)` |
| F7 parents | fixed | section 7a, A-134, D-286 |

Re-runs on the fixed code (clean detached worktree at `6e451b4`, `git status` clean):
- `test_chat_speak_again.py` 8, `test_chat_speak_overlap.py` 2, `test_chat_stop_result.py` 1, `test_speech_route_failure.py` 2, `test_sound_server_handover.py` 2: all OK.
- `-p "test_chat_*.py"` 169 OK; `-p "test_speech*.py"` 38 OK; IF-201 contract suite 16 OK; contract mocks 110 OK; `node --test "tests/js/*.test.mjs"` 163 of 163; browser `test_speak_again_browser.py` 2 OK (not skipped); `test_chat_views_browser.py` 12 OK.
- Whole unit suite twice: both 2071 tests (2066 plus the 5 new), 1 error each, the same host-dependent `test_tailscale` (F10), 4 skipped, 1 expected failure.
- Load: the 5 new tests plus `test_chat_speak_again.py` repeated 40 times next to 48 busy processes: 0 failures.
- `git diff --stat a91ed8c <fix branch> -- contracts tests/acceptance tests/helpers tests/smoke benchmarks stages.yaml specs`: empty. Only `chat_service.py`, `speech_stream.py`, `web_app.py` and the three new test files changed. `test_doc_check.py`: 0 findings in the new files. The other callers of the route (`research_chat.py`, `extensions/review/review_chat.py`) catch `Exception` around `speak()`, so the new `OSError` does not reach them (read, not run).
- Not re-run after the fixes: the stage ladder as a whole (I ran its steps singly), `trace_check`, `req_graph`, SysML checks (nothing in them depends on the code; the spec checks were re-run after A-134, section 7a).

Residual points after the fixes:
- **F1 wording.** One failed repeat now logs **two** ERROR lines in the app: the streamer's own "Sound server not reachable" (unchanged, it is shared with live answers) and the Chat agent's "Speak again: the voice route failed". With the fake route of TC-CHA-033 it is one line. REQ-CHA-033 AC-1 says "one error line". Owner: accept two lines (one per layer) and word AC-1 as "one error line of the Chat agent", or silence the streamer line for this route.
- **Still untested guards:** the mutants "a repeat takes the status although an answer runs" (N8) and "the status is restored although an answer runs" (N7) survive: these guards only decide the mood activity that the character shows, which the status of the new tests overrides. Low.
- **TC-CHA-035** is not repeated yet; the evidence stays incomplete until the owner repeats the hand check after these fixes (decision in 7a). Also the listen test for choppy long answers (question 9).

## 8. Next step

F1, F2, F3 and F7 are fixed and re-verified (section 7b). Open for the owner: (1) repeat the hand check TC-CHA-035 on the host with the fixed code and write down per step 1 to 4 the result, the browser, the audio device and the commit, and listen to a long answer spoken again (question 9); (2) decide the wording of REQ-CHA-033 AC-1 against two error lines in the app; (3) diff `goal/v3` against the TD-11 files before the merge (question 10). Then the owner approves this report; Phase 5 is the tag, the release-notes line and the status update of the eight requirements to Verified. The owner merges `verify-a132` (it holds the fixes, A-134 and this report) and no one pushes before that.
