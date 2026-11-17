# A-155 – The run report is a file of its own in `files` (proposed 2026-11-16, found by T-01)

Status: **Proposed**; needs the owner (two protected checks and the IF-101 mock change; `protected.patch` in this folder, built in a sandbox copy, the protected files were not edited).

## Finding (T-01)
The real service stores the run report as a file of its own, as decided (D-341, decision 2). Two approved contract checks assume that the files of a run are only the files the skill stored, and fail in their `_real` variants:

| Check | Assumption | Real behavior |
|---|---|---|
| TC-IF-101-30 (`test_the_files_of_a_task_are_listed_and_downloaded_and_there_is_no_delete`) | `files_changed` and the files list hold only `review-contract.md` | a second file, the run report, follows it |
| TC-IF-101-35 (`test_the_run_that_is_shown_and_a_run_by_its_id`) | `files == ["review-contract.md"]` | `["review-contract.md", <run report>]` |

`chat_done` still names only the skill's files (`done["files"] == ["review-contract.md"]`, TC-IF-101-37): the report is stored after the message is done.
A third existing check, an unprotected unit test (`tests/test_chat_tasks.py`, TC-WFM-037/038), was changed in the T-01 commit.

## Change (no requirement changes)
- TC-IF-101-30: the file of the skill, then the run report (`files_changed` twice, the list holds both).
- TC-IF-101-35: `files == ["review-contract.md", record["report"]]`.
- TC-IF-101-41 docstring example follows.
- The IF-101 mock gives every ended run a report file of its own, after `chat_done` (before: only a failed or stopped run, the done run's report was the skill's file; that was the mock's mistake, A-154 plan step 4).

Result in the sandbox: `test_if_101_chat_api.py` 82 tests OK (2 skipped as before), mock and real.

## To install (owner)
```
git apply specs/mia/goals/G-V3.REPORT/amendment-a155/protected.patch
git add tests/acceptance/contract/test_if_101_chat_api.py tests/helpers/mocks/if_101_chat_api.py
git commit -m "test: A-155 the run report is a file of its own in files (TC-IF-101-30, -35, mock)"
```
