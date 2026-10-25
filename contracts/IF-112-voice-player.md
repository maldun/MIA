# IF-112 – Voice player, v0

Owner (provider): N-1.3 Voice playback   Consumers: N-1.1 Chat and login views   Decided by: N-1   Mock complexity: 3 (a queue with a clock and a blocked-autoplay state)   Suite: `tests/acceptance/contract/test_if_112_voice_player.test.mjs` (`node --test`)

Playing the voice in this browser. Draft v0 from today's `templates/static/chat/sound.js` (`LineQueue`, `audio_claim`, `audio_owner`, `audio_reload`).

## Operations
| Name | Input | Output | Notes |
|---|---|---|---|
| `enqueue(line)` | `{id, url, serial}` | | lines play one after the other in arrival order; a new line never cuts the playing one |
| `mute(value)` | bool | | silences this device only; queued lines are dropped while muted |
| `stop()` | | | ends the playing line and clears the queue |
| `claim()` | | | this page asks to be the one that plays (at most every 3 s); the server answers `audio_owner` |
| `setOwner(value)` | bool | | the answer to `claim`; a page that is not the owner stays silent |
| `onSpeaking(callback)` | `callback(bool)` | | true when the first line starts, false when the queue is empty; the page repeats "speaking" to the character while true |
| `allowAutoplay()` | | | called after a user gesture; plays the line that was held back |

## Errors
| Condition | Behaviour | What the consumer may rely on afterwards |
|---|---|---|
| the browser blocks autoplay | the line is put back in front and `onBlocked` is called | the line plays after `allowAutoplay()`, nothing is lost |
| a line cannot be loaded | it is skipped and `onLineError(id)` is called | the next line plays |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| gap between lines | no overlap of two lines | REQ-FE-011 |
| `claim` rate | at most one per 3 s | `CLAIM_EVERY_MS` in sound.js |

## Golden examples
1. Typical: three lines enqueued play in order; `onSpeaking` gives true once and false once at the end.
2. Failure: a muted device plays nothing, a second device still plays.
3. Edge: autoplay blocked holds the first line; after `allowAutoplay()` all three play in order; `stop()` clears the rest and gives false.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from sound.js | – |
