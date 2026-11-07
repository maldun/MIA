# A-131: FR-46 changed to one window for the running skill (proposal)

Status: **proposed** (Draft). Nothing in `high-level-spec.md`, `requirements.md` or the nodes is changed. Source: owner, 2026-11-07, answering the questionnaire for goal G-V3. Decision id: to be given when the owner decides (next free: D-271).

## Why
FR-46 (HLS line 95) says "a subwindow of its own for every skill". The owner wants one subwindow that shows the skill that is currently being executed. FR-34 lists all runs in a panel and FR-46 revises its position; this note keeps that and changes the "one per skill" part.

## Proposed wording (text of FR-46 after the change, changes in bold)
**FR-46 Skill window and spoken-only chat** [–] (proposed; revises FR-34 and FR-35). MIA shall show, in **one window** of the web interface, **the skill that is currently running** and everything of its run that is not spoken: status card, phases, budgets, pause, resume and stop, the full result, intermediate material, the links to files and report, and a confirmation of each answer the user gave, so that the window is the history of the run. **When no skill runs, the window shows <open: the last run | an empty state | a list of earlier runs>; when several skills run, it shows <open: the one the user chose | the newest>.** The chat shall contain only text that is spoken, each a shortened or summed-up form worded in MIA's persona: the skill's questions are spoken in the chat and the users' answers are given in the chat; the full result is referenced by a link to the window; no card, log line, table or full result is put into the chat. On the page the character stands in a rectangular box, the chat is left of it and the **window** is below it. This revises FR-34 (position) and FR-35.

## Other places to change if the owner approves (in Plan, not here)
| Place | Change |
|---|---|
| AC-39 (HLS line 399) | "a subwindow" to the window of the running skill; the check "also after a reload" names the run shown |
| HLS section 8 (FB-01 affects) and line 531 | FR-34 (runs) and FR-43 (skills window): the names stay apart; "run window" or "subwindow" for this one (question Q-4 of `goals/G-V3/goal.md`) |
| FR-34 | "lists the running and finished runs" is read as the history of runs the window can show; open question Q-2 |
| Glossary | the name of the window |

## Open
Questions Q-2 and Q-4 of `goals/G-V3/goal.md` decide the open parts of the wording.
