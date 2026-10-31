# A-59: IF-102 v2, the suite on PostgreSQL, the delete notice, categories() and the real side by path (N-3.1 Verify F6, F7, F12; D-158, D-162)

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## What changes
| Installed file | Draft | Change |
|---|---|---|
| `contracts/IF-102-storage-interface.md` | `specs/mia/amendments/A-59/IF-102-storage-interface.md` | v2: a delete is told with `version: None` (golden 4, F7); `categories()`, the vote categories (golden 5, D-162); the tables and the delete rule follow IF-301/IF-302 (F12) |
| `tests/helpers/mocks/if_102_storage.py` | `specs/mia/contract-drafts/tests/helpers/mocks/if_102_storage.py` | delete tells the subscribers; `categories()` |
| `tests/acceptance/contract/test_if_102_storage.py` | `specs/mia/contract-drafts/tests/acceptance/contract/test_if_102_storage.py` | TC-IF-102-09 (delete notice), TC-IF-102-10 (`categories()`) |
| `tests/helpers/contract.py` | made by the script from the installed file, with `specs/mia/amendments/A-59/real_storage.py` | `_StorageAdapter` loads `storage`, `storage_files`, `storage_postgres` by file path with the real `graph_rules` and `graph_tables` (D-162): in one process the mock side cached the mock's `graph_rules`, and the real side of IF-102 then validated with the mock rules |
| `stages.yaml` | made by the script from the installed file | stage-3 step `contract-postgres`: `tools/contract_postgres.sh` (F6) |
| `specs/mia/test-spec.md` (not protected) | made by the script from the installed file | rows TC-IF-102-09 and -10 |

`contract.py` is shared with A-60 (N-3.2); both scripts build it from the installed file, so they install in either order.

## Checked on scratch copies (not installed, removed)
Branch v1-n31b plus the files of v1-n32b (A-60 and its `graph_rules.py` fixes), once A-59 then A-60, once A-60 then A-59: `contract.py` and `test-spec.md` came out identical, and a second run of both scripts changes nothing. In one process (IF-101, IF-102, IF-301, IF-302 suites, mock side first; venv mia312): 100 tests OK (3 IF-101 skips: no flask) on the file backend and on a throwaway PostgreSQL, in both orders. With a mutant of the real `graph_rules.py` (two adjacent data nodes accepted): installed, only `test_graph_rules_are_checked_on_write_real` (IF-102) and the IF-301 `_real` case fail, on files and on PostgreSQL; without A-59/A-60 the same mutant passes all 94 tests (the collision).

Install (on goal/v1 after the merge of v1-n31b): `bash tools/apply_amendment_a59.sh` (look), then `--do`; commit as "plan: A-59 installed".
