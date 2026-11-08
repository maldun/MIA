# A-101: plausibility records for REQ-SLY-013 and REQ-SLY-014 (G-V2.STORE)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a101.sh` is not yet run with `--do` in the repository.

## Owner's ratings (2026-11-08)
| Requirement | Rating | Basis in short |
|---|---|---|
| REQ-SLY-013 depth of a document (200 levels, every table) | plausible | one fixed number, exact on both sides, same limit as REQ-GTB-027; deepest real document 19 levels (probe of 193 files); about ten times that, far below the recursion limit (about 496); iterative, a few milliseconds |
| REQ-SLY-014 a document that contains itself (refused within one second) | plausible | the only number is 1 s, with a very large margin (iterative walk, each container once); only Python callers can build such a document; exact behaviour, tested with a time limit on both backends |

## What the script does
Inserts the two records in sorted place in `specs/mia/plausibility.yaml` (`rated_by: maldun`, `rated: '2026-11-08'`, `hardware: HW-target`). Nothing else changes. A record that is there already is skipped. It parses the result and refuses when a basis is not text, and prints the checker's exit code, the tracebacks and every error line.

## Checked by the drafter (scratch copy)
- `--do` twice: the second run changes nothing (checksum identical); 14 lines added; 522 items, keys sorted, one rater (`maldun`).
- `req_plausibility` over all requirements: exit 0, 0 tracebacks, no error.

## Install
```
bash tools/apply_amendment_a101.sh --report     # look only
bash tools/apply_amendment_a101.sh --do         # then commit "plan: A-101 installed"
```
The review items REQ-SLY-013, REQ-SLY-014, TC-SLY-012 and TC-SLY-013 still need your approval (`req_review.py`) once T-11 is done.
