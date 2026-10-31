# A-63: the TC-EVL tests become protected acceptance tests (N-4.1, D-164 F6)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
Verify F11 of N-4.1: the TC-EVL tests were written in the implementation commits and live in the unprotected `tests/`, while plan.md says the tests are written first and installed by the owner. The owner decided (D-164, F6) that they move to the protected `tests/acceptance/` by this amendment. Their content is that of branch v1-n41b after the Verify fixes (F1 to F12): every test has its TC id first, an `Example:` line and Given/When/Then, so `test_doc_check.py` (T1 to T4) reports nothing for them in `tests/acceptance/`.

## What changes
| Installed file | Change |
|---|---|
| `tests/acceptance/test_eval_platform.py` (new) | TC-EVL-001, -004, -008, -011 and the regressions of F2, F3, F7, F8, F12 |
| `tests/acceptance/test_decide_guard.py` (new) | TC-EVL-002 and the regressions of F5a, F5b (synthetic fixtures, no real holdout) |
| `tests/acceptance/test_judge_calibration.py` (new) | TC-EVL-003 and the three mutant killers of F6 |
| `tests/acceptance/test_check_baselines.py` (new) | TC-EVL-005 |
| `tests/acceptance/test_skill_path_doc.py` (new) | TC-EVL-006 |
| `tests/acceptance/test_measure_latency.py` (new) | TC-EVL-007 (latency half) and the regression of F1 |
| `specs/mia/nodes/N-4-evaluation-operation/nodes/N-4.1-evaluation/test-spec.md` | built from the installed file: one note line under "Test cases"; the Setup cell of each of the nine rows names its test file |
| `docs/skill-path.md` | built from the installed file: names `tests/acceptance/test_skill_path_doc.py` as the test of its examples |
| `tests/test_<name>.py` (the six old copies) | removed by the script, only after all six protected tests passed |

The drafts are the old files with three path lines one folder deeper (`REPO`, `helpers`, `tools`) and the `Run:` line; nothing else. The script refuses to install when an old copy changed after the drafts were made (the protected copy must be what was reviewed); `A63_DRAFT=1 bash tools/apply_amendment_a63.sh` redrafts.

Unchanged: the tests themselves, every requirement marker (`trace_check.py` finds them in `tests/acceptance/` as before), `tests/js/measure-fps.test.mjs` (the frame-rate half of TC-EVL-007; `tests/acceptance/` has no JavaScript runner yet), `.claude/settings.json` (its rule `Edit(tests/acceptance/**)` protects the new files).

Install (on goal/v1 after the merge of v1-n41b): `bash tools/apply_amendment_a63.sh` (look), then `--do` (installs, runs the six protected tests on the host, removes the old copies), commit as "plan: A-63 installed".
