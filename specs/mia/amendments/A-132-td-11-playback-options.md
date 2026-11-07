# A-132 (Draft): Plan step of TD-11, the backend playback route of the chat agent's voice, and "Speak again"

Status: **owner chose option B (2026-11-07, D-277); Draft requirements pending review. Nothing here is approved as a whole.** Decision ids: **D-277** (option B, the replacement of TD-11) and **D-278** (the follow-up answers: speak again for any message of MIA, TD-61 confirmed, the mock server, TD-11 dropped), both logged in `review-log.md`. Follows D-275 (TD-11 narrowed) and D-276 (finding: "Speak again" does nothing). No model step is involved (agent-app additions: no eval criterion, suite or threat entry; the steps stay the existing ones). Everything below was read in the code, nothing was run. `contracts/`, `tests/` and the files of G-V2 (except one note in `parallel-work.md`) and G-V3 are untouched.

## 1. The question

TD-11 as narrowed by the owner: the playback of the chat agent's voice goes through `SpeechService` (IF-204) instead of `SpeechStreamer` and the sound server, with the order of sentences, stop, speak again and repair (REQ-CHA-014) kept. D-276 added the finding that "Speak again" has no effect at all. What does Plan have to decide so that both can be checked?

## 2. What the route is today (read, not run)

| Step | Where | What happens |
|---|---|---|
| 1 | `web_app.py` `converse` (about line 406) | A `SpeechStreamer` is made for each answer. `update(text)` sends every finished sentence (the last one is held back), after `repair(settle(text))` (REQ-CHA-014); `finish(text)` sends the rest and an end marker. |
| 2 | `speech_stream.py` | A TCP client of the sound server on `SOUND_PORT`: one JSON line per sentence, `STREAM_REQ`, then `STREAM_END_REQ`. `wait(should_stop)` polls every 0.2 s and closes the connection when the chat is stopped. |
| 3 | `speak.py` `SoundServer` (a plain `socketserver.TCPServer`, one connection at a time) and `SoundHandler` | `Speaker.speak_chunks` renders the next sentence with Kokoro and the voice effect while the previous one plays. A closed connection sets `cancelled`: the waiting sentences are not rendered or played. |
| 4 | `Speaker.play_voice` → `play_media.play_sound(url=...)` | The rendered wav is **uploaded** with `requests.post` and the internal token to the web app (`/upload`). |
| 5 | `web_app.py` `publish_audio` | The file becomes `line-<serial>.wav` (12 kept) and `AudioRouter.announce` sends `audio_reload {url, serial}` to the one page that owns the voice. |
| 6 | `templates/static/chat/sound.js` | `VoicePlayer` (IF-112) queues the lines, plays them one after the other, stops on Stop. After a Stop, `audio_reload` is ignored for `STOP_DROP_MS` = 3000 ms unless a `chat_start` comes first. |

`SpeechService.synthesize` (IF-204) is **not** on this route. It is one sentence in, wav bytes out, with no playing, no ordering, no pipelining and no cancel; nothing outside tests calls it. The `audio_chunk` event (IF-101 line 79: "the audio bytes follow on the audio route") carries the sentence text only; since A-130 step 4.1 `ChatService` emits it per sentence during a live answer, and no page code handles it.

**Why "Speak again" does nothing (D-276, now explained):** `ChatService.speak_again` (chat_service.py line 378) only emits `audio_chunk` events. Live answers are spoken through steps 1 to 6; "Speak again" never enters step 1. REQ-BE-006 and REQ-CHA-006 already say "two requests give a new answer and a new audio stream" (status Verified), but their check, TC-CHA-006 and `tests/test_chat_answers.py`, only counts the events. So a Verified requirement is not met in use; this is a gap in the check, not a new requirement.

A second, hidden fault of the same button: after a Stop, the page drops every `audio_reload` for 3 s (sound.js line 210). "Speak again" within 3 s after a Stop would therefore stay silent even when the backend plays.

## 3. The options

| | **A: a backend playback pipeline on `SpeechService`** | **B: keep the sound server, make "Speak again" use it (chosen)** |
|---|---|---|
| What changes | The sound server and `SpeechStreamer` are replaced. A new part takes sentences, calls `SpeechService.synthesize` (one worker, to render ahead), writes the wav, assigns serials, calls `publish_audio`, and cancels on stop, for live answers and speak again. | `ChatService` gets one more injected function `speak(text, should_stop)`. `web_app.py` implements it with the existing `speak_answer` (`SpeechStreamer.finish` + `wait(should_stop)`). `stop()` also ends a speak-again playback. The page forgets the 3 s drop window when the user asks to speak again. |
| New parts / dependencies | One new part (the playback pipeline); `Speaker` (Kokoro, the voice effect) would have to live in the web app process or the pipeline would call the sound server's engine some other way. | None. |
| Interfaces | IF-204 needs ordering, pipelining and cancel (v1); IF-101 `audio_chunk` text (audio on the audio route) becomes true for the first time; the upload route (`/upload`, internal token) either stays or goes; IF-112 unchanged. | **None** (owner, D-277: contracts unchanged). IF-101 already says the audio follows on the audio route; IF-201 says `speak_again` gives `{"sentences": n}`. |
| Effort (estimate, not measured) | 3 to 5 days: the pipeline, moving or sharing the engine, stop, repair, serials, a host test of every voice path, plus a Plan for the new part. | 1 to 1.5 days: `ChatService`, `web_app.py`, `sound.js`, the stage 1 and 2 checks of section 6, one node test, one browser check with a small addition to the mock. |
| Risk to the working voice | **High.** The proven rendering-ahead and cancel logic of `speak_chunks` would be replaced; the process split (engine in its own process) would change; every live answer is affected. | **Low.** Live answers use the unchanged route. Only a new caller (speak again) is added; if it fails, the chat continues without that voice (REQ-CHA-033). |
| What the user gets | The same voice as today, one engine path. No visible gain. | "Speak again" works, also after a Stop. |
| Hand check | Full: every live answer, stop in the middle, speak again, mute, two pages, a long answer, an engine failure. About 30 minutes, repeated after each fix. | Short (TC-CHA-035, about 5 minutes): only what automation cannot hear (section 7). |
| What it leaves open | Nothing of TD-11. | The single voice path: moved to the new deferral **TD-61** (section 9). |

## 4. Decision (owner, 2026-11-07, D-277)

**B now.** The rest of TD-11 is replaced by a new deferral for a single engine path, **TD-61** (draft in `deferred.md`: target one voice path; the app has two today, the sound server and `SpeechService`). TD-11 is closed (Status **dropped**, `Closed:` names TD-61, D-275 and D-277; owner, D-278). TD-61 is **confirmed as drafted** (trigger and effort), Status open (D-278). `REQ-VOI-001` keeps its text and `Target:`; only its `Relaxed:` marker moves from TD-11 to TD-61, with a History line (an approved requirement's marker; flagged for the owner here and in the report).

## 5. Requirements for option B (Drafts)

Ids: `REQ-CHA-030` to `REQ-CHA-034` in N-2.2 and `REQ-VPB-006` in N-1.3. The owner reserved `REQ-CHA-030..039`, `TC-CHA-030..039`, `REQ-VPB-006..009` and `TC-VPB-006..009` for TD-11 (row in `specs/mia/goals/G-V2/parallel-work.md`). Texts in the node files, Status Draft:

- `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md`: REQ-CHA-030 speak again is spoken (any message of MIA with an id: an answer, a spoken summary, a question of a skill; owner Q8), 031 order of the sentences, 032 stop ends it, 033 no voice route: silent, one log line, no new text (owner Q4), 034 a speak-again during a live answer, or another speak-again, waits behind it (owner Q3). New `## Groups` table.
- `specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/requirements.md`: REQ-VPB-006 lines of a requested speak again are played also within 3 s of a stop. New `## Groups` table.

## 6. Checks and levels (owner Q7: automate "events and page only"; real sound stays a short hand check)

| Check | Verifies | Level, stage | What |
|---|---|---|---|
| TC-CHA-030 | REQ-CHA-030, 031 | component, 1 | a stored answer of three sentences and a stored question of a skill, a fake voice route: speak again hands over the spoken sentences in order; result and events as before |
| TC-CHA-031 | REQ-CHA-030 | component, 1 | the fake receives the stored text after the speech filter |
| TC-CHA-032 | REQ-CHA-032 | component, 2 | stop ends a speak again that is running, also when no answer is being generated |
| TC-CHA-033 | REQ-CHA-033 | component, 1 | the voice route fails: result and next message unaffected, one log line, nothing new for the page |
| TC-CHA-034 | REQ-CHA-034 | component, 2 | two speak-again requests do not overlap |
| **TC-CHA-036 (new level)** | REQ-CHA-031, 032, 034 | component, 2 | the hand-over to the sound server: the real `SoundServer` and `SoundHandler` on a localhost port, real TCP clients, a **fake sink** instead of the engine: order of sentences, a second request queued behind the first, a closed connection cancels the rest. Confirms by observation what the plausibility table (section 10) only read from the code. |
| TC-VPB-006 | REQ-VPB-006 | component, 1 (`node --test`) | speak again within 3 s of a stop: the lines are enqueued (real `sound.js` on `tests/js/fake-dom.mjs`, fake clock) |
| **TC-VPB-007 (new level)** | REQ-VPB-006 | component (browser), 2 | the existing browser harness (`tests/browser/`, Chromium, the chat mock server) **fits with a small addition**: the mock sends `audio_reload {url, serial, message}` after the speaker button and serves a short wav; the driver checks the page's audio element. The mock is test tooling under `ui/tools/`, not protected; the owner allows Step 4 to change `ui/tools/chat_mock_server.py` for this check (D-278). |
| TC-CHA-035 | REQ-CHA-030, 032 | demonstration, 4 | **shortened** hand check on the host (section 7) |

`stages.yaml` needs no new step: stage 1 `unit` and `js` find `tests/test_*.py` and `tests/js/*.test.mjs` by pattern; the two stage 2 Python checks run in the existing `unit` discover run (the browser one is skipped, never passed, where podman or the images are missing, like the other browser checks). No smoke test now (owner Q7).

**Failing first (a finding gets a test first):** TC-CHA-030 is the test of the finding. Against today's code it fails by assertion: the fake voice route receives no sentence (`[] != [...]`) because `ChatService` has no `speak` and `speak_again` never calls one. Step 4 needs only a minimal stub (a `speak=None` keyword) so the test imports and then fails for the right reason. TC-VPB-006 and TC-VPB-007 are red for the same reason on the page side (the line is dropped inside the window). TC-CHA-036 is a characterization of today's server and is expected green from the start; if it is red, that is a finding about the sound server (queue or cancel), reported before any fix.

## 7. The short hand check (TC-CHA-035, only what automation cannot hear)

1. Start MIA in the venv, open the page on `localhost`, ask a question with three or more sentences, wait until it is spoken.
2. Press the speaker button under the answer: the same answer is heard again, in order, in the same voice.
3. Press the speaker button, then Stop while it speaks: it ends within about a second and nothing is heard afterwards.
4. Press Stop while an answer is spoken, then the speaker button within 3 s: it is heard (no silent drop).

Order, the queue behind a live answer, the failing route and mute are checked automatically (TC-CHA-030 to 034, 036, TC-VPB-006, 007) and are not part of the hand check.

## 8. Contracts (owner Q5)

**Unchanged.** TD-11 touches no contract: IF-101 line 79 already says the audio bytes follow on the audio route, IF-201 `speak_again` is unchanged. The optional clarifying sentences of the first draft are dropped. No overlap with the IF-101 amendment of G-V3.PANEL or the IF-201 amendment of G-V3.CHAT remains at the contract level.

## 9. Where TD-11 meets G-V3 (read-only look at `goal/v3`)

| Point | G-V3 says | What must be agreed |
|---|---|---|
| The voice path | G-V3 and A-131: "the voice path stays as it is"; every chat text is spoken as today; TD-11 independent. | Option B keeps this true for live answers. |
| "Speak again" of a spoken summary or a question of a skill | In G-V3 the chat holds only spoken texts (summaries, questions). | Settled by the owner (Q8): any message of MIA with an id counts. G-V3.CHAT only has to give its new messages an id and a stored text. |
| `ChatService` | G-V3 changes the chat events and removes the status card. | Option B touches `ChatService.__init__` (one parameter), `speak_again` and `stop`. G-V3 may touch the same functions; whoever merges second rebases. |
| `sound.js` / `chat.js` | PANEL builds the Skill run view in the page. | REQ-VPB-006 touches only the voice code (`sound.js`, one call in `chat.js` for the speaker action). Low overlap; note it for PANEL. |
| TD-61 | Not in G-V3. | A voice-path merge would conflict with a G-V3 change of how chat texts are spoken; it is planned only after G-V3. |

## 10. Plausibility (proposals only; people rate; `plausibility.yaml` untouched)

| Requirement | Proposed | Basis (read, not measured) |
|---|---|---|
| REQ-CHA-030, 031 | plausible | `speak_answer(text)` in `web_app.py` already runs `SpeechStreamer.finish` and `wait`; it is the route live answers use. |
| REQ-CHA-032 | plausible | `SpeechStreamer.wait(should_stop)` closes the socket and `SoundHandler._watch_close` sets `cancelled`; this is the mechanism of the existing chat stop (owner check A3). The new part is that `stop()` today does nothing when no answer runs. |
| REQ-CHA-033 | plausible | `SpeechStreamer` already catches `OSError` and logs it. |
| REQ-CHA-034 | questionable until TC-CHA-036 ran | A lock around the voice call covers two speak-again requests. Against a live answer the queue rests on `SoundServer` being a single-threaded `TCPServer` (a second connection waits for the first handler), read from the class and not observed. Probe: TC-CHA-036, which runs the real server with a fake sink; it decides the rating before approval. |
| REQ-VPB-006 | plausible | `stoppedAt` is a plain variable in `initSound`; clearing it on the speak-again action is one line. |

No number is introduced, so there is no measured reference to give; a time limit for "ends within about a second" is deliberately **not** a requirement (the poll interval is 0.2 s and the engine's sentence in progress finishes; the checks use generous test limits).

## 11. Decided (owner, D-277) and what is still open

Decided: Q1 option B; Q2 TD-11 replaced by TD-61 (single engine path); Q3 speak again during a live answer is queued; Q4 route down: silent, one log line, no new text; Q5 contracts unchanged; Q6 id ranges reserved; Q7 automation levels as in section 6, no smoke test; Q8 any message of MIA with an id.

Decided in the follow-up (D-278): Q8 means any message **of MIA** with an id (answers, spoken digests, skill questions); a message of a user stays `not_found` (IF-201, TC-IF-201-06) and contracts stay unchanged. TD-61 is accepted as drafted, trigger and effort included (status open). Step 4 may change `ui/tools/chat_mock_server.py` for TC-VPB-007. TD-11 is dropped (not done), replaced by TD-61.

No open question is left for this Plan step; the Draft requirements REQ-CHA-030 to 034 and REQ-VPB-006, the checks and the test requirements still wait for the batched review.

## 12. What Step 4 (red tests) would need

- A dedicated session, not the implementing one; the minimal stub `ChatService(..., speak=None)` so the tests import.
- New files under `tests/` (not `tests/acceptance/`, `helpers/` or `smoke/` unless the owner moves the checks there): `tests/test_chat_speak_again.py` (TC-CHA-030 to 034, a fake voice route), `tests/test_sound_server_handover.py` (TC-CHA-036, the real server with a fake sink on a free localhost port), `tests/js/sound-speak-again.test.mjs` (TC-VPB-006, fake DOM, fake clock), `tests/test_speak_again_browser.py` with a driver in `tests/browser/` (TC-VPB-007). A new fake in `tests/helpers/` would need the owner's approval as before (D-272, D-274).
- The hand-calculated check for TC-CHA-030: "One. Two. Three." gives exactly three hand-over calls with `One.`, `Two.`, `Three.` in that order; TC-CHA-036: client 1 `One.`, `Two.`, `Three.`, client 2 `Four.` give the sink order `One.`, `Two.`, `Three.`, `Four.`.
- `plan.md` with three or four tasks (ChatService and stop; `web_app.py` wiring; `sound.js`; the mock server for TC-VPB-007), the page task independent of the others.
- The existing suites that must stay green: `tests/test_chat_answers.py` (TC-IF-201-06), `tests/test_speech_*.py`, the IF-204 and IF-201 contract suites, `node --test`.
