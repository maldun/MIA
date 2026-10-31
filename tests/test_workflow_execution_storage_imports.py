"""
TC-N24-001 (REQ-WFX-022, AC-15), N-2.4 integration step: the Workflow execution imports no database driver outside the storage client. Inspection of the
three parts together (Pipeline runner, Tools and sandbox, Run log) and every module of this folder they import. The one exception is the search index of
library.py (sqlite3, data/library.sqlite): the owner allows it as a cache that is rebuilt from the library files (D-147, D-138); the tests below pin that
it is the only one and that it stays a cache. Stdlib only. Run with: python tests/test_workflow_execution_storage_imports.py
"""
import ast
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                       # noqa: E402
from library import Library                                    # noqa: E402

DRIVERS = {"psycopg", "psycopg2", "sqlite3", "sqlalchemy", "pymysql", "asyncpg"}
# the modules of the three parts (architecture.sysml: pipelineRunner, toolDoor, runLog)
PARTS = ("core", "pipeline", "pipeline_model", "schema_check", "run_workflow", "tool_calls", "events", "run_log", "evidence", "run_events")
ALLOWED = {"library": {"sqlite3"}}                             # D-147: the search index is a cache


def imported_modules(path):
    found = set()
    for node in ast.walk(ast.parse(open(path, encoding="utf-8").read())):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module.split(".")[0])
            elif node.level:
                found.update(alias.name for alias in node.names)
    return found


def local_closure(starts):
    """the modules of this folder that the starts import, directly or through others"""
    seen, todo = set(), list(starts)
    while todo:
        name = todo.pop()
        path = os.path.join(ROOT, name + ".py")
        if name in seen or not os.path.exists(path):
            continue
        seen.add(name)
        todo.extend(imported_modules(path))
    return seen


class WorkflowExecutionStorage(unittest.TestCase):

    # REQ-WFX-022
    @mark.req("REQ-WFX-022")
    def test_no_module_of_the_workflow_execution_imports_a_database_driver(self):
        """TC-N24-001: the three parts and every local module they import use no database driver, apart from the index of library.py (D-147).

        Example: closure of core, pipeline, tool_calls, run_events ... (22 modules) -> only library.py imports sqlite3.
        """
        # Given: the modules of the three parts and what they import from this folder
        closure = local_closure(PARTS)
        self.assertTrue(set(PARTS) <= closure)
        # When: their imports are read
        found = {name: imported_modules(os.path.join(ROOT, name + ".py")) & DRIVERS for name in closure}
        # Then: no driver except the allowed cache
        self.assertEqual({name: drivers for name, drivers in found.items() if drivers}, ALLOWED)

    # REQ-WFX-022
    @mark.req("REQ-WFX-022")
    def test_the_index_of_the_library_is_rebuilt_from_the_files(self):
        """TC-N24-001 (D-147): the sqlite3 index is a cache: deleted, it comes back from the library files with the same content.

        Example: used_by("check.number@1") before and after deleting library.sqlite -> the same pipelines.
        """
        # Given: the shipped library with an index in a fresh folder
        folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, folder, True)
        index = os.path.join(folder, "library.sqlite")
        before = Library(os.path.join(ROOT, "library"), os.path.join(folder, "user"), index).used_by("check.number@1")
        self.assertTrue(before)
        # When: the index is deleted and the library opened again
        os.remove(index)
        after = Library(os.path.join(ROOT, "library"), os.path.join(folder, "user"), index).used_by("check.number@1")
        # Then: the index holds the same
        self.assertEqual(after, before)

    # REQ-WFX-022
    @mark.req("REQ-WFX-022")
    def test_no_code_keeps_state_in_the_index_that_the_files_cannot_rebuild(self):
        """TC-N24-001 (D-147): the cases table of the index cannot be rebuilt; no module outside the tests writes to it, so the index stays a cache.

        Example: calls of Library.add_case in the repository's .py files outside tests/ -> none.
        """
        # Given: every Python file of the repository outside tests/, specs/ and the worktrees
        callers = []
        for folder, dirs, files in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in ("tests", "specs", ".git", ".claude", "node_modules", "__pycache__")]
            for name in files:
                if name.endswith(".py") and name != "library.py":
                    # When: its calls are read
                    tree = ast.parse(open(os.path.join(folder, name), encoding="utf-8").read())
                    if any(isinstance(n, ast.Attribute) and n.attr == "add_case" for n in ast.walk(tree)):
                        callers.append(os.path.relpath(os.path.join(folder, name), ROOT))
        # Then: nobody writes cases
        self.assertEqual(callers, [])


if __name__ == "__main__":
    unittest.main()
