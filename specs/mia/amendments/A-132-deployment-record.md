# Deployment record: TD-11 option B (Phase 6 recorded empty)

| | |
|---|---|
| Version / tag | none (`[Unreleased]`; the tag comes with iteration 2, v0.2.0, D-289) |
| Goal | none: TD-11 is a change set on master (A-132, A-133, A-134, A-135, A-136, A-143) |
| Artifact | none: no tag, no image, no release artifact built for this change |
| Target | the owner's workstation, which runs master from the checkout |
| Date / by | 2026-11-08 / drafted by the Commit session, confirmed empty by the owner 2026-11-08 |
| Phase 6 | **empty** |

## Reason
The change touches the chat voice only (`chat_service.py`, `web_app.py`, `templates/static/chat/`); nothing is installed, no model, port, volume, configuration or dependency changes, and there is no release artifact to deploy. The owner runs master on the host, and the hand check TC-CHA-035 already ran there on the merged code (Firefox, passed; device and commit not recorded). Rollback: `git revert` of the TD-11 commits on master; no data or image to restore.

## Preflight, smoke tests, rollback
- Preflight and smoke tests: not run (nothing deployed). The ladder status is in the release notes (`A-132-release-notes.md`).
- Rollback: as above; the previous image `localhost/mia:v0.1.0` is untouched.

## Ready for validation: Yes
Validate is the owner's use of the voice: listen to a long answer spoken again, repeat a message right after a Stop (VAL-006 checks the 3 s). Findings go into feedback items as usual. Deploy for a tagged release (v0.2.0) is recorded then, with its own preflight, which must also cover the changes listed under "Known issues" of the release notes.
