# Start prompt for the parent session: install A-121 (snapshot contracts)

Read `CLAUDE.md`, then `specs/mia/goals/G-V2/parallel-work.md` (the parent session owns `contracts/`). Task: install the contract text of A-121, nothing else.

Inputs (all in `specs/mia/amendments/`): `A-121-draft-IF-203-v2.md` (approved as a whole, D-243), `A-121-contract-edits.patch` (the three contract edits, checked with `git apply --check` against master `7250239b`), `A-121-review-log-line.md` (the review-log row).

Steps:
1. `git status`: `contracts/IF-101-chat-api.md` and `contracts/IF-201-chat-turn.md` have edits that are not yours. Do not stage, change or discard them. Stage by path only, never `git add -A`.
2. Confirm IF-301 v2 is on master (`head -1 contracts/IF-301-graph-tables.md` says v2; it was, on 2026-11-17). The kind `skills` of IF-203 v2 depends on it.
3. Re-run `git apply --check specs/mia/amendments/A-121-contract-edits.patch`. If it fails (another session changed one of the three contracts), stop and report which hunk; do not hand-merge IF-302 numbering: v13 is the owner's decision (v12 is A-154).
4. Read the patch once against the draft (new rows, error rows, golden 8 to 12, the three version rows). Then `git apply` it. Touched files: `contracts/IF-203-workflow-library.md` (v2), `contracts/IF-302-record-tables.md` (v13), `contracts/IF-102-storage-interface.md` (v7).
5. Append the row of `A-121-review-log-line.md` to `specs/mia/review-log.md`: take the next free D-number at that moment (the draft says D-347; check the last row first), fill in the date, change nothing else. The log is append-only.
6. Checks: `python3 -I tools/check_d_numbers.py` (the 2 D-182 collisions are known), the traceability command of CLAUDE.md (no new errors for REQ-WFM-061 to 066), and the existing contract suites `tests/acceptance/contract/test_if_203_workflow_library.py`, `test_if_203_v1_transforms.py`, `test_if_302_record_tables.py`, `test_if_102_storage.py` with `/home/maldun/prog/Python/venvs/mia312/bin/python` (they test v0 to v6 behaviour and must stay green; TC-IF-302-01 may now fail because the set of tables changed: report it, do not edit the protected suite).
7. One commit, paths named: the three contracts and `review-log.md`, message `plan: A-121 installed, IF-203 v2, IF-302 v13, IF-102 v7 (REQ-WFM-061 to 066)`, ending with the Co-Authored-By line.

Do not touch: `tests/acceptance/`, `tests/helpers/` (protected; they need the owner's go after this commit), `plausibility.yaml`, `test-requirements.md`, the CONVERT folder.

Stop and report if: the patch does not apply, a contract changed meanwhile, a check outside the known ones turns red, or you think the text of the draft is wrong.

After the commit tell the owner (maldun): contracts are installed; next are the IF-203 v2 contract suite, the mock extension (kinds `skills` and `snapshots`, the four snapshot operations, `set_current_version`, `pins`, `forbidden`) and the amendment of TC-WFM-063 to 065, `snapshot_lab.py` and `snapshot_store.py` to `set_current_version`; all protected, so they need the owner's go. Only then T-CV-05 can be implemented in the CONVERT session.
