# Goal G-V3 – Skill window and spoken-only chat (FR-46, with FR-34 and FR-35 revised)

Drafted 2026-11-07 in Plan Step 0 on the owner's wish to start with the GUI change for the skills subwindow. Owner decisions of 2026-11-07 (questionnaire, quoted):
- Scope: "FR-46 only, but check if it means subwindow per skill. It should rather be a subwindow where the current skill that is executed is shown." Checked: FR-46 as written (line 95 of the HLS) says "a subwindow of its own for every skill"; the owner wants ONE window that shows the skill that is running. The changed wording is a proposal in `amendments/A-131-note.md`; no text of the HLS is changed here.
- Kind: "Can we do Goal be not in parallel? The visualisation should not be dependent on the implementation of the skills." Read as: a goal of its own, not a subgoal of G-V2, that does not depend on G-V2's implementation of skills (it consumes the events skills send today, with a scripted skill as stand-in). Whether "not in parallel" also means that no G-V2 session runs at the same time is not clear: open question Q-1.
- Voice: "Chat text change only": the voice path stays as it is; TD-11 stays independent.
- Supervision and depth: "Plan Step 0, supervised".

What the HLS says: FR-34 and FR-35 (FB-01, the skills panel and the skill turns in the chat) are proposed, were out of G-V1 and are not built; FR-46 revises both. So this goal builds FR-34 and FR-35 in the revised form of FR-46 (the card of REQ-CLV-023 is in the chat today).

- Kind: iteration
- Parent: –
- Statement: While a skill runs, one window of the page shows that skill's run (status, phases, budgets, pause, resume, stop, the answers the user gave, the full result and its files) and keeps it afterwards, and the chat holds only short spoken text with a link to the window.
- Exit criterion: OC-1 to OC-8, checked by AC-39 (revised for one window, Plan Step 3) together with the parts of AC-30 that stay; a validation criterion VAL-012 is written in Plan Step 3 (not yet existing)
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v3
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given a skill is running, when the user looks at the page, then one window shows that run: what it is doing now, its figures and budgets, and buttons to pause, resume and stop it | FR-46, FR-34 |
| OC-2 | Given a run has ended, when the user looks at the window, then it shows the full result, the material found on the way, the links to its files and report, and every answer the user gave, in order | FR-46, FR-34 |
| OC-3 | Given a run that has ended, when the page is reloaded or MIA is restarted, then the window still shows that run with its final figures; deleting the chat history empties the window and keeps the files | FR-34, FR-46 |
| OC-4 | Given a skill that asks questions and takes three phases, when it runs, then the chat shows only the questions, the users' answers, a short status for each phase the skill names and a short summary with a link, all in MIA's persona and spoken; no card, table, log line or full result is in the chat | FR-46, FR-35, FR-3 |
| OC-5 | Given a run that fails or is stopped, when it ends, then the window shows the reason and the chat holds one short message with a link | FR-34, FR-35 |
| OC-6 | Given a wide screen, when the page is shown, then the character stands in a box with the chat on its left and the window below it without overlap and without scrolling the page; given a phone, the parts are stacked and every part can be reached | FR-46, NFR-1 |
| OC-7 | Given any skill that reports progress and results the way skills do today, or a scripted stand-in for it, when it runs, then OC-1 to OC-6 hold without the skill knowing about the window | FR-46, owner decision on independence |
| OC-8 | Given a result that quotes web text with instructions in it, when it is shown in the window or summed up in the chat, then it is only text and changes nothing about what MIA does | NFR-3 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| events and interface IF-101 of the chat page (`task_status`, `files_changed`), with the amendment | real, amended | the window is driven by them |
| a scripted skill (questions, three phases, long result, failure, stop) | stand-in | the chat mock server `ui/tools/chat_mock_server.py` and the stub model; real skills need not be converted |
| records of runs (one per run, survives reload and restart) | real | storage as today (TD-21: PostgreSQL later); no change of the storage interface planned, to be confirmed in Plan |
| model server with the pins of `eval-spec.md` | real | only if the digest step (Q-3) is in this goal: MP-light for the dev suite |
| speech service | real, unchanged | the spoken short forms use the voice as today (TD-11 independent) |
| browser test harness (`tests/browser`, podman) | real | exists since D-141; used by the tests of the card and the Files tab |
| vis-network | out | later goal (FR-43) |
| G-V2 results (skill record, graph store, conversion) | out | not needed (OC-7) |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| numbers | no signal | 4 top-level items in scope (FR-3 partly, FR-34, FR-35, FR-46) and about 10 existing requirements to revise, 2 interface amendments, 1 possible model step; the checker's warning (91 requirements) counts every inherited requirement of the touched nodes, as for G-V2 | 2026-11-07 |
| PANEL (window, layout, run records, IF-101; no model) and CHAT (spoken-only chat with the digest step, eval criterion, prompt tuning) | open, owner decides | agent-app rule: the model-dependent part (summaries faithful and in persona, an eval suite with people-labelled cases) is checked differently and can be tuned unsupervised later; PANEL can be seen and tried without a model. Cost: one frozen interface (the run record and events) between them and a stand-in digest for PANEL. Recommendation: split if Q-3 says the digest step is in this goal, otherwise keep together | 2026-11-07 |
| a smaller first cut: only OC-1 to OC-3, OC-6, OC-7 (window and layout, chat unchanged) | open, owner decides | gives something to try early; the chat would still show the card until CHAT follows | 2026-11-07 |

## Scope
Top-level items: FR-34, FR-35, FR-46 (all in, as one revised unit); FR-3 only as far as the spoken short forms go. Acceptance criteria in scope: AC-39 (revised for one window) and the parts of AC-30 that stay; out: all other AC. Resolves with this goal: the reload target of TD-01 (card with final figures after a reload). Not in scope: the voice path (TD-11, A-130), the skills window with the graph editor (FR-43), everything of G-V2.

| Item | In/Out | Reason |
|---|---|---|
| FR-1 | out | conversation, history and persona do not change; what the chat holds while a skill runs is covered through FR-35 and FR-46 |
| FR-2 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-3 | partly | only: the spoken short forms of the chat go through the voice as today; the voice path itself does not change (owner 2026-11-07; TD-11 stays independent) |
| FR-4 | out | the status line (mood and activity) stays as it is (FB-01) |
| FR-5 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| FR-6 | out | skill files and the runner are not changed by this goal; the window reads the events skills already send (OC-7) |
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
| FR-34 | partly | not built in v0.1.0 (out of G-V1, FB-01); built here in the form revised by FR-46: runs and their cards, full result and links outside the chat, also after a reload and a restart |
| FR-35 | partly | not built in v0.1.0 (out of G-V1, FB-01); built here in the form revised by FR-46: the chat holds only spoken text (questions, answers, short status and summary in persona, link); open question Q-3 on the digest step |
| FR-36 | out | G-V2 |
| FR-37 | out | G-V2 |
| FR-38 | out | G-V2 |
| FR-39 | out | goal D (debates) |
| FR-40 | out | G-V2 |
| FR-41 | out | goal C (context graph) |
| FR-42 | out | goal C (N-6) |
| FR-43 | out | skills window, viewer and editor with vis-network: later goal (goal B of the HLS without FR-46); not the same window as the one of FR-46 |
| FR-44 | out | goal D (testbench and budgets) |
| FR-45 | out | G-V2 |
| FR-46 | in | the skill window and the spoken-only chat; wording changed by the owner 2026-11-07, one window for the running skill (proposal A-131) |
| FR-47 | out | G-V2 |
| NFR-1 | partly | the window and the new layout meet the same accessibility and device range (320 to 2560 px, 44 px targets, themes) |
| NFR-2 | out | not changed by this goal; the digest step, if in scope, keeps its input inside half the context (Plan) |
| NFR-3 | partly | the full result quotes web and paper text: shown as text in the window and the chat, it acts on nothing (TB-result) |
| NFR-4 | out | not changed by this goal; the existing checks keep running |
| NFR-5 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| NFR-6 | out | built in G-V1 (v0.1.0) or not touched; this goal does not change it |
| NFR-7 | out | not changed by this goal; if Plan finds that status events could delay the first chat text, it becomes a requirement of FR-46 and NFR-7 comes back in |
| NFR-8 | out | not changed by this goal; the existing checks keep running |
| NFR-9 | out | not changed by this goal; the existing checks keep running |
| REQ-CLV-023 | in | status card moves from the chat into the skill window; after a reload it resolves the reload target of TD-01 (Plan Step 1b) |
| REQ-CLV-024 | in | link target of the files comes from the window (Plan Step 1b) |
| REQ-WFM-031 | in | where the task card is shown (Plan Step 1b) |
| REQ-WFM-036 | in | the result at the end of the chat becomes a short spoken summary with a link (Plan Step 1b) |
| REQ-WFM-038 | in | the report is the link target; a run record for every skill (Plan Step 1b) |
| REQ-WFM-039 | in | manifest declares the phases worth telling; the result is full text (Plan Step 1b); nothing else of the manifest changes |
| REQ-FE-014 | in | chat view contains only spoken text (Plan Step 1b) |
| REQ-CHA-008 | in | persona of the status messages (Plan Step 1b) |
| REQ-CHA-014 | in | speech repair of status and summary (Plan Step 1b) |
| REQ-VOI-001 | out | voice path stays as it is (owner 2026-11-07); TD-11 and A-130 stay independent |
| IF-101 | in | amendment: `task_status`, a run list and the full result for the window, a marker for skill messages (A-131 and later) |
| IF-201 | in | amendment: skill turns in the history the chat model sees (later) |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-1.1 chat and login views (the window, the layout, the chat that holds only spoken text) | real | the card and the Files tab move here from the chat |
| N-2.3 task runtime (run records, status events) | real | one record per run so that the window survives reload and restart |
| N-2.2 chat agent (spoken short forms, the digest of a result, if in scope) | real | persona and repair as today |
| N-2.5 voice synthesis | real | task text gets the same repair as answers |
| skills | stand-in | a scripted skill on the chat mock server; real skills are not changed |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|

## Open questions for the owner
- Q-1 "Not in parallel": does it mean (a) a goal of its own and not a subgoal of G-V2, or (b) also not worked on while the G-V2 sessions run? This record assumes (a) only; the line of work `goal/v3` is separate either way.
- Q-2 One window: when no skill runs, does the window show the last run, an empty state, or a short list of earlier runs? FR-34 listed all runs of the shared chat history; the owner's wish names only the current skill. With several skills running at once, which one does the window show?
- Q-3 The spoken-only chat needs short spoken forms of status and result. Is the digest step (the chat model words a status and a summary of the full result, FR-35, `SkillDigestStep`) in this goal? If yes, an eval criterion, a suite with people-labelled cases and a baseline are needed (agent-app).
- Q-4 Name: FR-43 is the "skills window" (viewer and editor); the HLS says the names must stay apart. Keep "subwindow" for this one, or another name (for example "run window")?
- Q-5 Split: PANEL and CHAT, a smaller first cut, or keep together (see Split check).
- Q-7 Two open iteration goals: `goal_check.py` reports GL1 (one open iteration goal per iteration) for G-V2 and G-V3. A goal of its own that is independent of G-V2 means either a second iteration goal (the error stays until the owner accepts it or G-V3 becomes goal of a new iteration 3) or a subgoal of G-V2, which the owner's answers argue against. Needs your decision.
- Q-6 Does AC-30 stay for the parts the new wording does not change, or is it replaced by AC-39 as a whole?

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | FR-34, FR-35 and FR-46 are in the HLS of iteration 2 (approved 2026-11-05, D-186); the new wording (one window) is proposal A-131 |
| Plan | in progress | started 2026-11-07, Step 0 |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
