# A-96: undo the unexplained changes of plausibility.yaml (F-05)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a96.sh` is not yet run with `--do` in the repository.

## Owner's decisions (2026-11-08, questionnaire on F-05)
| Part of F-05 | Decision |
|---|---|
| 4 records REQ-API-004, REQ-API-007, REQ-VPB-002, REQ-CLV-011 lost their record | restored by re-rating on the current text: A-95 (installed, `3421746`) |
| `rated_by` renamed `maldun` -> `Stefan Reiterer` (464) and accepted-risk owners (42) | **restore `maldun`** |
| `rated` dates reset to 2026-11-07 (433) and accepted-risk `decided` dates | **restore the original dates** |
| 31 reworded `basis` texts | **show the pairs first** (`A-96-basis-pairs.md`), decision open |
| nine requirements without any record (REQ-CLV-023, REQ-WFM-031, 033, 034, 035, 037, 039, 059, 068) | rate them now (A-97, separate) |

## What A-96 does
For every record that is in the tag `plan-baseline-it2-store` and in the file now with the **same rating and the same basis** (433 records), it sets `rated`, `rated_by` and, where the record has one, `accepted_risk.decided` and `accepted_risk.owner` to the values of the tag. Not touched: records added since the tag (including the five of A-95), the 31 records with a reworded basis, every rating, every basis, the layout of the file (the same number of lines).

## Checked by the drafter (scratch copy)
- `--do` twice: the second run changes nothing (checksum identical); 950 lines change, none added or removed.
- All 433 restored records are identical to the tag as data (0 differ).
- What still differs from the tag after A-96: 38 added records, and 35 records with a different basis and `rated_by` (the 31 below and the four of A-95). No rating differs. `req_plausibility` then reports the nine missing records as errors and nothing else new.

## The 31 reworded bases (`A-96-basis-pairs.md`)
- All 31 new bases are the **same generic sentence** ("no number, measurement or model quality depends on it; the behaviour is fixed by an acceptance criterion and a contract mock (proposal)"); the old bases were specific to the requirement (for example REQ-GTB-009: "the registry maps a type ID to a class ...").
- All 31 were rated at the tag on **2026-11-07 by `maldun`**, so the date is real; only the rater name differs.
- Proposal (needs your decision): restore the old basis and `maldun` for these 31 as well. This is a small extension of the script (one more list of records), not drafted yet.

## Install
```
bash tools/apply_amendment_a96.sh --report     # look only
bash tools/apply_amendment_a96.sh --do         # then commit "plan: A-96 installed"
```
