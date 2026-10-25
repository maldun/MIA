# Plan: Graph tables (N-3.2)

**Requirements:** specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/requirements.md   **Test spec:** specs/mia/nodes/N-3-database/nodes/N-3.2-workflows-and-context-graphs/test-spec.md   **Status:** Draft (Plan for node N-3.2, 2026-10-25)

A leaf of the Database. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own (Phase 2, step 4) and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/` or `contracts/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Graph rules with property test | REQ-GTB-002 | TC-GTB-002, TC-GTB-003, TC-IF-301-01..03 | – |
| T-02 Table definitions of workflows and context graphs | REQ-GTB-001, REQ-GTB-003 | TC-GTB-001, TC-GTB-004 | T-01 |
| T-03 Check the five seed entries | REQ-GTB-004 | TC-GTB-005 | T-01 |

## Tasks

### T-01: Graph rules with property test
- Implements: REQ-GTB-002
- Tests to turn green: TC-GTB-002, TC-GTB-003, TC-IF-301-01..03
- Touches: `graph_rules.py` (new, plain module in the repository root like the others)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: –
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The rules of the mock `tests/helpers/mocks/graph_rules.py` are a starting point, not a copy to paste: the mock is protected and stays as it is. Property test against `graphlib`.

### T-02: Table definitions of workflows and context graphs
- Implements: REQ-GTB-001, REQ-GTB-003
- Tests to turn green: TC-GTB-001, TC-GTB-004
- Touches: `graph_tables.py` (new)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-301.

### T-03: Check the five seed entries
- Implements: REQ-GTB-004
- Tests to turn green: TC-GTB-005
- Touches: `library/`, `skills/` (read only); the seed files themselves are example workflows, delivered in the cycles of N-2.3 and the example-workflow task of the root plan (T-10)
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: This task checks the entries with the rules; writing the entries (specification, context graph, benchmark reference) belongs to the root task T-10. Until then the test is skipped with that reason, not weakened.
