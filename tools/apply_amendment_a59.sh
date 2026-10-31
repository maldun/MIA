#!/usr/bin/env bash
# Amendment A-59 (N-3.1 Verify, owner decisions D-158 and D-162): the IF-102 suite runs on PostgreSQL in a stage, a delete is told to the subscribers,
# the storage names the vote categories, and the real side of the suite tests the real Storage layer.
# Protected files that change:
#   contracts/IF-102-storage-interface.md                       v2: the delete notice (version None, golden 4); categories() (golden 5); tables and delete rule follow
#                                                               IF-301/IF-302 (F7, F12, D-162)
#   tests/helpers/mocks/if_102_storage.py                       delete tells the subscribers with version None; categories()
#   tests/acceptance/contract/test_if_102_storage.py            TC-IF-102-09 (a delete is told, a refused delete is not), TC-IF-102-10 (categories())
#   tests/helpers/contract.py                                   _StorageAdapter loads storage, storage_files, storage_postgres by file path with the REAL graph_rules
#                                                               (specs/mia/amendments/A-59/real_storage.py): in a full run the mock side had cached the mock's
#                                                               graph_rules under the same name, so the real side of IF-102 validated with the mock rules (D-162)
#   stages.yaml                                                 stage-3 step contract-postgres: tools/contract_postgres.sh (F6)
# Not protected, changed with it:
#   specs/mia/test-spec.md                                      the rows of TC-IF-102-09 and TC-IF-102-10
# contract.py, stages.yaml and test-spec.md are made from the INSTALLED files at run time (contract.py is shared with A-60), so A-59 and A-60 install in
# either order and the script cannot bring back an older copy; it refuses when an anchor is not found exactly once.
# The real side of TC-IF-102-09 and -10 is green already on branch v1-n31b (merge that first). The new stage step needs the local image
# docker.io/library/postgres:16 (never pulled) and a python with psycopg 3 (MIA_DB_PYTHON).
# INSTALL IT ON THE LINE OF WORK goal/v1 (worktree .claude/worktrees/goal-v1).
#   bash tools/apply_amendment_a59.sh           show the diff (changes nothing); add --report for the readable form
#   bash tools/apply_amendment_a59.sh --do      install and run the IF-102 suite (mock and file backend); commit afterwards as "plan: A-59 installed"
set -eu
cd "$(dirname "$0")/.."
. tools/amendment_lib.sh
amendment_args "$@"
A=specs/mia/amendments/A-59
D=specs/mia/contract-drafts
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
python3 - tests/helpers/contract.py specs/mia/test-spec.md stages.yaml "$WORK" "$A/real_storage.py" <<'PY'
import os
import sys
contract, spec, stages, work, snippet_path = sys.argv[1:6]


def edit(path, old, new, what, text=None):
    """old -> new exactly once; a text that has the new part already is left as it is (the copy then reports unchanged)."""
    text = open(path, encoding="utf-8").read() if text is None else text
    if new in text:
        return text
    if text.count(old) != 1:
        sys.exit("%s: %s is not found exactly once; install A-59 by hand" % (path, what))
    return text.replace(old, new)


def write(name, text):
    open(os.path.join(work, name), "w", encoding="utf-8").write(text)


old_adapter = '''        import tempfile
        from errors import StorageError
        from storage import Storage
        url = os.environ.get("MIA_TEST_DATABASE_URL")
        if url:
            from storage_postgres import PostgresBackend
            backend = PostgresBackend(url)
            backend._query("TRUNCATE records")
        else:
            from storage_files import FileBackend
            backend = FileBackend(tempfile.mkdtemp())
        self._store, self._error = Storage(backend), StorageError

    def __getattr__(self, name):
        from storage import StorageError as LayerError
        method = getattr(self._store, name)

        def call(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except LayerError as err:
'''
new_adapter = '''        import tempfile
        from errors import StorageError
        layer = _real_storage_module("storage")          # by file path with the real graph rules (A-59)
        url = os.environ.get("MIA_TEST_DATABASE_URL")
        if url:
            backend = _real_storage_module("storage_postgres").PostgresBackend(url)
            backend._query("TRUNCATE records")
        else:
            backend = _real_storage_module("storage_files").FileBackend(tempfile.mkdtemp())
        self._store, self._error, self._layer_error = layer.Storage(backend), StorageError, layer.StorageError

    def __getattr__(self, name):
        method = getattr(self._store, name)

        def call(*args, **kwargs):
            try:
                return method(*args, **kwargs)
            except self._layer_error as err:
'''
text = edit(contract, old_adapter, new_adapter, "the body of _StorageAdapter")
snippet = open(snippet_path, encoding="utf-8").read()
anchor = "class _StorageAdapter:\n"
if "def _real_storage_module" not in text:
    if text.count(anchor) != 1:
        sys.exit("%s: class _StorageAdapter is not found exactly once; install A-59 by hand" % contract)
    text = text.replace(anchor, snippet + anchor)
write("contract.py", text)

row8 = "| TC-IF-102-08 | IF-102 | Contract | 1 (mock) and 2 (real) | F-5: a run result and a source trust value are written and read back as versions; the second write of a source is version 2. | exact |\n"
rows = ("| TC-IF-102-09 | IF-102 | Contract | 1 (mock), 2 (real, files) and 3 (real, PostgreSQL) | golden 4 (A-59): a delete is told to the subscribers with version None; a refused delete tells nothing. | exact |\n"
        "| TC-IF-102-10 | IF-102 | Contract | 1 (mock), 2 (real, files) and 3 (real, PostgreSQL) | golden 5 (A-59, D-162): categories() gives the four vote categories in their order; a vote of each is stored. | exact |\n")
write("test-spec.md", edit(spec, row8, row8 + rows, "the row of TC-IF-102-08"))

after = '  - {id: contract-real, stage: 2, cmd: "python -m unittest discover -s tests/acceptance/contract -p \\"test_if_*.py\\" -k _real", needs: [acceptance]}\n'
step = ('  # contract-postgres (A-59): the IF-102 suite on a throwaway postgres:16 (local image, never pulled); MIA_DB_PYTHON names a python with psycopg 3\n'
        '  - {id: contract-postgres, stage: 3, cmd: "bash tools/contract_postgres.sh", needs: [contract-real]}\n')
write("stages.yaml", edit(stages, after, after + step, "the step contract-real"))
PY
copy $A/IF-102-storage-interface.md contracts/IF-102-storage-interface.md
copy $D/tests/helpers/mocks/if_102_storage.py tests/helpers/mocks/if_102_storage.py
copy $D/tests/acceptance/contract/test_if_102_storage.py tests/acceptance/contract/test_if_102_storage.py
copy "$WORK/contract.py" tests/helpers/contract.py
copy "$WORK/stages.yaml" stages.yaml
copy "$WORK/test-spec.md" specs/mia/test-spec.md
finish
echo
python3 tests/acceptance/contract/test_if_102_storage.py 2>&1 | tail -n 3
echo "the PostgreSQL side: MIA_DB_PYTHON=/path/to/python-with-psycopg bash tools/contract_postgres.sh"
