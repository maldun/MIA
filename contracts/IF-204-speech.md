# IF-204 – Speech synthesis, v0

Owner (provider): N-2.5 Voice synthesis   Consumers: N-2.2 Chat agent   Decided by: N-2   Mock complexity: 2 (generated audio bytes)   Suite: `tests/acceptance/contract/test_if_204_speech.py`

Text in, audio out; the engine (Kokoro today) is behind this one interface and replaceable. Python calls; draft v0. The gateway relays the chunks to the browsers (IF-101 `audio_chunk`).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `synthesize(sentence)` | one sentence | `{"audio": bytes, "format": "wav", "spoken_text", "seconds"}` | markup and stage directions are removed first; `spoken_text` is what was synthesised |
| `voice_line(name)` | name of a voice line | `{"audio": bytes, "format": "wav"}` | the audio of a stored line |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| nothing left to speak after the filter | `ServiceError("empty_text")` | no audio |
| the engine is not available | `ServiceError("unavailable")` | no audio; the chat continues without voice |
| unknown or missing voice line | `ServiceError("no_line")` | no audio, nothing else affected |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| time to the audio of one sentence on the host | proposal: at most 2 s for 20 words, set in Plan | NFR-7 |

## Golden examples
1. Typical: `synthesize("Hello there.")` gives wav bytes and `spoken_text == "Hello there."`.
2. Failure: engine down gives `unavailable`; `voice_line("missing")` gives `no_line`.
3. Edge: `synthesize("<b>Hi</b> *smiles* there")` speaks "Hi there"; `synthesize("*smiles*")` is `empty_text`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft | 8 |
