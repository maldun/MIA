# A-66: `max_cycles: 2.0` in the JS graph mock, the real side of TC-IF-104-06, the record of TD-06 (N-3.2 re-verification R1, R2)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The re-verification of N-3.2 (verification-report.md, "Re-verification") found: (R2) the JS mock of IF-104 accepts `max_cycles: 2.0` in a JSON body (JavaScript reads it as the integer 2) while the real rules refuse it as a float, and the row TC-IF-104-06 claims "2 (real)" although the JS real side skips; the real route is checked by `tests/test_graph_api.py`. (R1) TD-06 does not meet the deferral format (trace_check: 3 errors, 1 warning). The owner decided (D-169): `2.0` is refused (a positive integer, D-160), the mock follows the real rules, the row points at the real-route test, TD-06 and REQ-GTB-004 get the Relaxed/Target lines, a skip reason and a dated trigger.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `tests/helpers/mocks/if_104_graph_api.mjs` | `specs/mia/contract-drafts/tests/helpers/mocks/if_104_graph_api.mjs` | `fetch` parses the body with the reviver `keepFloatLimits`: a `max_cycles` or `max_seconds` written with a fraction or an exponent (`2.0`, `1e0`) keeps its source text, so `stops()` refuses it (needs the source text of `JSON.parse`, Node 21+; the host has Node 22) |
| `tests/acceptance/contract/test_if_104_graph_api.test.mjs` | `specs/mia/contract-drafts/tests/acceptance/contract/test_if_104_graph_api.test.mjs` | TC-IF-104-07: a hand-written body with `max_cycles: 2.0` is 422 `session_stopping_criterion`, with `2` it is saved (JSON.stringify cannot write `2.0`) |
| `specs/mia/test-spec.md` | made by the script from the installed file | row TC-IF-104-06: "1 (mock); real: `tests/test_graph_api.py` `test_a_session_limit_that_is_not_a_positive_integer_is_422`"; new row TC-IF-104-07 (real: `test_graph_rules.test_a_session_limit_is_a_positive_integer`) |
| `specs/mia/deferred.md` | made by the script from the installed file | TD-06: `Trigger: root task T-10, or 2026-12-31, whichever first`; `Target check: skip: library/workflows is missing (root task T-10); …` |
| node `requirements.md` | made by the script from the installed file | REQ-GTB-004: `Relaxed: TD-06`, `Target: …`, History A-66 |

`test-spec.md`, `deferred.md` and `requirements.md` are built from the installed files at install time (A-62 and A-65 also change `test-spec.md`), so the order of installation does not matter; each edit refuses when its anchor is not found exactly once, and a second run reports "unchanged".

Unchanged: the text of IF-301 and IF-104 (D-160 already says a limit is an integer; `2.0` is not one), the Python suites, `decomposition.yaml` (IF-301 version at the gate, D-169).

## Checked on a scratch copy (not installed)
See the implementation log of N-3.2, section "Re-verification findings".

Install (on goal/v1 after the merge of v1-n32c): `bash tools/apply_amendment_a66.sh` (look), then `bash tools/apply_amendment_a66.sh --do`, commit as "plan: A-66 installed".
