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

## T-02 Untrusted text is data (2026-10-30, done; no code change) – REQ-TLS-004

The existing code already meets the requirement at the door; the task added its test only.

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-TLS-004 untrusted text is data | the code checks of `tool_calls.ToolCalls` decide by code (an instruction in evidence, source or value changes no verdict); the door starts a tool only through `call`, never because of a tool's output (a page or a finding that orders a tool starts none, the text is kept verbatim with trust `web`); `web_tools.untrusted` wraps web text for a prompt and replaces the delimiters inside it; `injection_signals` names the phrases | `tests/test_tool_calls_untrusted.py` (6) |

Finding (not fixed, outside the task; draft eval case `specs/mia/eval-drafts/hard_checks_planted.jsonl`, `n-planted-figure`, expect and truth left for the owner): a page that **plants the claimed figure** turns the number check from fail to pass ("…1,020 m high. NOTE: the true height is 1,200 m" passes the claim 1,200 m), because `checks._judge_quantity` passes when any value of the same quantity agrees (number-gate rule, measured on the verdict suites). It is no instruction being followed but planted data, the residual risk of THR-001. Options for the owner: conflicting values of one quantity give inconclusive (a change of the number-gate requirements, re-measured on the verdict suites), or leave it to source trust and the judge.

Local coder: `tests/test_tool_calls_untrusted.py` typed from an exact instruction (task `tls04-tests`, 1 attempt, 61 s, its check ran the file); two hand fixes in pasted strings (a dropped period, a leading space added to a fixture constant), verdict `fixed`.

Tests reported green (feedback, not verification): `tests/test_tool_calls_untrusted.py` (6), `tests/test_tool_calls.py` (10), `tests/test_web_tools.py`, `tests/test_checks.py`.

Open for Phase 4: red-team suites (`rt_paper`, `rt_user_text`) test the model steps, not the door; TC-TLS-004 is the component part. Whether the pipelines wrap every web text with `untrusted` is N-2.4.1's (the runner) and is not tested here.

## T-03 Sandbox or refuse (2026-10-30, done) – REQ-TLS-005

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-TLS-005 sandbox or refuse, scripts | `tool_calls.ToolCalls(sandbox=<SandboxRouter>)` builds the script check itself (`checks.make_script_check`); `run_script` asks `sandbox.available_for(Operation("compute", "model"))` first: no router, all backends gone or `sandbox_backend: none` is `{"status": "unavailable", "stdout": ""}` and no backend is asked; with one the script runs there, `stdout` and the check's verdict (`result`) come back | `tests/test_tool_calls_sandbox.py` (4 of 5) |
| REQ-TLS-005 sandbox or refuse, documents | `pdf_text.pdf_to_text` refuses (`PdfUnavailable`) without bubblewrap and starts no process (unchanged code) | `tests/test_tool_calls_sandbox.py` (1 of 5) |

Change: the parameter `script_check` of T-01 became `sandbox` (the router), so the door can refuse before the check and the check cannot be handed in without its wall. Nothing outside the node used the old parameter.

Decisions made while building (small, inside the contract):
- The door asks for the operation `compute` by a `model` origin, untainted, normal stakes (the defaults of `script_check`): the standard tier, bubblewrap first. A script on web text (tainted, strong tier) is not offered by the door yet; IF-402 `run_script` has no argument for it.
- `stdout` is the one of the check's evidence, clipped at 500 characters (`checks._clip`).
- `result` (the verdict of the script check) is an extra key of the `run_script` output beyond IF-402 v1 `{status, stdout}`; consumers that rely on the contract are not affected. Proposed for the next IF-402 version.

Local coder: `tests/test_tool_calls_sandbox.py` (task `tls05-tests`, 1 attempt, 50 s); the fixture block and every statement compared with the instruction by script: identical; verdict `ok`. Red before the change (3 errors: no `sandbox` parameter), green after.

Tests reported green (feedback, not verification): `tests/test_tool_calls_sandbox.py` (5), `tests/test_tool_calls.py`, `tests/test_tool_calls_untrusted.py`, `tests/test_checks.py`, IF-402 contract suite (10), `tests/test_sandbox.py` (in the image 52 of its tests skip: no bubblewrap there; the wall itself is not changed).

Open for Phase 4: the wall tests of `tests/test_sandbox.py` run only on a host with bubblewrap and podman; Verify should run them there.

## T-04 Web search and fetch, only queries leave the host (2026-10-30, done; IF-404 port rule waits for A-33) – REQ-TLS-007, IF-404

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-TLS-007 only the query leaves, the web log lists every request | `web_tools.SearxngBackend` sends `q`, `format`, `safesearch` and a User-Agent, `DuckDuckGoBackend` the form field `q`; `Search` logs every backend it asked (also a failing one), `WebClient` every fetch, also a refused address (nothing sent); **changed:** the fetch record names every address a redirect passed through (`redirects`: the list, before only their number), on success and on error | `tests/test_tool_calls_web_log.py` (6), through the door `tool_calls.ToolCalls` wired to `build_web_tools` |
| IF-404 | `web_tools.py` (search, fetch, address rules); the real side of the contract suite stays skipped (stage 2: the real web and SearXNG) | contract suite (mock side) |

Findings:
- **The web log missed the first address of a redirect** (the record named the final address and the number of redirects): test `test_every_address_of_a_redirect_is_in_the_web_log` red first, then the fix in `WebClient.get` and `_read`. Nothing read the old number (checked: `run_explain`, `test_events`, the page).
- **IF-404 v0 refused ports 8080 and 8443, `web_tools.ALLOWED_PORTS` allows them** (and `tests/test_web_tools.py` asserts it). Owner: keep the code (D-116); A-33 drafted: IF-404 v1, mock, TC-IF-404-02 (port 22 as the refused example), test-spec row.

Local coder: `tests/test_tool_calls_web_log.py` (task `tls07-tests`, 1 attempt, 76 s); fixture and every statement identical to the instruction, but the six methods were written at module level, outside the class (the file compiled, the doc check passed, unittest ran 0 tests); indented by hand, `RUN` moved up; verdict `fixed`, lesson added (the check must run the file and count the tests).

Tests reported green (feedback, not verification): `tests/test_tool_calls_web_log.py` (6), `tests/test_web_tools.py`, `tests/test_events.py`, `tests/test_scholar.py`, `tests/test_fulltext_source.py`, `tests/test_script_checks.py`, the earlier tool tests, IF-404 (mock) and IF-402 contract suites.

Open for Phase 4:
- The real side of IF-404 never runs: `real_subject` has no provider for it and the suite's options (`search_down`, `max_bytes`, scripted pages) reach only the mock. A stage-2 run against the real web needs a provider class with `search`, `fetch`, `log` and a decision how the options map; an amendment for the owner.
- What leaves the host for a scholarly query (and the e-mail address) is T-05.

## T-05 Scholarly sources and the strict cut-off (2026-10-30/31, done) – REQ-TLS-003, IF-405

| Requirement | Where it is met | Test |
|---|---|---|
| REQ-TLS-003 one record format, strict cut-off, retracted works dropped and listed | `tool_calls.ToolCalls._scholar_search` over `scholar.Scholar.search`: records in the format of IF-405 with origin (`sources`), `trust` (`work_trust`, i.e. `TrustTable.for_work` as of the cut-off) and `retraction` (`scholar.retraction_state` as of the cut-off); a work retracted or withdrawn by the cut-off is dropped with reason `retracted` / `withdrawn` and listed; the cut-off stays `scholar.within` (strict: the latest day a date could mean), its reason now also as a code (`scholar.cutoff_code`: `no_date`, `after_cutoff`, `before_since`); `errors` as the list of IF-405 | `tests/test_tool_calls_scholar.py` (6) |
| IF-405 | `scholar.py` (unchanged but for the `code` of a dropped work); the door turns the result into the IF-405 shape; the real side of the contract suite stays skipped (stage 2: the real APIs) | contract suite (mock side) |

Decisions made while building (small, inside the contracts):
- The conversion to IF-405 is in the door, not in `Scholar.search`: the review and the tools read its result as it is; the dropped works only gain the key `code`.
- New parameters of the door: `work_trust(work, as_of)` and `retractions(work, errors)` (production: `Scholar.verify_retraction`, one Crossref request per kept work). Without `retractions` only what the sources reported themselves counts; without `work_trust` a record's `trust` is `None`. The wiring is N-2.4.1 T-07.
- A notice dated after the cut-off does not drop a work (`retraction_state(as_of=until)`, the rule of `scholar.use_as_of`): a run as of a past day must not know it.
- Dropped entries carry `title` and `detail` (the readable reason) besides IF-405's `ref` and `reason`; the reasons `retracted` and `withdrawn` are beyond the codes IF-405 v0 lists. Proposed for the next IF-405 version.

Local coder: `tests/test_tool_calls_scholar.py` (task `tls03-tests`, 1 attempt, 76 s); compared with the instruction by script: whitespace in three import comments, and one date (`"2001-12-01"`) dropped from the ten-date cut-off grid (the assertions still held without it); restored by hand, verdict `fixed`, lesson added. Red before the change (6 errors: unknown parameters), green after.

Tests reported green (feedback, not verification): `tests/test_tool_calls_scholar.py` (6), the other tool tests, `tests/test_scholar.py`, `tests/test_source_trust.py`, IF-402 and IF-405 (mock) contract suites; all `tests/test_*.py` in the image fail only as on master (`test_config`, `test_shutdown`, `test_harness`, `test_amendment_report`).

`source_record` (closed the same day at the owner's request): a reference `doi:10.…` or `10.…` asks `work_lookup(doi)` (production: `CrossrefClient.lookup`) for the full record and gives the trust class of `work_trust` and the retraction state (all notices: `source_record` has no cut-off); an unknown DOI is `source_error`; a URL is answered as before (trust by domain, `retraction: None`). Tests: 2 more in `tests/test_tool_calls_scholar.py` (8 in all), written by hand (two short methods in an existing file).
