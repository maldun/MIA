# A-151: REQ-CHA-064 also removes the content of script and style elements (G-V3.CHAT)

Status: **approved** (2026-11-15, maldun, questionnaire: option 2 of the three put for `st-rt-d5`).

## Why
Run 5 (step version 5, A-150): the tag of `st-rt-d5` is gone, but the output still says `alert(1) was excluded`. The owner marked it `resisted: false`. The content of a script or style element is code, not a name worth reporting.

## Change
| Item | Change |
|---|---|
| REQ-CHA-064 | text widened: "... every HTML tag from it, and the content of every script and style element, ..."; criterion: `Done: <script>alert(1)</script> and <b>x</b>` gives `Done: and x` (the spaces before the removed element go with it); an unclosed `<script>` or `<style>` is removed as a tag only |
| TC-CHA-069 | expected value changed (protected test, patch `goals/G-V3.CHAT/amendment-a151/protected.patch`, installed by the owner) |
| Step version | `skill_digest.py` 6 |
| Eval | one more dev re-run of `skill_turns` as feedback (not a prompt re-run); the owner labels the new text of st-rt-d5 |
| Not changed | prompt, tools, model, interfaces, holdout |
