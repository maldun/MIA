# Goal G-V3.PANEL – Skill run view

Drafted 2026-11-07 when the owner decided to split G-V3 into PANEL and CHAT (Q-3, Q-5). No model step in this subgoal.

- Kind: subgoal
- Parent: G-V3
- Statement: One view of the page, the Skill run view, shows the skill that is running with its status, phases, budgets and the buttons to pause, resume and stop it, and keeps the last run with its answers, full result and files, also after a reload and a restart; the status card is gone from the chat.
- Exit criterion: OC-1 to OC-7, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v3.panel
- Subgoals: –
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any skill is running (lookup and search included), when the user looks at the Skill run view, then it shows what the skill is doing now, its phases, figures and budgets, and buttons to pause, resume and stop it, and each button does what it says | G-V3 OC-1, FR-34, FR-46 |
| OC-2 | Given a run has ended, when the user looks at the view, then it shows the full result, the material found on the way, the links to the files and the report, and every answer the user gave, in order | G-V3 OC-2, FR-46 |
| OC-3 | Given no skill runs, when the user looks at the view, then it shows the last run, and no earlier one (a run list is a later addition); given several skills run, then it shows the one started most recently | G-V3 OC-2, FR-46 |
| OC-4 | Given a run that has ended, when the page is reloaded or MIA is restarted, then the view shows the same run with its final figures; deleting the chat history empties the view and keeps the files | G-V3 OC-3, FR-34 |
| OC-5 | Given a run that fails or is stopped, when it ends, then the view shows the reason | G-V3 OC-5, FR-34 |
| OC-6 | Given a wide screen, when the page is shown, then the character box, the chat on its right and the compact view across the full width below both do not overlap and the page does not scroll (the details of the view scroll inside it); given a phone, the parts are stacked and every part can be reached | G-V3 OC-6, NFR-1 |
| OC-7 | Given a scripted skill in place of a real one, when it runs, then OC-1 to OC-5 hold; given a result that quotes web text with instructions in it, then the view shows it as text only | G-V3 OC-7, G-V3 OC-8, NFR-3 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| IF-101 amendment (run record, `task_status`, full result, marker for skill messages) | real | PANEL provides it; CHAT works against a mock of it |
| scripted skill on the chat mock server | stand-in | no real skill needed |
| the chat that speaks its text (G-V3.CHAT) | stand-in | the chat stays as it is until CHAT is merged, except that the status card is removed; no dependency on CHAT |
| browser test harness | real | exists since D-141 |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| further cut | keep together | view, run record and layout form one chain; about 8 existing requirements to revise, no model | 2026-11-07 |

## Scope
Top-level items it serves: FR-34, FR-46 (the view). Requirements by ID (inside G-V3's scope):

| Item | In/Out | Reason |
|---|---|---|
| REQ-CLV-023 | in | retired as written (card in the chat); replaced by the status in the view; resolves the reload target of TD-01 |
| REQ-CLV-024 | in | the files list moves into the view |
| REQ-WFM-031 | in | where the status of a task is shown |
| REQ-WFM-038 | in | the report as link target; a run record for every skill |
| REQ-WFM-039 | partly | the phases a skill declares are read by the view and by CHAT (through a mock); nothing else of the manifest changes |
| IF-101 | in | amendment (run record, `task_status`, full result, marker for skill messages), provided here; G-V3.CHAT uses it through a mock |
| IF-302, IF-102 | in | amendment A-141: the table `skill_runs` (v8 and v4), provided here; no new operation |
| REQ-RTB-007 | in | the table `skill_runs` of the Record tables (N-3.3), the run records of REQ-WFM-130 to 138 are stored in it |

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-1.1 Skill run view and layout | real | |
| N-2.3 run records and status events | real | |
| N-3.3 Record tables (table `skill_runs`) | real | IF-302 v8, IF-102 v4 (A-141) |
| chat with spoken text (CHAT) | stand-in | unchanged chat without the card |
| skills | stand-in | scripted skill on the chat mock server |

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
| Plan | done | requirements, checks and `plan.md` approved (D-302, D-335 and the review rows), red tests installed (tag `plan-baseline-it2-panel`), contract changes IF-101 v16/v17, IF-302 v8/v9, IF-102 v4 (A-140, A-141, A-149) |
| Implement | done | T-01 to T-11 done (T-11 is the fix round of the first Verify run), the log is `implementation-log.md` |
| Verify | done | `verification-report.md` and `verification-report-run2.md` to `-run4.md`: four runs by fresh reviewers; the fourth (`798fc3a`) found no open finding; accepted deviations F-10 (TD-81, D-331) and F-15 to F-17 (TD-82 to TD-84, D-338) |
| Commit | done | master merged into `goal/v3` (`ed22e8e`, conflicts only in `task_registry.py`, `CHANGELOG.md`, `deferred.md`); unit suite 2213 tests green, JS 167, trace_check 549 = master 541 + the eight TD-81 to TD-84 errors; merged into master by the owner as `772abc2` on 2026-11-14; no version (the tag comes with iteration 2) |
| Deploy | empty | the Skill run view is reachable only with the iteration goal; delivered with G-V3 / iteration 2 |
| Validate | open | |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
