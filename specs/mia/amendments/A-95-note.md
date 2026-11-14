# A-95: five plausibility records (G-V2.STORE Verify, F-05 and the rating of REQ-GTB-022)

Status: **draft for the owner's look-only review, 2026-11-08**; `tools/apply_amendment_a95.sh` is not yet run with `--do` in the repository.

## Why
- REQ-GTB-022 (A-93) has no plausibility record; the owner rated it **plausible** on 2026-11-08.
- The comparison of `specs/mia/plausibility.yaml` with the tag `plan-baseline-it2-store` (F-05) shows four requirements that lost their record in the rewrite of `d80fdb5`: REQ-API-004, REQ-API-007, REQ-VPB-002, REQ-CLV-011. All four changed after their first rating of 2026-10-26 (D-149, D-153, D-157, D-163, D-165; REQ-API-007 and REQ-VPB-002 gained numbers), so a copy of the old record would rate text that no longer exists. The owner rated each of them again on the current text, all **plausible**, 2026-11-08.

## What the script does
Inserts five records in sorted place in `specs/mia/plausibility.yaml` (`rated_by: Stefan Reiterer`, `rated: '2026-11-08'`, `hardware: HW-target`, a basis text per requirement). Nothing else in the file changes. A record that is there already is skipped, so a second `--do` changes nothing.

## Checked by the drafter (scratch copy)
- `--do` twice: checksum of the file identical after the second run; the file parses (506 items, was 501).
- `req_plausibility`: no "no plausibility record" for the five.
- **Two warnings remain** (REQ-API-004, REQ-API-007: "numeric bound but no claim recorded"). A claim needs a reference with a measured number; there is none for a count of 5 or 10 messages per minute, and the drafter did not invent one. The same warning exists 31 times in the file already. A claim can be added when a reference exists (for example from Validate).

## Not part of A-95
- The other re-attributions in the file since the tag (464 `rated_by` from `maldun`, 433 `rated` dates moved to 2026-11-07, 42 accepted-risk owners) stay as they are; they change no rating. Say if they should be restored.
- The bases of 31 records were reworded (REQ-GTB-005..020, REQ-RUN-016..019, REQ-WFM-040..049); no rating changed.

## Install
```
bash tools/apply_amendment_a95.sh --report     # look only
bash tools/apply_amendment_a95.sh --do         # then commit "plan: A-95 installed"
```
