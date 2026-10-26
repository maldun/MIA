# Plan: Chat agent (N-2.2)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/test-spec.md   **Status:** Draft (Plan for node N-2.2, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Chat turn: one shared MIA, queue, stop, bounded history | REQ-CHA-001, REQ-CHA-002, REQ-CHA-003, REQ-CHA-004, REQ-CHA-005, IF-201 | TC-CHA-001, TC-CHA-002, TC-CHA-003, TC-CHA-004, TC-CHA-005, contract suite of IF-201 | T-01 of the root plan (mocks installed) |
| T-02 Regenerate, speak again, voice lines | REQ-CHA-006, REQ-CHA-007 | TC-CHA-006, TC-CHA-007 | T-01 |
| T-03 Persona, mood, score shifts the mood | REQ-CHA-008, REQ-CHA-009, REQ-CHA-010 | TC-CHA-008, TC-CHA-009, TC-CHA-010 | T-01 |
| T-04 Structured memory, no memory from untrusted text, memory open to users | REQ-CHA-011, REQ-CHA-012, REQ-CHA-013 | TC-CHA-011, TC-CHA-012, TC-CHA-013 | T-01 |
| T-05 Silent repair of behaviour violations | REQ-CHA-014 | TC-CHA-014 | T-01 |
| T-06 Votes, case on a minus, adaptation, counters | REQ-CHA-015, REQ-CHA-016, REQ-CHA-017, REQ-CHA-018 | TC-CHA-015, TC-CHA-016, TC-CHA-017, TC-CHA-018 | T-01 |
| T-07 Tasks and memos recited, storage only through the interface | REQ-CHA-019, REQ-CHA-020 | TC-CHA-019, TC-CHA-020 | T-01 |

## Tasks

### T-01: Chat turn: one shared MIA, queue, stop, bounded history
- Implements: REQ-CHA-001, REQ-CHA-002, REQ-CHA-003, REQ-CHA-004, REQ-CHA-005, IF-201
- Tests to turn green: TC-CHA-001, TC-CHA-002, TC-CHA-003, TC-CHA-004, TC-CHA-005, contract suite of IF-201
- Touches: `chat_service.py`, `behaviour.py`, `moods.py`, `communicator.py`, `extraction.py`, `source_trust.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-201; the queue is 5 in all and 2 per user.

### T-02: Regenerate, speak again, voice lines
- Implements: REQ-CHA-006, REQ-CHA-007
- Tests to turn green: TC-CHA-006, TC-CHA-007
- Touches: `chat_service.py`, `behaviour.py`, `moods.py`, `communicator.py`, `extraction.py`, `source_trust.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Consumes IF-204.

### T-03: Persona, mood, score shifts the mood
- Implements: REQ-CHA-008, REQ-CHA-009, REQ-CHA-010
- Tests to turn green: TC-CHA-008, TC-CHA-009, TC-CHA-010
- Touches: `chat_service.py`, `behaviour.py`, `moods.py`, `communicator.py`, `extraction.py`, `source_trust.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-04: Structured memory, no memory from untrusted text, memory open to users
- Implements: REQ-CHA-011, REQ-CHA-012, REQ-CHA-013
- Tests to turn green: TC-CHA-011, TC-CHA-012, TC-CHA-013
- Touches: `chat_service.py`, `behaviour.py`, `moods.py`, `communicator.py`, `extraction.py`, `source_trust.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-05: Silent repair of behaviour violations
- Implements: REQ-CHA-014
- Tests to turn green: TC-CHA-014
- Touches: `chat_service.py`, `behaviour.py`, `moods.py`, `communicator.py`, `extraction.py`, `source_trust.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: `behaviour.py`; detectors keep their recorded precision and recall.

### T-06: Votes, case on a minus, adaptation, counters
- Implements: REQ-CHA-015, REQ-CHA-016, REQ-CHA-017, REQ-CHA-018
- Tests to turn green: TC-CHA-015, TC-CHA-016, TC-CHA-017, TC-CHA-018
- Touches: `chat_service.py`, `behaviour.py`, `moods.py`, `communicator.py`, `extraction.py`, `source_trust.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Rate 0.5 % for a nearly stopped behaviour (OPEN-2).

### T-07: Tasks and memos recited, storage only through the interface
- Implements: REQ-CHA-019, REQ-CHA-020
- Tests to turn green: TC-CHA-019, TC-CHA-020
- Touches: `chat_service.py`, `behaviour.py`, `moods.py`, `communicator.py`, `extraction.py`, `source_trust.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –
