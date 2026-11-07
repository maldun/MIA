# A-131: FR-46 changed to one Skill run view for the running skill; the status card leaves the chat (proposal)

Status: **proposed** (Draft). Nothing in `high-level-spec.md`, `requirements.md`, the nodes, `deferred.md` or `glossary.md` is changed. Source: the owner, 2026-11-07 (answers Q-1 to Q-7 logged as D-271, Q-8 to Q-11 as D-273; the amendment itself is not approved). Goal: G-V3 with the subgoals G-V3.PANEL and G-V3.CHAT.

## Why
FR-46 (HLS line 95) says "a subwindow of its own for every skill". The owner wants one view for the running skill. The owner also wants the status card out of the chat: "I want to drop the status card as I want that the chat gives a summary at the end. The current implementation is confusing. However, a small summary should be put inside the text. Another thing which may be ambiguous is that only text in the chat should be spoken. Therefore, status summaries or questions to answer should land in the chat. Status of the skill, buttons etc. should be in the window."

## Proposed wording of FR-46 (changes in bold)
**FR-46 Skill run view and spoken-only chat** [–] (proposed; revises FR-34 and FR-35). MIA shall show, in **one view** of the web interface, **the Skill run view, the skill that is currently running** and everything of its run that is not spoken: status, phases, budgets, pause, resume and stop, the full result, intermediate material, the links to files and report, and a confirmation of each answer the user gave, so that the view is the history of the run. **When no skill runs, the view shows the last run, and no earlier one; when several skills run, it shows the one started most recently. Every skill, lookup and search included, has a run in the view and ends with a short spoken summary in the chat.** The chat shall contain only text that is spoken, each a shortened or summed-up form worded in MIA's persona: the skill's questions **to answer** and the users' answers, **a status summary for each phase the skill names, and at the end a short summary in the text with a link to the Skill run view**; no **status card,** log line, table or full result is put into the chat, **and no text is put into the chat that is not spoken**. On the page the character stands in a rectangular box, the chat is left of it and the **Skill run view** is below it. This revises FR-34 (position, and the card) and FR-35.

## What is retired and what stays
| Item | Retired | Stays |
|---|---|---|
| REQ-CLV-023 (status card in the chat) | the card in the chat as written | replaced by a requirement of the Skill run view: status, phases, budgets, pause, resume, stop (G-V3.PANEL, Plan Step 1b); TC-CLV-023, its browser scenario in `tests/test_task_files_browser.py` and the card model in `tests/js` are rewritten for the view |
| AC-30, card part ("the card with its final figures, the full result and the file links are in the skills panel, at 360 and 1440 px, also after a reload and a restart; deleting the chat history empties the panel and keeps the files") | the word panel and the card | moves into AC-39 as the Skill run view part |
| AC-30, chat part | – | (for every skill, lookup and search included, Q-9) the chat shows the questions, the answers, a status message per declared phase and one summary with a link and nothing else of the run; a failed run shows the reason and a link; lookup and search follow the same rule; the questions, answers, summary and last status message are in the model history, the other status messages are not; status messages and summary are spoken with repair; on the real pinned model the summaries and status messages are faithful and in persona, decided on a suite whose criterion is fixed in Plan |
| FR-34 "skills panel beside the chat, a tab on the phone"; list of all runs | the panel, the tab, the list | the view below the character box (stacked on the phone); runs and files records stay; the view shows the last run only (Q-2, Q-8); a run list is a later addition |
| FR-35 | – | text unchanged except that the summary is "in the text" and that status summaries are spoken like every chat text; the 1200 character bound and the history rule stay |
| REQ-CLV-024 (files list and links) | the Files tab as a tab | the list, the links, the redraw after `files_changed` and no delete control, now in the view |
| REQ-WFM-031 (where the task status is shown), REQ-WFM-036 (result at the end) | the card as the place of status; the full result at the end of the chat | status in the view; at the end a short summary in the text with a link |
| REQ-WFM-038, REQ-WFM-039, REQ-CHA-008, REQ-CHA-014 | – | changed as listed in `goals/G-V3/goal.md` (Plan Step 1b) |
| REQ-FE-014 (status line with mood and activity, FR-4) | – | stays as it is; FB-01 named it as affected by mistake of the text (its text is the status line) |
| FR-3 and the voice path, TD-11 and A-130 | – | unchanged; every chat text is spoken as today |

## TD-01 (proposal only, `deferred.md` is not edited)
The reload target of TD-01 (a card that is still there after a reload) is superseded by the run history of the Skill run view (G-V3.PANEL OC-3, OC-4). Proposed wording: Requirement: the new requirement of the Skill run view; Target: the Skill run view shows the last run with its final figures after a reload and a restart (browser test); Trigger: the Plan of G-V3.PANEL; Status stays open. The browser part of TD-01 and TD-02 is done (D-269).

## Proposal for the glossary (`glossary.md` is not edited)
- **Skill run view:** the one view on the page, below the character box, that shows the skill that is running (status, phases, budgets, pause, resume, stop, the answers given, the full result and its files) and, when none runs, the last run. It is not the skills window of FR-43 (viewer and editor of skills).
- Retired as terms: *status card* (in the chat) and *skills panel* (FR-34).

## Open
Nothing open on the wording; the amendment as a whole is not approved yet. A run list in the view is a later addition (Q-8).
