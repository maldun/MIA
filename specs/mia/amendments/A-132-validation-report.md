# Validation report: TD-11 option B, speak again (2026-11-08, closed: accepted as is by the owner)

**Goal:** none (change set on master)   **Exit criterion:** TD11-V1 to V5 (`A-132-validation-plan.md`); the 3 s under VAL-006   **Met:** yes, accepted as is by the owner (V2 partial, FB-07 accepted)
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
| REQ-VPB-006 | 3 s (`STOP_DROP_MS`) | VAL-006 session | the stop window was never the limit in use | **confirmed** by the owner (2026-11-08): "3 s is fine, in practice it never needed 3 s" (the owner's observation in use, no measurement); the value stays, the accepted risk of A-136 stays as recorded (follow-up under VAL-006) |

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
| TD-61 | yes; FB-07 (lines fed bit by bit on a repeat, noticed, accepted) is input for its Plan step | next voice iteration or 2026-12-31 | keep (`deferred.md` is protected: the pointer to FB-07 lives here and in FB-07) |
| TD-62 | unrelated | unchanged | keep |

## Feedback items
- FB-07 (No action, Triaged): short stops between sentences on a repeat; accepted as is, revisit with TD-61.

## Decision
Accepted as is and validation closed by the owner on 2026-11-08, after one session (14:20 to 14:21) and without the multi-day use. Limits stay as written under "Quality in use" (one browser and device, no phone, no several users, device name not recorded). Status updates: REQ-CHA-030..036 and REQ-VPB-006 are Validated. The 3 s stays an accepted risk (A-136). No new iteration is started for TD-11; FB-07 and TD-61 wait for the next voice iteration or 2026-12-31.
