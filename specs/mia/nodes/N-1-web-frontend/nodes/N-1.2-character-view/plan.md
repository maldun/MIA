# Plan: Character view (N-1.2)

**Requirements:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.2-character-view/requirements.md   **Test spec:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.2-character-view/test-spec.md   **Status:** Draft (Plan for node N-1.2, 2026-10-25)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 One expression API, mood map, shocked reaction | REQ-CHV-002, REQ-CHV-004, REQ-CHV-006, REQ-CHV-001 | TC-CHV-001, TC-CHV-002, TC-CHV-004, TC-CHV-006, TC-IF-111-01.. | T-01 of the root plan (mocks installed) |
| T-02 Living character (mouth, blending, blinking, idle motion) | REQ-CHV-003 | TC-CHV-003 (reviewer checklist, Demonstration) | T-01 |
| T-03 Editors, model selection and variant label | REQ-CHV-005, REQ-CHV-007, REQ-CHV-008 | TC-CHV-005, TC-CHV-007, TC-CHV-008 | T-01 |
| T-04 Secure context, no outside request, plain stack, delivered by the backend | REQ-CHV-011, REQ-CHV-012, REQ-CHV-013, REQ-CHV-014 | TC-CHV-011..014 | T-01 |
| T-05 Accessibility and devices of the character | REQ-CHV-009 | TC-CHV-009 | T-01 |
| T-06 Frame rate | REQ-CHV-010 | TC-CHV-010 (BM-MIA-002) | T-01, T-03 |

## Tasks

### T-01: One expression API, mood map, shocked reaction
- Implements: REQ-CHV-002, REQ-CHV-004, REQ-CHV-006, REQ-CHV-001
- Tests to turn green: TC-CHV-001, TC-CHV-002, TC-CHV-004, TC-CHV-006, TC-IF-111-01..
- Touches: `templates/static/chat/character.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-111; extends `tests/js/character.test.mjs`. The chat must keep working with the iframe blocked.

### T-02: Living character (mouth, blending, blinking, idle motion)
- Implements: REQ-CHV-003
- Tests to turn green: TC-CHV-003 (reviewer checklist, Demonstration)
- Touches: `templates/static/chat/character.js`, `ui/godot/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Demonstration by the owner; no automatic test can decide it.

### T-03: Editors, model selection and variant label
- Implements: REQ-CHV-005, REQ-CHV-007, REQ-CHV-008
- Tests to turn green: TC-CHV-005, TC-CHV-007, TC-CHV-008
- Touches: `templates/static/chat/character.js`, `ui/godot/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: A second `.vrm` model loads and reports the unmapped presets and gestures.

### T-04: Secure context, no outside request, plain stack, delivered by the backend
- Implements: REQ-CHV-011, REQ-CHV-012, REQ-CHV-013, REQ-CHV-014
- Tests to turn green: TC-CHV-011..014
- Touches: `templates/static/chat/character.js`, `ui/tools/build_web.sh`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Godot stays at 4.6.1; no bundler files.

### T-05: Accessibility and devices of the character
- Implements: REQ-CHV-009
- Tests to turn green: TC-CHV-009
- Touches: `templates/static/chat/character.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Touch targets of 44 px or more.

### T-06: Frame rate
- Implements: REQ-CHV-010
- Tests to turn green: TC-CHV-010 (BM-MIA-002)
- Touches: `ui/godot/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01, T-03
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Measured on the desktop and on a phone in the network; the measurement tool is built in N-4.1 T-05.
