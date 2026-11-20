# Current-state deployment: MIA

**Kind:** current-state   **Commit:** 6f44b59c (v0.2.1) built on 2026-11-20   **Stages passed:** unit/JS/smoke at the tag (see verification report)   **How to reach it:** http://127.0.0.1:8585
**Known gaps:** same as the release record `specs/mia/deployment/deployment-record.md` (no character page, no voice, sandbox off, five acceptance records not yet copied). Today the running stack **is** the release image; no separate instance exists. `deploy/build.sh` needs a tag, so a deploy command for an arbitrary commit is a gap (Plan item); until then the current state is redeployed by hand from the line of work.
**Rollback:** redeploy the previous commit with the same steps. No credentials in this record.
