# Implementation log: Character view (N-1.2)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 One expression API, mood map, shocked reaction | partly | `feat(character)` | `tests/js/character-bridge.test.mjs` (10 tests: TC-CHV-001 failure reported once and the iframe hidden, TC-CHV-002 one bridge for expression, speaking, inset, view, background, foreign origin and bad JSON ignored, `unmapped` passed on); the Godot test `test_bridge.gd` (31 checks) passes unchanged | the shocked reaction (REQ-CHV-006, Could) has no preset and is not built, see below |
| T-02 Living character | no code change | | `test_bridge.gd`: the mouth follows the voice (max vowel weight 0.51), the watchdog; blinking and idle exist in `expression_engine.gd` | TC-CHV-003 is the reviewer checklist (owner, demonstration) |
| T-03 Editors, model selection and variant label | deferred | | | see below |
| T-04 Secure context, no outside request, plain stack, delivered by the backend | done | `feat(character)` | `character-bridge.test.mjs` (TC-CHV-012: not a secure context, no iframe, reported as `insecure`); `tests/test_character_stack.py` (6 tests, venv: TC-CHV-013 Godot 4.6 and GL Compatibility, no C#/bundler files; TC-CHV-011 no address outside the host in the GDScript and the export presets; TC-CHV-014 the backend serves the export with the wasm type and no cache, and says so when it is not built) | |
| T-05 Accessibility and devices of the character | done | `feat(godot)` | `ui/godot/tools/test_reduced_motion.gd` (8 checks, TC-CHV-009): with the preference the head sway and the breathing are a quarter, not frozen, and normal again when off | the bridge reads `prefers-reduced-motion` once at start (web only) |
| T-06 Frame rate | deferred to the field | | | owner decision D-62 (VAL-006); the measurement tool is N-4.1 T-05 |

## Findings
| Finding | Task | Covered by test |
|---|---|---|
| The character is told it is on a plain-HTTP LAN page only by failing to start; the page now refuses to load it outside a secure context and reports `insecure`, so the notice and the full-width chat appear at once | T-04 | `TC-CHV-012` tests |
| A `failed` or `unmapped` message of the character was ignored by the page; now `failed` disables the iframe (reported once, whatever the cause) and `unmapped` is passed on | T-01 | `character-bridge.test.mjs` |
| **IF-111 and today's code differ:** the draft says an unknown expression name falls back to `neutral` (TC-IF-111-02); the Godot bridge and the backend (`test_character_integration.py`, `test_bridge.gd`) deliberately keep the current expression and refuse the unknown name. The fallback to neutral for an unknown **mood** is the mood-to-expression mapping (REQ-CHV-004). **Needs a decision and an amendment of the protected contract text and test** | T-01 | `test_bridge.gd` "the current expression stays after an unknown name" |
| The Godot tests need `ui/godot/assets/mia.vrm` (git-ignored) and one `--import`; a runner now exists | all | `ui/tools/run_godot_tests.sh` (8 of 8 tests pass; `test_editor_live` needs a running MIA and is skipped) |

## Reuse check (owner rule: use existing code)
- Reused as it is: `host_bridge.gd` (the whole page-to-character wire: expression, gesture, speaking, background, viewport_inset, view, origin check, bad JSON), `expression_engine.gd` (blending, blinking, idle), the backend route `/character/<file>` and the existing presets. Changed: `character.js` (injectable window, WebGL check and secure flag; `failed` and `unmapped`), `expression_engine.gd` (a `reduced_motion` flag that scales the idle sway), `host_bridge.gd` (reads the preference at start). Nothing rewritten.
- The 39 existing JS tests and the existing Godot tests pass unchanged.

## Deferred (new features, not built; owner decides the time)
- REQ-CHV-007 character model selection (Should) and REQ-CHV-008 variant label (Could): the messages `model` and `variant` and the answer `unmapped` need runtime loading of a second VRM and outfit switching in Godot; no code exists. The page already passes `unmapped` on.
- REQ-CHV-006 shocked reaction (Could): no `shocked` preset exists in `data/presets`; it comes with the votes of N-2.2.
- REQ-CHV-005 editors: the editors and the live update exist (`expression_editor.gd`, `gesture_editor.gd`, `preset_api.gd`, tests pass); the 2 s live-update measurement is VN-5.
- A decision for the owner: build the model selection and the variants now or after the first human tests.

## Plan amendments
None. (The IF-111 text and TC-IF-111-02 need one, see the findings.)

## Open questions for Phase 4 and the integration step
- The real side of the IF-111 contract suite is the Godot bridge. Its checks are the GDScript tests; a JS adapter that drives headless Godot is not planned. Proposal: the integration step lists `test_bridge.gd` as the real-side test of IF-111 and the JS suite keeps the mock.
