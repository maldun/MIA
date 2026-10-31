# A-60: IF-301 v1, session limits and malformed parts (N-3.2 Verify F1, F2, F9)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The verification of N-3.2 found that a malformed edit (a `stop` that is not an object, an edge endpoint that is a list) crashed the graph rules, so `PUT /api/workflows/<id>` answered HTTP 500 (F1), and that the session rule took any truthy limit (`-1`, `"0"`, `true`, NaN; F2). The owner decided (D-160): a session limit is a positive integer (an int >= 1, not a bool), IF-301 says so in a text amendment, the mock follows. The real side is fixed test-first on branch v1-n32b (`graph_rules.py`). F9: `tests/helpers/contract.py` still said "N-3.2 Graph tables not integrated yet" for IF-301 although `real_subject` gives `graph_tables` since A-02.

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `contracts/IF-301-graph-tables.md` | `specs/mia/amendments/A-60/IF-301-graph-tables.md` | v1: "any document gives a rule or None, never an exception"; the rules `node_identity` and `session_stopping_criterion` in detail (a limit given is an int >= 1, not a bool; `null` = not given; a `stop` that is not an object; an endpoint that is not text); golden 4; version line |
| `tests/helpers/mocks/graph_rules.py` | `specs/mia/contract-drafts/tests/helpers/mocks/graph_rules.py` | the mock's rules as above (`_stops`, the edge endpoint check). The mock of IF-102 uses the same file, so it gets stricter too |
| `tests/acceptance/contract/test_if_301_graph_tables.py` | `specs/mia/contract-drafts/tests/acceptance/contract/test_if_301_graph_tables.py` | TC-IF-301-04 (golden 4) on the mock and the real side |
| `tests/helpers/contract.py` | made by the script from the installed file, with `specs/mia/amendments/A-60/real_graph_tables.py` | (F9) the IF-301 line of `REAL_NOT_READY`: "unused: real_subject gives graph_tables" with a comment (A-02, A-60). (New finding) `real_subject("IF-301")` loads `graph_tables` with the real `graph_rules` by file path (`_real_graph_tables`): the mock side of the suite imports the mock's `graph_rules` first under the same module name, and a plain `import graph_tables` then validated with the cached **mock** rules, so the `_real` tests of the whole suite ran the mock rules (run alone they ran the real ones) |
| `specs/mia/test-spec.md` | made by the script from the installed file | the row TC-IF-301-04 |
| node `requirements.md` | made by the script from the installed file | IF-301: Verified by TC-IF-301-01..04, History v1 (A-60) |

`contract.py`, `test-spec.md` and `requirements.md` are built at install time from the installed files, so A-59 (N-3.1, also touches `contract.py`) and A-60 can be installed in either order.

Unchanged: the existing suite cases (the case `max_cycles: 0` stays), `decomposition.yaml` (IF-301 `version: v0`, node status: at the gate, F9), the JavaScript mock of IF-104 (`tests/helpers/mocks/if_104_graph_api.mjs`, it has its own copy of the session rule and still takes any truthy limit: owner to decide whether IF-104's mock follows).

The same module-name collision exists for the real side of IF-102 (`storage.py` imports `graph_tables`, which then gets the mock's `graph_rules` when the IF-102 mock ran first in the process): not changed here, `_StorageAdapter` belongs to N-3.1 and stays as it is (D-158); owner to decide.

## Owner to confirm
A limit that is `null` counts as not given (so `{"max_cycles": 3, "max_seconds": null}` is valid). D-160 says nothing about `null`; this reading keeps a form that sends an empty field working.

## Checked on a scratch copy (not installed)
A copy of branch v1-n32b (with the F1/F2 fixes), script run `--do`: all six files updated; a second run reports everything unchanged (`--do` is safe to repeat). Host: the IF-301 suite 8 tests OK (4 mock, 4 real, none skipped), the IF-102 suite OK. In the image (one container at a time): the IF-301, IF-102, IF-104 (Python) and IF-203 suites, N-3 steps 00 to 03, `test_graph_rules.py`, `test_graph_tables.py`, `test_storage.py`, `test_graph_api.py`: all OK. Before the install, TC-IF-301-04 failed on the old mock (10 sub-cases) and, in the full suite, on the real side too (the collision above); after it, a mutant of the real `graph_rules.py` (a limit counts when truthy) turns only `..._real` red (6 sub-cases), so the real side now tests the real rules. A fuzz of 20 000 random documents: the drafted mock and the real rules never raise; the installed mock raises 712 times.

Install (on goal/v1 after the merge of v1-n32b): `bash tools/apply_amendment_a60.sh` (look), then `bash tools/apply_amendment_a60.sh --do`, commit as "plan: A-60 installed".
