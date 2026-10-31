#!/usr/bin/env bash
# Amendment A-59 (N-3.1 Verify, owner decisions D-158): the IF-102 suite runs on PostgreSQL in a stage, and a delete is told to the subscribers.
# Protected files that change:
#   contracts/IF-102-storage-interface.md                       v2: the delete notice (version None, golden 4); tables and delete rule follow IF-301/IF-302 (F7, F12)
#   tests/helpers/mocks/if_102_storage.py                       delete tells the subscribers with version None
#   tests/acceptance/contract/test_if_102_storage.py            TC-IF-102-09: a delete is told, a refused delete is not
#   stages.yaml                                                 stage-3 step contract-postgres: tools/contract_postgres.sh (F6; made from the installed file at run time)
#   specs/mia/test-spec.md                                      the row of TC-IF-102-09 (made from the installed file at run time, so it cannot go stale)
# The real side of TC-IF-102-09 is green already: the Storage layer tells deletes since the F7 fix of branch v1-n31b (merge that first).
# The new stage step needs the local image docker.io/library/postgres:16 (never pulled) and a python with psycopg 3 (MIA_DB_PYTHON).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a59.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a59.sh --do      install and run the IF-102 suite (mock and file backend); commit afterwards as "plan: A-59 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-59
D=specs/mia/contract-drafts
SPEC=$(mktemp)
STAGES=$(mktemp)
trap 'rm -f "$SPEC" "$STAGES"' EXIT
python3 - specs/mia/test-spec.md "$SPEC" <<'PY'
import sys
after = "| TC-IF-102-08 | IF-102 | Contract | 1 (mock) and 2 (real) | F-5: a run result and a source trust value are written and read back as versions; the second write of a source is version 2. | exact |"
row = "| TC-IF-102-09 | IF-102 | Contract | 1 (mock), 2 (real, files) and 3 (real, PostgreSQL) | golden 4 (A-59): a delete is told to the subscribers with version None; a refused delete tells nothing. | exact |"
text = open(sys.argv[1], encoding="utf-8").read()
if row not in text:
    if after not in text:
        sys.exit("the row of TC-IF-102-08 is not where A-59 expects it: check specs/mia/test-spec.md")
    text = text.replace(after, after + "\n" + row)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
python3 - stages.yaml "$STAGES" <<'PY'
import sys
after = '  - {id: contract-real, stage: 2, cmd: "python -m unittest discover -s tests/acceptance/contract -p \\"test_if_*.py\\" -k _real", needs: [acceptance]}'
step = ('  # contract-postgres (A-59): the IF-102 suite on a throwaway postgres:16 (local image, never pulled); MIA_DB_PYTHON names a python with psycopg 3\n'
        '  - {id: contract-postgres, stage: 3, cmd: "bash tools/contract_postgres.sh", needs: [contract-real]}')
text = open(sys.argv[1], encoding="utf-8").read()
if "id: contract-postgres" not in text:
    if after not in text:
        sys.exit("the step contract-real is not where A-59 expects it: check stages.yaml")
    text = text.replace(after, after + "\n" + step)
open(sys.argv[2], "w", encoding="utf-8").write(text)
PY
copy $A/IF-102-storage-interface.md contracts/IF-102-storage-interface.md
copy $D/tests/helpers/mocks/if_102_storage.py tests/helpers/mocks/if_102_storage.py
copy $D/tests/acceptance/contract/test_if_102_storage.py tests/acceptance/contract/test_if_102_storage.py
copy "$STAGES" stages.yaml
copy "$SPEC" specs/mia/test-spec.md
finish
echo
python3 tests/acceptance/contract/test_if_102_storage.py
echo "the PostgreSQL side: MIA_DB_PYTHON=/path/to/python-with-psycopg bash tools/contract_postgres.sh"
