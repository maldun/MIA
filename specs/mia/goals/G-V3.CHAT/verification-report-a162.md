# Verification report A-162 (REQ-EVL-012 to 015), 2026-11-20

Reader: a session that did not write the code (read of the plan package, `harness.py` at `76708761`, the tests; not of the chat). Verdict: **Verified, no findings, one note.**

| Requirement | Code | Checks | Result |
|---|---|---|---|
| REQ-EVL-012 options of the step with the pin's seed and temperature | `Harness._digest`, `call(messages, options)` merges `{**options, **fixed}` | TC-EVL-012 (`tests/acceptance/test_eval_digest_production.py`) | pass |
| REQ-EVL-013 pin's `num_ctx` in every call | `fixed` takes `num_ctx` from the pin; `PINS["MP-light"]["num_ctx"] = 8192`; run header holds it | TC-EVL-013 | pass |
| REQ-EVL-014 input by reference (path, SHA-256) | `read_reference`; scorer gets `dict(case, input=data)` | TC-EVL-014, `tests/test_harness_reference.py` | pass |
| REQ-EVL-015 bad reference stops the run, names the case | `InputReferenceError(SuiteError)` re-raised by `_run_case`; pre-check over all selected cases in `run()` | TC-EVL-015 | pass |

Runs: acceptance file 5 of 5, `test_harness_reference` 2, `test_harness` (1 expected failure, as before), `test_harness_converted`, `test_eval_cli`, `test_eval_cli_converted`, `test_skill_digest`: all OK.

## Mutations (each restored afterwards, `git status` of `harness.py` clean)
| Mutant | Caught by |
|---|---|
| `with_options=True` removed | acceptance test (1 failure) |
| `num_ctx` dropped from `fixed` | acceptance test (1 failure) |
| hash check made always true | acceptance test and reference test |
| pre-check in `run()` removed | reference test |
| pin and step options swapped (the step wins) | **not caught** |

Note N-1 (no action): the last mutant survives because the digest step has only `num_predict` in its options today (`skill_digest.OPTIONS`), so the order is not observable. The requirement text ("merged with") does not demand a precedence; the code makes the pin win. A test is due only when a step option can collide with the pin.

Known and accepted (hand-over): the REQ-EVL-015 error stops the whole run, not one case; the `result_ref` form is documented in the A-162 draft only. No suite, label or baseline changed.
