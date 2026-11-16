# Goal G-V3.REPORT – A report at the end of every skill run

Opened 2026-11-16 from feedback FB-08 (the owner: the sources in the Skill run view should be clickable links) and the owner's decisions of the same day (questionnaire, D-340, amendment A-154, `specs/mia/amendments/A-154-report-of-a-skill-run.md`).

- Kind: subgoal
- Parent: G-V3
- Statement: Every skill run ends with a short report that says what happened, also when nothing was found, and the Skill run view shows it with clickable web links and lets the user download it.
- Exit criterion: OC-1 to OC-4, with the checks of its requirements below
- Supervision: supervised
- Accepted by: Stefan Reiterer (owner)
- Line of work: goal/v3.report
- Subgoals: –
- Status: Agreed

## Outcome criteria
| ID | Expected outcome | Derived from |
|---|---|---|
| OC-1 | Given any skill run that ends, with or without output, when the user looks at the run in the window that shows runs, then there is a short report that says whether the run succeeded, was stopped or failed, and why | FR-46, G-V3 OC-5 |
| OC-2 | Given a run that found sources, when the user opens the report in that window, then every web address of a source can be clicked and opens in a new page, and an address that is not a web address cannot be clicked | FR-46 (FB-08) |
| OC-3 | Given a report, when the user wants to keep or pass it on, then it can be downloaded as a file | FR-46 |
| OC-4 | Given text from the web, a model or a user that contains markup, links or instructions, when it is shown in a report, then nothing in it acts on its own and the page loads nothing from other places | NFR-3, G-V3 OC-8 |

## Dependencies and bounds
| Item (DEP-n / HR-nnn) | Real or stand-in | Note |
|---|---|---|
| files volume (REQ-WFM-037) | real, unchanged | the report is a file of it |
| IF-101 v18 (field `report` of the run record) | real after the owner installs `amendment-a154/protected.patch`; the mock and the contract suite follow in Plan step 4 | |
| renderer of the chat messages (marked, DOMPurify, vendored) | real, unchanged | the report needs its own rule for addresses: only http and https |
| skills `lookup`, `review`, `search` | real | scripted stand-ins in the tests; no model needed for the checks of this goal |

## Split check
| Suggestion | Decision (split / keep together) | Reason | Date |
|---|---|---|---|
| back end (report, record field) and front end (Report part) as two subgoals | keep together | 8 new requirements and 2 changed ones, one shared interface change (IF-101 v18), no model step, one reviewer can check it in one sitting | 2026-11-16 |

## Scope
Top-level items it serves: FR-46 (the Skill run view), NFR-3 (TB-web, TB-result). Requirements by ID (inside G-V3's scope).

| Item | In/Out | Reason |
|---|---|---|
| REQ-WFM-139 | in | new (A-154), every run ends with a report |
| REQ-WFM-140 | in | new (A-154), the run record names it (IF-101 v18) |
| REQ-WFM-141 | in | new (A-154), addresses and texts in a report (group UT) |
| REQ-CLV-048 | in | new (A-154), the Report part in the Full run |
| REQ-CLV-049 | in | new (A-154), links in the report (group UT) |
| REQ-CLV-050 | in | new (A-154), the part before the end of the run |
| REQ-CLV-051 | in | new (A-154), the file is gone |
| REQ-CLV-052 | in | new (A-154), no active content (group UT) |
| REQ-CLV-043 | in | changed (A-154), the report is excepted |
| REQ-WFM-137 | in | changed (A-154), the report is stored as data |
| REQ-WFM-037 | out | used unchanged (files volume) |

Out as a whole: the other requirements of G-V3, G-V3.PANEL and G-V3.CHAT (finished and merged); the run record and the view stay as they are, except for the field `report`.

## Parts
| Part | Real or stand-in | Notes |
|---|---|---|
| N-2.3 Workflow management (report writer, fallback, field `report`) | real | |
| N-1.1 Chat and login views (Report part, report renderer) | real | |
| skills lookup, review, search | real | `lookup` has an interim report file since 36cc3a9 (no outcome line, no field) |

## Frozen requirements
| Requirement | Shared by | Reason |
|---|---|---|
| – | – | no siblings |

## Agreement
| Subgoal | Agreed by | Date |
|---|---|---|
| G-V3.REPORT | Stefan Reiterer (owner), by the questionnaire that approved A-154 (D-340) | 2026-11-16 |

## Phases
| Phase | State | Record or reason |
|---|---|---|
| Explore | done | FB-08 (`specs/mia/feedback/FB-08.md`) and the owner's questionnaire of 2026-11-16 (store, REQ-CLV-043 exception, every skill, placement); no new top-level item (FR-46 covers it) |
| Plan | in progress | requirements, checks, model and glossary approved (D-340, A-154), protected part of A-154 installed; step 4: red tests written (`tests/js/report-render.test.mjs` committed; `plan-step4/protected.patch` waits for the owner's install; browser checks open, `plan.md` decision 6); step 5: `plan.md` Draft |
| Implement | open | |
| Verify | open | in a fresh context before the merge |
| Commit | open | subgoal: merged into the parent's line by the owner |
| Deploy | empty | reachable only with the iteration goal; delivered with G-V3 / iteration 2 |
| Validate | open | the owner looks at a `/lookup` run: the sources are links |

## Joint amendments
| ID | Requirement | Agreed by | Date |
|---|---|---|---|
| D-340 | A-154: REQ-CLV-043 and REQ-WFM-137 changed, IF-101 v18, eight new items | Stefan Reiterer (owner) | 2026-11-16 |
