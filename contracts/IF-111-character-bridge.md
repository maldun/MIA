# IF-111 – Character bridge, v0

Owner (provider): N-1.2 Character view   Consumers: N-1.1 Chat and login views   Decided by: N-1   Mock complexity: 2 (a fake character that keeps its last state)   Suite: `tests/acceptance/contract/test_if_111_character_bridge.test.mjs` (`node --test`)

The wire between the chat page and the character iframe. Draft v0 from today's `templates/static/chat/character.js` (`postMessage` of JSON strings on the same origin); additions are marked **[new]**.

## Messages
Page to character (`character.receive(jsonString, origin)`):
| type | fields | effect |
|---|---|---|
| `expression` | `name` | the character shows the preset; an unknown name falls back to `neutral` |
| `speaking` | `value` bool | the mouth moves while true (the page repeats it while a line plays) |
| `viewport_inset` | `left, right, top, bottom, width, height` | the area covered by the chat; negative values count as 0 |
| `view` | `name` | camera view |
| `background` | `name` | background |
| `variant` **[new]** | `name` or null | outfit variant; null = the chat's variant |
| `model` **[new]** | `name` | load a VRoid model |

Character to page (callback `onMessage(jsonString)`):
| type | fields | meaning |
|---|---|---|
| `ready` | | loaded; sent once; the page then sends the current view and inset |
| `failed` **[new]** | `reason` | cannot load (no WebGL, export missing); the page hides the iframe |
| `unmapped` **[new]** | `presets[]`, `gestures[]` | after `model`: what the new model cannot map |

## Errors
| Condition | Behaviour | What the consumer may rely on afterwards |
|---|---|---|
| message from another origin or from another window | ignored | state unchanged |
| not valid JSON, or an unknown `type` | ignored, no exception | state unchanged |
| load failure | `failed` once | the chat keeps working without the iframe |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| time from iframe load to `ready` | at most 15 s, else the page treats it as failed (`LOAD_TIMEOUT_MS`) | REQ-FE-006 |
| frame rate while shown | 30 fps or more on a mid-range phone, 60 on desktop | NFR-7 |

## Golden examples
1. Typical: after `ready`, `expression {name: "happy"}` shows happy; `speaking {value: true}` then `false` moves and stops the mouth.
2. Failure: a load failure sends `failed`; messages afterwards change nothing and cause no error.
3. Edge: an expression `nonsense` shows `neutral`; a message with a foreign origin or `{not json` is ignored; `viewport_inset` with `left: -5` counts as 0.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from character.js | – |
