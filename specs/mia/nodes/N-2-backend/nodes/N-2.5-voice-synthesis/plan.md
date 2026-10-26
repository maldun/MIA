# Plan: Voice synthesis (N-2.5)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.5-voice-synthesis/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.5-voice-synthesis/test-spec.md   **Status:** Draft (Plan for node N-2.5, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Speech per sentence and markup filtering | REQ-VOI-001, REQ-VOI-002, IF-204 | TC-VOI-001, TC-VOI-002, contract suite of IF-204 | T-01 of the root plan (mocks installed) |
| T-02 Voice lines | REQ-VOI-003 | TC-VOI-003 | T-01 |
| T-03 Default voice lines generated | REQ-VOI-004 | TC-VOI-004 | T-01 |

## Tasks

### T-01: Speech per sentence and markup filtering
- Implements: REQ-VOI-001, REQ-VOI-002, IF-204
- Tests to turn green: TC-VOI-001, TC-VOI-002, contract suite of IF-204
- Touches: `speak.py`, `speech_stream.py`, `speech_text.py`, `voice_effects.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-204. The voice effects of `voice_effects.py` stay as they are.

### T-02: Voice lines
- Implements: REQ-VOI-003
- Tests to turn green: TC-VOI-003
- Touches: `speak.py`, `speech_stream.py`, `speech_text.py`, `voice_effects.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Every mood of the map has a line or is declared silent.

### T-03: Default voice lines generated
- Implements: REQ-VOI-004
- Tests to turn green: TC-VOI-004
- Touches: `speak.py`, `speech_stream.py`, `speech_text.py`, `voice_effects.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: No third-party recording.
