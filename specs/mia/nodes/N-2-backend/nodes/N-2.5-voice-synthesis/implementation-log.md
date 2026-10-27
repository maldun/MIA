# Implementation log: Voice synthesis (N-2.5)

## T-01 Speech per sentence and markup filtering (2026-10-27) – partly done
- Built: `speech_service.py` (`SpeechService.synthesize` / `voice_line`, `SpeechError` with the codes of IF-204) on top of the existing `Speaker.render_voice`; `speech_text.py` now removes html tags.
- Finding: `speech_text("<b>Hi</b> *smiles* there")` spoke the tags (IF-204 golden 3). Test: `tests/test_speech_service.py::SpeechTextMarkupTest`.
- Tests (feedback only): `tests/test_speech_service.py` 7 green; `test_speech_text`, `test_speech_repair`, `test_voice_lines` green in the image.
- **Open, needs an amendment (protected):** (1) `tests/helpers/contract.py` has no `real_subject` for IF-204 (`REAL_NOT_READY` still lists it), so the `_real` cases of `test_if_204_speech.py` still skip; an adapter must map `SpeechError` to the mock's `ServiceError` and use a fake Speaker plus a `hello.wav` line. (2) TC-VOI-001/-002 do not exist as test files; the unit tests above cover AC-13 but carry no TC marker. (3) `SpeechStreamer` still sends sentences to the sound server, not through `SpeechService`: wiring waits for the N-2.2/N-2.5 integration.

## T-02 Voice lines (2026-10-27)
- Existing code already met the two criteria of REQ-VOI-003 for `VoiceLines` (`pick` skips and logs a missing file, `uncovered` is empty for the real mood map: `tests/test_voice_lines.py`), so it is unchanged.
- Gap found: `SpeechService.voice_line` ignored the mood map. Now `SpeechService(speaker, folder, lines=VoiceLines)` delivers the audio of a picked file; silent or unknown mood = `no_line`. Tests: `MoodLineDeliveryTest` in `tests/test_speech_service.py`.
- Open: `web_app.py` does not create a `SpeechService` yet; nothing calls it until the N-2.2/N-2.5 integration. TC-VOI-003 has no marker file (see T-01).

## T-03 Default voice lines generated (2026-10-27)
- `tools/make_voice_lines.py` renders `library/voice_line_texts.json` (owner's texts for 9 moods; spelling fixed: Hooray, embarrassed, plain apostrophe) with `Speaker` (Kokoro + voice effect) into `voice/expressions/<mood>_default.wav` and lists them in `library/voice_lines.json`. Tests: `tests/test_make_voice_lines.py` (fake Speaker; written after the code, the delegated version failed twice).
- The wavs are made on the host (models and `setup_cfg.json` are not in a worktree) and are untracked like all of `voice/`; the texts file is the provenance for REQ-VOI-004.
- Open: `annoyed.wav` and the other old clips of `voice/expressions` have no recorded origin; the owner says whether `annoyed` is ours or should get a generated text too (then add it to the texts file).
