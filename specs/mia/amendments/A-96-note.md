# A-96: undo the unexplained changes of plausibility.yaml, one rater name (F-05)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a96.sh` is not yet run with `--do` in the repository.

## Owner's decisions (2026-11-08)
| Part of F-05 | Decision |
|---|---|
| 4 records REQ-API-004, REQ-API-007, REQ-VPB-002, REQ-CLV-011 lost their record | restored by re-rating on the current text: A-95 (installed, `3421746`) |
| `rated_by` renamed `maldun` -> `Stefan Reiterer` (464) and accepted-risk owners (42) | restore `maldun` |
| `rated` dates reset to 2026-11-07 (433) and accepted-risk `decided` dates | restore the original dates |
| 31 reworded `basis` texts (all the same generic sentence) | **restore the old bases** (`A-96-basis-pairs.md` shows old and new) |
| name of the rater | **`maldun` everywhere** in the file: `maldun` is the nickname of Stefan Reiterer; the records of A-95 and the added ones follow |

## What A-96 does (one script, three steps)
1. For every record in the tag `plan-baseline-it2-store` and in the file now with the same rating (464 records: 433 with the same basis, 31 with a reworded basis), `rated`, `rated_by` and, where there is one, `accepted_risk.decided` and `accepted_risk.owner` are set to the values of the tag.
2. For the 31 reworded records the **basis of the tag** is restored (lines copied exactly from the tag). The four records of A-95 keep their basis (re-rated on their current text).
3. Every `rated_by`, every `accepted_risk.owner`, every "... by Stefan Reiterer" in `accepted_risk.decided` and the header comment become `maldun`. This also changes the four records of A-95 and the 38 records added since the tag, and (through A-97's script) the nine new ones.
Not touched: any rating, any other basis, any other field. `review-log.md` is a different file and keeps "Stefan Reiterer" as the person who approved (not part of this decision; say if it should change too).

## Checked by the drafter (scratch copy)
- `--do` twice: the second run changes nothing (checksum identical). 113 lines added, 144 removed (the 31 bases are shorter again).
- All 464 records of the tag (without the four of A-95) are identical to the tag as data; the only rater and owner name in the file is `maldun`; no rating differs from the tag; `grep "Stefan Reiterer"` finds nothing in the file.
- With A-97 in either order and rerun the result is the same file (checksum identical); `req_plausibility` over all requirements: no missing record, keys sorted, 515 items.

## Install (A-96 and A-97 both, in any order)
```
bash tools/apply_amendment_a96.sh --report     # look only
bash tools/apply_amendment_a96.sh --do         # then commit "plan: A-96 installed"
```
