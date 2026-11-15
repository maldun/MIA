# Hand-over for the Verify session of TD-11, option B (written 2026-11-08): verify independently

Read `CLAUDE.md` first. Skills: `dev-workflow`, `verify-phase`. `agent-app-verify` does not apply (no model step: no prompt, pipeline, eval suite or model pin changed). Phase 4 of the workflow, for the change set of TD-11 (A-132, A-133), on `master`.

**You are the independent reviewer.** Start in a fresh context. You did not write this code. Do not trust the implementation log or my reported runs as evidence: re-run everything yourself, in a clean environment, and write what you saw.

## What is to verify
Change set: master commits `c17ec52` (first red test) up to `36acda3` (review). In order:
| Part | Commits |
|---|---|
| Step 4, red tests | `c17ec52` (TC-CHA-030..034), `cef28fa` (TC-VPB-006), `8f2b4a7` (TC-CHA-036), `fc78af7` (TC-VPB-007 and the mock) |
| Implement (A-132) | `7e5f91a` (task 1), `410a4dd` (mock fix), `e1a75d9` (task 2), `d9d656c` (task 3), `7ac34ee` (log) |
| A-133, Stop during a repeat | `b1386ea` (amendment, Draft requirements), `69216bf` (red tests), `4918f4f` (approved), `62a32d0` (fix) |
| Records | D-275 to D-285 in `specs/mia/review-log.md`; `A-132-*.md`, `A-133-*.md`, `A-132-hand-check-result.md` in `specs/mia/amendments/` |

Production files changed: `chat_service.py`, `web_app.py`, `templates/static/chat/sound.js`, `chat.js`, `app.js`. Test tooling: `ui/tools/chat_mock_server.py`. List the exact diff yourself with `git diff 43f2988 master -- chat_service.py web_app.py templates/ ui/tools/ tests/` (`43f2988` is the merge of the TD-11 Plan step).

Requirements (all Approved, D-283 and D-285): REQ-CHA-030, 031, 032, 033, 034, 035, 036 (N-2.2, group SA) and REQ-VPB-006 (N-1.3). Checks: TC-CHA-030 to 037, TC-VPB-006, 007. Test requirements: TR-VOICE-001 to 005 (`specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/test-requirements.md`). Contracts are unchanged on purpose (IF-101, IF-201, IF-204): confirm that `contracts/` has no diff.

## Your job (verify-phase)
1. Re-run all checks in a clean environment (below) and write the requirement-by-requirement matrix: requirement, check, result, evidence.
2. Confirm the protected material is unchanged except for approved amendments: `contracts/`, `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`, `benchmarks/`. The new tests live in `tests/` (not in the protected folders); decide whether that is right or whether the owner should move them (open question below).
3. Check the code against the SysML model: `REQ-CHA-030..036` are in `specs/mia/architecture.sysml` (definition, usage, `satisfy`, `allocate`, `dependency`); run `bash tools/check_sysml.sh specs/mia/architecture.sysml` and `python3 -I tools/check_sysml_model.py .`. Check that `ConversationCore` (`mia.conversation`) is the part that does what the model says.
4. Review each task commit for correctness, interface and security gaps (the injected `speak` callback, the thread and lock use in `chat_service.py`, the `should_stop` hand-over to `SpeechStreamer.wait`, the new mock routes).
5. Look for **unspecified behavior**: code that does something no requirement says (list in the next section) and report it as a finding for an amendment.
6. Write the verification report: `specs/mia/amendments/A-132-verification-report.md` (proposal; the older nodes keep theirs in the node folder, for example `.../N-2.2-chat-agent/verification-report.md`, which is of an earlier goal and not yours to rewrite).

## Commands
Python tests with the venv `/home/maldun/prog/Python/venvs/mia312/bin/python`; no model or GPU runs; no stash; commit nothing outside the report.
- `python tests/test_chat_speak_again.py` (8 tests, about 1 s)
- `python tests/test_sound_server_handover.py` (2 tests, about 3 s)
- `node --test "tests/js/*.test.mjs"` (163 tests; the two of TC-VPB-006 are in `tests/js/sound-speak-again.test.mjs`)
- `python tests/test_speak_again_browser.py` (2 tests, about 20 s; needs podman and the images `localhost/mia:latest` and `localhost/mia-browser`; skipped, never passed, where they are missing)
- `python tests/test_chat_views_browser.py` (12 tests, about 45 s; the wire check TC-CLV-021 must stay green: the mock now sends `audio_reload` only with `MOCK_VOICE=1`)
- all chat tests: `python -m unittest discover -s tests -p "test_chat_*.py"` (166 tests), plus `-p "test_speech*.py"` (36) and `python tests/acceptance/contract/test_if_201_chat_turn.py` (16)
- the whole unit suite: `python -m unittest discover -s tests` and stage 1 and 2 of `run_stages.py` (stage ladder `stages.yaml` in the repo root)
- traceability: `python ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests` (**540 errors are the old M41 backlog, D-270, as on master before TD-11; none names a TD-11 id**; check that), `goal_check.py`, `python ~/.claude/skills/plan-phase/scripts/req_graph.py --spec-dir specs/mia --tests-dir tests` (26 errors and 46 warnings before and after), `req_plausibility.py` (one warning is known: REQ-VPB-006's 3 s has no claim, it is a code constant, D-285), `test_doc_check.py --tests-dir tests` (the new Python files have no finding)
- hand check: not for you to repeat unless the owner asks; read `specs/mia/amendments/A-132-hand-check-result.md`

## Known state (reported by earlier sessions; verify, do not believe)
- TC-CHA-036 is a **characterization**: it was green from the start by design. Its fake sink is only as good as the engine behind it (TR-VOICE-002: only the hand check hears the real engine).
- TC-VPB-006 and TC-VPB-007 each have a **green control** test (a late line without the request is still dropped); check that these controls can fail (that is, that they do test something).
- The hand check TC-CHA-035 failed once at step 3 (no stop button), led to A-133, and then passed on 2026-11-08, reported by the owner as "it works now". **The per-step results, the browser and the audio device were not written down**; ask the owner for them or mark the evidence as incomplete in the report.
- Decisions that only the code makes (no requirement says them), for your list of findings:
  1. `ChatService.stop()` returns True when it ended a spoken-again playback although no answer ran (so the `chat_stop` acknowledgement says `stopped: true`).
  2. A stop ends every playback that runs or waits at that moment; a speak again requested after the stop is spoken (generation counter).
  3. Any exception of the voice route (not only `OSError`) is logged once with `logger.error` and drops the rest of that request.
  4. In the app the voice route makes one connection per sentence (decided by the owner, D-280).
  5. A speak again that finds an answer running leaves that answer's status alone; otherwise it takes the activity `speaking` and restores the former one at the end.
- Not covered by a test: a speak again requested **while an answer is running** (item 5 above, the `not self._running` guard in `chat_service.py`), and a stop that comes while two repeats wait (TC-CHA-037 covers one blocked and one waiting repeat; read it).
- One test of another area errored once in a loaded full run and passed in three later runs: `tests/test_chat_review.py::test_the_status_says_waiting_while_a_question_is_open`. Run the suite at least twice; report it if it flakes again (it is not a TD-11 file).
- `tests/test_chat_speak_again.py` has one test with `time.sleep(0.2)` (TC-CHA-037, the second request must be in line before the stop). Judge whether that is stable enough on a loaded machine.

## Open questions for the owner (collect them in the report, do not decide them)
1. Where do the new tests belong? They are in `tests/` (plain files, not in `tests/acceptance/`, `tests/helpers/`, `tests/smoke/`), as the test spec of A-132 says, so the deny rules do not protect them. Move them into the protected folders or not?
2. Latent fault noted for TD-61, not part of TD-11: the sound server's handler ends only after the client has closed its connection; a client that waits for the reply and does not close keeps the single-threaded server blocked (`SpeechStreamer.wait` always closes, so today's route is not hit).
3. REQ-VPB-006's 3 s is the constant `STOP_DROP_MS`, not a measured bound: accept the plausibility warning or give it a reference?
4. Per-sentence connections lose the rendering ahead of the engine (D-280 accepted this, TD-61 is the target): check on the host that long answers do not sound choppy when they are spoken again; this is not in the hand check.

## Rules that bite
- Report, do not fix: a finding becomes a test or an amendment through the owner; you change no production code and no protected file.
- Never describe a green run of this session as more than what it is: evidence for the matrix, with the command and the date.
- Do not touch `contracts/`, G-V2 or G-V3 files, or approved requirement text. The branch `goal/v3` may change `chat_service.py`, `sound.js` and `chat.js` as well (A-132 section 9): note any overlap you see.
- `TD-61` (single voice path) is **not** in scope; it waits for G-V3.

## After Verify
Phase 5 (Commit) if the report is "Verified": the owner merges; the TD-11 change set is already on `master`, so Commit here is the tag, the release notes line and the requirement status update (the statuses are Approved now, `Verified` after your report). Deploy is probably empty with a reason (chat voice only, no new artifact); Validate is the owner's use of the voice.
