"""MIA's web_app with `store: database` while the database does not answer (V-3 of G-V4.VIEW's verification, handed to TRANSFER; REQ-API-021,
REQ-API-050): the start goes on, the store answer says the store does not answer, the graph routes answer 503 `store_unreachable`.
Runs MIA's real web_app from a copy of the checkout in a separate process (tests/helpers/web_app_probe.py).
Run with: /home/maldun/prog/Python/venvs/mia312/bin/python tests/test_web_app_live_store.py"""
import os
import socket
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))
from markers import mark                                           # noqa: E402
from web_app_probe import WebAppProbe, checkout_with, last_json    # noqa: E402

ASK = """
accounts.create(wa._account_store, "anna", "pw-anna-1", "tests")
web = wa.app.test_client()
out = {"login": web.post("/api/login", json={"user": "anna", "password": "pw-anna-1"}).status_code}
for path in ("/api/v2/store", "/api/v2/graphs"):
    answer = web.get(path)
    out[path] = [answer.status_code, answer.get_json(silent=True)]
print(json.dumps(out))
"""


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class DatabaseDownAtStart(unittest.TestCase):

    @mark.req("REQ-API-021", "REQ-API-050")
    def test_mia_starts_and_answers_store_unreachable(self):
        """Example: store database at 127.0.0.1:<free port>, no copy -> the import works; /store says reachable false; /graphs 503."""
        try:
            import psycopg  # noqa: F401
        except ImportError:
            self.skipTest("psycopg 3 is missing (requirements-db.txt)")
        # Given: MIA configured for a database nobody answers, no copy
        folder = checkout_with({"accounts_enabled": True, "store": "database"}, drop=("store", "copy", "autosync"))
        url = "postgresql://mia@127.0.0.1:%d/mia?connect_timeout=3" % free_port()
        # When: web_app is imported and the store and the list are asked
        done = WebAppProbe.run(folder, ASK, env={"MIA_DATABASE_URL": url})
        # Then: it started, and both answers say the store does not answer
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        out = last_json(done)
        self.assertEqual(out["login"], 200)
        self.assertEqual(out["/api/v2/store"], [200, {"store": "database", "reachable": False, "shown": "live", "live_reachable": False,
                                                      "lag": {"graphs": 0, "since": None}}])
        self.assertEqual(out["/api/v2/graphs"][0], 503)
        self.assertEqual(out["/api/v2/graphs"][1]["error"], "store_unreachable")


if __name__ == "__main__":
    unittest.main()
