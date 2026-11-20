# Parked: G-V5 "First test run" (D-386)

Owner decision 2026-11-20: the definition of G-V5 is deferred until G-V4 is closed; G-V4 will change along the way, so defining the test run now makes little sense. The drafts are kept here, **outside `goals/`**, so that `goal_check.py` does not count G-V5 as a second open iteration goal (GL1). Nothing in this folder is approved or agreed.

## What is parked
| File | What it is |
|---|---|
| `goal.md` | the draft iteration goal: statement, eight outcome criteria, measure ideas, scope table, dependencies |
| `LEFTOVER/goal.md`, `LEFTOVER/top-level-spec.md` | leftovers of G-V2, G-V3 and G-V4 (FR-82 to FR-85, NFR-21); unreviewed |
| `VALIDATE/goal.md`, `VALIDATE/top-level-spec.md` | validation of G-V2, G-V3 and G-V4 and improvement of graphs (FR-86 to FR-90, FR-106 to FR-109, NFR-22); unreviewed |

## The goal_check and trace_check findings that belong to G-V5, not to G-V4
These are the findings on the earlier goals that the rework does not fix; G-V4 does not carry them:
- `goal_check`: GL1 (two open iteration goals) comes back as soon as G-V5 is defined while G-V4 is open; GL3 of G-V2 (SNAPSHOT scope ids, interface versions, TOOLBOX `IF-302`).
- `trace_check`: 553 errors at the tag of v0.2.1; WARN for deferral triggers without a date and deferrals not listed in the node verification reports (for example TD-90).
- The lists in `goals/G-V2/remainder-for-next-goal.md` and the open items of `goals/G-V3/verification-report.md` (V2-1 to V2-3, V2-6, V2-8, V3-6, F-04, TD-82 to TD-90).

## When to take it up
When G-V4 is closed: read these drafts again with what G-V4 has become, update them, and define G-V5 in Explore and Plan (move the folders back to `goals/`).
