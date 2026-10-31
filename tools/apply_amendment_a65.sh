#!/usr/bin/env bash
# Amendment A-65 (N-3.1 re-verification R3a, owner decision D-168): IF-102 v3, values that not every backend can keep alike are refused with
# `invalid`, rule `schema`: a NUL character in a text, a number that is not finite (NaN, inf), an id that is not text.
# Note: specs/mia/amendments/A-65/A-65-note.md
# Protected files that change (all made from the INSTALLED files at run time, so the script needs A-59 installed first and cannot bring back an
# older copy; A-62 and other amendments may come before or after, the anchors are lines only A-59 wrote):
#   contracts/IF-102-storage-interface.md               v3: the Errors row, the title, the version line
#   tests/helpers/mocks/if_102_storage.py               put refuses these values (specs/mia/amendments/A-65/mock_unstorable.py)
#   tests/acceptance/contract/test_if_102_storage.py    TC-IF-102-11 (specs/mia/amendments/A-65/suite_case.py), mock and real
# Not protected, changed with it:
#   specs/mia/test-spec.md                              the row of TC-IF-102-11 after TC-IF-102-10
# The real side is green already: the Storage layer refuses these values since branch v1-n31c (merge that first).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a65.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a65.sh --do      install and run the IF-102 suite (mock and file backend); commit afterwards as "plan: A-65 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-65
CONTRACT=contracts/IF-102-storage-interface.md
MOCK=tests/helpers/mocks/if_102_storage.py
SUITE=tests/acceptance/contract/test_if_102_storage.py
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - "$CONTRACT" "$MOCK" "$SUITE" specs/mia/test-spec.md "$WORK" "$A" <<'PY'
import os
import sys
contract, mock, suite, spec, work, drafts = sys.argv[1:7]


def edit(path, old, new, what, text=None):
    """old -> new exactly once; a text that has the new part already is left as it is (the copy then reports unchanged)."""
    text = open(path, encoding="utf-8").read() if text is None else text
    if new in text:
        return text
    if text.count(old) != 1:
        sys.exit("%s: %s is not found exactly once (is A-59 installed?); install A-65 by hand" % (path, what))
    return text.replace(old, new)


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


def draft(name):
    return open(os.path.join(drafts, name), encoding="utf-8").read()


text = edit(contract, "# IF-102 – Storage interface, v2\n", "# IF-102 – Storage interface, v3\n", "the title of v2")
row = "| a workflow breaks a graph rule | `invalid` with `rule` in `node_identity`, `adjacent_data_nodes`, `adjacent_process_nodes`, `session_stopping_criterion`, `cycle` (detail: the cycle as ids) | nothing stored, no version consumed |\n"
new_row = ("| a text with a NUL character (in the document, its keys or the id), a number that is not finite (NaN, inf) or an id that is not text "
           "(A-65) | `invalid` with `rule` `schema` | nothing stored, no version consumed |\n")
text = edit(contract, row, row + new_row, "the Errors row of the graph rules", text)
v2 = text[text.index("| v2 | 2026-10-31 |"):]
v2 = v2[:v2.index("\n") + 1] if "| v2 | 2026-10-31 |" in text else ""
v3 = ("| v3 | 2026-10-31 | values that not every backend keeps alike are refused with `invalid`/`schema`: NUL, numbers that are not finite, "
      "ids that are not text (TC-IF-102-11; D-168, N-3.1 re-verification R3a) | A-65 |\n")
if not v2:
    sys.exit("%s: the version line v2 (A-59) is missing; install A-59 first" % contract)
write("contract.md", edit(contract, v2, v2 + v3, "the version line v2", text))

text = edit(mock, "\n\nclass StorageMock:\n", "\n\n" + draft("mock_unstorable.py") + "class StorageMock:\n", "class StorageMock")
check = ('        rows = self._table(table)\n        versions = rows.get(record_id, [])\n')
write("mock.py", edit(mock, check, ('        rows = self._table(table)\n'
                                    '        unstorable = _unstorable(record_id, doc)\n'
                                    '        if unstorable:                           # IF-102 v3 (A-65)\n'
                                    '            raise StorageError("invalid", rule="schema", detail=unstorable)\n'
                                    '        versions = rows.get(record_id, [])\n'), "the start of put", text))

case = draft("suite_case.py")
write("suite.py", edit(suite, '\n\nif __name__ == "__main__":\n', "\n" + case.rstrip("\n") + '\n\n\nif __name__ == "__main__":\n', "the end of the suite"))

row10 = "| TC-IF-102-10 | IF-102 | Contract | 1 (mock), 2 (real, files) and 3 (real, PostgreSQL) | golden 5 (A-59, D-162): categories() gives the four vote categories in their order; a vote of each is stored. | exact |\n"
row11 = ("| TC-IF-102-11 | IF-102 | Contract | 1 (mock), 2 (real, files) and 3 (real, PostgreSQL) | A-65 (D-168): a NUL character, a number that is not "
         "finite and an id that is not text are refused with invalid/schema; nothing is stored. | exact |\n")
write("test-spec.md", edit(spec, row10, row10 + row11, "the row of TC-IF-102-10"))
PY
copy "$WORK/contract.md" "$CONTRACT"
copy "$WORK/mock.py" "$MOCK"
copy "$WORK/suite.py" "$SUITE"
copy "$WORK/test-spec.md" specs/mia/test-spec.md
finish
echo
python3 "$SUITE" 2>&1 | tail -n 3
echo "the PostgreSQL side: MIA_DB_PYTHON=/path/to/python-with-psycopg bash tools/contract_postgres.sh"
