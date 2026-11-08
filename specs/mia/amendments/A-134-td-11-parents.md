# A-134: parents of the TD-11 requirements (Draft, proposed by the Verify session 2026-11-08, finding F7 of `A-132-verification-report.md`)

Status: **Draft, not approved.** The owner decided on 2026-11-08 to change the `Parent` of the eight requirements (answer to question 8 of the report). The choice of the new parents below is a proposal for the owner to confirm or change; no requirement text, `architecture.sysml` or trace link has been changed yet.

## Problem
`decomp_check.py` (stage 1 step `decomposition`, required for merge) reports "no parent one level up" for REQ-CHA-030..036 (N-2.2) and REQ-VPB-006 (N-1.3): their `Parent` is a requirement of the same node. 63 errors at the plan gate (`43f2988`), 65 now (A-133 added REQ-CHA-035 and 036). No older REQ-CHA or REQ-VPB id has the error; they point to REQ-BE-nnn or REQ-FE-nnn.

## Proposal (Parent field in `requirements.md` and the matching `dependency` line in `architecture.sysml`)
| Requirement | Parent now | Proposed parent | Why |
|---|---|---|---|
| REQ-CHA-030, 031, 033, 034 | REQ-CHA-006 | REQ-BE-006 | the parent of REQ-CHA-006 ("the Backend shall ... speak any answer again") |
| REQ-CHA-032 | REQ-CHA-004 | REQ-BE-006 | REQ-BE-004 says "end the running generation" and does not cover a spoken-again playback; REQ-BE-006 does (stopping the repeat is part of speaking again). Alternative: keep REQ-BE-004 and widen its text (a change of an approved requirement, so a second amendment) |
| REQ-CHA-035, 036 | REQ-CHA-032, REQ-CHA-035 | REQ-BE-006 | same reason; the chain to the sibling stays as a `dependency` |
| REQ-VPB-006 | REQ-VPB-002 | REQ-FE-012 | the parent of REQ-VPB-002 ("When a user mutes or stops the voice, the Web Frontend shall silence it on that device only"); REQ-VPB-006 is the page side of speaking again after such a stop |

The old sibling links stay as `dependency` lines (REQ-CHA-032 on REQ-CHA-004, REQ-CHA-035 on REQ-CHA-032 and so on), so no information is lost.

## Steps once approved (Phase 2)
1. Edit the `Parent:` line of the eight requirements in `specs/mia/nodes/N-2-backend/nodes/N-2.2-chat-agent/requirements.md` and `specs/mia/nodes/N-1-web-frontend/nodes/N-1.3-voice-playback/requirements.md`.
2. Edit `architecture.sysml`: the `dependency from r_req_cha_0nn` lines (about 5740 to 5746) and `dependency from r_req_vpb_006` (about 5662) point to the new parents; keep the sibling dependencies as extra lines.
3. `bash tools/check_sysml.sh specs/mia/architecture.sysml`, `python3 -I tools/check_sysml_model.py .`, `decomp_check.py` (expected 65 to 57 errors, none of TD-11), `trace_check.py` (no new error), `req_graph.py` (26 errors and 46 warnings as before).
4. Record the decision in `specs/mia/review-log.md` (D-nnn).

## Open for the owner
- Confirm or change the parents above (in particular REQ-CHA-032: REQ-BE-006 or a widened REQ-BE-004).
- Whether the text of REQ-BE-006 should say that the playback can be stopped (not needed for the check, only for clarity).
