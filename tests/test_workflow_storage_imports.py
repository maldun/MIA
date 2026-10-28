"""TC-WFM-025 (REQ-WFM-025): the Workflow management keeps and reads workflows and context graphs only through the storage interface (IF-102):
neither workflow_library.py nor any module it imports from this repository imports a database driver. Inspection of the code, stdlib only.
Run with: python tests/test_workflow_storage_imports.py"""
import ast
import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(ROOT)

DRIVERS = {'psycopg', 'psycopg2', 'sqlite3', 'sqlalchemy', 'pymysql', 'asyncpg'}


def imported_modules(path):
    """Top-level names imported by a file; relative imports count by their module or imported names."""
    with open(path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                modules.add(name.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module.split('.')[0])
            elif node.level:
                modules.update(a.name for a in node.names)
    return modules


def local_closure(start):
    """The modules of this folder that `start` imports, directly or through others (the fallback imports included)."""
    seen, todo = set(), [start]
    while todo:
        name = todo.pop()
        if name in seen:
            continue
        seen.add(name)
        path = os.path.join(ROOT, name + '.py')
        if os.path.exists(path):
            todo.extend(m for m in imported_modules(path) if os.path.exists(os.path.join(ROOT, m + '.py')))
    return seen


class TestWorkflowStorageImports(unittest.TestCase):
    def test_the_workflow_library_and_what_it_imports_use_no_database_driver(self):
        closure = local_closure('workflow_library')
        self.assertIn('storage', closure)
        for name in sorted(closure):
            with self.subTest(module=name):
                path = os.path.join(ROOT, name + '.py')
                self.assertEqual(imported_modules(path) & DRIVERS, set(), f"{name}.py imports a database driver")

    def test_the_workflow_library_reaches_state_through_the_storage_interface(self):
        self.assertIn('storage', imported_modules(os.path.join(ROOT, 'workflow_library.py')))

    def test_the_storage_client_is_the_one_that_imports_a_driver(self):
        self.assertIn('psycopg', imported_modules(os.path.join(ROOT, 'storage_postgres.py')))


if __name__ == '__main__':
    unittest.main()
