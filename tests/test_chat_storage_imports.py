"""TC-CHA-020 (REQ-CHA-020): the Chat agent keeps and reads state only through the storage interface (IF-102): none of its modules imports a database driver;
the storage client is the one that does. Inspection of the code, stdlib only. Run with: python tests/test_chat_storage_imports.py"""
import ast
import os
import sys
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

DRIVERS = {'psycopg', 'psycopg2', 'sqlite3', 'sqlalchemy', 'pymysql', 'asyncpg'}

CHAT_AGENT = [
    'chat_service.py',
    'chat_log.py',
    'chat_api.py',
    'chat_ops_api.py',
    'items_api.py',
    'trust_persona_api.py',
    'behaviour.py',
    'moods.py',
    'research_chat.py',
    'extraction.py',
    'source_trust.py',
]


def imported_modules(path):
    with open(path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for name in node.names:
                modules.add(name.name.split('.')[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                modules.add(node.module.split('.')[0])
    return modules


class TestChatStorageImports(unittest.TestCase):
    def test_the_chat_agent_imports_no_database_driver(self):
        for file in CHAT_AGENT:
            path = os.path.join(os.path.dirname(__file__), '..', file)
            if not os.path.exists(path):
                continue
            self.assertEqual(
                imported_modules(path) & DRIVERS,
                set(),
                f"File {file} imports a database driver",
            )

    def test_the_storage_client_is_the_one_that_imports_a_driver(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'storage_postgres.py')
        self.assertIn('psycopg', imported_modules(path))

    def test_the_chat_service_reaches_state_through_the_storage_interface(self):
        path = os.path.join(os.path.dirname(__file__), '..', 'chat_service.py')
        self.assertIn('storage', imported_modules(path))


if __name__ == '__main__':
    unittest.main()
