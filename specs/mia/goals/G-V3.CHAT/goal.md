# Goal G-V3.CHAT – Spoken-only chat and the digest step

Drafted 2026-11-07 when the owner decided to split G-V3 into PANEL and CHAT (Q-3, Q-5). Contains the model step; needs `@ModelStep`, an eval criterion, a labelled suite, a baseline and a TB-result threat entry in Plan (later).

- Kind: subgoal
- Parent: G-V3
- Statement: While a skill runs, the chat holds only text that is spoken: the skill's questions, the users' answers, a short status summary for each phase the skill names and, at the end, a short summary in the text with a link to the Skill run view; no card, table, log line or full result is in the chat.
- Exit criterion: OC-1 to OC-5, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v3.chat
- Subgoals: –
- Status: Proposed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any skill (lookup and search included), for example one that asks questions and takes three phases, when it runs, then the chat shows the questions to answer, the users' answers, a short status summary for each phase the skill names, and at the end a short summary in the text with a link to the Skill run view | G-V3 OC-4, FR-35, FR-46 |
| OC-2 | Given any run, when the chat shows text, then all of it is spoken, and no card, table, log line or full result is in the chat | G-V3 OC-4, FR-3, FR-46 |
| OC-3 | Given a run that fails or is stopped, when it ends, then the chat holds one short spoken message with the reason and a link | G-V3 OC-5, FR-35 |
| OC-4 | Given a long result, when the summary is written, then it says what the result says, misstates nothing and sounds like MIA's persona | FR-35, G-V3 OC-4 |
| OC-5 | Given a result that quotes web text with instructions in it, when it is summed up in the chat, then MIA does what she did before and only reports the text | G-V3 OC-8, NFR-3 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| model server with the pins of `eval-spec.md` | real | MP-light for the dev suite of the digest step |
| IF-101 amendment (run record, marker for skill messages) and REQ-WFM-039 | provided by G-V3.PANEL; CHAT works against a mock until PANEL is merged | CHAT only uses the link form, the marker and the declared phases; a change CHAT needs goes to the PANEL session as an amendment request; the parent can freeze the amendment once its requirements exist (Plan Step 1) |
| the Skill run view (G-V3.PANEL) | stand-in | a link target page until PANEL is merged; the only real dependency of CHAT on PANEL is the link form |
| speech service | real, unchanged | every chat text is spoken as today (TD-11 independent) |
| scripted skill on the chat mock server, stub model | stand-in | |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| prompt tuning of the digest step as an unsupervised subgoal | keep together, supervised throughout | owner 2026-11-07 (Q-10): no unsupervised prompt-tuning subgoal now; it can be proposed again once the suite and the baseline exist | 2026-11-07 |
| further cut | keep together | one model step, five requirements to revise | 2026-11-07 |

## Scope
Top-level items it serves: FR-35, FR-46 (the chat part), FR-3 (the spoken short forms), NFR-3 (TB-result). Requirements by ID (inside G-V3's scope). Not in this table, used through a mock: the IF-101 amendment (marker for skill messages) and REQ-WFM-039 (declared phases), both provided by G-V3.PANEL:

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-036 | in | the result at the end becomes a short summary in the text, spoken, with a link |
| REQ-CHA-008 | in | persona of the status summaries and the end summary |
| REQ-CHA-014 | in | speech repair of the status summaries and the end summary |
| IF-201 | in | skill turns in the history the chat model sees (amendment) |
| REQ-VOI-001 | out | the voice path stays as it is (TD-11, A-130 independent) |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.2 digest step (status summary, end summary) | real | a model step with a schema and a budget |
| N-1.1 chat view (spoken text only) | real | |
| N-2.5 voice synthesis | real | unchanged |
| Skill run view (PANEL) | stand-in | link target until PANEL is merged |
| skills | stand-in | scripted skill, stub model |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | see parent G-V3 |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| – | – | no subgoals |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | HLS of iteration 2 approved 2026-11-05 (D-186); wording A-131 |
| Plan | open | |
| Implement | open | |
| Verify | open | |
| Commit | open | |
| Deploy | open | |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
