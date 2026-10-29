#!/usr/bin/env bash
# Amendment A-24 (owner's rule 2026-10-29: skills are self-contained extensions; follow-up of A-23, D-100): REQ-WFM-039 (skills as extensions, N-2.3 plan T-11), REQ-CLV-023 (status card) and
# REQ-CLV-024 (files list) with TC-CLV-023/-024 and N-1.1 plan T-09 (built on 2026-10-29), and the CORRECTION of IF-302 v4: `reports` is versioned like every table (v5), with the mock and
# a contract test (TC-IF-302-06). Plan files and protected files that change:
#   N-2.3 requirements.md, test-spec.md, plan.md   N-1.1 requirements.md, test-spec.md, plan.md   specs/mia/architecture.sysml
#   contracts/IF-302-record-tables.md   tests/helpers/mocks/if_302_record_tables.py   tests/acceptance/contract/test_if_302_record_tables.py
# NOT part of this amendment (A-25): the mock, the real adapter and the contract tests of IF-101 v8 (task_status, pause/resume, files, options, result at the end).
# Run it yourself in the MAIN checkout, after the branch is merged:
#   bash tools/apply_amendment_a24.sh           show the compared files and the diff (changes nothing)
#   bash tools/apply_amendment_a24.sh --do      copy the drafts over the installed files and run the checks; commit afterwards as "plan: A-24 ..."
#   bash tools/apply_amendment_a24.sh --full    the whole diff instead of the first 60 lines per file
# Idempotent: identical files are left alone.
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-24
N2=specs/mia/nodes/N-2-backend/nodes/N-2.3-workflow-management
N1=specs/mia/nodes/N-1-web-frontend/nodes/N-1.1-chat-and-login-views
D=specs/mia/contract-drafts/tests
copy $A/N23-requirements.md $N2/requirements.md
copy $A/N23-test-spec.md $N2/test-spec.md
copy $A/N23-plan.md $N2/plan.md
copy $A/N11-requirements.md $N1/requirements.md
copy $A/N11-test-spec.md $N1/test-spec.md
copy $A/N11-plan.md $N1/plan.md
copy $A/architecture.sysml specs/mia/architecture.sysml
copy $A/IF-302-record-tables.md contracts/IF-302-record-tables.md
copy $D/helpers/mocks/if_302_record_tables.py tests/helpers/mocks/if_302_record_tables.py
copy $D/acceptance/contract/test_if_302_record_tables.py tests/acceptance/contract/test_if_302_record_tables.py
finish
echo
echo "model checks after the amendment (about 15 s):"
bash tools/check_sysml.sh specs/mia/architecture.sysml
python3 -I tools/check_sysml_model.py .
echo
bash tools/run_in_image.sh tests/acceptance/contract/test_if_302_record_tables.py tests/test_record_tables.py
