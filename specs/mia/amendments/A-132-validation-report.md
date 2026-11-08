# Validation report: TD-11 option B, speak again (DRAFT of 2026-11-08, ratings are proposals)

**Goal:** none (change set on master)   **Exit criterion:** TD11-V1 to V5 (`A-132-validation-plan.md`); the 3 s under VAL-006   **Met:** partly, first session only
**Deployed version:** master at `95e74a1`, no tag (deployment record: `A-132-deployment-record.md`, Phase 6 empty)
**Period:** 2026-11-08, one session 14:20 to 14:21; the multi-day use of task 1 has not happened yet   **Validators:** the owner   **Facilitator:** none (self-run)
Code state, audio device: Firefox on this system; the device name was not given, "Firefox sound on this system".

## Planned validation
| Criterion | Result (proposed) | Evidence |
|---|---|---|
| TD11-V1 speaker button heard | pass | step 2 "pressing speaker worked" (a 3-sentence answer); not tried on old messages of different length |
| TD11-V2 long answer, no choppy gaps | **partial** | the repeat has short stops between sentences, order right, also for a short answer (FB-07); a long answer was not named separately |
| TD11-V3 Stop, and speak again right after | pass | step 3 "stop worked", step 4 "stop during speaking works"; the owner gave no opinion on the 3 s and did not say whether the button was pressed inside 3 s |
| TD11-V4 press while an answer is written | pass | step 5 "works" (status and Stop not described in detail) |
| TD11-V5 exploratory | none given | – |

## Provisional requirements settled (M37)
| Requirement | Proposed value | Settled by | Observed | Result |
|---|---|---|---|---|
| REQ-VPB-006 | 3 s (`STOP_DROP_MS`) | VAL-006 session | no opinion on too long or too short | **still open:** needs the owner's view after some days of use; new criterion: no repeat swallowed and no late line of a stopped answer heard in the days of use |

## Quality in use
| Dimension | Observed | Contexts not covered |
|---|---|---|
| Effectiveness | heard every time in one session | several days, old messages of other lengths, a long answer |
| Efficiency | not measured | delay to first sound |
| Satisfaction | short stops on repeat (FB-07); no other remark | – |
| Freedom from risk | no stuck status reported | – |
| Context coverage | one browser, one device | phone, other browsers, other audio devices, several users |

## Open deferrals reviewed (M26)
| TD | Still serves the purpose? | Trigger | Decision (proposed) |
|---|---|---|---|
| TD-61 | yes, but FB-07 is a first sign that one connection per sentence is audible | next voice iteration or 2026-12-31 | keep; add FB-07 to its Plan step; the owner decides |
| TD-62 | unrelated | unchanged | keep |

## Feedback items
- FB-07 (usability, New): short stops between sentences on a repeat.

## Not decided here
The owner decides: whether FB-07 is disturbing enough to bring forward; whether the validation is closed after the multi-day use or accepted as is; the 3 s.
