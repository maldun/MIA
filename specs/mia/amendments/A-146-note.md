# A-146: TC-CLV-036 measures the floating part, not the summary (finding F-05, owner G-V3.PANEL)

Status: **approved** (2026-11-13, maldun, D-331).

## Why
TC-CLV-036 measures the height of `details#srv-full`. Since the layout round the opened part floats above the strip as `.srv-full-body`; the details element is only its summary (18.8 px), so the check cannot fail on the part. The reviewer's probe measured the body: 257 px at the default share (34 % of 757 px) and 189 px at 25 %, so the limit holds today.

## Change
Test-spec text of TC-CLV-036 (N-1.1): "its height" becomes "the height of the opened part (the element that holds the result, answers, material, files and counts)", and the bound stays 34 % of the viewport (25 % at the share 25 %). The browser check measures `.srv-full-body` when open, and fails when the part is missing or has no content. No requirement changes (REQ-CLV-036 says "the Full run part").

## Delivery
Payload with `install.py` for the protected browser test (`tests/acceptance/`), together with A-145 if the owner wants one install step.

## Done (2026-11-13)
No payload: the measurement lives in `tests/browser/skill_run_view.py`, which is not a protected folder. The three measurements (`height`, `height_25`, the share check of TC-CLV-045) now read `#srv-full-body`. Checked: the 12 browser tests pass; with the CSS limit raised from 34 to 1.6 times 34 dvh the tests of TC-CLV-036 and TC-CLV-045 fail (they could not before).
