# A-146: TC-CLV-036 measures the floating part, not the summary (finding F-05, owner G-V3.PANEL)

Status: **proposed** (Draft, 2026-11-13).

## Why
TC-CLV-036 measures the height of `details#srv-full`. Since the layout round the opened part floats above the strip as `.srv-full-body`; the details element is only its summary (18.8 px), so the check cannot fail on the part. The reviewer's probe measured the body: 257 px at the default share (34 % of 757 px) and 189 px at 25 %, so the limit holds today.

## Change
Test-spec text of TC-CLV-036 (N-1.1): "its height" becomes "the height of the opened part (the element that holds the result, answers, material, files and counts)", and the bound stays 34 % of the viewport (25 % at the share 25 %). The browser check measures `.srv-full-body` when open, and fails when the part is missing or has no content. No requirement changes (REQ-CLV-036 says "the Full run part").

## Delivery
Payload with `install.py` for the protected browser test (`tests/acceptance/`), together with A-145 if the owner wants one install step.
