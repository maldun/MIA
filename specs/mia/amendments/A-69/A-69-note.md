# A-69: deferrals from the first Verify of N-2.2 and N-2.5 (TD-09, TD-10, TD-11), TD-03 and TD-04 confirmed

Status: **proposed** (draft for the owner to read and install; nothing protected is changed by the agent).

## Why
The first Verify of N-2.2, N-2.3 and N-2.5 (verification-report.md of each node) found requirements that G-V1 meets only in part. The owner decided on 2026-11-01 (D-173) to record them as deferrals, so the traceability knows them: deleting the history after a confirmation (REQ-CHA-005, TD-09), the persona check dialogues (REQ-CHA-008, AC-8, TD-10) and the chat audio through IF-204 (REQ-VOI-001, TD-11). TD-03 and TD-04 (N-2.3) were "proposed, to be confirmed"; the owner confirmed both.

## What changes
| Installed file | Change |
|---|---|
| `specs/mia/deferred.md` | new TD-09, TD-10, TD-11 (TD-09 carries `Sign-off: Stefan Reiterer, 2026-11-01` because it concerns deleting personal data; the target check of TD-10 and TD-11 is `specified only` / `skip: ...`); the Decision line of TD-03 and TD-04 reads `D-173, 2026-11-01, Stefan Reiterer` |
| node `N-2.2-chat-agent/requirements.md` | REQ-CHA-005: `Relaxed: TD-09` and `Target`; REQ-CHA-008: `Relaxed: TD-10` and `Target`; History line A-69 |
| node `N-2.5-voice-synthesis/requirements.md` | REQ-VOI-001: `Relaxed: TD-11` and `Target`; History line A-69 |

The three files are built from the installed ones at install time, so the order of installation does not matter; each edit refuses when its anchor is not found exactly once, and a second run reports "unchanged". The scope rows in `goals/G-V1/goal.md` and the decision D-173 are not protected and are committed with this draft.

## Checked on a scratch copy of goal/v1 (not installed)
Install with `--do`: three files updated, `trace_check.py` reports no error for TD-09, TD-10, TD-11, TD-03 or TD-04; a second run says "nothing to do". The first scratch run found two trace errors (TD-09 needs a sign-off, TD-10 needs `specified only`); both fixed in the script.

Install (on goal/v1): `bash tools/apply_amendment_a69.sh` (look), then `bash tools/apply_amendment_a69.sh --do`, commit as "plan: A-69 installed".
