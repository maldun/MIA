# Plan: Voice playback (N-1.3)

**Requirements:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/requirements.md   **Test spec:** specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/test-spec.md   **Status:** Draft (Plan for node N-1.3, 2026-10-25)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Playback queue and claim of the voice by one page | REQ-VPB-001 | TC-VPB-001, TC-IF-112-01.. | T-01 of the root plan (mocks installed) |
| T-02 Mute and stop per user | REQ-VPB-002 | TC-VPB-002 | T-01 |
| T-03 Voice lines with a missing file | REQ-VPB-003 | TC-VPB-003 | T-01 |
| T-04 No outside request, delivered by the backend | REQ-VPB-004, REQ-VPB-005 | TC-VPB-004, TC-VPB-005 | T-01 |

## Tasks

### T-01: Playback queue and claim of the voice by one page
- Implements: REQ-VPB-001
- Tests to turn green: TC-VPB-001, TC-IF-112-01..
- Touches: `templates/static/chat/sound.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-112; extends `tests/js/sound.test.mjs`.

### T-02: Mute and stop per user
- Implements: REQ-VPB-002
- Tests to turn green: TC-VPB-002
- Touches: `templates/static/chat/sound.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Mute is a setting of this device, not of the account.

### T-03: Voice lines with a missing file
- Implements: REQ-VPB-003
- Tests to turn green: TC-VPB-003
- Touches: `templates/static/chat/sound.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: One report event, no error shown.

### T-04: No outside request, delivered by the backend
- Implements: REQ-VPB-004, REQ-VPB-005
- Tests to turn green: TC-VPB-004, TC-VPB-005
- Touches: `templates/static/chat/sound.js`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Shares the browser test with the other parts.
