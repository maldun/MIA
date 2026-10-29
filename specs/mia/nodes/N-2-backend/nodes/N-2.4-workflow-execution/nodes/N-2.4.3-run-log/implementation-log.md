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
`invalid_user` are new error codes next to `unknown_type` and `unknown_run`; the contract text does not list them yet, the next amendment of IF-401 can).

Not done, for the next steps of the node cycle:
- **The runner does not write through `RunEvents` yet** (N-2.4.1): today `EventStream` puts the events into the run record of `RunLog` (one JSON line per run, with the events inside). Two formats now exist side by side. To decide at the wiring: make the sink of `EventStream` write through `RunEvents` and let `RunLog` keep only the run record
  (input, output, status, feedback) for the harness, or keep both.
- The account of an answer in the chat (`ChatService.account`, IF-101 `account`) still reads the pipeline events kept in the chat log, not the run log: the link to IF-401 is open.

## T-02 to T-04: REQ-LOG-004 and the replay marker on recorded runs (2026-10-30)
Both checks pass on the existing code; nothing in the production code changed (the rule: test first, change only what fails). New: `tests/test_run_log_node.py` (4 tests, on the `Lab` of `tests/test_run_explain.py`: a complete lookup over the recorded
web of the research suite, scripted model, no network). It follows the new rule for readable tests (conventions §5: test ID first, an `Example:` line, Given / When / Then; `test_doc_check.py`: 0 findings); the earlier test files of this
node (`test_run_events.py`, `test_run_log_files.py`) were brought up to the same form.
Still open in the node: the runner does not write through `RunEvents` yet (N-2.4.1), the chat's account is not linked to IF-401, and the three new error codes are not in the contract text.
