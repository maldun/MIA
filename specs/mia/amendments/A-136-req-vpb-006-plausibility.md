# A-136: plausibility record of REQ-VPB-006, the 3 s as an accepted risk (drafted by the Verify session 2026-11-08; approved D-288)

Status: **approved as proposed by the owner 2026-11-08 (D-288) and applied.** The owner decided on 2026-11-08 to accept the plausibility warning of REQ-VPB-006 as an accepted risk (answer "accept the warning" in the Verify session, question 3 of `A-132-verification-report.md`, section 7a) and approved this amendment unchanged (alternative A and B not chosen; follow-up VAL-006 kept). Applied: the record of REQ-VPB-006 in `specs/mia/plausibility.yaml` (8 lines added, 1 changed). Result: `req_plausibility.py` 45 errors and 93 warnings as before, 41 questionable, 41 accepted risks; `trace_check.py` 540 errors, none of TD-11.

## Problem
`req_plausibility.py` warns for REQ-VPB-006: "the requirement has a numeric bound but no claim is recorded: which number is checked against which reference?". The 3 s of REQ-VPB-006 ("also within 3 seconds after a stop") is the constant `STOP_DROP_MS = 3000` in `templates/static/chat/sound.js` (D-165: late lines of a stopped answer arrive within the ~0.2 s poll plus one upload). No measurement is its reference, so no claim can be checked (D-285).

## Proposal (one item of `specs/mia/plausibility.yaml`, key `REQ-VPB-006`, line about 3512)
The record is changed in two places: a new block `accepted_risk` and the rating `questionable` (the tool allows an accepted risk only on a questionable or unknown item and warns on a plausible one: `req_plausibility.py` line 278). The basis, hardware, date and rater stay as D-285 wrote them.

```yaml
    REQ-VPB-006:
      accepted_risk:
        decided: '2026-11-08 by maldun'
        follow_up: VAL-006
        owner: 'maldun'
        reason: the 3 s is the constant STOP_DROP_MS of sound.js (D-165), not a measured bound; it
          only decides how long a late line of a stopped answer is dropped, and the field shows
          whether it fits
      basis:
      - (unchanged: no number or model quality depends on it; the stop window is one variable in sound.js that speakAgain() clears; observed by TC-VPB-006 (node) and TC-VPB-007 (Chromium))
      hardware: HW-target
      rated: '2026-11-08'
      rated_by: maldun
      rating: questionable
```

## What the Verify session tried (on a copy, the protected file untouched)
`req_plausibility.py` over all `requirements.md` with the copy: before **45 errors, 93 warnings, 414 plausible, 40 questionable, 40 accepted risks**; after **45 errors, 93 warnings, 413 plausible, 41 questionable, 41 accepted risks**. The line for REQ-VPB-006 changes from "no claim is recorded" to "accepted risk (maldun): ..."; no new error. The 45 errors are the backlog of other requirements (none is TD-11). So the warning does not disappear: it becomes a documented accepted risk, like the other 40.

## Points for the owner
1. **The rating changes from plausible to questionable** (D-285 had rated it plausible with the warning known). That is what "accepted risk like the other 40" means in this tool; if you would rather keep `plausible` and live with the warning, choose alternative A and nothing changes in the file.
2. `follow_up: VAL-006` ("fast and light enough in daily use", read in the field) is my proposal because the other 40 use it; name another follow-up if you prefer.
3. The date and `by maldun` follow the other records (`decided` and `rated_by` write the user name `maldun`).

## Alternatives
- **A. No change**: keep the rating `plausible` and the known warning (D-285), only record the decision in the review log.
- **B. Give it a reference**: measure the late-line delay (poll plus one upload) on the host and add a `claims` entry `3000 ms against that measurement`; needs a measurement and a reference item, so a small task of its own.

## Steps once approved (Phase 2)
1. Replace the item `REQ-VPB-006` in `specs/mia/plausibility.yaml` by the block above (hand edit, as D-283 and D-285 did; `plausibility-proposal.yaml` has no TD-11 ids).
2. Run `req_plausibility.py` (expect the line above and 45 errors, 93 warnings, 41 accepted risks) and `trace_check.py` (no new error).
3. Record the decision as `D-288` in `specs/mia/review-log.md` and set the status of this file to approved with the date.
