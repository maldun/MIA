# IF-402 – Tool calls, v3

Owner (provider): N-2.4.2 Tools and sandbox   Consumers: N-2.4.1 Pipeline runner   Decided by: N-2.4   Mock complexity: 3 (counted calls, trust labels, scripted tools)   Suite: `tests/acceptance/contract/test_if_402_tool_calls.py`

The one door to everything a workflow step may do besides a model call. A tool knows no particular workflow. Python calls; draft v0 from `checks.py`, `number_gate.py`, `sandbox.py`, `web_tools.py`, `scholar.py`, `source_trust.py`.

## Operation
`call(run, tool, args)`: `run` = `{"id", "limits": {tool: max calls}}` (the budgets of the run); returns `{"output", "trust"}` where `trust` is `code` (computed by code), `web` (text from the web or a paper, untrusted), or `model`.

| Tool | Arguments | Output |
|---|---|---|
| `number_check` | `claim`, `evidence` (list of text) | `{"status": "pass" \| "fail" \| "inconclusive", "detail"}`; a number is a pass if it agrees with a number of the evidence within rounding |
| `quote_in_source` | `quote`, `source_text` | `{"status": "pass" \| "fail"}`; the quote must occur verbatim |
| `schema_check` | `value`, `schema` | `{"status": "pass" \| "fail", "problems"}`; each problem is a readable text that names the path and the key or rule (`$: missing 'reason'`), the text a retry tells the model |
| `run_script` | `code`, `inputs` | `{"status": "ok" \| "unavailable" \| "failed", "stdout", "result"}`; `ok` only for a script that ran to its end; without a sandbox (also one that went away during the call): `unavailable`, nothing runs; a script that was rejected, crashed or timed out: `failed`; `result` is the full result of the script check (status, detail, evidence) |
| `web_search` | `query` | list of `{url, title, content}` |
| `fetch_page` | `url`, `max_chars` (optional) | `{"ref", "url", "title", "text", "clipped", "signals"}`: the whole page as untrusted text, clipped to `max_chars`; `signals` are the phrases that look like instructions to a model |
| `fetch_passages` | `url`, `question` | `{"ref", "hash", "passages": [{"id","quote"}]}`; every passage keeps its source reference |
| `scholar_search` | `query`, `until`, `since` | `{"works", "errors", "dropped"}` as IF-405; every dropped work is `{"ref", "title", "reason", "detail"}`, the reasons of IF-405 plus `retracted` and `withdrawn` (as of `until`) |
| `source_record` | `ref` | `{"ref","class","trust","retraction"}` |

## Errors
| Condition | Signal | What the consumer may rely on afterwards |
|---|---|---|
| unknown tool | `ServiceError("unknown_tool")` | nothing counted |
| arguments the tool does not take (missing or unknown) | `ServiceError("bad_arguments", detail=…)` | nothing counted |
| the tool's limit for this run is used up | `ServiceError("budget", detail=tool)` | nothing executed, nothing counted |
| the web or a source refuses or fails | `ServiceError("source_error", detail=…)` | the budget is counted; other tools work |
| no sandbox | `run_script` output status `unavailable` | the operation is refused, never weakened |

## Bounds
| Quantity | Bound | Source |
|---|---|---|
| every output | carries its trust label | NFR-3, REQ-BE-064 |
| what leaves the host | only the text of a web or scholarly query | NFR-5 |

## Golden examples
1. Typical: `number_check("The tower is 1,200 m high", ["The tower is 1,020 m high"])` is `fail` with trust `code`.
2. Failure: the second `web_search` of a run with limit 1 is `budget`; `run_script` without a sandbox is `unavailable` and nothing ran.
3. Edge: a quote that is not verbatim in the source fails `quote_in_source`; `fetch_passages` returns the source reference with every passage.
4. Typical: `fetch_page("https://example.org/a")` returns the text of the page with its reference and trust `web`; an unknown page is `source_error`.

## Version history
| Version | Date | Change | Amendment |
|---|---|---|---|
| v0 | 2026-10-25 | first draft from the current tools | – |
| v1 | 2026-10-30 | `schema_check` problems are readable texts with path and key, as `schema_check.py` gives them | A-32 |
| v2 | 2026-10-31 | `fetch_page`: the whole page, the tool the research pipelines read pages with, so the runner reaches it through the door (REQ-RUN-012, D-122) | A-34 |
| v3 | 2026-10-31 | `run_script` status `failed` and its `result`; the dropped works of `scholar_search`; the error `bad_arguments` (findings 6, 8, 11 of the N-2.4.2 verification, D-132) | A-42 |
