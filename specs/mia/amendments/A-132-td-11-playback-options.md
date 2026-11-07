# A-132 (Draft): Plan step of TD-11, the backend playback route of the chat agent's voice, and "Speak again"

Status: **Draft, written 2026-11-07 for owner review; nothing here is approved.** Decision id proposed: **D-277** (not logged). Follows D-275 (TD-11 narrowed) and D-276 (finding: "Speak again" does nothing). No model step is involved (agent-app additions: no eval criterion, suite or threat entry; the steps stay the existing ones). Everything below was read in the code, nothing was run. `contracts/`, `tests/` and the files of G-V2 and G-V3 are untouched.

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

| | **A: a backend playback pipeline on `SpeechService`** | **B: keep the sound server, make "Speak again" use it (recommended)** |
|---|---|---|
| What changes | The sound server and `SpeechStreamer` are replaced. A new part takes sentences, calls `SpeechService.synthesize` (one worker, to render ahead), writes the wav, assigns serials, calls `publish_audio`, and cancels on stop, for live answers and speak again. | `ChatService` gets one more injected function `speak(text, should_stop)`. `web_app.py` implements it with the existing `speak_answer` (`SpeechStreamer.finish` + `wait(should_stop)`). `stop()` also ends a speak-again playback. The page forgets the 3 s drop window when the user asks to speak again. |
| New parts / dependencies | One new part (the playback pipeline); `Speaker` (Kokoro, the voice effect) would have to live in the web app process or the pipeline would call the sound server's engine some other way. | None. |
| Interfaces | IF-204 needs ordering, pipelining and cancel (v1); IF-101 `audio_chunk` text (audio on the audio route) becomes true for the first time; the upload route (`/upload`, internal token) either stays or goes; IF-112 unchanged. | No contract text must change: IF-101 already says the audio follows on the audio route, IF-201 says `speak_again` gives `{"sentences": n}`. One optional clarifying sentence in IF-101 and IF-201 is proposed in section 8. |
| Effort (estimate, not measured) | 3 to 5 days: the pipeline, moving or sharing the engine, stop, repair, serials, a host test of every voice path, plus a Plan for the new part. | 0.5 to 1 day: `ChatService`, `web_app.py`, `sound.js`, three stage 1 or 2 tests, one node test. |
| Risk to the working voice | **High.** The proven rendering-ahead and cancel logic of `speak_chunks` would be replaced; the process split (engine in its own process) would change; every live answer is affected. | **Low.** Live answers use the unchanged route. Only a new caller (speak again) is added; if it fails, the chat continues without that voice (REQ-CHA-033). |
| What the user gets | The same voice as today, one engine path. No visible gain. | "Speak again" works, also after a Stop. |
| Hand test | Full: every live answer, stop in the middle, speak again, mute, two pages, a long answer, an engine failure. About 30 minutes, repeated after each fix. | Short: speak again, speak again during a live answer, stop during speak again, speak again right after a Stop. About 10 minutes. |
| What it leaves open | Nothing of TD-11. | TD-11 "through `SpeechService`" stays unmet; `SpeechService` stays a tested but unused interface. |

## 4. Recommendation

**B now; keep A as a narrowed TD-11 with no trigger date.** The only thing the user feels is that "Speak again" does not work (REQ-BE-006 is Verified but not met). B fixes that with no new part and no change to the live voice. A costs several days and puts the working voice at risk to give the user nothing visible; its only gain is one engine path, and nobody asked for that. If the owner wants A anyway, it needs its own Plan (the pipeline as a part with its requirements, an IF-204 v1 and a contract suite for ordering and cancel) before any code, which this paper does not provide.

Decisions for the owner: B or A; whether TD-11 stays open for A (and with which trigger), is dropped, or is replaced by a new deferral for the single engine path (section 9, question 2).

## 5. Requirements for option B (Drafts, ids chosen free on master and on the branches I looked at)

Ids: `REQ-CHA-030` to `REQ-CHA-034` in N-2.2 and `REQ-VPB-006` in N-1.3. The G-V3 goal records name the ids they will take only by node, so the parent session has to reserve `REQ-CHA-030` to `039`, `TC-CHA-030` to `039` and `REQ-VPB-006` to `009`, `TC-VPB-006` to `009` for TD-11 (they are the numbers after the highest ones on master, goal/v3 and goal/v2.convert today). The texts are in the node files, Status Draft:

- `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md`: REQ-CHA-030 speak again plays (the answer is spoken on the voice route), 031 order of the sentences, 032 stop ends it, 033 no voice route, no failure, 034 one speak again at a time (a speak again does not overlap the previous speak again; its order against the voice of a live answer is kept by the sound server, not by this requirement). New `## Groups` table (the file had none); old requirements keep no group, as before.
- `specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/requirements.md`: REQ-VPB-006 lines of a requested speak again are played also within 3 s of a stop. New `## Groups` table.

## 6. Checks and scenarios

The check rows and plain-language scenarios (Verifies / Given / When / Then) are in `test-spec.md` of N-2.2 (TC-CHA-030 to 035, new `## Scenarios` section) and of N-1.3 (TC-VPB-006). Summary:

| Check | Verifies | Level, stage | What |
|---|---|---|---|
| TC-CHA-030 | REQ-CHA-030, 031 | component, 1 | a stored answer of three sentences, a fake voice route: speak again hands the three spoken sentences over in order; the result and the events are as before |
| TC-CHA-031 | REQ-CHA-030 | component, 1 | the fake receives the stored text, not a repaired copy (the stored text is what the page shows, REQ-CHA-014) |
| TC-CHA-032 | REQ-CHA-032 | component, 2 | stop ends a speak again that is running, also when no answer is being generated |
| TC-CHA-033 | REQ-CHA-033 | component, 1 | the voice route fails: the result and the next chat message are unaffected, the failure is logged |
| TC-CHA-034 | REQ-CHA-034 | component, 2 | two speak again requests do not overlap |
| TC-VPB-006 | REQ-VPB-006 | component, 1 (`node --test`) | speak again within 3 s of a stop: the lines are enqueued |
| TC-CHA-035 | REQ-CHA-030, 032, 033, 034 | demonstration, 4 | hand test on the host (section 7) |

**Failing first (a finding gets a test first):** TC-CHA-030 is the test of the finding. Against today's code it fails by assertion: the fake voice route receives no sentence (`[] != [...]`) because `ChatService` has no `speak` and `speak_again` never calls one. Step 4 needs only a minimal stub (a `speak=None` keyword) so the test imports and then fails for the right reason, not with an `ImportError`. TC-VPB-006 is red for the same reason on the page side (the line is dropped inside the window).

## 7. Hand test on the host (TC-CHA-035, the checklist for the owner)

1. Start MIA in the venv, open the page on `localhost`, ask a question with three or more sentences, wait until it is spoken.
2. Press the 🔊 under the answer: the same answer is spoken again, in order, in the same voice.
3. Press 🔊 while a new answer is being spoken: the live voice is not cut; the speak again follows after it.
4. Press 🔊, then Stop while it speaks: it ends within about a second and nothing is spoken afterwards.
5. Press Stop while an answer is spoken, then press 🔊 within 3 s: it is spoken (no silent drop).
6. Mute the page, press 🔊: nothing is heard and the next answer speaks normally after un-muting.
7. Stop the sound server (or kill its process), press 🔊: the chat continues, the next message gets an answer; the log has one error line.

## 8. Contract text (proposal, optional; `contracts/` untouched)

Not required for B. If the owner wants the realization written down:
- IF-101, row `speak_again`, Notes: "one `audio_chunk` per sentence to every connected page; the answer is also spoken on the voice route (the audio follows on the audio route); 404 unknown id".
- IF-201, row `speak_again`, Notes: the same sentence.
Each is a version bump (IF-101 v16, IF-201 v3) and a change of a protected contract text, so it is an amendment decided by the owner. **Overlap:** G-V3.PANEL owns the IF-101 amendment alone and G-V3.CHAT amends IF-201. The text above must be given to them as an extra line of their amendments, or applied in a separate small bump before theirs; two separate bumps of the same contract in two branches would conflict.

## 9. Where TD-11 meets G-V3 (read-only look at `goal/v3`)

| Point | G-V3 says | What must be agreed |
|---|---|---|
| The voice path | G-V3 and A-131: "the voice path stays as it is"; every chat text is spoken as today; TD-11 independent. | Option B keeps this true for live answers. |
| "Speak again" of a short spoken summary | In G-V3 the chat holds only spoken texts (summaries, questions). "Speak again" under such a message must play it too. | REQ-CHA-030 is about "any answer" (IF-201 `speak_again` takes any answer id); G-V3.CHAT has to name it in its scope so that its new message kinds (summary, question) are answers for this purpose. |
| IF-101 / IF-201 text | PANEL owns the IF-101 amendment, CHAT amends IF-201. | The optional lines in section 8, as above. |
| `ChatService` | G-V3 changes the chat events and removes the status card. | Option B touches `ChatService.__init__` (one parameter), `speak_again` and `stop`. G-V3 may touch the same functions; whoever merges second rebases. |
| `sound.js` / `app.js` | PANEL builds the Skill run view in the page. | REQ-VPB-006 touches only the voice code (`sound.js`, one call in `chat.js` for the 🔊 action). Low overlap; note it for PANEL. |
| TC-CHA-006, REQ-CHA-006 | G-V3 does not change them. | They stay; TC-CHA-030 to 035 add the check that was missing. |

## 10. Plausibility (proposals only; people rate; `plausibility.yaml` untouched)

| Requirement | Proposed | Basis (read, not measured) |
|---|---|---|
| REQ-CHA-030, 031 | plausible | `speak_answer(text)` in `web_app.py` already runs `SpeechStreamer.finish` and `wait`; it is the route live answers use. |
| REQ-CHA-032 | plausible | `SpeechStreamer.wait(should_stop)` closes the socket and `SoundHandler._watch_close` sets `cancelled`; this is the mechanism of the existing chat stop (owner check A3). The new part is that `stop()` today does nothing when no answer runs. |
| REQ-CHA-033 | plausible | `SpeechStreamer` already catches `OSError` and logs it. |
| REQ-CHA-034 | plausible | A lock around the voice call of speak again is plain code. Against a live answer, `SoundServer` is a single-threaded `TCPServer`, so a second connection waits for the first handler; that is read from the class, not observed, and is not part of this requirement. The hand test step 3 observes it. |
| REQ-VPB-006 | plausible | `stoppedAt` is a plain variable in `initSound`; clearing it on the speak-again action is one line. |

No number is introduced, so there is no measured reference to give; a time limit for "ends within about a second" is deliberately **not** a requirement (the poll interval is 0.2 s and the engine's sentence in progress finishes; the hand test only observes it). If the owner wants a limit, it needs a measurement on the host first.

## 11. Open questions for the owner (to turn into a questionnaire)

1. Option B (recommended) or A.
2. Under B: TD-11's remaining target "through `SpeechService`" is kept open without a trigger date, dropped, or replaced by a new deferral for a single engine path?
3. Is `speak_again` while an answer is being generated queued behind the live voice (proposed, REQ-CHA-034) or refused?
4. If the voice route is down: silent with a log line (proposed, REQ-CHA-033) or a visible note on the page?
5. Add the optional one-sentence clarifications to IF-101 and IF-201 (section 8), and who applies them (G-V3 amendment lines or a separate bump)?
6. Reserve the id ranges of section 5 for TD-11 (parent session).
7. Is the hand test of TC-CHA-035 enough, or should a smoke test on the stack follow (the stack has no sound server today; see TD-24 and TD-25 for the same gap)?

## 12. What Step 4 (red tests) would need

- A dedicated session, not the implementing one; the minimal stub `ChatService(..., speak=None)` so the tests import.
- Under `tests/` (not `tests/acceptance/`, `helpers/` or `smoke/` unless the owner moves the checks there): `tests/test_chat_speak_again.py` for TC-CHA-030 to 034 with a fake voice route (records sentences and honours `should_stop`), and `tests/js/sound-speak-again.test.mjs` for TC-VPB-006 on the fake DOM of `tests/js/fake-dom.mjs`. A new fake in `tests/helpers/` would need the owner's approval as before (D-272, D-274).
- The hand-calculated check for TC-CHA-030: three sentences "A. B. C." give exactly three hand-over calls with the texts `A.`, `B.`, `C.` in that order.
- `stages.yaml` rows for the six new checks; `plan.md` with two or three tasks (ChatService and stop; `web_app.py` wiring; `sound.js`), the third independent of the first two.
- The existing suites that must stay green: `tests/test_chat_answers.py` (TC-IF-201-06), `tests/test_speech_*.py`, the IF-204 and IF-201 contract suites, `node --test`.
