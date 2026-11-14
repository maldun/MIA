# Goal G-V3 – Skill run view and spoken-only chat (FR-46, with FR-34 and FR-35 revised)

Drafted 2026-11-07 in Plan Step 0 on the owner's wish to start with the GUI change for the skills subwindow; updated the same day with the owner's answers to the open questions. Owner decisions of 2026-11-07 (first questionnaire, quoted):
- Scope: "FR-46 only, but check if it means subwindow per skill. It should rather be a subwindow where the current skill that is executed is shown." FR-46 as written (line 95 of the HLS) says "a subwindow of its own for every skill"; the owner wants ONE window for the running skill. The changed wording is a proposal in `amendments/A-131-note.md`; no text of the HLS is changed here.
- Kind: "Can we do Goal be not in parallel? The visualisation should not be dependent on the implementation of the skills." The goal does not depend on G-V2's implementation of skills; it consumes the events skills send today, with a scripted skill as stand-in.
- Voice: "Chat text change only": the voice path stays as it is; TD-11 stays independent.
- Supervision and depth: "Plan Step 0, supervised".

Owner decisions of 2026-11-07 (answers to the open questions, relayed by the coordinator; logged as D-271, Q-8 to Q-11 as D-273):
- Q-1: G-V3 is its own goal; work may overlap with the G-V2 sessions.
- Q-2: when no skill runs, the window shows the last run; with several running skills the most recently started one is shown.
- Q-3: the digest step IS in G-V3, as its own subgoal.
- Q-4: the window is called **Skill run view** (kept apart from FR-43's skills window).
- Q-5: follows Q-3: two subgoals, G-V3.PANEL (no model) and G-V3.CHAT (the digest step and the spoken-only chat).
- Q-6 (the owner's own words): "I want to drop the status card as I want that the chat gives a summary at the end. The current implementation is confusing. However, a small summary should be put inside the text. Another thing which may be ambiguous is that only text in the chat should be spoken. Therefore, status summaries or questions to answer should land in the chat. Status of the skill, buttons etc. should be in the window."
- Q-8: only the last run is reachable in the Skill run view (a run list is a later addition).
- Q-9: all skills, lookup and search too, get a run in the view and end with a short spoken summary in the chat.
- Q-10: G-V3.CHAT is supervised throughout; there is no unsupervised prompt-tuning subgoal now.
- Q-11: yes to the PANEL/CHAT cut, with the IF-101 amendment owned by PANEL alone and CHAT using a mock of it (Agreement rows filled; logged as D-273).
- Layout (2026-11-08, after the clickable mockup): chat on the right, large character box on the left, the Skill run view a compact strip across the full width below both, details behind a collapsed "Full run" part; kept with the wording of the hand-over of 2026-11-08; the size follows the mockup ("use the mock-up"); the sentence "the page does not scroll" stays for the wide screen only. Changes A-131 (FR-46 sentence, FR-34 row, glossary) and OC-6 of G-V3 and G-V3.PANEL; the approved HLS text of FR-46 changes only through A-131. Logged as D-300 in `review-log.md`.
- Name (2026-11-08, D-301): "G-V2 B" in the other session is this goal; the name G-V3 stays; the graph editor (FR-43) is out of scope.
- Q-7: G-V3 is a second, parallel iteration goal. `goal_check.py` GL1 ("more than one open iteration goal") reports it as an ERROR for G-V2 and G-V3 and has no field to explain it; the error stays, is not weakened or hidden, and this decision is its explanation.

What the HLS says: FR-34 and FR-35 (FB-01, the skills panel and the skill turns in the chat) are proposed, were out of G-V1 and are not built; FR-46 revises both. So this goal builds FR-34 and FR-35 in the revised form of FR-46. The status card is in the chat today (REQ-CLV-023); it leaves the chat entirely (A-131 lists what is retired and what stays).

- Kind: iteration
- Parent: –
- Statement: While a skill runs, one view of the page (the Skill run view) shows that run (status, phases, budgets, pause, resume, stop, the answers the user gave, the full result and its files) and keeps the last run afterwards; the chat holds only spoken text: the skill's questions, status summaries and a short summary at the end, with a link to the view.
- Exit criterion: OC-1 to OC-8, checked by AC-39 (revised for the Skill run view, Plan Step 3) together with the parts of AC-30 that stay (A-131); a validation criterion VAL-012 is written in Plan Step 3 (not yet existing)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v3
- Subgoals: G-V3.PANEL, G-V3.CHAT
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any skill is running (lookup and search included), when the user looks at the page, then the Skill run view shows that run: what it is doing now, its phases, figures and budgets, and buttons to pause, resume and stop it; none of this is in the chat | FR-46, FR-34 |
| OC-2 | Given a run has ended, when the user looks at the Skill run view, then it shows the full result, the material found on the way, the links to its files and report, and every answer the user gave, in order; when no skill runs it shows the last run, and with several running skills the most recently started one | FR-46, FR-34 |
| OC-3 | Given a run that has ended, when the page is reloaded or MIA is restarted, then the Skill run view still shows that run with its final figures; deleting the chat history empties the view and keeps the files | FR-34, FR-46 |
| OC-4 | Given any skill (lookup and search included), for example one that asks questions and takes three phases, when it runs, then the chat shows only text that is spoken: the questions to answer, the users' answers, a short status summary for each phase the skill names (a skill without phases, such as lookup, has none), and at the end a short summary in the text with a link to the Skill run view; no card, table, log line or full result is in the chat, and nothing in the chat is unspoken | FR-46, FR-35, FR-3 |
| OC-5 | Given a run that fails or is stopped, when it ends, then the Skill run view shows the reason and the chat holds one short spoken message with a link | FR-34, FR-35 |
| OC-6 | Given a wide screen, when the page is shown, then the character stands in a large box on the left with the chat on its right and the Skill run view as a compact strip across the full width below both, without overlap and without scrolling the page (the details of the view scroll inside it); given a phone, the parts are stacked in the order character, chat, view and every part can be reached | FR-46, NFR-1 |
| OC-7 | Given any skill that reports progress and results the way skills do today, or a scripted stand-in for it, when it runs, then OC-1 to OC-6 hold without the skill knowing about the Skill run view | FR-46, owner decision on independence |
| OC-8 | Given a result that quotes web text with instructions in it, when it is shown in the Skill run view or summed up in the chat, then it is only text and changes nothing about what MIA does | NFR-3 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| events and interface IF-101 of the chat page (`task_status`, `files_changed`), with the amendment | real, amended | the Skill run view is driven by them; provided by PANEL, used by CHAT through a mock |
| a scripted skill (questions, three phases, long result, failure, stop) | stand-in | the chat mock server `ui/tools/chat_mock_server.py` and the stub model; real skills need not be converted |
| records of runs (one per run, survives reload and restart) | real | storage as today (TD-21: PostgreSQL later); a new table `skill_runs` (IF-302 v8, IF-102 v4, A-141, REQ-RTB-007), no new operation |
| model server with the pins of `eval-spec.md` | real | the digest step (G-V3.CHAT): MP-light for the dev suite |
| speech service | real, unchanged | every chat text is spoken as today (TD-11 independent) |
| browser test harness (`tests/browser`, podman) | real | exists since D-141 |
| vis-network | out | later goal (FR-43) |
| G-V2 results (skill record, graph store, conversion) | out | not needed (OC-7); work may overlap with the G-V2 sessions |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| numbers | no signal | 4 top-level items in scope (FR-3 partly, FR-34, FR-35, FR-46) and about 10 existing requirements to revise, 2 interface amendments, 1 model step; the checker's warning counts every inherited requirement of the touched nodes, as for G-V2 | 2026-11-07 |
| PANEL (Skill run view, status, buttons, history, reload; no model) and CHAT (spoken-only chat with the digest step, eval criterion, labelled suite, baseline) | split into G-V3.PANEL and G-V3.CHAT | owner 2026-11-07 (Q-3, Q-5): the digest step is in the goal and is model-dependent, so it is checked differently (eval suite with people-labelled cases); PANEL can be tried without a model. Cost: CHAT works against a mock of the IF-101 amendment that PANEL provides and links to a stand-in view until PANEL is merged | 2026-11-07 |
| a smaller first cut | not taken | the split above already gives PANEL as an early, model-free piece | 2026-11-07 |

## Scope
Top-level items: FR-34, FR-35, FR-46 (all in, as one revised unit); FR-3 only as far as the spoken short forms go. Acceptance criteria in scope: AC-39 (revised for one window) and the parts of AC-30 that stay; out: all other AC. Resolves with this goal: the reload target of TD-01 is superseded by the run history of the Skill run view (the card is gone; the proposal for the TD-01 wording is in A-131). Not in scope: the voice path (TD-11, A-130), the skills window with the graph editor (FR-43), everything of G-V2.

| Item | In/Out | Reason |
|---|---|---|
| FR-1 | out | conversation, history and persona do not change; what the chat holds while a skill runs is covered through FR-35 and FR-46 |
| FR-2 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-3 | partly | only: the spoken short forms of the chat go through the voice as today; the voice path itself does not change (owner 2026-11-07; TD-11 stays independent) |
| FR-4 | out | the status line (mood and activity) stays as it is (FB-01) |
| FR-5 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-6 | out | skill files and the runner are not changed by this goal; the Skill run view reads the events skills already send (OC-7) |
| FR-7 | out | workflow graph model: G-V2 |
| FR-8 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-9 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-10 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-11 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-12 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-13 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-14 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-15 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-16 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-17 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-18 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-19 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-20 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-21 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-22 | out | graph app; the skills window with editor is a later goal (FR-43) |
| FR-23 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-24 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-25 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-26 | out | testbench with budgets is goal D |
| FR-27 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-28 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-29 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-30 | out | the context graph is goal C |
| FR-31 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-32 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-33 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-34 | partly | not built in v0.1.0 (out of G-V1, FB-01); built here in the form revised by FR-46 as the Skill run view (G-V3.PANEL): status, phases, buttons, full result and links outside the chat, also after a reload and a restart; the last run is shown, not a list of all runs (Q-2) |
| FR-35 | partly | not built in v0.1.0 (out of G-V1, FB-01); built here in the form revised by FR-46 (G-V3.CHAT): the chat holds only spoken text, status summaries and questions to answer, and a short summary at the end in the text; the digest step is in scope (Q-3) |
| FR-36 | out | G-V2 |
| FR-37 | out | G-V2 |
| FR-38 | out | G-V2 |
| FR-39 | out | goal D (debates) |
| FR-40 | out | G-V2 |
| FR-41 | out | goal C (context graph) |
| FR-42 | out | goal C (N-6) |
| FR-43 | out | skills window, viewer and editor with vis-network: later goal (goal B of the HLS without FR-46); not the Skill run view of FR-46 |
| FR-44 | out | goal D (testbench and budgets) |
| FR-45 | out | G-V2 |
| FR-46 | in | the Skill run view (PANEL) and the spoken-only chat (CHAT); wording changed by the owner 2026-11-07, one view for the running skill (proposal A-131) |
| FR-47 | out | G-V2 |
| NFR-1 | partly | the Skill run view and the new layout meet the same accessibility and device range (320 to 2560 px, themes); 44 px targets on the phone layout only, the compact strip keeps smaller buttons on a wide screen (owner 2026-11-08, REQ-CLV-042) |
| NFR-2 | out | not changed by this goal; the digest step, if in scope, keeps its input inside half the context (Plan) |
| NFR-3 | partly | the full result quotes web and paper text: shown as text in the Skill run view and the chat, it acts on nothing (TB-result) |
| NFR-4 | out | not changed by this goal; the existing checks keep running |
| NFR-5 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| NFR-6 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| NFR-7 | out | not changed by this goal; if Plan finds that status events could delay the first chat text, it becomes a requirement of FR-46 and NFR-7 comes back in |
| NFR-8 | out | not changed by this goal; the existing checks keep running |
| NFR-9 | out | not changed by this goal; the existing checks keep running |
| REQ-CLV-023 | in | retired as written: the status card leaves the chat entirely (Q-6); replaced by a requirement of the Skill run view, which resolves the reload target of TD-01 (PANEL) |
| REQ-CLV-024 | in | the files list and its links move into the Skill run view (PANEL, Plan Step 1b) |
| REQ-WFM-031 | in | where the status of a task is shown: the Skill run view, no card in the chat (PANEL, Plan Step 1b) |
| REQ-WFM-036 | in | the result at the end of the chat becomes a short summary in the text, spoken, with a link (CHAT, Plan Step 1b) |
| REQ-WFM-038 | in | the report is the link target; a run record for every skill (PANEL, Plan Step 1b) |
| REQ-WFM-039 | partly | manifest declares the phases worth telling; the result is full text (PANEL, used by CHAT through a mock, Plan Step 1b); nothing else of the manifest changes |
| REQ-FE-014 | out | its text is the status line with mood and activity (FR-4) and stays; FB-01 named it as affected, but the spoken-only chat is a new requirement of CHAT (Plan Step 1b) |
| REQ-CHA-008 | in | persona of the status summaries and the end summary (CHAT, Plan Step 1b) |
| REQ-CHA-014 | in | speech repair of status summaries and the end summary (CHAT, Plan Step 1b) |
| REQ-VOI-001 | out | voice path stays as it is (owner 2026-11-07); TD-11 and A-130 stay independent |
| IF-101 | in | amendment: `task_status`, the run record and the full result for the Skill run view, a marker for skill messages; provided by PANEL, used by CHAT through a mock |
| IF-201 | in | amendment: skill turns in the history the chat model sees (CHAT) |
| IF-302, IF-102 | in | amendment A-141: the table `skill_runs` for the run records (PANEL) |
| REQ-RTB-007 | in | the table `skill_runs` of the Record tables (PANEL, A-141) |
| REQ-BE-078 | in | new: only the spoken text of a skill run is put into the chat (CHAT) |
| REQ-CHA-040 | in | new, questions of a skill in the chat (group ST) |
| REQ-CHA-041 | in | new, status message per declared phase (group ST) |
| REQ-CHA-042 | in | new, no status for other phases (group ST) |
| REQ-CHA-043 | in | new, end summary (group ST) |
| REQ-CHA-044 | in | new, failed run in the chat (group ST) |
| REQ-CHA-045 | in | new, every added message is spoken (group ST) |
| REQ-CHA-046 | in | new, history of a run for the chat model (group ST) |
| REQ-CHA-047 | in | new, repair of the messages of a run (group ST) |
| REQ-CHA-048 | in | new, digest step without tools (group UT) |
| REQ-CHA-049 | in | new, quoted instruction is reported, not followed (group UT) |
| REQ-CHA-050 | in | new, input of a model call (group BG) |
| REQ-CHA-051 | in | new, long result read in pieces (group BG) |
| REQ-CHA-052 | in | new, prompt asks for 1200 characters (group BG) |
| REQ-CHA-053 | in | new, faithful summary (group SQ) |
| REQ-CHA-054 | in | new, summary in persona (group SQ) |
| REQ-CHA-055 | in | new, no status message for a skill without phases (group ST) |
| REQ-CHA-056 | in | new, link added by code (group ST) |
| REQ-CHA-057 | in | new, stopped run in the chat (group ST) |
| REQ-CHA-058 | in | new, no card, table, log line or full result in the chat (group ST) |
| REQ-CHA-059 | in | new, exclusions from the history of the chat model (group ST) |
| REQ-CHA-060 | in | new, repaired text is the text shown and spoken (group ST) |
| REQ-CHA-061 | in | new, result goes to the digest step as text (group UT) |
| REQ-CHA-062 | in | new, summary from the digests only (group BG) |
| REQ-CHA-063 | in | new, summary passed on uncut (group BG) |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-1.1 chat and login views (the Skill run view, the layout, the chat that holds only spoken text) | real | the card is retired; status, buttons and the Files tab live in the Skill run view |
| N-2.3 task runtime (run records, status events) | real | one record per run so that the Skill run view survives reload and restart |
| N-2.2 chat agent (spoken status summaries, the end summary: the digest step) | real | persona and repair as today |
| N-2.5 voice synthesis | real | task text gets the same repair as answers |
| skills | stand-in | a scripted skill on the chat mock server; real skills are not changed |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|

None yet: the IF-101 amendment is provided by PANEL only and CHAT works against a mock of it (cut of 2026-11-07); if the owner prefers a joint ownership, its requirements are frozen at G-V3 once they exist (Plan Step 1) |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V3.PANEL | Stefan Reiterer (owner), IF-101 amendment owned by PANEL alone | 2026-11-07 |
| G-V3.CHAT | Stefan Reiterer (owner), CHAT uses a mock of the IF-101 amendment | 2026-11-07 |

## Open questions for the owner
None open for Step 0 (Q-1 to Q-11 answered, D-271 and D-273). Settled in Plan Step 1b: a stopped run is shown as the last run with its reason (REQ-WFM-134, OC-5). The later run list is not in this goal.

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | FR-34, FR-35 and FR-46 are in the HLS of iteration 2 (approved 2026-11-05, D-186); the new wording (one Skill run view, no card in the chat) is proposal A-131 |
| Plan | in progress | started 2026-11-07; Steps 0 to 3 done for both subgoals (D-300 to D-303 and D-332), contract change applied; Step 4 (red tests) and Step 5 (plan.md) open |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
