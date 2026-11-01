# A-68: the smoke gate drops `--model`; the holdout guard tests see a read (N-4.1 re-verification R1, R4)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The re-verification of N-4.1 (verification-report.md, "Re-verification") found two things in protected tests; the owner decided both on 2026-11-01 (D-172):
- (R1) `tests/smoke/smoke_gate.py` starts `tools/eval.py run ... --model gemma4:12b-it-qat --pin MP-light`. Since D-166 the pin decides the model and `--model` next to `--pin` is refused, so SMOKE-GATE-001 and -002 stopped before any case ran (red by construction). The pin already names the same model and digest (`MP-light`, checked by SMOKE-GATE-002).
- (R4) the fixtures of `HoldoutSuitesOnTheCommandLine` are valid suites, so a holdout suite that is read and then refused looks the same as one that is refused unread: two mutants survived (the early refusal in `open_suite`, `holdout=args.holdout` in `list`). The tests now watch the calls of `harness.load_suite`.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `tests/smoke/smoke_gate.py` | `specs/mia/amendments/A-68/tests/smoke/smoke_gate.py` | the command of `run_smoke_cases` has no `--model`; a comment says why. `MODEL` stays for the digest lookup |
| `tests/acceptance/test_decide_guard.py` | `specs/mia/amendments/A-68/tests/acceptance/test_decide_guard.py` | `HoldoutSuitesOnTheCommandLine.watch_reads` records the folders `harness.load_suite` is asked to read; `test_list_shows_no_holdout_suite` and `test_cases_and_run_refuse_a_holdout_suite_without_the_flag` assert that `toy.holdout` is not among them |

Unchanged: every other test, the requirements, the suites.

## Checked on a scratch copy of v1-n41c (not installed)
- `tests/acceptance/test_decide_guard.py`: 11 tests OK with the real code.
- Mutant "early refusal in `open_suite` removed": `test_cases_and_run_refuse_a_holdout_suite_without_the_flag` fails. Mutant `list_suites(SUITES, holdout=True)`: `test_list_shows_no_holdout_suite` fails. Both passed before.
- The smoke command line of the draft is no longer refused by `eval.py` (the host lacks the `ollama` package, so the run itself was not made; `smoke_gate.py` against a live Ollama stays with the owner, Phase 6).

Install (on goal/v1 after the merge of v1-n41c): `bash tools/apply_amendment_a68.sh` (look), then `bash tools/apply_amendment_a68.sh --do`, commit as "plan: A-68 installed".
