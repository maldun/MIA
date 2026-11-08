# A-131: FR-46 changed to one Skill run view for the running skill; the status card leaves the chat (proposal)

Status: **approved** (2026-11-08, maldun, D-302). The HLS (FR-46, FR-34, FR-35, AC-30, AC-39), `glossary.md` and `deferred.md` (TD-01) are changed in a separate step. Requirements named here stay Draft until that step is done and merged.

Earlier status line (kept for the record): Status: **proposed** (Draft). Nothing in `high-level-spec.md`, `requirements.md`, the nodes, `deferred.md` or `glossary.md` is changed. Source: the owner, 2026-11-07 (answers Q-1 to Q-7 logged as D-271, Q-8 to Q-11 as D-273; the amendment itself is not approved). Goal: G-V3 with the subgoals G-V3.PANEL and G-V3.CHAT.

## Why
FR-46 (HLS line 95) says "a subwindow of its own for every skill". The owner wants one view for the running skill. The owner also wants the status card out of the chat: "I want to drop the status card as I want that the chat gives a summary at the end. The current implementation is confusing. However, a small summary should be put inside the text. Another thing which may be ambiguous is that only text in the chat should be spoken. Therefore, status summaries or questions to answer should land in the chat. Status of the skill, buttons etc. should be in the window."

## Proposed wording of FR-46 (changes in bold)
**FR-46 Skill run view and spoken-only chat** [–] (proposed; revises FR-34 and FR-35). MIA shall show, in **one view** of the web interface, **the Skill run view, the skill that is currently running** and everything of its run that is not spoken: status, phases, budgets, pause, resume and stop, the full result, intermediate material, the links to files and report, and a confirmation of each answer the user gave, so that the view is the history of the run. **When no skill runs, the view shows the last run, and no earlier one; when several skills run, it shows the one started most recently. Every skill, lookup and search included, has a run in the view and ends with a short spoken summary in the chat.** The chat shall contain only text that is spoken, each a shortened or summed-up form worded in MIA's persona: the skill's questions **to answer** and the users' answers, **a status summary for each phase the skill names, and at the end a short summary in the text with a link to the Skill run view**; no **status card,** log line, table or full result is put into the chat, **and no text is put into the chat that is not spoken**. On the page the character stands in a **large** rectangular box **on the left**, the chat is **right of it** and the **Skill run view** is **a compact strip across the full width below both**. This revises FR-34 (position, and the card) and FR-35.

## What is retired and what stays
| Item | Retired | Stays |
|---|---|---|
| REQ-CLV-023 (status card in the chat) | the card in the chat as written | replaced by a requirement of the Skill run view: status, phases, budgets, pause, resume, stop (G-V3.PANEL, Plan Step 1b); TC-CLV-023, its browser scenario in `tests/test_task_files_browser.py` and the card model in `tests/js` are rewritten for the view |
| AC-30, card part ("the card with its final figures, the full result and the file links are in the skills panel, at 360 and 1440 px, also after a reload and a restart; deleting the chat history empties the panel and keeps the files") | the word panel and the card | moves into AC-39 as the Skill run view part |
| AC-30, chat part | – | (for every skill, lookup and search included, Q-9) the chat shows the questions, the answers, a status message per declared phase and one summary with a link and nothing else of the run; a failed run shows the reason and a link; lookup and search follow the same rule; the questions, answers, summary and last status message are in the model history, the other status messages are not; status messages and summary are spoken with repair; on the real pinned model the summaries and status messages are faithful and in persona, decided on a suite whose criterion is fixed in Plan |
| FR-34 "skills panel beside the chat, a tab on the phone"; list of all runs | the panel, the tab, the list | the compact view below the character box and the chat (character, chat and view stacked on the phone, in this order); runs and files records stay; the view shows the last run only (Q-2, Q-8); a run list is a later addition |
| FR-35 | – | text unchanged except that the summary is "in the text" and that status summaries are spoken like every chat text; the 1200 character bound and the history rule stay |
| REQ-CLV-024 (files list and links) | the Files tab as a tab | the list, the links, the redraw after `files_changed` and no delete control, now in the view |
| REQ-WFM-031 (where the task status is shown), REQ-WFM-036 (result at the end) | the card as the place of status; the full result at the end of the chat | status in the view; at the end a short summary in the text with a link |
| REQ-WFM-038, REQ-WFM-039, REQ-CHA-008, REQ-CHA-014 | – | changed as listed in `goals/G-V3/goal.md` (Plan Step 1b) |
| REQ-FE-014 (status line with mood and activity, FR-4) | – | stays as it is; FB-01 named it as affected by mistake of the text (its text is the status line) |
| FR-3 and the voice path, TD-11 and A-130 | – | unchanged; every chat text is spoken as today |

## TD-01 (proposal only, `deferred.md` is not edited)
The reload target of TD-01 (a card that is still there after a reload) is superseded by the run history of the Skill run view (G-V3.PANEL OC-3, OC-4). Proposed wording: Requirement: the new requirement of the Skill run view; Target: the Skill run view shows the last run with its final figures after a reload and a restart (browser test); Trigger: the Plan of G-V3.PANEL; Status stays open. The browser part of TD-01 and TD-02 is done (D-269).

## Proposal for the glossary (`glossary.md` is not edited)
- **Skill run view:** the one view on the page, a compact strip across the full width below the character box and the chat, that shows the skill that is running (status, phases, budgets, pause, resume, stop, the answers given, the full result and its files) and, when none runs, the last run. It is not the skills window of FR-43 (viewer and editor of skills).
- Retired as terms: *status card* (in the chat) and *skills panel* (FR-34).

## Layout of 2026-11-08 (owner, after the clickable mockup `explore-skill-rework/forms/skill-run-view-mockup.html`)
The owner chose: the chat on the right, the 3D character large on the left, the Skill run view as a compact strip across the full width under both (about 30 % of the first draft's height), details behind a collapsed "Full run" part; on the phone character, chat, view stacked in this order. The three places above (FR-46 sentence, FR-34 row, glossary) carry this wording; it replaces the layout of 2026-11-07 (chat left of the character box, view below the box). The size is given by the mockup as reference; Plan Step 1b writes it as a requirement with screen sizes. The mockup is no requirement and no test.

## Step 1b of G-V3.PANEL (2026-11-08): the requirements this amendment proposes (all Draft)
Nothing below is approved; approved requirements keep their text (REQ-CHA-008, REQ-CHA-014 carry the proposal next to it).

| Node | Requirement | Change |
|---|---|---|
| N-1 | REQ-FE-032 (new, Parent FR-46) | the status, phases, budgets, controls, answers, result and files are in the Skill run view, not in the chat |
| N-1.1 | REQ-CLV-023 | proposal recorded: superseded by REQ-CLV-030 to REQ-CLV-039 on approval; its Relaxed TD-01 is met by REQ-CLV-038 |
| N-1.1 | REQ-CLV-024 | reworded: the files list lives in the Full run part |
| N-1.1 | REQ-CLV-030 to 047 (new) | header, phases, budgets and counts, controls, run that is shown, reason, Full run part, link from the chat, reload, empty view, wide layout, strip height, phone layout, texts as text, elements of a skill, sizes as shares of the viewport set by the user in the browser (default 16 % and 34 %), kept in the browser, strip content scrolls inside |
| N-2.3 | REQ-WFM-031, 036, 038, 039 | reworded (Draft): status to the view, a short summary with a link at the end of the chat, the report files named in the run record, phases in the manifest |
| N-2.3 | REQ-WFM-130 to 138 (new, group RV) | run record of every run in the table `skill_runs`, figures and reason, result and material, answers, the run that is shown, run records deleted when the history records of the account are deleted in the storage, runs without knowledge of the view, texts stored as data, elements of a skill |
| N-3.3 | REQ-RTB-007 (new), REQ-RTB-001 | the table `skill_runs`; the 15 tables proposed next to the approved text (A-141) |
| N-2.2 | REQ-CHA-008, REQ-CHA-014 | proposal next to the approved text: persona and speech repair also for status summaries and the end summary |
| IF-101 | A-140 (note `A-140-note.md`) | v16: `task_status` fields (with `state`, `elements`; `paused`, `done` stay), the run record routes, event `skill_run_changed`, marker of skill messages in the live events and the history, `Files:` suffix of `chat_done` dropped |
| N-2.2 | REQ-BE-078 (N-2, new), REQ-CHA-040 to 055 (new, groups ST, UT, BG, SQ) | the chat of a run: questions, status per declared phase, end summary and failure message with a link added by code, only spoken text, the history rule, speech with repair, the digest step without tools, input at most half the context, long results in pieces, the 1200 characters in the prompt only, eval criteria for faithful and persona and for the injected instruction (suite EV-skill_turns, MP-light, holdout 21) |
| IF-201 | A-142 (note `A-142-note.md`, proposed) | v3: the operation `skill_turn`, the marker and the link in skill messages, the history rule |
| IF-302, IF-102 | A-141 (note `A-141-note.md`) | v8: the table `skill_runs` (answer of the owner, 2026-11-08) |
History deleted: no operation of the product deletes the chat history today (IF-101 v15, code). Owner 2026-11-08: the trigger is a delete of the history records in the storage (IF-102 `history`, notified by `subscribe`); a clear-chat button is a later feature. Wherever FR-34, AC-30 and OC-3 say "deleting the chat history", this is meant.

Ids: the owner's ranges of 2026-11-08 gave REQ-WFM-080 to 099, but `goals/G-V2/parallel-work.md` reserves REQ-WFM-071 to 129 for the G-V2 subgoals; the new WFM requirements therefore start at 130. REQ-RTB-007 was assigned by the owner on 2026-11-08.

## Revised AC-39 (proposal; replaces the HLS row AC-39 and the card and panel part of AC-30, HLS not changed here)
AC-39 (Skill run view and spoken-only chat; FR-46, FR-34, FR-35): on a scripted run of a skill with two questions, three declared phases and a long result (stub model): every message the chat shows has a spoken form and is shorter than the full result; the questions are in the chat and spoken; an answer is given in the chat and appears in the Full run part of the Skill run view in order; the chat shows no card, status table, log line or full result; the strip of the view shows the skill name, start time, state, phases (the failed or stopped one marked), the Time and Searches meters, pause, resume and stop, and for a failed or stopped run the reason in one line; the Full run part is collapsed after loading and holds the result, the answers, the material found, the files without a delete control and the counts; the view shows the last run after a reload and after a restart, and is empty after the chat history is deleted while the files stay; at 1440 x 900 px the character box on the left, the chat on its right and the strip across the full width below both do not overlap, the page does not scroll and the strip is at most 150 px high; at 360 px the parts are stacked in the order character, chat, view and every part can be reached; each chat message that refers to the result links to the Full run part; a result that quotes web text with instructions is shown and stored as text and changes nothing. The summaries and status messages of the chat are decided on the real pinned model by the suite of G-V3.CHAT. Method: test (stub model), demonstration; checks TC-CLV-030 to 043, TC-WFM-130 to 137 (scenarios and test requirements: Step 3).

## VAL-012
Added to `test-spec.md`, validation criteria: the owner follows a run in the view without reading the chat, judges the strip height (it settles the Provisional of REQ-CLV-041) and the end summary, for one week on desktop and phone.

## Open
Nothing open on the wording; the amendment as a whole is not approved yet. A run list in the view is a later addition (Q-8).
