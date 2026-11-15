# A-130: the skipped IF-101 and IF-201 cases of an answer (TD-11, REQ-VOI-001)

Status: **Draft; not approved as a whole, nothing applied.** Owner decisions so far (2026-11-07): Q1 split the `expression` event out of TD-11 (decided); Q2 helper change not approved yet (pending); Q3 new TD-11 target wording proposed, awaiting the owner's decision. Decision id proposed: D-268 (master's last is D-267; not yet in `review-log.md`, log it on approval). Owner answers of 2026-11-07 behind it: the protected `tests/helpers/contract.py` may change only through an amendment the owner approves first; `audio_chunk` stays text, the page keeps the voice; Plan step only.

## 1. Does text-only `audio_chunk` need a contract change?
**No.** IF-101 v15 (line 79) already defines `audio_chunk` as `{id, index, sentence}`, one per sentence, `index` from 0, in order, "the audio bytes follow on the audio route". IF-201 (`subscribe`, golden 1) gives the same payloads. IF-204 is Python calls only (`synthesize`, `voice_line`); the gateway relays chunks "(IF-101 `audio_chunk`)" and the page plays voice lines through `audio_reload` and `/audio/<file>` (v15). So the contract texts of IF-101, IF-201 and IF-204 stay as they are. The gap is in the real `ChatService`, not in the contracts.

## 2. What the real code does today (read, not run)
- `chat_service.py` emits `audio_chunk` only in `speak_again` (line 383). During an answer (`chat_start`, `chat_delta`, `chat_done`) it emits **no** `audio_chunk`, and it emits **no** `expression` event at all (the expression goes through `web_app.py`: `on_emotion`, `PresetExpressor`).
- The chat voice runs through `SpeechStreamer` and `Speaker.render_voice` (`web_app.py:406`); `SpeechService` (IF-204) is used by tests only.

## 3. Which skips are replaced by what
All skips are `raise unittest.SkipTest(...)` in the protected helper, gated on a scripted answer that has an `emotion`:

| Place in `tests/helpers/contract.py` | Skips | Replaced by | Needs |
|---|---|---|---|
| line 205, `_RealBackendAdapter` (IF-101 real) | TC-IF-101-04 (`test_an_answer_streams_to_every_connected_user`) | no skip: the real `ChatService` run through the routes | per-sentence `audio_chunk` during an answer **and** the `expression` event |
| line 431, `_ChatTurnAdapter` (IF-201 real) | TC-IF-201-01 (`test_an_answer_is_delivered_as_events`) | no skip: the real `ChatService` with a scripted model | per-sentence `audio_chunk` during an answer (this test checks no `expression`) |
| line 410, `__getattr__` "not in the real Backend yet" | any other operation not built | unchanged, not part of TD-11 | – |
| line 402, `run_with_variant` | REQ-CHV-008 | unchanged, not part of TD-11 | – |

**Mismatch with the TD-11 record:** its target names "the skipped cases of IF-201 and IF-101", but they are gated on `emotion`, so the IF-101 case also needs the `expression` event of an answer. That is not voice. It belongs to the character (REQ-CHV, N-1.2 / N-2.2 "answer as a stream of sentences with expression events"). TD-11 alone can turn only TC-IF-201-01 green; TC-IF-101-04 stays skipped until the expression event is also built. The reason texts of both skips say "N-2.5", which is also not exact for the expression part.

## 4. Proposed implementation shape (for the Implement phase, after approval)
1. `ChatService` emits `audio_chunk` per finished sentence of the streamed answer, with the text filtered by `speech_text` (as `speak_again` does), no payload change.
2. The backend path of the chat agent's voice (`web_app.py`) takes its audio from `SpeechService.synthesize` instead of calling `SpeechStreamer` and `render_voice` directly. This is wiring inside N-2; no new part (SpeechService exists), no new dependency, no interface change. Risk (from TD-11): the working voice. Mitigation: `test_speech_service.py`, `test_speech_stop.py`, `test_speech_repair.py`, the page tests; hand test on the host.
3. The expression event of an answer: separate question, see below.

## 5. Protected helper (**approved by the owner, Stefan Reiterer, 2026-11-07, as drafted (D-272); not yet applied**: `tests/helpers/` untouched)
- Line 431: remove the skip for an answer with `emotion` in `_ChatTurnAdapter` once step 4.1 is green (the adapter already builds the real `ChatService`).
- Line 205: remove the skip in `_RealBackendAdapter` only when step 4.1 and the expression event are green; until then narrow the reason text to "the `expression` event of an answer is not in the real Backend yet" so that it no longer names N-2.5 and voice.
- No test file under `tests/acceptance/` changes; the new versions are written outside the implementing session after approval.

## 6. Requirements and test rows
None needed. REQ-VOI-001 (Relaxed TD-11, with its Target), REQ-BE-016, the N-2.2 requirement "stream of sentences with expression events", TC-VOI-001, TC-IF-201-01 and TC-IF-101-04 already cover the behaviour. The approved text of REQ-VOI-001 is not touched. If the owner wants the per-sentence emission of a live answer stated on its own, that is a new requirement for the owner to ask for.

## 7. Owner decisions
1. **Decided (owner, 2026-11-07):** the `expression` event of an answer is split out of TD-11. TD-11 covers only TC-IF-201-01; TC-IF-101-04 stays skipped with a narrower reason (section 5, line 205, pending approval).
2. **Decided and applied (owner, 2026-11-07, D-272, D-274):** the helper change of section 5 and a second one (dict form of the scripted answer of the IF-201 adapter), `161d156` and `36aa640`.
3. **Superseded by D-275 (owner, 2026-11-07):** step 2 (playback through `SpeechService`) turned out to be a new playback pipeline, not wiring; TD-11 stays open narrowed to that route and needs a Plan step. The wording below is kept for the record; the Target in `deferred.md` follows D-275, not this text. Proposed new target of TD-11 and of the `Target:` line of REQ-VOI-001:
   > the chat agent emits one `audio_chunk` event per sentence during an answer, its voice audio comes from `SpeechService` (IF-204) on the backend path, and the skipped IF-201 case TC-IF-201-01 runs green; the IF-101 case TC-IF-101-04 stays skipped until the expression event of an answer exists (TD-60)

## 8. Proposed deferral for the expression event (Draft, proposed only)
The `expression` event of an answer is not emitted by the real `ChatService` (the expression goes through `web_app.py`). It needs its own deferral or goal; the owner chooses. If a deferral, a draft from the parent range:

- TD-60 (**Draft, proposed, not in `deferred.md`**) – The real chat agent does not emit the `expression` event of an answer
- Kind: defer
- Requirement: the N-2.2 requirement "answer as a stream of sentences with expression events"; IF-101 `expression`; related REQ-CHV (character)
- Interim criterion: expressions reach the page through `web_app.py` (`on_emotion`, `PresetExpressor`)
- Target: `ChatService` emits `expression {name}` during an answer; the skip at `tests/helpers/contract.py:205` is removed and TC-IF-101-04 runs green
- Decision: open (owner)
- Status: Draft
