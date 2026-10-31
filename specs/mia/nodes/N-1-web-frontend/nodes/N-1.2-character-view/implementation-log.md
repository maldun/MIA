# Implementation log: Character view (N-1.2)

| Task | Status | Commit | Tests green (reported) | Notes |
|---|---|---|---|---|
| T-01 One expression API, mood map, shocked reaction | partly | `feat(character)` | `tests/js/character-bridge.test.mjs` (10 tests: TC-CHV-001 failure reported once and the iframe hidden, TC-CHV-002 one bridge for expression, speaking, inset, view, background, foreign origin and bad JSON ignored, `unmapped` passed on); the Godot test `test_bridge.gd` (31 checks) passes unchanged | the shocked reaction (REQ-CHV-006, Could) has no preset and is not built, see below |
| T-01 (D-140) An unknown expression name shows neutral (IF-111 v2, A-48) | done | `fix(character)` T-01 (D-140) | **red before:** `test_bridge.gd` 2 checks FAILED ("handled", "shows 'neutral' (got 'surprised')"); `test_character_integration.py` 4 of 33 (3 failures, 1 error). **green after:** `run_godot_tests.sh` 8 of 8 (`test_editor_live` skipped, needs MIA); `test_character_integration.py` 33 (1 skipped, as before), `test_converse_behaviours.py` 3; `node --test tests/js/*.test.mjs` 131; IF-111 suite 6 pass, 6 skipped (the real side, as before); contract and N-1 integration 17 pass, 16 skipped; N-1 steps 1 pass, 3 skipped; trace check: the IF-111 "no marker" warning is gone | Existing tests changed only because the owner decided the behaviour (A-48, D-140). `host_bridge.gd` maps a name the library lacks to `neutral` (the engine's `play` is unchanged: the editors only play known names); `expressor.py` sends `neutral` for an unknown key, also without a `neutral` entry. The unknown name is still reported as a warning (Godot) and a log error (backend); `unmapped` is untouched (it belongs to `model`). `character.js` only forwards the name: no change. Open: the bridge now returns ok (and emits `handled` with ok) for an unknown name; the contract is silent; nothing consumes it |
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
| ~~IF-111 and today's code differ~~ **closed (D-140):** v1 (A-04) kept the current expression and refused an unknown name; v2 (A-48) shows `neutral`. The Godot bridge and the backend follow v2, done in the commit of "T-01 (D-140)" below. The fallback of an unknown **mood** (REQ-CHV-004) is unchanged and now agrees with it | T-01 (D-140) | `test_bridge.gd` "an unknown name shows 'neutral'"; `test_character_integration.py` (unknown name shows neutral in the expressor and on the page; an unknown mood and an unknown name show the same face) |
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
None by this node. IF-111 v2 and TC-IF-111-02 came with A-48 (installed in 0568820); T-01 (D-140) follows it.

## Open questions for Phase 4 and the integration step
- The real side of the IF-111 contract suite is the Godot bridge. Its checks are the GDScript tests; a JS adapter that drives headless Godot is not planned. Proposal: the integration step lists `test_bridge.gd` as the real-side test of IF-111 and the JS suite keeps the mock.

## Owner's answers of 2026-10-31 (D-137)
REQ-CHV-007 and REQ-CHV-008 out of G-V1 (after the first human tests). REQ-CHV-006 (shocked) is built with the votes of N-2.2. IF-111 is right: an unknown expression falls back to `neutral`; the bridge and the backend change test-first (open task, next).
