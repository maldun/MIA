# Verification report: Voice playback (N-1.3)

**Goal:** G-V1 (iteration), supervised; node N-1.3 (leaf of N-1), verified as a black box with the mocks of its neighbours
**Branch:** goal/v1 @ a9aa3ac (node commit `a8fb6e0`, built on master before goal/v1 began at 53c6766)   **Parent line of work:** master   **Plan baseline:** plan-baseline-it1
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context, never saw the implementation chat)

## Verdict
Proposed: **Not verified** (REQ-VPB-001, -002, -005 and IF-112 are met; REQ-VPB-003 is not met end to end, F1 and F2; REQ-VPB-004 is met by inspection and the page's CSP, but its specified browser check did not run, F3). After the fixes of F1 and F2 only the fix commits need a review; F3 needs the owner's browser run.

## Automated checks (local runs, no CI)
| Check | Result |
|---|---|
| Stage log | no CI run; all results below are local runs of this reviewer on the worktree (host node v22.22.0, image localhost/mia:latest) |
| Tests (unit, acceptance, contract, e2e) | `node --test "tests/js/*.test.mjs"`: 123 pass, 0 fail (13 of them in `voice-player.test.mjs`, 3 in `no-outside-requests.test.mjs`). `node --test tests/acceptance/contract/*.mjs`: 16 pass, 16 skipped (all `[real]`; IF-112 real: "N-1.3 Voice playback not integrated yet"). Python in the image (`podman run --rm --init --network none ...`): `test_audio_router.py` 23 OK, `test_chat_page.py` 11 OK (strict CSP), `test_voice_lines.py` 8 OK, `test_speech_service.py` 9 OK, `test_frontend_delivery.py` 2 OK (1 skipped: no podman in the image). `python3 tests/test_frontend_delivery.py -v` on the host: 2 OK (the stage `chat-on-stub` started in the MIA image, page and `sound.js` served, stopped again). Browser check `ui/tools/chat_audio_e2e.js`: not run (no browser) |
| IF-112 suite, real side | skipped by the protected `REAL_NOT_READY`. Reviewer's scratch run with an own adapter (real `VoicePlayer` on a synchronous fake element; `played` = lines that ended audibly, `tick` = the playing line ends): 10 of 10 green. With `played` counted at the start of a line TC-IF-112-04 fails: the real player starts a line on `enqueue`, the mock only on `tick`; the adapter of the integration step must count at the end (see F6) |
| Integration N-1 | `step_00` fails (`'happy' !== 'neutral'`, an expression of IF-111, not N-1.3; known on master too); steps 01..03 skipped |
| Statistical checks, benchmarks, flakiness | none specified for N-1.3 |
| Protected material vs. baseline | `contracts/IF-112-voice-player.md`, `tests/acceptance/contract/test_if_112_voice_player.test.mjs`, `tests/helpers/mocks/if_112_voice_player.mjs`: identical to master, 53c6766 and a8fb6e0. `tests/helpers/contract.mjs`: one line more than master (`IF-104` entry of REAL_NOT_READY, amendment A-36, commit 4892783), not N-1.3. The node commit touches no protected file |
| Traceability (trace_check.py) | for N-1.3: ERROR `test-spec.md`: 5 checks but no `## Scenarios` section (M39); WARN REQ-VPB-001..005 and IF-112: "no mark.req marker found" (the JS tests carry the TC ids in their names, no marker; `test_frontend_delivery.py` has no `mark.req`). Global WARN: `test-requirements.md` has no TR items, so (a) cannot be checked for this node |
| test_doc_check.py | `tests/test_frontend_delivery.py`: 4 errors (T1 no docstring in the container test, T2 no `Example:` line, T3 two bodies without Given/When/Then). The two JS files: 0 errors (the tool does not read JS bodies) |
| Refactoring commits / agent configuration | no `refactor:` commit; no agent configuration touched |
| Architecture rules | `VoicePlayer` is the provider of IF-112 in `templates/static/chat/sound.js`; imports none; the page talks to the backend only through the socket passed in (audio_reload, audio_owner, audio_claim, audio_ended) |
| Static / security | no linter configured (CLAUDE.md). `sound.js` makes no request of its own (no fetch/XHR/WebSocket), sets `audio.src` to the url the server sends; CSP of the chat page `media-src 'self' blob:`, `connect-src 'self'` (web_app.py:685-686). No output to HTML, no shell. Privacy out of scope (D-131) |
| Mutation testing (scratch copies) | 12 mutants of `VoicePlayer` against `voice-player.test.mjs`: all killed (order guard, mute, error event, skip after failed play, owner stop, owner drop, stop clears, held line in front, held flag, claim rate, ended line, speaking false). `initSound` wiring: removing `player.mute(muted)` or `player.setOwner(...)` survives the whole JS suite; removing `player.enqueue(...)` is caught only by a text match (F4). `no-outside-requests.test.mjs`: an outside URL added to `sound.js` or as the script `src` of `index.html` is caught; one added to `templates/static/vendor/*.js` is not (the vendor folder is not scanned; the CSP still blocks it at run time) |
| Usability | not applicable beyond the mute toggle and the autoplay hint; both need the browser (manual checks) |
| Deployable artifact | the page and `sound.js` are served by the MIA image (test_frontend_delivery, host run) |

## Verification matrix
| Requirement | Method | Evidence | Result | Plausible? |
|---|---|---|---|---|
| REQ-VPB-001 play in order, no overlap | Test | TC-VPB-001 (3 tests in `voice-player.test.mjs`), TC-IF-112-01/02 (mock; real via scratch adapter 10/10); mutants "order", "ended line" killed | **Met on the fake element**; but see F1: with a real browser a missing file makes the next line be skipped | yes; the fake does not model the play promise of a real element (F1) |
| REQ-VPB-002 mute / stop on this device only | Test | TC-VPB-002 (4 tests), TC-IF-112-03/04; mutants "mute", "owner-stop", "owner-enq", "stop-clear" killed | **Met** for `VoicePlayer`; the page wiring (mute toggle, `audio_owner`) has no test (F4); `stop()` has no user control on the page (F5) | yes |
| REQ-VPB-003 voice line: play, skip a missing file, report to the backend | Test | TC-VPB-003 (2 tests): `onLineError(id)` once and the next line plays, on a fake that fires either the `error` event or a rejected `play()` | **Not met**: (F2) `initSound` never sets `onLineError`, lines have no `id`, and no event to the backend exists (IF-101 has none, web_app.py has no handler); (F1) a real element does both (event and rejected promise): the reviewer's scratch test with a spec-like fake gives reports `['a','a','b']` for one missing line and line b is never heard | the green tests are plausible only for the fake; not for a browser |
| REQ-VPB-004 no request leaves the host | Test (specified: headless browser recording every request, stage 2, exact) | `no-outside-requests.test.mjs` (static scan of `index.html`, `static/chat/*.js|css`, 3 tests); CSP header `default-src 'self'`, `media-src 'self' blob:`, `connect-src 'self'` (tested by `test_chat_page.py`); reviewer's grep: the only outside URLs in `templates/` are comments in vendored libraries | **Met by inspection and CSP**; the specified browser test was not run (F3) | yes |
| REQ-VPB-005 delivered by the backend | Test (specified: compose stack, real browser, stage 3) | `test_frontend_delivery.py` 2 OK on the host: no frontend service in `deploy/compose.yaml`, `COPY . MIA/` in the Containerfile, `/`, `/static/chat/sound.js`, `/static/chat/chat.js` served by the MIA image (stage `chat-on-stub`, the stub server, not the compose stack) | **Met** (with the stub server inside the backend image instead of the compose stack; F7) | yes |
| IF-112 voice player | Test (contract suite, mock stage 1, real stage 2) | mock 5/5 green; real skipped (protected); scratch adapter 10/10 | **Met** for operations, errors, bounds; text gap on mute (F6) | yes |

## Test requirements (M41)
| Test requirement | Source | Kind | Applies to | Credibility aspect | Verified by | Met? |
|---|---|---|---|---|---|---|
| – | – | – | – | – | – | `test-requirements.md` has no TR items (global WARN of trace_check); the fidelity of the fake audio element is the credibility gap of this node (F1) |

## Goal acceptance (node part)
| Item | Result |
|---|---|
| Requirements of N-1.3 verified | 3 of 5 met (001, 002, 005), 004 by inspection only, 003 not met; IF-112 met |
| Frozen requirements unchanged | G-V1 has no frozen requirements |
| Protected checks identical to the baseline | yes (see above) |
| Nothing outside the node's parts touched | yes: `sound.js`, three new test files, the log |
| Every stop condition logged | the open questions (adapter, IF-112 mute text) are in the log; the unrun browser check is logged |
| Exit criterion | checked at the integration of N-1 and in Validate |

## Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-VPB-003 "report it to the backend" | F2: no report reaches the backend | owner decision, then Phase 3 |
| specified, not done | REQ-VPB-002 "a user ... stops the voice" | F5: `stop()` exists, no control of the page calls it | owner decision (integration of N-1) |
| specified, not done | TC-VPB-004 as a browser request log | F3 | owner browser run |
| done, not specified | muted lines keep running without sound (mouth moves, `audio_ended` sent) | F6: IF-112 says they are dropped | Phase 2 amendment of the IF-112 text |
| done, not specified | `claimIfUsed`, `claim({initial, force})`, `queued`, `playing`, `onEnded` | helpers beyond IF-112, used by the page; harmless | none (note for the IF-112 v1 text) |

Human review: specification side via `review-log.md`; code read for marked items: none marked.

## Quality evidence per characteristic (M32)
| Characteristic | Requirement(s) | Evidence | Result | Gap or `not now` |
|---|---|---|---|---|
| Functional suitability | REQ-VPB-001..003 | unit and contract tests, mutants | partly | F1, F2 |
| Performance efficiency | – | – | – | not now: no budget for this node |
| Compatibility | REQ-VPB-004 | CSP, static scan | met by inspection | F3 |
| Interaction capability | REQ-VPB-002 | – | not shown | mute toggle and hint need the browser (manual checks) |
| Reliability | REQ-VPB-001, -003 | blocked-autoplay tests | partly | F1 (stale play promise) |
| Security | REQ-VPB-004 | CSP test, no own requests | met | – |
| Maintainability | – | `VoicePlayer` extracted, readable; `initSound` thin | met | F4 (wiring untested) |
| Flexibility, Safety | – | – | – | not now: not relevant for a leaf in the page |

## Open deferrals (M26)
None for N-1.3.

## Review findings
Per commit: `a8fb6e0` is the only node commit (T-01..T-04 in one commit; the log names two, `feat(sound)` and `test(frontend)`; one commit per task was planned). It stays in its bounds and keeps `LineQueue`, `mayClaim` and the socket events unchanged. Findings:

| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | `templates/static/chat/sound.js:151` and `:155-167`: the settle handlers of `audio.play()` never check that their line is still `this.current`. In a browser a missing file fires `error` (handler at `:67-71`) **and** rejects the pending play promise (NotSupportedError); `pause()` (stop, `setOwner(false)`) and a new `src` reject a pending promise with AbortError. Result (reviewer's scratch test with a spec-like fake, three lines, a missing): `onLineError` gets `a, a, b`, b is never heard, `current` ends `null` while c plays; `stop()` during a pending play reports the stopped line as an error; a line enqueued right after `stop()` plays with `current = null`, so its `audio_ended` carries no serial. Pre-existing in the old `startNext` (same pattern), not caught because the fake of `voice-player.test.mjs` does only one of the two | High (REQ-VPB-001 a line lost, REQ-VPB-003 one report) | needs test: a fake element that settles play promises as the HTML spec does (error event plus NotSupportedError; AbortError on pause and on a new src); then Phase 3: ignore a settled promise whose line is no longer `this.current`, and an AbortError |
| F2 | `templates/static/chat/sound.js:189-190` and `:201-203`: `initSound` sets `onBlocked` but not `onLineError`, and enqueues lines without `id`; there is no event to the backend (no handler in web_app.py, none in IF-101 v10). REQ-VPB-003 "report it to the backend" is not done; TC-VPB-003 tests only the IF-112 callback | Medium (Should) | owner decision: (a) add an event, e.g. `audio_line_error {serial, url}`, to IF-101 (amendment) with a handler that logs it, then wire `onLineError` (Phase 3, test on the page wiring); or (b) amend REQ-VPB-003 so that the report ends at the IF-112 callback |
| F3 | `tests/js/no-outside-requests.test.mjs`: TC-VPB-004 is specified as a headless browser recording every request of a session (stage 2, exact); the implementation is a static source scan (does not scan `templates/static/vendor/`). The browser check was not run | Medium (check outside its specification) | owner runs the browser check (manual check 3); or Phase 2 amendment: accept scan + CSP test as the stage-1 evidence and keep the browser log for the N-1 integration step |
| F4 | `templates/static/chat/sound.js:170-241` (`initSound`): no test drives the page wiring; the mutants "no `player.mute(muted)`" (`:193`) and "no `player.setOwner`" (`:209`) survive all 123 JS tests; `enqueue` is guarded only by a text match (`no-outside-requests.test.mjs:38`) | Low | needs test: `initSound` with a fake socket, storage and elements (mute toggle sets `audio.muted` and storage, `audio_owner` of another sid silences, `audio_reload` enqueues, hint click calls `allowAutoplay`) |
| F5 | `initSound` returns no `stop`; the composer's Stop button (`app.js:222`) does not reach the voice. REQ-VPB-002 names "stops the voice" | Low | owner decision at the N-1 integration: should Stop also silence the voice on this device, or is mute the user's stop? Then N-1.1 wires `stop()` |
| F6 | `contracts/IF-112-voice-player.md` (operation `mute`): "queued lines are dropped while muted"; the real player keeps them running without sound (the mouth moves, `audio_ended` sent), the mock drops them, so `onSpeaking` differs between mock and real when muted. Also: the real player starts a line on `enqueue`, the mock on `tick`, so the adapter of the integration step must count `played` at the end of a line (the reviewer's adapter: 10/10) | Low | Phase 2 amendment (already proposed in the log): IF-112 v1 text "muted lines run without sound"; the mock's `mute` follows; the adapter goes into `make` and `contract.mjs` at the N-1 integration step (owner) |
| F7 | `tests/test_frontend_delivery.py:26-39`: TC-VPB-005 runs the stub server in the MIA image (stage `chat-on-stub`), not the compose stack with a real browser as specified (stage 3); the file fails `test_doc_check` (4 errors) and carries no `mark.req` | Low | amendment of the test spec (accept the stub stage) or a compose run in the N-1 integration; docstrings, Given/When/Then and markers in Phase 3 |
| F8 | `test-spec.md` has no `## Scenarios` section (trace_check ERROR, M39); the JS tests carry no requirement marker (WARN for REQ-VPB-001..005, IF-112) | Low (plan) | Phase 2: scenarios for TC-VPB-001..005; a marker convention for JS tests that trace_check reads |
| F9 | one commit for four tasks; the log names two commits that do not exist | Info | note for the commit phase |

## Accepted deviations
None yet (candidates: F3 and F7 if the owner accepts the substitute checks).

## Manual checks for the owner (browser)
1. **Voice in order, one page plays:** `bash tools/start_testing.sh start chat-on-stub`, then `python ui/tools/browser_check.py "http://127.0.0.1:8685/?character=0" shot.png --eval "$(cat ui/tools/chat_audio_e2e.js)"`: both lines play one after the other, only this page gets them, the talking state ends.
2. **Two pages claim the voice:** open the page in two tabs (or phone and computer); click in tab A, say something: only A speaks; click in tab B, say something: only B speaks, A is silent; close B: A gets the voice again.
3. **No outside request (TC-VPB-004):** in the browser's DevTools, Network tab with "Preserve log", load the page, log in, chat with a spoken answer, mute, unmute: every request goes to 127.0.0.1:8685 (0 outside the host); the console shows no CSP violation.
4. **Mute and autoplay:** mute in tab A: no sound, the mouth still moves; reload: still muted (stored per device); a second device still plays. In a fresh private window (autoplay blocked) the sound hint appears; one click plays the held line and the next ones in order, nothing is lost.
5. **Missing file (F1, F2):** with the stub, make a line's file disappear (delete the wav under the audio folder right after `audio_reload`, or let the server announce a wrong url): watch the DevTools console and the next line: today the next line is expected to be skipped (F1) and no report reaches the server (F2).

## Not checked
- Real audio output and timing (no browser, no sound device in this session).
- The CI stage log (none exists for this node); all results are local runs.
- Test requirements (none defined).

## Notes for Phase 7 (validation)
- Whether the character's mouth moving while muted (F6) feels right to the users.
- Whether users expect the Stop button to silence the voice (F5).

## Re-verification (2026-10-31)
**Branch:** goal/v1 @ 0568820 (fix commits of `v1-n13`: 61e7eb9, 9d0bc1f, 2264299, f0e9838, 86e690b, a804a30, 22df54a; merged in 7700b61)   **Reviewer:** Claude Opus 5.5 (AI, fresh context, never saw the implementation chat)   **Inputs:** this report (F1..F9), implementation-log.md ("Verify findings"), A-50, D-140, D-141, D-142, IF-112 with suite and mock. Local runs only (no CI); no model server, no outside network (Python tests in the image with `--network none`).

### Verdict (re-verification)
Proposed: **Verified with accepted deviations.** REQ-VPB-001, -002, -003 (as amended by A-50), -004, IF-112 are met with tests that fail before the fixes and pass after; REQ-VPB-005 is met with the stub stage instead of the compose stack (F7, deviation to accept). Remaining items are Low/Info (N1..N5 below, F7, F8) and the owner's by-ear checks; none blocks the node. If the owner does not accept F7 and the open N1 test, the status is "Not verified" until they are done.

### Per finding
| # | State | Evidence |
|---|---|---|
| F1 stale play promise | **Fixed** (61e7eb9) | `sound.js:152-155`: settle handlers act only while their line is `current`; `specAudio` in `voice-player.test.mjs` settles `play()` as the HTML spec does. Reviewer run of the new tests against the pre-fix `sound.js`/`app.js` (7700b61^1): 7 of 21 fail (both F1 tests among them); after: 21/21. Mutant "no `current === line` guard on the reject handler": killed (2 tests). Gap: the same guard on the resolve handler is not killed (N1) |
| F2 report beyond the callback | **Decided and applied** (A-50, D-140, D-142; f0e9838, 22df54a) | REQ-VPB-003, REQ-FE-013 (Text, AC, History), test-spec TC-VPB-003, SysML `doc` of both: the report ends at `onLineError`; the page writes one `console.warn` (`sound.js:195-196`), lines carry `id` = url (`:207-210`). Test "on the page a missing line is reported once in the browser console ..." red before, green after; mutants "no `onLineError` wiring" and "no `id`" killed. `check_sysml_model.py`: OK |
| F3 TC-VPB-004 not a browser log | **Fixed** (D-141; 86e690b) | `tests/test_page_requests.py` on the host: 4/4 OK (31 s). Planted `<img src="http://192.0.2.1:9/x.png">` in `index.html`: 2 FAIL (outside url and CSP message). Planted script-built request in `sound.js` (`['http:','','192.0.2.1:9','y.png'].join('/')`): the source scan passes (3/3), the browser test FAILs (2) - it catches what the scan misses. With a missing browser image (scratch copy, constant renamed): `OK (skipped=1)`, 0 tests run - skips, never passes. See N4, N5 |
| F4 page wiring untested | **Fixed** (9d0bc1f, 2264299) | `page()` drives `initSound` on fakes. Reviewer mutants: no `player.mute(muted)` -> 1 fail; no `player.setOwner(...)` -> 1 fail; `audio_reload` without `id` -> 1 fail; `stop: () => {}` -> 1 fail. `enqueue` is now driven through `audio_reload` |
| F5 Stop does not reach the voice | **Decided and applied** (D-140; 9d0bc1f) | `initSound` returns `stop` (`sound.js:246`), `app.js:233` calls it in `onStop`; tests red before. The `app.js` line is checked by a source regex (an entry point without exports): it fails on a reformatting, not only on a behaviour change (Info). See N3 for what Stop does not cover |
| F6 muted lines | **Decided and applied** (D-140: the code follows IF-112, text unchanged; 2264299) | `enqueue` drops while muted, `mute(true)` clears the queue (`sound.js:80`, `:87`); the playing line ends without sound - same as the mock (`mute` empties the queue, `enqueue` drops). Mutants on both lines killed. `audio_ended` is informational on the server (`web_app.py:794-797`), so dropped lines lose nothing there. The integration-step adapter hint (count `played` at the end of a line) is kept in the log |
| F7 TC-VPB-005 on the stub, docs | **Partly**: docs fixed (a804a30: docstrings, Given/When/Then, `mark.req`; `test_doc_check` 0 errors on `test_frontend_delivery.py` and `test_page_requests.py`); the method (stub stage in the MIA image instead of the compose stack with a real browser) is unchanged and not amended | owner: accept as deviation, or run the compose stack at the N-1 integration step |
| F8 Scenarios, JS markers | **Open** (Plan) | `trace_check`: ERROR `test-spec.md` no `## Scenarios` (unchanged); `// mark.req(...)` comments added to the JS tests but `trace_check` reads `*.py` only, so WARN REQ-VPB-001..003, IF-112 stays |
| F9 commit granularity | **Note** (commit phase) | the fix commits are one per finding, as the log says |

### New findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| N1 | `templates/static/chat/sound.js:154`: the `this.current === line` guard on the **resolve** handler survives all 131 JS tests (mutant: guard removed, 0 fail). It matters: per the HTML spec "notify about playing" takes the pending play promises and resolves them in a later task, so a `stop()` (or `setOwner(false)`) between the start and that task gives `_setSpeaking(true)` after the stop - the character keeps talking (heartbeat) until the next line ends. Reviewer's scratch test with a fake that takes the promises at start and resolves one task later: with the guard `[]`, without `[true]` | Low (REQ-VPB-002 "stop ... character stops talking"; the code is right, the test is missing) | test | add to `voice-player.test.mjs` a `specAudio` variant that resolves `play()` one task after the element starts, and a test "stop right after a line starts leaves speaking false" (Phase 3, no code change) |
| N2 | `templates/static/chat/sound.js:159`: the `AbortError` return is unreachable from the player's own `pause()`/new `src` (the guard at `:154` already drops those; mutant "line removed" survives, 0 fail). It is reached only by a pause from outside (OS media key, the browser) while a line starts: then `current` stays set, no `ended` or `error` follows, and every later line waits in the queue until a Stop or an ownership change. Before 61e7eb9 such a line was reported and skipped | Low | owner decision | either drop the line (the guard covers the player's own aborts, an outside abort then skips the line as before) or keep it and add a test for an outside pause; not specified by IF-112 either way |
| N3 | `templates/static/chat/app.js:233`, `composer.js:37`: Stop silences only what this page holds at the click. The Stop button is shown only while an answer runs, so the voice of an answer that has finished in text but is still being spoken cannot be stopped (only muted); and `chat_stop` (`chat_service.py:266-273`) does not cancel lines still being synthesised, so a line uploaded after the click (`web_app.py:479-497`) plays | Low (REQ-VPB-002 "stops the voice") | owner decision | judge in the by-ear check 3 below; if it bothers, either a short "drop lines for N s after Stop" in `initSound` or a voice Stop that stays visible while `playing` (N-1.1, amendment) |
| N4 | `tests/test_page_requests.py:54`: the browser container runs with `--network host`, i.e. with the host's full outside network, not on loopback only as D-141 says; a regression that requests an outside address would really try to send it (only the CSP stops it). The performance log sees only the page's requests, not the browser process's own | Low | owner decision | run the browser in the stub container's network namespace (`--network container:mia-test-chat-on-stub`) with that container on a network without an outside route, or accept and record in D-141 |
| N5 | `tests/test_page_requests.py:48-52`: a stage that is "running already" is reused. The container name `mia-test-chat-on-stub` is global and `start_testing.sh` says a running stage keeps its old code, so the test can check another worktree's checkout or stale code and pass | Low (evidence credibility) | test | skip (never pass) when the stage was not started by this test, or use `restart`; at least print which checkout the stage mounts |
| N6 | `trace_check.py` reads only the first id of `mark.req("A", "B")`: WARN REQ-FE-026 and REQ-FE-030 although `test_page_requests.py:60` and `test_frontend_delivery.py:18,38` mark them | Info (tool) | - | fix the tool's regex or one id per marker |

### Check results (reviewer's runs)
| Check | Result |
|---|---|
| `node --test "tests/js/*.test.mjs"` | 131 pass, 0 fail (`voice-player.test.mjs` 21, `no-outside-requests.test.mjs` 3) |
| `node --test tests/acceptance/contract/*.mjs tests/integration/N-1/*.mjs` | 33 tests: 17 pass, 16 skipped (all `[real]`, IF-112 real "N-1.3 Voice playback not integrated yet"); steps `tests/integration/N-1/step_0*/`: step 00 pass (the earlier `'happy' !== 'neutral'` is gone with A-48), 01..03 skipped |
| Python, MIA image (`localhost/mia:latest`, `--network none`, one container at a time) | `test_audio_router.py` 23 OK, `test_chat_page.py` 11 OK, `test_voice_lines.py` 8 OK, `test_speech_service.py` 9 OK, `test_frontend_delivery.py` 2 OK (1 skipped: no podman in the image) |
| `python3 tests/test_page_requests.py` (host) | 4 OK in 31 s; stage started and stopped by the test (two containers of the reviewer at once: the stub and the browser - the test needs both); mutants above |
| Browser image | `localhost/mia-browser` ea481da53461, created 2026-10-31 17:17 UTC; `/browser-versions.txt`: chromium and chromium-driver 156.0.8078.73-1~deb13u1, selenium 4.25.0 (as the log and D-142); `SE_OFFLINE=true`. `tests/browser/Containerfile`: base pinned by digest, apt and pip only at build time; at test time `podman image exists` is checked first and `page_requests.py` gives selenium `/usr/bin/chromedriver`, so nothing is pulled or downloaded |
| Protected IF-112 files | `contracts/IF-112-voice-player.md`, `tests/acceptance/contract/test_if_112_voice_player.test.mjs`, `tests/helpers/mocks/if_112_voice_player.mjs`: identical to master; `tests/helpers/contract.mjs`: only the `IF-104` line of A-36 (not N-1.3). The merge 7700b61 touches no file under `contracts/`, `tests/acceptance/`, `tests/helpers/`, `tests/integration/` |
| trace_check (N-1.3 lines) | ERROR `test-spec.md` no `## Scenarios` (F8); WARN REQ-VPB-001..003, IF-112 (JS markers not read), REQ-FE-013, REQ-FE-026, REQ-FE-030 (N6); WARN TD-01..04 "not listed in this report": they are the deferrals of A-26 (status card, Files tab, tokens, lookup glue), none concerns N-1.3 |
| test_doc_check | `test_page_requests.py`, `test_frontend_delivery.py`: 0 errors, 0 warnings |
| Model | `check_sysml_model.py`: OK (pilot parser not run: the merge changed only two `doc` texts) |
| Mutants (scratch worktree of 0568820, removed) | killed: no `mute(muted)`, no `setOwner`, no reject guard, enqueue ignores mute, mute keeps the queue, no `onLineError` wiring, no `id`, empty `stop`; survived: no resolve guard (N1), no AbortError return (N2) |
| Code review of the fix commits | in bounds (`sound.js`, one line of `app.js` as D-140 asks, tests, specs); no new request, no HTML output, no shell; `page_requests.py` and `test_page_requests.py` run fixed argument lists, no shell |

### Manual checks for the owner (by ear, browser)
Start: `bash tools/start_testing.sh start chat-on-stub`, open `http://127.0.0.1:8685/?character=0`.
1. **Two tabs claim the voice:** tab A and tab B (or phone and computer). Click in A, ask something: only A speaks. Click in B, ask: only B speaks, A is silent. Close B: A speaks the next line.
2. **Mute per device, autoplay hint:** mute in A: no sound, no new line starts (lines are dropped, the mouth stops after the current line); reload A: still muted; B (when it has the voice) still plays. Unmute: the next line is heard. In a fresh private window (autoplay blocked) the sound hint appears; one click plays the held line and the next ones in order.
3. **Stop silences the voice:** during a long spoken answer press Stop: the voice stops at once on this device and the mouth stops. Listen for a line that still comes a moment later (N3), and try to stop a voice whose text is already complete (no Stop button, N3).
4. **Missing file:** make the next line's file disappear (delete the `line-*.wav` under the audio folder right after it is announced, or let the stub announce a wrong url): the DevTools console shows exactly one warning `MIA voice: line skipped ...`, nothing is shown on the page, the following line plays.

### Not checked
- Real audio output, timing and the character's mouth (no sound device; checks 1-4 above).
- CI stage log (none); all results are local.
- TC-VPB-005 on the compose stack (F7).
- The pilot SysML parser (`tools/check_sysml.sh`).

## Re-verification 2 (2026-10-31)
**Branch:** goal/v1 @ f4da817 (fix commits of `v1-n13b`: 10c2fb0 N1, f7229dd N5, 31c8f90 F7; merged in 402a319)   **Reviewer:** Claude Opus 5.5 (AI, fresh context, never saw the implementation chat)   **Inputs:** "Re-verification (2026-10-31)" above, implementation-log.md (D-144 table, D-145 note), requirements.md, test-spec.md (TC-VPB-005 on the stack), D-140, D-141, D-142, D-144, D-145. Local runs only (no CI). The merge 402a319 touches no file under `contracts/`, `tests/acceptance/`, `tests/helpers/`, `tests/integration/` (`git diff --stat 402a319^1 402a319`: the node's log and test-spec, `voice-player.test.mjs`, three Python tests).

### Verdict (re-verification 2)
Proposed: **Verified with accepted deviations.** F7 is closed: TC-VPB-005 ran on the compose stack (not skipped, 5/5 OK) and checks what REQ-VPB-005 / AC-29 ask. N1 and N5 now have tests that fail on the defect. The remaining items are recorded by the owner for the N-1 integration step (N2..N4, D-145), the plan item F8, the tool item N6, and one new Low finding on the test's cleanup (M1: two anonymous volumes left per run), which does not touch the evidence. Condition: the owner's by-ear checks below; if one of them fails, the status is "Not verified".

### Per finding
| # | State | Evidence |
|---|---|---|
| F7 TC-VPB-005 on the stub | **Fixed** (31c8f90; D-144) | `python3 tests/test_delivery_on_stack.py` on the host, 18:30:12-18:32:13 UTC: 5 tests, OK, 121 s, none skipped (the 4 stack tests ran through `setUpClass`: build of `localhost/mia:vpb005` with `--pull=never`, `podman-compose -p mia-vpb005 up -d --no-build`, Chromium of `localhost/mia-browser`). What it checks against REQ-VPB-005 / AC-29: every request of the browser session (page, scripts, socket, an uploaded voice line played to `ended`) goes to the mia container's published port (`:134-144`, `:147-160`); `sound.js` over the http front and over the https front (Caddy) is byte-equal to `/opt/mia/MIA/templates/static/chat/sound.js` in the mia container (`:163-175`); the project runs exactly mia, graph, https, searxng, no frontend container (`:178-189`). That is the requirement. The red evidence (scratch copy with `<script src="https://cdn.example.org/x.js">` in `templates/index.html`: 1 FAIL with that url) is in the log; not repeated (one stack run is ~2 min and leaves volumes, M1); `CheckItself` shows `outside()` finds another host and ignores `data:`/`blob:`. Setup failures raise (error, not pass); missing tools/images/model server skip. Nothing pulled: `podman images -a` (709 entries, ids and tags) identical before and after, the `ollama` container ran throughout and still runs. Cleanup: no container, network or image tag `mia-vpb005`/`localhost/mia:vpb005` left, `deploy/setup_cfg.local.json` removed again, `git status --ignored` unchanged; but **two anonymous volumes left** (M1) |
| N1 resolve guard untested | **Fixed** (10c2fb0) | `specAudio(..., { resolveLater: true })` and the test "a stop just after a line starts leaves the character silent ..." Reviewer mutant in a scratch copy (`sound.js:154`, `if (this.current === line)` removed from the resolve handler): `voice-player.test.mjs` 21 pass, **1 fail** (that test); unmutated: 22/22 |
| N5 running stage reused | **Fixed** (f7229dd) | `own_stage()` (`test_page_requests.py:41-49`) matches the messages of `tools/testing_stages.d/_common.sh:25,31`. Reviewer run with the stage started by hand first: `test_page_requests.py` `OK (skipped=1)`, `test_frontend_delivery.py` `OK (skipped=1)`, the stage still ran afterwards (then stopped by hand). Stage stopped first: `test_page_requests.py` 5 OK (20 s), the stage gone afterwards. `StageUse` unit test covers the parse |
| N2 outside pause leaves the queue waiting | **Recorded** (D-145, integration step of N-1) | mutant "no `AbortError` return" (`sound.js:159`) still survives (22/22), as expected for a recorded item |
| N3 Stop vs. lines in synthesis | **Recorded** (D-145) | by-ear check 3 below |
| N4 browser `--network host` | **Recorded** (D-145); applies also to `test_delivery_on_stack.py:128` | unchanged |
| N6 trace_check reads the first id only | **Open** (tool, Info) | WARN REQ-FE-026, REQ-FE-030 unchanged |
| F8 Scenarios, JS markers | **Open** (Plan) | trace_check ERROR "no `## Scenarios`" unchanged |

### New findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| M1 | `tests/test_delivery_on_stack.py:115-116`: the cleanup (`podman-compose ... down -v`, `network rm`) removes the named volumes but not the **anonymous volumes** of the searxng image (`VOLUME /etc/searxng /var/cache/searxng`). The reviewer's run left `a6148ff23dbd…` (holds an empty `settings.yml` mount point) and `b576255c68cb…`, created 18:31:14Z, no labels. test-spec TC-VPB-005 and the D-144 log row say the test removes its volumes; the log checked only names `mia-vpb005*`. The host has ~28 such pairs from today (several stack tests and stages), so the pattern is not unique to this test | Low (host hygiene; the evidence is not affected) | test | collect the volume mounts of the project's containers (`podman inspect` before `down`) and remove them after `down`, or `podman rm -v` the containers; add the check "no volume of the project's containers is left" to the test's own teardown. The two volumes of this run were left in place as evidence; the owner may `podman volume rm` them |
| M2 | `tests/test_delivery_on_stack.py:111`: `--pull=never` stops image pulls, but the build's `RUN pip install -r MIA/requirements.txt` (`deploy/Containerfile:9`) still has network: when `requirements.txt` changes and the layer cache misses, the test downloads from PyPI, against "nothing pulled" (TC-VPB-005 row). In this run every layer was cached (no new image id) | Info | owner decision | `podman build --network none` in the test (a cache miss then fails the build with a clear message, or skips), or record that the test relies on the cached layers of `localhost/mia:latest` |
| M3 | `tests/test_delivery_on_stack.py:105-109`: while the test runs it writes `deploy/setup_cfg.local.json` (`{}`) into the checkout and removes it afterwards; in a worktree shared by several sessions another process sees the file for ~2 min | Info | - | none needed now; the file is git-ignored and removed (checked) |

### Check results (reviewer's runs)
| Check | Result |
|---|---|
| `python3 tests/test_delivery_on_stack.py` (host) | 5 OK, 121 s (wall 2 min 1 s); details and cleanup in F7 and M1 |
| `node --test "tests/js/*.test.mjs"` | 132 pass, 0 fail (`voice-player.test.mjs` 22) |
| `node --test tests/acceptance/contract/*.mjs tests/integration/N-1/*.mjs` | 33 tests: 17 pass, 0 fail, 16 skipped (the `[real]` and the later N-1 steps, as before) |
| `python3 tests/test_page_requests.py` (host) | 5 OK, 20 s, the stage started and stopped by the test; with a running stage: skipped, stage untouched (N5) |
| Python, MIA image (`localhost/mia:latest` 22619de57b4b, `--network none`, on a `git archive HEAD` copy in the scratchpad, removed) | `test_audio_router.py` 23 OK, `test_chat_page.py` 11 OK, `test_voice_lines.py` 8 OK, `test_speech_service.py` 9 OK, `test_frontend_delivery.py` 2 OK (1 skipped: no podman in the image). On a read-only mount of the checkout three files error (`mia_logger.py` writes `mia.log` next to the package) - an environment effect, not a defect of this node |
| trace_check (N-1.3 lines) | ERROR `test-spec.md` no `## Scenarios` (F8); WARN REQ-VPB-001..003, IF-112, REQ-FE-013 (JS markers not read), REQ-FE-026, REQ-FE-030 (N6); WARN TD-02..04 not listed here (deferrals of A-26, none concerns N-1.3) |
| test_doc_check | `test_delivery_on_stack.py`, `test_page_requests.py`, `test_frontend_delivery.py`: 0 errors, 0 warnings |
| Code review of 10c2fb0, f7229dd, 31c8f90 | test files and specs only, no product code; subprocess calls with fixed argument lists, no shell; the stack binds 127.0.0.1 only (`MIA_BIND`, port 127.0.0.1-mapped in `compose.yaml:24`); the model server is the host's (`OLLAMA_URL`), the `ollama` profile is never started |

### Manual checks for the owner (by ear, browser)
Unchanged from "Re-verification (2026-10-31)" above (D-145: one checklist file for N-1.3 and N-4.2, not written yet): (1) two tabs claim the voice, (2) mute per device and the autoplay hint, (3) Stop silences the voice at once, and listen for a late line and for a voice whose text is already complete (N3), (4) a missing file gives one console warning and the next line plays. Start: `bash tools/start_testing.sh start chat-on-stub`, open `http://127.0.0.1:8685/?character=0`. Optional on the stack: the same page over the https front of `deploy/up.sh` from a phone (REQ-VPB-005 by ear).

### Not checked
- Real audio output, timing and the mouth (no sound device): the checks above.
- The planted-outside-request run of TC-VPB-005 (log evidence accepted, see F7); CI stage log (none).

## Re-verification 3 (2026-10-31)
**Branch:** goal/v1 @ b072735 (fix commits of `v1-n13c`: 71d3743 M1, 512ddff M2, 45c8e21 M3, 73130c0 log, b22df4f D-150, 3597b9e runbook; merged in 63b7324. Fix commits of `v1-n13d`: 76f02a0 A4 test, a9c62b6 A3 speech stop, b825e8c A3 page drop (D-157), 525e8f8 A4 trap, 5965fd8 test skip; merged in 3620732; e032c94 is unrelated)   **Reviewer:** Claude Opus 5.5 (AI, fresh context, never saw the implementation chat)   **Inputs:** Re-verification 2 above, implementation-log.md (D-148, D-150, D-154, D-157 tables), requirements.md (REQ-VPB-002 AC with D-157), test-spec.md, IF-112, IF-101 v14, D-144, D-145, D-148, D-150, D-154, D-157, owner checklist `specs/mia/owner-checklist-2026-10-31.md` section A. Local runs only (no CI); scratch copies (`git archive HEAD`) in the reviewer's scratchpad, removed afterwards.

### Verdict (re-verification 3)
Proposed: **Verified with accepted deviations**, on one condition: the owner decides R1 below (accept it as a deviation, or route the small fix). Every earlier finding that was to be fixed in this node is closed with a test that fails on the defect (mutants below); M1..M3 are shown on a real stack run; the owner's by-ear checks A1..A4 are all ok (A3, A4 on the re-run). R1 (Medium) is new behaviour of b825e8c that goes beyond REQ-VPB-002's amended criterion: after a Stop the page drops *every* line until the next `chat_start`, also lines that do not belong to the stopped answer (the shocked line of a minus vote, IF-101 v13). If the owner rejects R1 as a deviation and wants it fixed, the status is "Verified with findings" until the fix commit is reviewed.

### Verification matrix (changes only)
| Requirement | Method | Evidence (this round) | Result |
|---|---|---|---|
| REQ-VPB-001 | Test | `node --test "tests/js/*.test.mjs"` 136/136 (`voice-player.test.mjs` 24/24); owner A1 ok | Met (unchanged) |
| REQ-VPB-002 (AC amended, D-157) | Test + by ear | page: `voice-player.test.mjs` "after the page's Stop the lines of the stopped answer that still arrive are dropped ..." (3 mutants killed, below); backend: `tests/test_speech_stop.py` 4/4 (three runs in the image), `tests/test_converse_behaviours.py` 6/6 (5 mutants killed); owner A2 ok, A3 ok on the re-run on the full app rebuilt from goal/v1 | Met; R1 (behaviour beyond the AC) |
| REQ-VPB-003 | Test + by ear | `tests/test_page_requests.py` `test_a_broken_line_gives_one_console_warning_and_the_next_line_plays` (headless Chromium, own stub stage): green on HEAD, **red** with master's `sound.js` (53c6766) in a scratch copy (`0 != 1` warnings); owner A4 ok on the re-run | Met |
| REQ-VPB-004 | Test | `tests/test_page_requests.py` (host) 6/6 OK, 28 s, none skipped, the stage started and removed by the test | Met (unchanged) |
| REQ-VPB-005 | Test | `tests/test_delivery_on_stack.py` (host) 5/5 OK, 127 s, none skipped; cleanup clean (M1..M3 below) | Met (unchanged) |
| IF-112 | Test | contract suite: 5 [mock] pass, 5 [real] skipped "not integrated yet" (the integration step of N-1, as before) | Mock side met; real side open at N-1 step |

### Per finding
| # | State | Evidence |
|---|---|---|
| M1 anonymous searxng volumes left | **Fixed** (71d3743, b22df4f) | reviewer's stack run 21:15:56-21:18:03 UTC: `podman volume ls` 19 before, 19 after, identical; networks identical; no container or tag `vpb005` left |
| M2 the build could reach PyPI | **Fixed** (512ddff, 3597b9e) | `podman build --pull=never --network none` built from cache in that run; nothing pulled. `podman images -a` 734 -> 733: one dangling id `a3f58e712025` gone, most likely the cached layer of an earlier run of the same checkout that this run tagged and `rmi -f` removed (another session also ran test containers at that time, so not attributed with certainty) |
| M3 file written into the checkout | **Fixed** (45c8e21) | `git status --short --ignored` identical before and after the run (25 lines). Note: a `deploy/setup_cfg.local.json` (`{}`, 20:22) exists in the worktree from before the run; it is not from this test |
| A3 Stop, then the voice started again (D-154) | **Fixed** (a9c62b6 backend, b825e8c page) | mutants, each on a scratch copy, in the MIA image `--network none`: `web_app.py:432` `streamer.wait()` without `should_stop` -> converse test FAIL; `speech_stream.py:122` stop ignored -> 1 FAIL; `speak.py:304` closed connection not a stop -> 1 FAIL; `speak.py:308` no watch after the end marker -> 2 FAIL; `speak.py:257-260` no cancel check -> 3 FAIL. Page: `sound.js:209` no drop, `:215` `chat_start` does not clear, `:252` Stop does not mark -> each 1 FAIL (23/24). Owner A3 ok on the re-run |
| A4 no console warning for a broken line (D-154) | **Closed** (test 76f02a0; cause: the stage served master) | browser test red with master's `sound.js`, green on HEAD (see matrix); owner A4 ok on the re-run from the goal-v1 worktree |
| A4 trap: which checkout a stage serves (D-157) | **Fixed for a stage it starts** (525e8f8, 5965fd8); see R2 | `tests/test_testing_stages.py` on the host 4/4; mutant "no `serving` in `start`" -> 1 FAIL, "no `serving` in `status`" -> 2 FAIL |
| N2 outside pause leaves the queue waiting | **Recorded** (D-145, N-1 step) | mutant `sound.js:159` still survives (24/24), as expected |
| N3 Stop vs. lines in synthesis | **Partly closed** by A3 (a9c62b6, b825e8c): lines still being made after `chat_stop` are no longer spoken or played. Open part (D-145): no Stop button once the answer's text is complete |
| N4 browser `--network host` | **Recorded** (D-145) | unchanged |
| N6 trace_check reads the first id only | **Open** (tool, Info) | WARN REQ-FE-012, -026, -030 unchanged (e.g. `test_speech_stop.py` marks `REQ-VPB-002, REQ-FE-012`) |
| F8 Scenarios section | **Open** (Plan) | trace_check ERROR "no `## Scenarios`" unchanged |

### New findings
| # | Finding | Severity | Needs | Proposal |
|---|---|---|---|---|
| R1 | `templates/static/chat/sound.js:209,215,252`: after the page's Stop, `initSound` drops **every** `audio_reload` until the next `chat_start`. REQ-VPB-002's amended AC (D-157) speaks of "the lines of the stopped answer" only. Lines outside an answer are dropped as well: a minus vote calls `character_reaction("shocked")` (`chat_service.py:404` -> `web_app.py:249-254`), which IF-101 v13 (`vote` row) says is "followed by ... the shocked line on the audio route". Typical path: the user stops an answer they dislike and votes minus on it -> MIA's shocked line is silent; the same for a minus by another user while this page holds the voice (multi-user), and for lines of a task whose `chat_start` comes late (IF-101 v8). Shown by a reviewer test on a scratch copy of `voice-player.test.mjs` (`page()`, `stop()`, `chat_done {status: stopped}`, `expression shocked`, `audio_reload shocked`): played `['a']`, expected `['a', 'shocked']` | Medium (a contract behaviour silently lost on a plausible path; no crash, no wrong audio) | owner decision, then test (and an AC line) | let the mark end at the next `chat_start` **or** a short time after the Stop (late lines of the stopped answer arrive within the ~0.2 s poll plus one upload; e.g. 3 s), test-first with the fake clock of `page()`: "a shocked line 3 s after the Stop plays"; record the window in REQ-VPB-002's AC. Alternative: accept as a deviation until lines carry an answer id (option (a) of D-154) |
| R2 | `tools/start_testing.sh:39-41` with `tools/testing_stages.d/_common.sh:25`: `start` prints `serving <this checkout> at <hash>` and then, when the stage's container runs already, only `<name> is running already`, although that container mounts the folder it was first started from. The log (D-157 row) says "its `running already` line says so", but the line names no folder. The A4 trap (a stage started from the main folder, then `start` from the worktree) still prints the worktree as served | Low (tooling; the checklist now says to start from the worktree) | test | in `start_container`, when the container runs, read its mount (`podman inspect -f '{{range .Mounts}}{{if eq .Destination "/opt/mia/MIA"}}{{.Source}}{{end}}{{end}}'`) and print `... running already, serving <that folder>`, with a warning when it differs from `ROOT`; same in `status`. Test in `ServedCheckout` with a dummy stage |
| R3 | `requirements.md` REQ-VPB-002: the AC was changed on the implementation branch (b825e8c) by the owner's decision D-157, with a history line but without an amendment number (A-50 had one) | Info | - | none, if the owner's decision counts as the approval; otherwise give it an A-number in the amendment list |

### Per-commit review (both directions, M42)
- 71d3743, 512ddff, 45c8e21, b22df4f (`tests/test_delivery_on_stack.py`): test code only; fixed argument lists, no shell; own project, tag and ports per run (`secrets.token_hex`, `free_port`); a volume left raises; skips without tools, images or the model server. 3597b9e: runbook text. Nothing outside the task.
- a9c62b6 (`speak.py`, `speech_stream.py`, `web_app.py:432`): outside the node, allowed by D-154. Correct: the end of the client's connection before the end marker (`_read_stream`) or while it waits for the reply (`_watch_close`) sets `cancelled`; `speak_chunks` waits on the event instead of sleeping and stops rendering; the handler sends no reply to a client that went away. `wait()` without `should_stop` behaves as before (one blocking `recv`). The watch thread sets `cancelled` also after a normal reply, when the connection closes; harmless (the stream is done). Tests mirror the A3 scenarios (Given/When/Then, `Example:`). No spec gap beyond R1.
- b825e8c (`sound.js`, requirements/test-spec AC, JS test): implements D-157 option (b); R1 is its only gap. IF-112 unaffected (the mark is in `initSound`, not in `VoicePlayer`).
- 76f02a0, 525e8f8, 5965fd8: tests and tooling; R2.
- Protected files: neither branch touches `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `contracts/`, `benchmarks/`, `stages.yaml`. The IF-112 contract, suite and mock are unchanged since re-verification 2 and equal `specs/mia/contract-drafts/`. The protected changes since f4da817 (IF-101 v14 and others) come only from the owner's install commits a262376, 424c329, 849ac36 (A-52..A-61), none of them in IF-112.

### Check results (reviewer's runs)
| Check | Result |
|---|---|
| `node --test "tests/js/*.test.mjs"` | 136 pass, 0 fail |
| contract suites `tests/acceptance/contract/*.mjs`, `tests/integration/N-1/*.mjs` | 35 tests: 18 pass, 0 fail, 17 skipped (IF-112 [real] and later N-1 steps) |
| Python in `localhost/mia:latest` (2bed302a3cd2), `--network none`, on a `git archive HEAD` copy | `test_speech_stop.py` 4 OK (3 runs), `test_converse_behaviours.py` 6 OK, `test_audio_router.py` 23 OK, `test_chat_page.py` 11 OK, `test_voice_lines.py` 8 OK, `test_speech_service.py` 9 OK, `test_frontend_delivery.py` 2 OK (1 skipped: no podman in the image), `test_testing_stages.py` 4 OK (1 skipped: no git in the image) |
| host | `test_testing_stages.py` 4 OK; `test_page_requests.py` 6 OK (28 s); `test_delivery_on_stack.py` 5 OK (127 s); no container of the tests left; the owner's `mia_*`, `mia-searxng` and `ollama` untouched |
| `trace_check.py` (N-1.3 lines) | ERROR no `## Scenarios` (F8); WARN IF-112, REQ-FE-011/012/013/026/030, REQ-VPB-001 (JS markers not read, N6); REQ-VPB-002, -003 no longer WARN (Python markers now). WARN TD-03, TD-04, TD-06 not listed: open deferrals of other nodes (A-26, D-160), none concerns N-1.3 |
| `test_doc_check.py` | the new or changed tests (`test_speech_stop.py`, the A3 test of `test_converse_behaviours.py`, `ServedCheckout`, the A4 browser test): 0 errors; `test_converse_behaviours.py:86,93,99` have errors from before this round |
| `check_sysml_model.py` | OK (REQ-VPB-002's `doc`, the requirement text, unchanged) |

### Owner's by-ear results (evidence, checklist section A)
A1 two tabs claim the voice: ok. A2 mute per device and the autoplay hint: ok. A3 Stop silences the voice: first run not ok (D-154), ok on the re-run after D-157 on the full app rebuilt from goal/v1. A4 a broken line file: first run not ok (served master's page, D-157), ok on the re-run from the goal-v1 worktree. All by the owner, 2026-10-31.

### Not checked
- Real audio, timing and the mouth by the reviewer (no sound device): covered by the owner's A1..A4.
- A3 end to end with real speech synthesis and a model (no model server allowed): covered by `test_speech_stop.py` (real speech process, recording speaker) and the owner's A3 re-run.
- IF-112 against the real player in the contract suite: open until the N-1 integration step (as before). CI stage log: none.
