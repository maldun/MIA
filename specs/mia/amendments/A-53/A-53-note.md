# A-53: IF-401 v2, the secret rule and the comparison pinned (N-2.4.3, D-148)

Status: **proposed** (drafts for the owner to read and install; nothing protected is changed by the agent).

## Why
The re-verification of N-2.4.3 (2026-10-31) found: N1, the IF-401 suite does not pin the rules of D-144 (the old type exemption of `events.redact` and the mutants "types only" and "length ignored" of `RunEvents.compare` keep it green on mock and real); N2, the contract says a secret-like key is "stored as `[removed]`" with no exception, while the code keeps an empty text `""` (D-146); F9, the suite fails the test-doc rules T2 and T3. D-148: one IF-401 amendment for all three.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `contracts/IF-401-run-events.md` | `specs/mia/amendments/A-53/IF-401-run-events.md` | v2: the row of `emit` (a value under a secret-like key, at any depth, is `[removed]` whatever its type; `""` stays, D-144, D-146), the row of `compare` (same types with another payload, an extra event also at the end, is a difference), golden examples 2 and 3, the version line |
| `tests/helpers/mocks/if_401_run_events.py` | `specs/mia/contract-drafts/tests/helpers/mocks/if_401_run_events.py` | `_clean` keeps `""` under a secret-like key (it removed it, against D-146); numbers, lists and objects were already removed |
| `tests/acceptance/contract/test_if_401_run_events.py` | `specs/mia/contract-drafts/tests/acceptance/contract/test_if_401_run_events.py` | TC-IF-401-02: text, number, `null`, list and object under secret-like keys (top level and nested) become `[removed]`, `""` stays, other keys keep their values; TC-IF-401-04: run d (same types, `run_end` `{"status": "failed"}`) and run e (an extra `check_run` at the end) differ from a. Every test has an `Example:` line and Given/When/Then comments (F9). No new test ids |
| `specs/mia/test-spec.md` | made from the installed file by `tools/apply_amendment_a53.sh` | the rows of TC-IF-401-02 and -04 name v2 (A-53) and the new rules |

No code change: `events.redact` and `RunEvents.compare` follow these rules since the fixes of D-144 (v1-n243b). The keys in the new cases (`password`, `token`, `api_key`, `secret`) are secret-like for both the mock (substring) and the real log (`events._SECRET_KEY`).

## Checked on a scratch copy (not installed)
`git archive` of goal/v1 @ 40fff9c with the drafts, `bash tools/apply_amendment_a53.sh --do`: the IF-401 suite in the image (`--network none`) 10 tests OK, none skipped (5 mock, 5 real); a second run of the script reports nothing to do. The new suite against the old mock: TC-IF-401-02 mock fails (`'[removed]' != ''`), so the mock draft is needed. Mutants of the real provider, each turns exactly one real test red: redact keeps numbers/booleans/`None` (the old rule), redact keeps everything but texts, redact removes `""` too (TC-IF-401-02); compare by types only, compare ignores the length (TC-IF-401-04). `test_doc_check.py` on the drafted suite: 0 findings (was 4×T2, 4×T3).

Install (on goal/v1): `bash tools/apply_amendment_a53.sh` (look), then `bash tools/apply_amendment_a53.sh --do`, commit as "plan: A-53 installed".
