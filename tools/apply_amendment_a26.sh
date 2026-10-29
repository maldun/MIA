#!/usr/bin/env bash
# Amendment A-26 (housekeeping after the usability work of 2026-10-29, D-104): four deferral records (new specs/mia/deferred.md, M26) and the quality model brought up to date (M32).
# The records are PROPOSALS: the owner confirms, changes or drops each (the Decision line names him). The four requirements they concern get the lines `Relaxed: TD-nn` and `Target:`:
#   REQ-CLV-023 (TD-01), REQ-CLV-024 (TD-02), REQ-WFM-032 (TD-03), REQ-WFM-039 (TD-04). The quality model names the new requirements per characteristic and gets Q-4 (extensions are code of the repository).
# Files that change:  specs/mia/deferred.md (new, protected)   specs/mia/quality.md   N-1.1 requirements.md   N-2.3 requirements.md
# specs/mia/architecture.sysml: two lists of modules name the files that moved into extensions/review (T-11, D-103); python3 -I tools/check_sysml_model.py . is red on master without this fix.
# Run it yourself in the MAIN checkout, after the branch is merged:
#   bash tools/apply_amendment_a26.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a26.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-26 ..." (name the paths, no `git add -A`)
#   bash tools/apply_amendment_a26.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-26
copy $A/deferred.md specs/mia/deferred.md
copy $A/quality.md specs/mia/quality.md
copy $A/N11-requirements.md specs/mia/nodes/N-1-web-frontend/nodes/N-1.1-chat-and-login-views/requirements.md
copy $A/N23-requirements.md specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management/requirements.md
copy $A/architecture.sysml specs/mia/architecture.sysml
finish
echo
echo "checks after the amendment:"
python3 -I tools/check_sysml_model.py .
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 ~/.claude/skills/dev-workflow/scripts/trace_check.py --spec-dir specs/mia --tests-dir tests | sed -n 1,3p
python3 ~/.claude/skills/plan-phase/scripts/quality_check.py --quality specs/mia/quality.md --requirements $(find specs/mia -name requirements.md) | tail -5
