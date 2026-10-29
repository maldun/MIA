# Plan: Workflow management (N-2.3)

**Requirements:** specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md   **Test spec:** specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/test-spec.md   **Status:** Draft (Plan for node N-2.3, 2026-10-26)

A leaf. Each task is small, vertical, fits one session and starts from a red test. The tests are written first in a session of their own and installed by the owner; the implementing session never edits `tests/acceptance/`, `tests/helpers/`, `tests/integration/`, `tests/smoke/`, `benchmarks/`, `contracts/`, `eval/suites/` or `eval/baselines/`.

## Task list

| Task | Implements | Green when | Depends on |
| --- | --- | --- | --- |
| T-01 Versioned library and graph rules | REQ-WFM-002, REQ-WFM-003, REQ-WFM-004, REQ-WFM-026, IF-203 | TC-WFM-002, TC-WFM-003, TC-WFM-004, TC-WFM-026, contract suite of IF-203 | T-01 of the root plan (mocks installed) |
| T-02 Skills as tasks, drafts, specification before trust, time record | REQ-WFM-001, REQ-WFM-005, REQ-WFM-006, REQ-WFM-007 | TC-WFM-001, TC-WFM-005, TC-WFM-006, TC-WFM-007 | T-01 |
| T-03 Context graphs, schedule and estimate, variant per workflow | REQ-WFM-008, REQ-WFM-009, REQ-WFM-010 | TC-WFM-008, TC-WFM-009, TC-WFM-010 | T-01 |
| T-04 Verify workflow: code checks first, unclear without evidence, failed check informs the judge | REQ-WFM-011, REQ-WFM-012, REQ-WFM-013 | TC-WFM-011, TC-WFM-012, TC-WFM-013 | T-01 |
| T-05 Verify quality: judgement, stable verdicts, confidence by code, no invented source | REQ-WFM-014, REQ-WFM-015, REQ-WFM-023, REQ-WFM-024 | TC-WFM-014, TC-WFM-015, TC-WFM-023, TC-WFM-024 | T-01 |
| T-06 Lookup workflow and search command | REQ-WFM-016, REQ-WFM-017 | TC-WFM-016, TC-WFM-017 | T-01 |
| T-07 Review workflow: report, stages and slices, stop by code, source records, keyword extension, staged screening | REQ-WFM-018, REQ-WFM-019, REQ-WFM-020, REQ-WFM-021, REQ-WFM-027, REQ-WFM-028 | TC-WFM-018, TC-WFM-019, TC-WFM-020, TC-WFM-021, TC-WFM-027, TC-WFM-028 | T-01 |
| T-08 Method transfer and storage only through the interface | REQ-WFM-022, REQ-WFM-025 | TC-WFM-022, TC-WFM-025 | T-01 |
| T-09 Skill ids and options, task monitor, pause, run mode, class of the model | REQ-WFM-019, REQ-WFM-029, REQ-WFM-030, REQ-WFM-031, REQ-WFM-032, REQ-WFM-033, REQ-WFM-034, REQ-WFM-035 | TC-WFM-019, TC-WFM-029 to TC-WFM-035 | T-07 |
| T-10 Result at the end, files volume, report record | REQ-WFM-036, REQ-WFM-037, REQ-WFM-038 | TC-WFM-036, TC-WFM-037, TC-WFM-038 | T-09 |
| T-11 Skills as extensions: lookup, search and review move into folders of their own | REQ-WFM-039 | TC-WFM-039 | T-09 |

## Tasks

### T-01: Versioned library and graph rules
- Implements: REQ-WFM-002, REQ-WFM-003, REQ-WFM-004, REQ-WFM-026, IF-203
- Tests to turn green: TC-WFM-002, TC-WFM-003, TC-WFM-004, TC-WFM-026, contract suite of IF-203
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01 of the root plan (mocks installed)
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Provides IF-203; the graph rules module comes from N-3.2.

### T-02: Skills as tasks, drafts, specification before trust, time record
- Implements: REQ-WFM-001, REQ-WFM-005, REQ-WFM-006, REQ-WFM-007
- Tests to turn green: TC-WFM-001, TC-WFM-005, TC-WFM-006, TC-WFM-007
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-03: Context graphs, schedule and estimate, variant per workflow
- Implements: REQ-WFM-008, REQ-WFM-009, REQ-WFM-010
- Tests to turn green: TC-WFM-008, TC-WFM-009, TC-WFM-010
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The estimate comes from stored costs.

### T-04: Verify workflow: code checks first, unclear without evidence, failed check informs the judge
- Implements: REQ-WFM-011, REQ-WFM-012, REQ-WFM-013
- Tests to turn green: TC-WFM-011, TC-WFM-012, TC-WFM-013
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Delivered as a library entry that runs on the platform (D-50).

### T-05: Verify quality: judgement, stable verdicts, confidence by code, no invented source
- Implements: REQ-WFM-014, REQ-WFM-015, REQ-WFM-023, REQ-WFM-024
- Tests to turn green: TC-WFM-014, TC-WFM-015, TC-WFM-023, TC-WFM-024
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Statistical; criteria decided against the baseline.

### T-06: Lookup workflow and search command
- Implements: REQ-WFM-016, REQ-WFM-017
- Tests to turn green: TC-WFM-016, TC-WFM-017
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Lookup is the proof-of-concept scenario.

### T-07: Review workflow: report, time slices, stop by code, source records
- Implements: REQ-WFM-018, REQ-WFM-019, REQ-WFM-020, REQ-WFM-021, REQ-WFM-027, REQ-WFM-028
- Tests to turn green: TC-WFM-018, TC-WFM-019, TC-WFM-020, TC-WFM-021, TC-WFM-027, TC-WFM-028
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-08: Method transfer and storage only through the interface
- Implements: REQ-WFM-022, REQ-WFM-025
- Tests to turn green: TC-WFM-022, TC-WFM-025
- Touches: `library.py`, `context_graph.py`, `skill_store.py`, `plans.py`, `verification.py`, `review_*.py`, `research*.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-01
- Done when: the listed tests are green and all other tests are unchanged
- Notes: –

### T-09: Skill ids and options, task monitor, pause, run mode, class of the model
- Implements: REQ-WFM-019, REQ-WFM-029, REQ-WFM-030, REQ-WFM-031, REQ-WFM-032, REQ-WFM-033, REQ-WFM-034, REQ-WFM-035
- Tests to turn green: TC-WFM-019, TC-WFM-029, TC-WFM-030, TC-WFM-031, TC-WFM-032, TC-WFM-033, TC-WFM-034, TC-WFM-035, contract suite of IF-101 v8 (events task_status, operations pause and resume)
- Touches: `chat_service.py`, `task_monitor.py`, `skill_options.py`, `model_class.py`, `review_request.py`, `review_stages.py`, `review_chat.py`, `skills/review_*.md`, `library/`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-07
- Done when: the listed tests are green and all other tests are unchanged
- Notes: Design: `specs/mia/eval-drafts/review-usability-design.md`. The monitor is generic (any task reports through `update`); the page work (status card) is a task of N-1 (amendment of its requirements follows with the contract tests of IF-101 v8).

### T-10: Result at the end, files volume, report record
- Implements: REQ-WFM-036, REQ-WFM-037, REQ-WFM-038
- Tests to turn green: TC-WFM-036, TC-WFM-037, TC-WFM-038, contract suites of IF-101 v8 (files, file) and IF-302 v4 (table reports)
- Touches: `chat_service.py`, `file_store.py`, `files_api.py`, `report_record.py`, `report_tex.py`, `review_chat.py`, `web_app.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-09
- Done when: the listed tests are green and all other tests are unchanged
- Notes: The table `reports` is IF-302 v4 (new in A-23). The Files tab of the page is a task of N-1.

### T-11: Skills as extensions
- Implements: REQ-WFM-039
- Tests to turn green: TC-WFM-039
- Touches: `task_registry.py`, `extensions/`, `legacy_tasks.py`, `chat_service.py`, `web_app.py`, `research_chat.py`, `review_chat.py`
- Must not touch: tests/acceptance/, tests/helpers/, tests/smoke/, tests/integration/, benchmarks/, contracts/, eval/suites/, eval/baselines/
- Depends on: T-09
- Done when: the listed tests are green, `COMMANDS` names no skill, `legacy_tasks.py` and the old `run_*` arguments of `ChatService` are gone, and all other tests are unchanged
- Notes: Today (A-23) each skill describes itself in its own module (`lookup_task`, `search_task`, `review_task`) and `web_app.py` registers them; the step to a folder with a manifest and a loader is this task. Open: where the code of a skill lives (a package under `extensions/<id>/`) and how its tests are found.
