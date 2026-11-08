# A-103: plausibility records for REQ-GTB-028 and REQ-SLY-015 (G-V2.STORE)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a103.sh` is not yet run with `--do` in the repository. **Install it after A-102** (A-102 creates the two requirements it rates).

## Owner's ratings (2026-11-08)
| Requirement | Rating | Basis in short |
|---|---|---|
| REQ-GTB-028 size of a record (100,000 values, every path counted) | plausible | one fixed number, exact on both sides; about 190 times the largest stored document (529 values, probe of 202 files); iterative walk that stops at the limit, a few milliseconds |
| REQ-SLY-015 size of a document (the same limit, every table) | plausible | same number and basis; shared containers are memoised, so the refusal of a 2**30-path document is far inside the limit of one second; exact behaviour, tested with a time limit on both backends |

## What the script does
Inserts the two records in sorted place in `specs/mia/plausibility.yaml` (`rated_by: maldun`, `rated: '2026-11-08'`, `hardware: HW-target`). Nothing else changes. A record that is there already is skipped. It parses the result and refuses when a basis is not text, and prints the checker's exit code, the tracebacks and every error line.

## Checked by the drafter (scratch copy with A-102 installed)
- `--do` twice: the second run changes nothing (checksum identical); 14 lines added; 524 items, keys sorted, one rater (`maldun`).
- `req_plausibility` over all requirements: exit 0, 0 tracebacks, no error.

## Install (after A-102)
```
bash tools/apply_amendment_a103.sh --report     # look only
bash tools/apply_amendment_a103.sh --do         # then commit "plan: A-103 installed"
```
