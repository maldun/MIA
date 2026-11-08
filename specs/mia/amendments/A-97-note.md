# A-97: plausibility records for nine requirements of other goals (F-14)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a97.sh` is not yet run with `--do` in the repository.

## Why
The global `req_plausibility` run shows nine requirements without any record: REQ-CLV-023 and REQ-WFM-031, 033, 034, 035, 037, 039, 059, 068 (finding F-14 of the third Verify run). All are `Draft` and belong to Workflow-management goals that are not built yet, so they are not a blocker of G-V2.STORE; the owner chose to rate them now. All nine were rated **plausible** on 2026-11-08 (REQ-WFM-031, 033, 035 and 037 after a second question; REQ-WFM-059 although its numbers are open: the basis says the rating is of the rule, not of a number).

## What the script does
Inserts nine records in sorted place in `specs/mia/plausibility.yaml` (`rated_by: maldun` as decided for A-96, `rated: '2026-11-08'`, `hardware: HW-target`, one basis text per requirement that names what the check rests on). Nothing else in the file changes. A record that is there already is skipped.

## Checked by the drafter (scratch copy)
- `--do` twice: the second run changes nothing (checksum identical); 63 lines added; the keys stay sorted (515 items, was 506).
- After `--do`: `req_plausibility` over all `requirements.md` files reports no missing record.
- With A-96 in either order the result is the same file (checksum identical).
- Warnings of kind "numeric bound without claim" are not changed by A-97 (35 of them in the file now; REQ-WFM-034 and REQ-WFM-031/033 may add to them). No reference was invented.

## Install
```
bash tools/apply_amendment_a97.sh --report     # look only
bash tools/apply_amendment_a97.sh --do         # then commit "plan: A-97 installed"
```
