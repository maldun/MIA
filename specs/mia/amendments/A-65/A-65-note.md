# A-65: IF-102 v3, values no backend keeps alike are `invalid`/`schema` (N-3.1 re-verification R3a, D-168)

Status: **proposed** (draft for the owner; nothing protected is changed by the agent).

## What changes (all made by `tools/apply_amendment_a65.sh` from the installed files; A-59 must be installed)
| Installed file | Change |
|---|---|
| `contracts/IF-102-storage-interface.md` | v3: an Errors row "a text with a NUL character (document, keys, id), a number that is not finite (NaN, inf) or an id that is not text: `invalid`, rule `schema`, nothing stored"; title and version line |
| `tests/helpers/mocks/if_102_storage.py` | `put` refuses these values (`specs/mia/amendments/A-65/mock_unstorable.py`) |
| `tests/acceptance/contract/test_if_102_storage.py` | TC-IF-102-11 (`specs/mia/amendments/A-65/suite_case.py`), mock and real |
| `specs/mia/test-spec.md` (not protected) | the row of TC-IF-102-11 after TC-IF-102-10 |

The anchors are lines only A-59 wrote, so A-62 (IF-101; it also changes `contract.py` and `test-spec.md`) can be installed before or after A-65. `contract.py` is not touched.

## Checked on scratch copies (removed)
Branch v1-n31c plus the A-62 files of v1-n11b: A-65 then A-62, and A-62 then A-65. The five shared files came out identical in both orders, and a second run of A-65 changes nothing. IF-102 suite: 22 tests OK on mock and files, and 22 OK on mock and a throwaway PostgreSQL (11 cases each side). TC-IF-102-11 is red on the A-59 mock.

Install (on goal/v1 after the merge of v1-n31c): `bash tools/apply_amendment_a65.sh` (look), then `--do`; commit as "plan: A-65 installed".
