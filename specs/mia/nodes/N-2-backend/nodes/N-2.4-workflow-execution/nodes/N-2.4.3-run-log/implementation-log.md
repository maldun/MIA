# Implementation log: Run log (N-2.4.3)

## T-01 the provider of IF-401 and the check of the existing code (2026-10-30) – REQ-LOG-001, -002, -003 (comparison), -005
Method (owner's rule: test the existing code first, change only what fails): the existing run log (`run_log.py`, `events.py`, `run_explain.py`, `reproduce.py`) was read against the five requirements. What was missing was
the object that IF-401 describes (emit / events / account / check_order / compare by run id); the pieces below it exist and were not rewritten.

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-LOG-001 account from events, no model-written part | `RunEvents.account` (the logged `plain` texts in the order of seq) | `tests/test_run_events.py` (TC-LOG-001), contract TC-IF-401-01 |
| REQ-LOG-002 typed events, one run id, the user, secrets removed, order checked | `RunEvents.emit` (14 types of the contract, `events.redact`, `events.clean_text`), `check_order`; the strict payload schemas stay in `events.EventStream` (`tests/test_events.py`, 23 tests) | `tests/test_run_events.py` (TC-LOG-002), contract TC-IF-401-02, -03 |
| REQ-LOG-003 replay and comparison | comparison: `RunEvents.compare`; replay offline: `reproduce.py` (existing, works on the run record of `RunLog`) | `tests/test_run_events.py` (compare), `tests/test_run_log_node.py` (TC-LOG-003, marker REQ-LOG-003: the baseline and the decomposed lookup are replayed offline, no differences, no divergences; a changed input is not a replay); more cases in `tests/test_run_explain.py` |
| REQ-LOG-004 statements traceable to a query | `evidence.py` / `context_graph.provenance` (existing) | `tests/test_run_log_node.py` (TC-LOG-004, marker REQ-LOG-004): on the recorded baseline and decomposed lookups 100 % of the claims and draft sentences lead back to a query; without the `query_issued` events none does |
| REQ-LOG-005 run events as append-only files (A-28) | `RunEvents`: `<folder>/<run_id>.jsonl`, one line per event, a cut last line is skipped; `run_log.py` appends its run records | `tests/test_run_log_files.py` (TC-LOG-005), `tests/test_run_events.py` |

Built: `run_events.py` (`RunEvents`, `RunEventsError`, `TYPES`), `tests/test_run_events.py` (11 tests, green), the adapter for the contract suite as a draft (A-29, `specs/mia/contract-drafts/tests/helpers/contract.py`): with it the four contract tests run
as `_real` too (8 tests, none skipped; tested on a scratch copy).

Decisions made while building (small, kept inside the contract): the file is one per run, so `events(run_id)` needs no scan of a month; a half-written last line is skipped by the reader and the next event starts on a line of its own;
the seq is counted by one writer per file (a second instance on the same file would clash: the runner writes from one process); the payload must be an object, the run id a plain name (`invalid_run`, `invalid_payload`,
`invalid_user` are new error codes next to `unknown_type` and `unknown_run`; the contract v1 lists them since A-30, D-110, with TC-IF-401-05).

Not done, for the next steps of the node cycle:
- **The runner does not write through `RunEvents` yet** (N-2.4.1): today `EventStream` puts the events into the run record of `RunLog` (one JSON line per run, with the events inside). Two formats now exist side by side. To decide at the wiring: make the sink of `EventStream` write through `RunEvents` and let `RunLog` keep only the run record
  (input, output, status, feedback) for the harness, or keep both.
- The account of an answer in the chat (`ChatService.account`, IF-101 `account`) still reads the pipeline events kept in the chat log, not the run log: the link to IF-401 is open.

## T-02 to T-04: REQ-LOG-004 and the replay marker on recorded runs (2026-10-30)
Both checks pass on the existing code; nothing in the production code changed (the rule: test first, change only what fails). New: `tests/test_run_log_node.py` (4 tests, on the `Lab` of `tests/test_run_explain.py`: a complete lookup over the recorded
web of the research suite, scripted model, no network). It follows the new rule for readable tests (conventions §5: test ID first, an `Example:` line, Given / When / Then; `test_doc_check.py`: 0 findings); the earlier test files of this
node (`test_run_events.py`, `test_run_log_files.py`) were brought up to the same form.
Still open in the node: the runner does not write through `RunEvents` yet (N-2.4.1), the chat's account is not linked to IF-401, and the three new error codes are not in the contract text.

## T-05 run events as append-only files, no database driver (2026-10-31) – REQ-LOG-005 (A-28)
State found (test first, owner's rule of T-01): `tests/test_run_log_files.py` (TC-LOG-005) and `tests/test_run_events.py` (append-only file per run, restart goes on with the next seq) green. Gap: the
inspection read the four files named in D-107 (A-28) and not `run_events.py`, the provider of IF-401 built later (D-109), which is now the file the runner writes through.
- Changed: `tests/test_run_log_files.py` inspects five files (`run_events.py` added). Red before: on a scratch copy with `import sqlite3` planted in `run_events.py` the old test passed and the new one
  failed (`['sqlite3'] != []`); green on the real code. No production code changed.
- Green after (image, feedback, not verification): `test_run_log_files.py` (2), `test_run_events.py` (11), `test_run_log_node.py` (4), contract `test_if_401_run_events.py` (10).
- Not changed, for Verify: the plan's title of T-05 ("State only through the storage interface", Notes "Needs the mock of IF-102") is the wording before A-28; the code of the Run log needs no IF-102.
  AC-15 also says "or outside the storage client": read as a check of the whole repository, `library.py` (the derived index `data/library.sqlite`, not Run log code) imports `sqlite3`;
  `tests/test_workflow_storage_imports.py` does not reach it. Question 2 of the hand-over below.
- Files outside the task's Touches: `tests/test_run_log_files.py` (a node test, free).

## T-01 follow-up: the runner writes through RunEvents (2026-10-31) – REQ-LOG-002, REQ-LOG-001, IF-401
State found: the open item of T-01 "the runner does not write through `RunEvents` yet" was closed by N-2.4.1 T-07 (`356f90b`: `pipeline._RunEventsSink`, wired in `web_app.py` as `run_events`, folder
`<runs>/events`, D-120: both formats side by side, moving `RunLog` behind IF-401 is technical debt); chat runs carry the real user (D-129, N8 of D-130). The runner was tested only against the mock
of IF-401 (`tests/test_runner_interfaces.py`); nothing showed the provider fed by the real runner.
- Added: `tests/test_run_events.py::RunnerWritesThroughTheLog` (1 test): a run of the real `Runner` written through the real `RunEvents` is `run_start` .. `run_end`, `check_order` empty, one
  run id and the user `anna`, the question's bearer token and e-mail address are `[removed]` in the stored file, the account is the plain texts of its events.
- Red before: against `pipeline.py` of `356f90b^` (before the wiring) `TypeError: Runner.__init__() got an unexpected keyword argument 'run_events'`; green on the current code. A mutation of
  `run_events.py` without `redact` keeps the test green: the stream of `events.py` already removes the secrets before the sink, so the writer's own removal is a second layer (its unit test
  catches the mutation). No production code changed.
- Green after (image, feedback): `test_run_events.py` (12), `test_runner_interfaces.py` (8), `test_pipeline.py` (26).
- Seen, not changed (for Verify): the account of the IF-401 file of a run is coarse: the skill's description, the tool names, the status (`run_start`, `tool_call`, `run_end` carry a plain text);
  the node steps the chat shows ("start" events with the node's `plain`) are not in the 14 types of IF-401 and go only to `RunLog`. See question 1 of the hand-over.
- Files outside the task's Touches: `tests/test_run_events.py` (a node test).

## Hand-over for Verify (2026-10-31, evening)
| Task | State | Commit | Tests (reported green in the image; feedback, not verification) |
|---|---|---|---|
| T-01 typed events, IF-401 | done (2026-10-30), wiring follow-up today | T-01 of 2026-10-30, `92ade85` | `test_run_events.py` (12), contract `test_if_401_run_events.py` (10, mock and real), `test_events.py` (23) |
| T-02 account | done (2026-10-30) for IF-401 `account`; the chat's account not linked (question 1) | 2026-10-30 | `test_run_events.py` (TC-LOG-001) |
| T-03 replay, comparison | done (2026-10-30) | 2026-10-30 | `test_run_log_node.py` (TC-LOG-003), `test_run_explain.py` (16) |
| T-04 statements to a query | done (2026-10-30) | 2026-10-30 | `test_run_log_node.py` (TC-LOG-004) |
| T-05 append-only files, no driver | done today | `0959b74` | `test_run_log_files.py` (2) |

Also green after the changes: `test_runner_interfaces.py` (8), `test_pipeline.py` (26), `test_run_workflow.py` (12), `test_chat_backend.py` (40), contract `test_if_101_chat_api.py` (60, 3 skipped).
No production code changed in this node today; no amendment drafted, no new id taken.

Open questions (Verify and the owner):
1. **The account of a chat answer is not read from IF-401** (IF-101 `account`: "from the run log, IF-401"; REQ-LOG-001). `ChatService.account` (N-2.1) renders the steps kept with the answer in the
   chat log, and only for skills that show a status block (the chat skill does not: "No steps were kept for this answer."). Linking it is outside this node: `decomposition.yaml` lists only N-2.4.1
   and N-2.4.2 as consumers of IF-401, the answer record keeps no run id, and the node steps the chat shows are not IF-401 types (an IF-401 account is the description, tool names and status).
   Options: (a) N-2.1 consumes IF-401: the answer keeps its run id, `account` reads `RunEvents.account`; amendment of the decomposition and IF-101's adapter, and either an IF-401 v2 with a step
   type or the coarser account; (b) keep the account from the events kept with the answer (event data, no model text), keep them for every answer, amend IF-101's wording; (c) defer with FB-03,
   recorded as a deviation. Recommended: (b) for G-V1, (a) in the next iteration together with moving `RunLog` behind IF-401 (the debt of D-120).
2. **Scope of AC-15 "or outside the storage client".** Read as the Run log only (the test), it holds. Read for the whole repository, `library.py` imports `sqlite3` for its derived index
   (`data/library.sqlite`); no test reaches it. Options: (a) keep the reading of the test here and hand `library.py` to the N-2.4 integration step (TC-N24-001, REQ-WFX-022) as a finding;
   (b) a repository-wide check now, which fails until the index moves behind IF-102 or is excepted as a cache by amendment. Recommended: (a).
3. **The plan's T-05** still has the title and note before A-28 ("State only through the storage interface", "Needs the mock of IF-102"). Options: correct the two lines as a docs fix (recommended),
   or leave them and let Verify read A-28.
4. Low: the replay (`reproduce.py`) and the account of a task rest on `RunLog` records, the comparison on the IF-401 files: two formats side by side (D-120 debt); `RunEvents` keeps one counter per
   run id in memory for the life of the process (one integer per run, no limit). The contract suite `test_if_401_run_events.py` (protected) has no `Example:` lines and no Given/When/Then
   (`test_doc_check.py` T2, T3); a fix needs an amendment. Recommended: record, no change in G-V1.

## Owner's answers of 2026-10-31 (D-138)
(1) The chat log keeps the steps of every answer (the chat skill too); IF-101 wording by A-49; IF-401 by run id in the next iteration (open task, next). (2) TC-LOG-005 checks the run log only; `library.py` (sqlite3 index) reported to the N-2.4 integration step (TC-N24-001). (3) T-05's title and note corrected in plan.md. (4) Low items recorded, no change in G-V1: replay and the task account read `RunLog`, the comparison reads IF-401; `RunEvents` keeps a counter per run id for the life of the process; the IF-401 suite fails the test-doc rules T2, T3 (an amendment, later).

## Chat account built (2026-10-31, D-138)
`ChatService` keeps the plain steps of every answer in the record field `steps` (also when no status block is shown, e.g. the chat); `account()` reads `steps`, else the `pipeline` of older records; `pipeline` stays what the block shows. Test `test_a_chat_answer_keeps_its_steps_for_the_account` (`tests/test_chat_backend.py`), red before ("No steps were kept"), green after; the IF-101 suite passes. File outside the node (`chat_service.py`, N-2.1): the owner's decision D-138. Open: A-49, the wording of IF-101 (`account` "from the run log, IF-401" -> from the steps kept with the answer). Commit `7f0d59e`.

## Verify findings fixed (2026-10-31, D-144)
Tests in the image (`localhost/mia:latest`, `--network none`); feedback, not verification.

### F1 (and F6, first half): a task that asks questions keeps its steps – T-02, REQ-LOG-001, IF-101 v11
- Test: `tests/test_chat_tasks.py::test_a_task_that_asks_keeps_its_steps_for_the_account` (a task with `needs=("ask",)` reports two steps around its question). Red before: account
  `[{'seq': 1, 'plain': 'No steps were kept for this answer.'}]`; green after.
- Fix: `chat_service.py` `pipeline_event` keeps the plain steps also while `_late` (dropped `and not self._late`); the progress of such a task still goes only to the status card.
- F6: the Example line of `tests/test_chat_backend.py::test_a_chat_answer_keeps_its_steps_for_the_account` now names the `talk` step it asserts.
- Green after: `test_chat_tasks.py` (12), `test_chat_backend.py` (41), contract `test_if_101_chat_api.py` (60, 3 skipped). File outside the node (`chat_service.py`, N-2.1): D-144.
