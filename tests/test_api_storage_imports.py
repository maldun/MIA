"""
N-2.1 T-05, TC-API-012 (REQ-API-012): inspection of the imports of the modules of the API and accounts, and the calls of the accounts on a recording
storage mock (IF-102). Standard library and the mocks only:  python tests/test_api_storage_imports.py
"""
import ast
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

import accounts                                   # noqa: E402
from api_sessions import SessionService           # noqa: E402
from if_102_storage import StorageMock            # noqa: E402
from markers import mark                          # noqa: E402

DRIVERS = {"psycopg", "psycopg2", "sqlite3", "sqlalchemy", "pymysql", "asyncpg"}
IF_102_OPERATIONS = {"put", "get", "history", "ids", "delete", "subscribe"}
API_AND_ACCOUNTS = ["web_app.py", "chat_api.py", "presets_api.py", "tls_proxy.py", "accounts.py", "accounts_api.py", "api_sessions.py", "graph_api.py",
                    "internal_auth.py", os.path.join("tools", "accounts_cli.py")]


def imported_modules(path):
    """the top-level names of every module the file imports (relative imports of the package are left out)"""
    with open(path, encoding="utf-8") as fp:
        tree = ast.parse(fp.read())
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(name.name.split(".")[0] for name in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.add(node.module.split(".")[0])
    return modules


class Recording:
    """the storage mock of IF-102 that notes every call as (operation, table)"""

    def __init__(self):
        self.store, self.calls = StorageMock(), []

    def __getattr__(self, name):
        method = getattr(self.store, name)

        def call(table, *args, **kwargs):
            self.calls.append((name, table))
            return method(table, *args, **kwargs)
        return call


class StateOnlyThroughTheStorageInterface(unittest.TestCase):
    """the API and accounts keep and read accounts only through IF-102; the database driver is imported by the storage client alone"""

    @mark.req("REQ-API-012")
    def test_no_module_of_the_api_imports_a_database_driver(self):
        """TC-API-012: none of the modules of the API and accounts imports a database driver.

        Example: accounts.py imports hashlib, hmac, os -> no psycopg, no sqlite3.
        """
        # Given
        paths = [os.path.join(REPO, name) for name in API_AND_ACCOUNTS]
        # When
        found = {os.path.basename(path): imported_modules(path) & DRIVERS for path in paths}
        # Then
        self.assertEqual(found, {os.path.basename(path): set() for path in paths})

    @mark.req("REQ-API-012")
    def test_the_storage_client_is_the_one_that_imports_a_driver(self):
        """TC-API-012: the PostgreSQL storage client imports psycopg, so the inspection looks at real imports.

        Example: storage_postgres.py -> psycopg.
        """
        # Given
        path = os.path.join(REPO, "storage_postgres.py")
        # When
        modules = imported_modules(path)
        # Then
        self.assertIn("psycopg", modules)

    @mark.req("REQ-API-012")
    def test_accounts_are_kept_and_read_only_through_the_storage_interface(self):
        """TC-API-012: creating an account, changing its password and checking it are calls of IF-102 on the table accounts and nothing else.

        Example: create anna, set a new password, verify it -> every call is put, get, history or ids on "accounts".
        """
        # Given
        store = Recording()
        # When
        accounts.create(store, "anna", "pw-anna-1", "setup")
        accounts.set_password(store, "anna", "pw-anna-2", "anna")
        ok = accounts.verify(store, "anna", "pw-anna-2")
        # Then
        self.assertTrue(ok)
        self.assertEqual({table for _, table in store.calls}, {"accounts"})
        self.assertTrue({name for name, _ in store.calls} <= IF_102_OPERATIONS)
        self.assertEqual(len(store.store.history("accounts", "anna")), 2)

    @mark.req("REQ-API-012")
    def test_the_session_service_reads_accounts_through_the_storage_interface(self):
        """TC-API-012: a login reads the account through IF-102 only; the session itself is kept in memory.

        Example: ben logs in -> the calls are on the table accounts; whoami gives ben.
        """
        # Given
        store = Recording()
        accounts.create(store, "ben", "pw-ben-123", "setup")
        store.calls.clear()
        service = SessionService(store)
        # When
        token = service.login("ben", "pw-ben-123")
        # Then
        self.assertEqual(service.whoami(token)["user"], "ben")
        self.assertEqual({table for _, table in store.calls}, {"accounts"})
        self.assertTrue({name for name, _ in store.calls} <= IF_102_OPERATIONS)

if __name__ == "__main__":
    unittest.main()
