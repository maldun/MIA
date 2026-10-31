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
