# Hand-over for the G-V3 session (written 2026-11-08): the owner chose a different layout for the Skill run view

For the session that works on **G-V3** (branch `goal/v3`, worktree `.claude/worktrees/goal-v3`). Read this before the next edit of A-131 or the G-V3 requirements. Nothing in the G-V3 files was changed by this note; the changes below are **proposed**, the owner decides in the G-V3 session.

## What happened
In a separate Explore session a clickable mockup of the Skill run view and the spoken-only chat was built on a scripted skill (stub data, no MIA code): `specs/mia/explore-skill-rework/forms/skill-run-view-mockup.html` (merged into master, `c95f088`; open it in a browser; `#demo=review,answer,tick` plays steps on load). The owner looked at it and asked for a **different layout than A-131 and G-V3.PANEL OC-6 assume**.

## The owner's layout (2026-11-08, own words in short)
- The chat is on the **right**, not on the left.
- The 3D character (the figure) is **more prominent**: the large box on the left, as tall as the page.
- The Skill run view goes **under both** the character and the chat, as a strip across the full width, and is **much smaller than in the first draft** (about 30 % of the first draft's height: about 140 px against about 535 px in the mockup).
- On a phone: character, chat, view stacked, in this order (unchanged).

## What the compact view shows (as built in the mockup, for the owner to confirm in the G-V3 Plan)
- In the strip: the skill name and start time, the phases as small pills (the failed or stopped phase is marked), the Time and Searches meters side by side, pause / resume / stop in the header line, the state badge, a one-line reason when a run failed or was stopped.
- Behind a collapsed "Full run" part (max 34 % of the viewport height, scrolls inside): result, the answers the user gave, the material found on the way, the files (no delete control), the counts. The link in the chat summary ("Open in the Skill run view") opens it.

## Where the G-V3 files say something else (to change if the owner keeps this layout)
| File (branch `goal/v3`) | Now | Proposed |
|---|---|---|
| `amendments/A-131-note.md`, proposed FR-46 wording (last sentence of the paragraph) | "the character stands in a rectangular box, the chat is left of it and the Skill run view is below it" | "the character stands in a large rectangular box on the left, the chat is right of it, and the Skill run view is a compact strip across the full width below both" |
| `amendments/A-131-note.md`, table row FR-34 | "the view below the character box (stacked on the phone)" | "the compact view below the character box and the chat" |
| `amendments/A-131-note.md`, glossary proposal "Skill run view" | "below the character box" | "below the character box and the chat, across the full width" |
| `goals/G-V3.PANEL/goal.md`, OC-6 | "the character box, the chat on its left and the view below the box do not overlap and the page does not scroll" | "the character box, the chat on its right and the view below both ..." (the "page does not scroll" part: the strip is small and its "Full run" part scrolls inside itself; check the wording against that) |
| HLS line 95, FR-46 (approved text of the HLS, **do not change here**) | "the chat is left of it" | changes only through the amendment (A-131) |

## What was not checked
- The mockup was checked by screenshots in headless Chromium (running and failed states, 600 px wide for the phone order) and by a syntax check; the buttons, the answer chips, the live clock, the reload / clear controls and the link that opens the "Full run" part were not clicked by hand. Nothing in it is a requirement or a test.
- The number "30 %" is the owner's wish read against the mockup's first draft, not a measured requirement; if it becomes one, Plan fixes the unit (height in px or share of the viewport) and the screen sizes.
- The read of "figure" as "the 3D character" is the agent's and was not confirmed in words. The owner corrected the agent once about where the view goes (first read: under the chat only) and then asked for the mockup to be merged; that is no approval of A-131 or of any requirement.

## Not done
No edit of A-131, G-V3 files, `requirements.md`, `architecture.sysml` or `deferred.md`. The G-V2 session on master is not affected.
