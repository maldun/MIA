# Implementation log: Tools and sandbox (N-2.4.2)

Goal G-V1 (line of work `goal/v1`). Method (owner's rule: test the existing code first, change only what fails): the tools exist (`checks.py`, `schema_check.py`, `sandbox.py`, `web_tools.py`, `scholar.py`, `source_trust.py`); what was missing is the one door of IF-402 that offers them to every workflow, counts the calls and labels the outputs.

## T-01 Code checks first, budget and trust label per call (2026-10-30, done; contract adapter waits for A-32) – REQ-TLS-001, REQ-TLS-008, IF-402

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-TLS-001 code checks as tools | `tool_calls.ToolCalls` tools `number_check` (`checks.number_check`), `quote_in_source` (`checks.quote_in_source`), `schema_check` (`schema_check.check`), trust `code` | `tests/test_tool_calls.py` (4 of 10) |
| REQ-TLS-008 budget and trust label per call | `ToolCalls.call`: limit per tool and run (`budget` naming the tool, nothing run or counted), `unknown_tool` (not counted), a failing web or scholarly source is `source_error` and counted; `used(run_id)`; every output `{output, trust}` | `tests/test_tool_calls.py` (6 of 10) |
| IF-402 | `tool_calls.py` (new module of the part VerificationSuite, the door; the plan lists only the modules behind it) | contract suite, real side through A-32 (scratch copy: 10 of 10) |

Decisions made while building (small, inside the contract):
- IF-402 has three statuses for `number_check`: `not_applicable` of `checks.py` (no evidence, no number in the claim) becomes `inconclusive`.
- `quote_in_source`: a near match (`inconclusive` in `checks.py`) is `fail`: a quotation counts only verbatim (golden 3).
- `fetch_passages` cuts the page with `web_tools.chunk_text` (about 1500 characters, sentence breaks); passage ids from `evidence.passage_id`; the hash is the first 16 hex digits of SHA-256 of the page text. Choosing passages by the `question` is not done here (T-04).
- `source_record` gives `retraction: None`; the retraction state of a work is T-05.
- `run_script` with a script check gives `{"status": "ok", "stdout": "", "result": <check result>}`; the real sandbox path and its `stdout` are T-03. Without one: `unavailable`, nothing runs.
- A tool whose source is not configured (no web search handed in) is `source_error`, counted.

Finding (owner decided, D-115, A-32 drafted): golden 5 of IF-402 v0 compared the schema problems with `["reason"]`; `schema_check.py` writes `$: missing 'reason'`. The owner chose to amend the test: IF-402 v1 says the problems are readable texts with path and key; TC-IF-402-05 checks that the one problem names `reason`.

Local coder: `tests/test_tool_calls.py` typed by the local model from an exact instruction (task `tls01-tests`, 2 attempts, 247 s); one hand fix (`out["ref"]` for `out["output"]["ref"]`), verdict `fixed`. The module `tool_calls.py` was written before the tests ran (the model typed the tests in parallel); the tests fail without it (import error) and pass with it.

Tests reported green (feedback, not verification): `tests/test_tool_calls.py` (10), IF-402 contract suite (installed: 5 mock, 5 real skipped; scratch copy with A-32: 10); on the scratch copy with A-32 all 15 contract suites and the integration steps of N-2 and N-2.4 as before.

Open for Phase 4:
- TC-TLS-001's criterion (AC-2: in the run log the code checks precede the first model call of each claim) is about the order inside a run; the door only offers the checks. The order is the pipelines' (`CheckRunner` runs code checks cheapest first; the lookup pipeline calls them before the judge). Verify should decide whether TC-TLS-001 needs a run-log test at N-2.4 level.
- Nothing calls `ToolCalls` yet: the pipelines still get their tools from `build_web_tools` and `CheckRunner`; the wiring is N-2.4.1 T-07 (interfaces only).
