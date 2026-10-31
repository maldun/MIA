# Verification report: Character view (N-1.2)

No earlier verification report existed in this folder (D-144 names an N-1.2 verify result, but no file was written); this file starts with the section below.

## Verification (2026-10-31)

**Goal:** G-V1 (iteration), supervised; node N-1.2 (leaf) verified as a black box against its mocks
**Branch:** goal/v1 @ ee64d7d   **Parent line of work:** master   **Plan baseline:** plan-baseline-it1
**Date:** 2026-10-31   **Reviewers:** – (human), Claude Opus 5.5 (AI, fresh context; it never saw the implementation chat)
**Commits reviewed:** 51c2961 (T-01 part, T-04, T-05; on master before goal/v1), f111f75 (T-01, D-140: unknown expression shows neutral), 88f484d (REQ-CHV-006 data, D-143). Scope: REQ-CHV-001..014 and IF-111, without REQ-CHV-007 and REQ-CHV-008 (out, D-137).

### Verdict (proposal)
**Not verified.** The commit 88f484d breaks two Godot tests of the character (F1); REQ-CHV-005 cannot meet its 2 s criterion with a 10 s poll (F2). After F1 is fixed (and F2 decided) the expected status is *verified with accepted deviations* (REQ-CHV-006 partly, waiting for N-2.2; REQ-CHV-010 in the field, D-62; the stage-2 browser checks that were replaced by unit tests or inspection).

### Automated checks (local runs, not CI)
| Check | Result |
|---|---|
| JS unit tests `node --test "tests/js/*.test.mjs"` | 132 pass, 0 fail |
| JS contract and N-1 integration `node --test tests/acceptance/contract/*.mjs tests/integration/N-1/*.mjs` | 33: 17 pass, 16 skipped (real sides "not integrated yet"), 0 fail |
| IF-111 contract suite | 6 pass against the mock; 6 real-side cases skipped (N-1.2 not integrated; the real side is `test_bridge.gd`, see F6) |
| Godot tests `bash ui/tools/run_godot_tests.sh` (Godot 4.6.1 Flatpak, after one `--import`) | **7 of 9 pass; test_editor 4 FAILED, test_expressions 1 FAILED** (F1); test_editor_live skipped (needs MIA) |
| Python tests in the image (`tools/run_in_image.sh`): test_character_integration 33 (1 skip), test_presets_api 28, test_character_stack 6, test_converse_behaviours 3, test_make_voice_lines 3, test_voice_lines 8, test_expression_llm 25, test_character_pack 23 | all OK |
| Protected IF-111 files vs. amendments | `contracts/IF-111-character-bridge.md` equals `amendments/A-48/`; mock and suite equal `contract-drafts/` of A-48; their only changes since the plan gate are A-04 (df7daf3) and A-48 (0568820) |
| trace_check (whole spec) | exit 1 from other parts (93 errors, none for N-1.2); for this node only warnings: no `req` marker for REQ-CHV-001, -005, -006, -009, -012 (their tests are JS or GDScript with TC ids in the names) |
| test_doc_check | the new tests of f111f75 pass; test_character_stack.py (51c2961) has 10 T1/T2/T3 errors; older tests of the character path have more (pre-existing) |
| Files Godot wrote | `ui/godot/tools/test_reduced_motion.gd.uid` (untracked; the other tools' .uid files are tracked) and `ui/godot/.godot/` (ignored); both left uncommitted |

### Mutation checks (scratch worktree of ee64d7d, removed afterwards)
| Mutation | Caught by |
|---|---|
| character.js: secure-context check removed | character-bridge.test.mjs (1 fail) |
| character.js: `failed` reported on every message, not once | character-bridge.test.mjs (1 fail) |
| character.js: a `failed` message no longer hides the iframe | character-bridge.test.mjs (1 fail) |
| character.js: the `event.source` check removed | character-bridge.test.mjs (1 fail) |
| expressor.py: the neutral fallback removed | test_character_integration.py (3 failures, 1 error) |
| host_bridge.gd: the neutral fallback removed | test_bridge.gd (2 failed) |
| expression_engine.gd: reduced motion ignored | test_reduced_motion.gd (2 failed) |
| library.json as before 88f484d (no `shocked`) | test_editor.gd and test_expressions.gd pass again: 88f484d causes F1 |

### Verification matrix
| Requirement | Method | Evidence | Result |
|---|---|---|---|
| REQ-CHV-001 Chat without the character | Test | character-bridge.test.mjs: `failed`, timeout, no WebGL hide the iframe, reported once, later messages send nothing (mutations caught). Specified as a stage-2 browser test (message sent and answered with the iframe blocked): not run | Met at unit level; browser part open (F7) |
| REQ-CHV-002 One expression API | Inspection, Test | Inspection: the page reaches the character only through `character.js` `send()` (one `postMessage`); in Godot all paths go through `ExpressionEngine.play` / `gestures.play`. Tests: TC-CHV-002 (JS), test_bridge.gd. AC-17 "14 presets and 5 gestures played through the API": test_expressions.gd checks the presets load, not that each is played; it now fails (F1) | Partly (F1) |
| REQ-CHV-003 Living character | Demonstration | test_bridge.gd: the mouth follows the voice; blinking and idle in expression_engine.gd. Reviewer checklist not done | Owner check (by eye) |
| REQ-CHV-004 Mood map | Test | test_character_integration.py: every mood maps to an expression with a preset; unknown mood and unknown name both give neutral | Met |
| REQ-CHV-005 Editors, live update | Test | test_editor.gd (**4 FAILED**, F1), test_gesture_editor.gd pass, test_presets_api.py pass; test_editor_live skipped. `preset_api.gd:25` polls every 10 s: a change by another user appears after up to 10 s, AC-17 asks 2 s | **Not met** (F1, F2) |
| REQ-CHV-006 Shocked reaction | Test | Preset `shocked` in `ui/godot/presets/library.json:14` and line in `library/voice_lines.json` (D-143); TC-CHV-006 (mock negative vote shows shocked) does not exist; the minus-vote trigger is N-2.2. `expressions.json` has no `shocked`, so the backend `PresetExpressor.express("shocked")` sends `neutral` today (probed in the image) (F3) | Partly met, waiting for N-2.2 (F3) |
| REQ-CHV-007, REQ-CHV-008 | – | out of G-V1 (D-137); the page passes `variant` and `unmapped` on | Out of scope |
| REQ-CHV-009 Reduced motion | Test, Demonstration | test_reduced_motion.gd (8 checks; mutation caught); preference read once at start (`host_bridge.gd:37`). The browser part of AC-1 (360/768/1440 px, both themes, 44 px targets) was not run | Partly (browser part: owner check) |
| REQ-CHV-010 Frame rate | Measurement | deferred to the field (D-62, VAL-006) | Verified in Phase 7 |
| REQ-CHV-011 No outside request | Test | test_character_stack.py: no http(s) address in the top-level .gd files and in export_presets.cfg (static scan). Specified as a browser test recording every request: not run | Met by inspection; browser test open (F7) |
| REQ-CHV-012 Secure context | Test | character-bridge.test.mjs TC-CHV-012 (mutation caught). But `templates/index.html:36` gives the iframe its `src` in the HTML and the module script removes it only later, so on plain HTTP the browser has already started loading the character (F4) | Partly (F4) |
| REQ-CHV-013 Plain stack | Inspection | Host Godot is 4.6.1 (flatpak info); project.godot: GL Compatibility on desktop and mobile; no C# or bundler files. The test checks "4.6", not "4.6.1" | Met by inspection (test weaker than AC, F8) |
| REQ-CHV-014 Delivered by the backend | Test | test_character_stack.py: `/character/*` served by Flask with wasm type and no-cache; 404 with "not built". AC-29 (compose stack, real browser) not run here: the owner's stack must not be touched | Met at component level; stage 3 open |
| IF-111 Character bridge | Test | Mock side 6/6; real side: test_bridge.gd (neutral fallback, foreign JSON, unknown type, inset, view, speaking) and the JS page tests. The contract's bound "ready within 15 s (`LOAD_TIMEOUT_MS`)" differs from the code, 30 s (F5) | Partly (F5, F6) |

### Specification vs. code (M42)
| Direction | Item | Finding | Destination |
|---|---|---|---|
| specified, not done | REQ-CHV-005 AC-17 (2 s) | poll interval 10 s (`ui/godot/preset_api.gd:25`) | owner decision (F2) |
| specified, not done | IF-111 bound "ready within 15 s" | `LOAD_TIMEOUT_MS = 30000` (`templates/static/chat/character.js:3`, unchanged since b077cfe); the test only compares the timer with the constant | owner decision (F5) |
| specified, not done | REQ-CHV-012 "does not load" | iframe `src` set in the HTML before the check (F4) | Phase 3 |
| specified, not done | TC-CHV-006 | no test; trigger with N-2.2 | N-2.2 / Phase 3 (F3) |
| done, not specified | `gesture` message | `host_bridge.gd:78` accepts `{"type":"gesture"}`; IF-111 lists no such message (the page never sends it) | Low; amendment or leave (F9) |
| plan inconsistency | IF-111 bounds "60 fps on desktop" | REQ-CHV-010 and AC-19 say 30 fps on both (HLS amendment 9) | Phase 2 amendment of the contract text (F9) |

D-144 (the bridge's `handled` signal stays "ok" for an unknown expression) is followed: `host_bridge.gd:101-105` returns the result of playing `neutral`.

### Per-commit review
- **51c2961** (T-01 part, T-04, T-05): page side of `failed`, `unmapped`, secure context; reduced motion; runner. Correct and tested; findings F4 (src race), F7 (browser checks replaced by unit tests or a static scan), F8 (version 4.6 not 4.6.1), doc-check errors in test_character_stack.py, the `.uid` of test_reduced_motion.gd never committed.
- **f111f75** (D-140, IF-111 v2): bridge and backend show `neutral` for an unknown name; tests red first (as logged) and caught by my mutations; Given/When/Then docstrings. No finding.
- **88f484d** (D-143, shocked data): adds the preset and the voice line and updates the Python tests that pin 14 presets, but not the two Godot tests (`test_expressions.gd:5` REQUIRED list, `test_editor.gd:109` "14 presets", and `test_editor.gd:178-193` uses `shocked` as the *new* name to save, which now exists): F1. It does not add `shocked` to `expressions.json` (F3). The node's implementation-log.md was not updated (it still says "no `shocked` preset exists").

### Review findings
| # | Finding | Severity | Resolution / destination |
|---|---|---|---|
| F1 | 88f484d broke `test_expressions.gd` ("library loads 14 presets (got 15)") and `test_editor.gd` (4 checks: line 109 counts 14; lines 178-188 save a "new" preset named `shocked`, which is now shipped). Proven by restoring the old library on a scratch copy | High | Phase 3: add `shocked` to REQUIRED in test_expressions.gd, count 15 in test_editor.gd:109, rename the editor's test preset (e.g. `test_shocked`); log it in implementation-log.md |
| F2 | REQ-CHV-005: another user's change appears after up to 10 s (`preset_api.gd:25` POLL_SECONDS 10), AC-17 asks 2 s; no test measures it | High | Owner decision: poll at 2 s or less (or push by socket) with a test, or amend AC-17 to 10 s |
| F3 | `expressions.json` has no `shocked` entry; `PresetExpressor.express("shocked")` sends `neutral` (probed), so the backend path `express_and_reload("shocked")` cannot show it; TC-CHV-006 missing | Medium | Needs test, then data: add `shocked` (preset and voice) with a test that express("shocked") sends "shocked"; with N-2.2's trigger |
| F4 | `templates/index.html:36` sets the iframe `src` in the HTML; `character.js` removes it only after the deferred module runs, so over plain HTTP (dev run on a LAN address; the compose stack serves HTTP on loopback only) the character request is already sent. Same for `?character=0` | Medium | Needs test (stage-2 browser test that records requests on an insecure origin), then Phase 3: `data-src`, set by character.js after the checks |
| F5 | IF-111 bound: ready within 15 s, else failed; code waits 30 s | Medium | Owner decision: amend the contract to 30 s (proposal: a 20 MB export on a phone may need it) or change the code with a test of the value |
| F6 | IF-111 real side: the contract suite's real cases are skipped; the log proposes `test_bridge.gd` as the real-side test | Medium | Owner decision at the N-1 integration step (accept the proposal and record it) |
| F7 | Stage-2 browser tests of TC-CHV-001, -009 (sizes, themes, 44 px), -011 (request recording), -012 replaced by unit tests or a static scan; a headless browser is now approved (D-140 F3) | Low | Phase 3 at the integration step, or accepted deviation |
| F8 | TC-CHV-013 test checks "4.6", AC-20 says 4.6.1 exact; test_character_stack.py has 10 doc-check errors; `test_reduced_motion.gd.uid` untracked | Low | Phase 3 (small) |
| F9 | `gesture` message accepted but not in IF-111; IF-111 bounds say 60 fps desktop vs 30 in REQ-CHV-010 | Low | Phase 2 amendment of the contract text with the next IF-111 change |
| F10 | implementation-log.md does not record 88f484d and still says no `shocked` preset exists | Low | Log update |

### Open deferrals and known limitations
- REQ-CHV-010: field measurement (D-62, VAL-006).
- REQ-CHV-006: trigger by a minus vote comes with N-2.2 (running).
- REQ-CHV-007, REQ-CHV-008: out of G-V1 (D-137).
- REQ-CHV-014 AC-29 and the browser checks: not run here (owner's stack not touched).

### Manual checks for the owner (by eye)
Use the https front (`https://<host>:8586/`) after the stack runs the commits up to ee64d7d (and the export rebuilt with `ui/tools/build_web.sh`).
1. **Shocked face:** open `https://<host>:8586/character/?menu`, choose the expression `shocked`: wide eyes, brows up and pinched, mouth open and turned down, head slightly back, gesture hands_up (D-143). In the chat page, in the browser console: `document.getElementById('character').contentWindow.postMessage(JSON.stringify({type:'expression',name:'shocked'}), location.origin)` shows the same face. (The line `shocked_default.wav` must exist in `voice/expressions/`.)
2. **Unknown expression shows neutral:** in the chat page console send first `{type:'expression',name:'happy'}`, then `{type:'expression',name:'nonsense'}` (same call as in 1): the face goes to neutral, not stays happy.
3. **Living character (REQ-CHV-003):** send a chat message with sound on: the mouth moves with the voice and stops after it; expressions blend (no jumps); blinking; idle sway. On the desktop and on a phone.
4. **Reduced motion (REQ-CHV-009):** turn on "reduce animation" (GNOME Settings, Accessibility; or Chrome DevTools, Rendering, "Emulate CSS prefers-reduced-motion: reduce"), **reload** the page (read once at start): the head sway and breathing are clearly smaller but not frozen; off and reload: normal.
5. **Editors and live update (REQ-CHV-005):** on device A open `/character/?menu`, expression editor, save a new preset; on device B with the same page open, note how long until it appears without reload (expected today: up to 10 s, the requirement says 2 s). Repeat with the gesture editor.
6. **Layouts (REQ-CHV-009 browser part):** the chat page at 360, 768 and 1440 px wide in light and dark theme: the character sits in the free area, the character menu buttons are 44 px or more.
7. **Character blocked (REQ-CHV-001):** open `/?character=0`: the chat works full width without the character.

### What could not be checked
CI stage log (local runs only); stage-2 browser tests and stage-3 compose test (owner's stack not touched); the 2 s live update; frame rate; anything visual.
