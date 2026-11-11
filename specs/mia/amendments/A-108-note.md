# A-108: wording of task T-06, record-only skills (G-V2.MODEL, owner's decision (c) of 2026-11-08)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a108.sh` is not yet run with `--do` in the repository.

## What is wrong in the installed text
A-107 (installed) wrote into `plan.md` task T-06 that a record-only skill (a record, but no manifest folder or entry module) "is listed by its command" and that `TaskRegistry.commands` shows the record's command. T-06 was built smaller, as the owner decided under (c) on 2026-11-08: such a skill is **not a `Task`**, is not in `TaskRegistry.commands()`, is not runnable, causes no problem report and is not found by `TaskRegistry.parse`; it is listed through `SkillCatalog.list()` only, until G-V2.CONVERT moves the skills one by one. The tests (`tests/test_skill_catalog_loader.py`) pin exactly that. The Verify reports already state the code correctly; only the plan text and point 1 of `A-107-note.md` say more than the code does.

## What A-108 contains
| File | Change |
|---|---|
| `goals/G-V2.MODEL/plan.md` | T-06: test (3) and the notes reworded to the decision above |
| `review-log.md` | row D-310 appended; it also says that A-108 supersedes point 1 of `A-107-note.md` (that note stays unchanged: an installed amendment record is history) |
No code, test, protected file, contract or requirement text changes. The wording is not part of a requirement text, so no requirement comes back in review (the review fingerprint covers requirement blocks, not `plan.md`).

## Points for the owner
1. A one-sentence correction of a plan text; if you prefer, skip the amendment and let D-310 alone stand: say so and I drop the script.
2. ID choice: A-108 follows A-107; D-310 follows D-309.

## Checked by the drafter (scratch copy; nothing installed in the repository)
`--do` three times: runs 2 and 3 change nothing; the look-only run changes nothing; the old phrase "listed by its command" no longer occurs in `plan.md` afterwards.

## Install
```
bash tools/apply_amendment_a108.sh --report     # look only
bash tools/apply_amendment_a108.sh --do         # then commit "plan: A-108 installed"
```
