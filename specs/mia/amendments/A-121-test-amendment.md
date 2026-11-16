# Amendment of the protected CONVERT tests after A-121 (D-241, D-240)

Date 2026-11-15, owner go ("go", deny rules lifted for this step only and restored after the commit). Changes against tag `plan-baseline-it2-convert`:
- `tests/helpers/snapshot_lab.py`: `LibraryLab.restore` (pointer meaning) is now `set_current_version`; `restore` is back to the IF-203 v0 meaning (new version with the old content, not used by snapshot code); `set_lifecycle` takes `evidence=None` (assumption 6).
- `tests/acceptance/test_skill_snapshots.py`: two tests added for TC-WFM-063: names never overwrite (`Conflict`, suffix " (2)", D-240 O3) and failure in the middle of a restore (roll back, automatic snapshot stays, D-240 O4). No existing test changed.
- `snapshot_store.py` (stub, not protected): `Conflict` added, docstrings name `set_current_version`.

Result: `test_call_recording` OK; `test_skill_snapshots` 8 tests, all red on the stub; `test_skill_conversion` unchanged (19 failures). A throwaway reference implementation (outside the repo) turned all 8 snapshot tests green.
Open: the test-spec row of TC-WFM-063 should mention the two added scenarios (owner's list of protected-doc changes if test-spec is protected).
