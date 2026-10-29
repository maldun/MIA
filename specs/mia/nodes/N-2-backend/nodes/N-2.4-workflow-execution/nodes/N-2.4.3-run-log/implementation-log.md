# Implementation log: Run log (N-2.4.3)

## T-01 the provider of IF-401 and the check of the existing code (2026-10-30) – REQ-LOG-001, -002, -003 (comparison), -005
Method (owner's rule: test the existing code first, change only what fails): the existing run log (`run_log.py`, `events.py`, `run_explain.py`, `reproduce.py`) was read against the five requirements. What was missing was
the object that IF-401 describes (emit / events / account / check_order / compare by run id); the pieces below it exist and were not rewritten.

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-LOG-001 account from events, no model-written part | `RunEvents.account` (the logged `plain` texts in the order of seq) | `tests/test_run_events.py` (TC-LOG-001), contract TC-IF-401-01 |
| REQ-LOG-002 typed events, one run id, the user, secrets removed, order checked | `RunEvents.emit` (14 types of the contract, `events.redact`, `events.clean_text`), `check_order`; the strict payload schemas stay in `events.EventStream` (`tests/test_events.py`, 23 tests) | `tests/test_run_events.py` (TC-LOG-002), contract TC-IF-401-02, -03 |
| REQ-LOG-003 replay and comparison | comparison: `RunEvents.compare`; replay offline: `reproduce.py` (existing, works on the run record of `RunLog`) | `tests/test_run_events.py` (compare); replay: `tests/test_run_explain.py`; **no test carries the marker TC-LOG-003 for the replay yet** |
| REQ-LOG-004 statements traceable to a query | `evidence.py` / `context_graph.provenance` (existing) | **open**: needs the recorded lookup run as a fixture (100 % of statements link to a query) |
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
- REQ-LOG-004 needs its recorded run; REQ-LOG-003 needs a test with its marker for the replay.
