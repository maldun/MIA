"""The provider of IF-104 v2 (G-V4.VIEW T-02, T-03): store setting, session, origin, owner, an unreachable store and the read routes. Run with: python tests/test_graph_api_v2.py"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "helpers"))

from flask import Flask                      # noqa: E402

import accounts                              # noqa: E402
import graph_api_v2                          # noqa: E402
import graph_model                           # noqa: E402
from markers import mark                     # noqa: E402
from storage import Storage                  # noqa: E402
from storage_files import FileBackend        # noqa: E402

ORIGIN = "http://localhost"


class Down:
    """a backend whose every call fails, as a lost database connection does"""

    def ids(self, table):
        raise OSError("down")


class StoreSetting(unittest.TestCase):
    @mark.req("REQ-API-019", "REQ-API-020")
    def test_the_setting_is_files_database_or_a_stop(self):
        """Example: {} -> files; {"store": "database"} -> database; {"store": None} -> ValueError naming store and None."""
        # Given configurations without, with good and with bad store settings
        # When the setting is read
        # Then files is the default, the two names pass, and anything else stops with the setting and the value named
        self.assertEqual(graph_api_v2.store_setting({}), "files")
        self.assertEqual(graph_api_v2.store_setting({"store": "database"}), "database")
        for bad, shown in ((None, "None"), ("Files", "'Files'"), ("", '""'), (True, "True")):
            with self.assertRaises(ValueError) as caught:
                graph_api_v2.store_setting({"store": bad})
            self.assertIn('"store"', str(caught.exception))
            self.assertIn(shown, str(caught.exception))

    @mark.req("REQ-API-020")
    def test_create_app_refuses_an_unknown_store_name(self):
        """Example: create_app(..., store="postgres", ...) -> ValueError (the names are files and database)."""
        # Given / When / Then
        with self.assertRaises(ValueError):
            graph_api_v2.create_app(Down(), None, "postgres", (ORIGIN,))


class Provider(unittest.TestCase):
    def setUp(self):
        root = tempfile.mkdtemp(prefix="v2-")
        self.addCleanup(shutil.rmtree, root, True)
        self.accounts_store = Storage(FileBackend(os.path.join(root, "accounts")))
        for name in ("anna", "ben"):
            accounts.create(self.accounts_store, name, "pw-" + name + "-x", "test")
        self.backend = FileBackend(os.path.join(root, "graphs"))

    def client(self, user, backend=None):
        app = graph_api_v2.create_app(backend or self.backend, self.accounts_store, "files", (ORIGIN,))
        web = app.test_client()
        if user:
            self.assertEqual(web.post("/api/login", json={"user": user, "password": "pw-" + user + "-x"}, headers={"Origin": ORIGIN}).status_code, 200)
        return web

    @mark.req("REQ-API-047")
    def test_a_change_without_an_origin_is_refused(self):
        """Example: anna saves with no Origin header -> 403 bad_origin (a change needs the page's origin)."""
        # Given anna logged in
        web = self.client("anna")
        # When she saves with no Origin
        answer = web.put("/api/v2/graphs/g", json={"graph": {}})
        # Then the change is refused for its origin
        self.assertEqual((answer.status_code, answer.get_json()["error"]), (403, "bad_origin"))

    @mark.req("REQ-API-046")
    def test_a_change_by_another_account_is_refused(self):
        """Example: ben (second account) saves -> 403 not_owner."""
        # Given ben logged in
        web = self.client("ben")
        # When he saves from the page's origin
        answer = web.put("/api/v2/graphs/g", json={"graph": {}}, headers={"Origin": ORIGIN})
        # Then he is not the owner
        self.assertEqual((answer.status_code, answer.get_json()["error"]), (403, "not_owner"))

    @mark.req("REQ-API-021", "REQ-API-022", "REQ-API-050")
    def test_a_store_that_is_down_is_named_and_refused(self):
        """Example: a backend that raises -> store reachable false, live_reachable false; the list 503 store_unreachable; me still answers."""
        # Given anna logged in on a store that does not answer
        web = self.client("anna", backend=Down())
        # When she asks for the store, the list and herself
        store, listing, me = web.get("/api/v2/store"), web.get("/api/v2/graphs"), web.get("/api/v2/me")
        # Then the store says it is down, the list is refused, me answers
        self.assertEqual(store.get_json(), {"store": "files", "reachable": False, "shown": "live", "live_reachable": False, "lag": {"graphs": 0, "since": None}})
        self.assertEqual((listing.status_code, listing.get_json()["error"]), (503, "store_unreachable"))
        self.assertEqual(me.get_json(), {"user": "anna", "owner": True})

    @mark.req("REQ-API-045")
    def test_without_the_accounts_guard_every_route_needs_a_session(self):
        """Example: the blueprint on an app without the guard (accounts switched off) -> /api/v2/me 401 unauthenticated."""
        # Given the v2 routes on an app that sets no account
        app = Flask(__name__)
        app.register_blueprint(graph_api_v2.create_graph_v2_blueprint(self.backend, "files", lambda a: True, lambda: [ORIGIN]))
        # When me and store are asked
        answers = [app.test_client().get(p) for p in ("/api/v2/me", "/api/v2/store")]
        # Then both need a session
        self.assertEqual([(a.status_code, a.get_json()["error"]) for a in answers], [(401, "unauthenticated")] * 2)


def small(graph_id):
    return {"id": graph_id, "context_graph_id": "ctx", "testbench_id": "tb", "description": "small",
            "nodes": [{"id": "var.in", "data": {"type": "data", "value": "x"}}, {"id": "step.a", "data": {"type": "transform", "toolbox_id": "tool.a"}}],
            "edges": [{"id": "e1", "from": "var.in", "to": "step.a", "data": {}}]}


class Reading(unittest.TestCase):
    """the read routes of T-03 beyond the contract cases: bad versions, unknown graphs, duplicate steps, context graphs"""

    def setUp(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        self.accounts_store = Storage(FileBackend(os.path.join(root, "accounts")))
        accounts.create(self.accounts_store, "anna", "pw-anna-x", "test")
        self.backend = FileBackend(os.path.join(root, "graphs"))
        graph_model.GraphModel(Storage(self.backend), author="anna").save_graph(small("g.one"))
        self.web = graph_api_v2.create_app(self.backend, self.accounts_store, "files", (ORIGIN,)).test_client()
        self.web.post("/api/login", json={"user": "anna", "password": "pw-anna-x"}, headers={"Origin": ORIGIN})

    @mark.req("REQ-API-049")
    def test_a_version_that_is_not_stored_is_not_found(self):
        """Example: g.one has version 1; ?version=0, 2, -1 and abc each answer 404 not_found with detail version."""
        # Given g.one with one version
        # When versions that do not exist or are no number are asked for
        answers = [self.web.get("/api/v2/graphs/g.one?version=" + v) for v in ("0", "2", "-1", "abc")]
        # Then each is not found, naming the version
        self.assertEqual([(a.status_code, a.get_json()["error"], a.get_json().get("detail")) for a in answers], [(404, "not_found", "version")] * 4)

    @mark.req("REQ-API-049")
    def test_an_unknown_graph_is_not_found_on_every_read(self):
        """Example: g.none read, its versions and its arrangement -> 404 not_found without detail."""
        # Given no graph g.none
        # When it is read three ways
        answers = [self.web.get("/api/v2/graphs/g.none" + p) for p in ("", "/versions", "/arrangement")]
        # Then each is not found
        self.assertEqual([(a.status_code, a.get_json()["error"], a.get_json().get("detail")) for a in answers], [(404, "not_found", None)] * 3)

    @mark.req("REQ-API-026")
    def test_a_step_id_used_twice_is_one_problem(self):
        """Example: step.a three times -> one duplicate_step problem; a connection to var.gone -> missing_step at its end."""
        # Given a graph with one step ID three times and a connection to a missing step
        graph = small("g.dup")
        graph["nodes"] += [dict(graph["nodes"][1]), dict(graph["nodes"][1])]
        graph["edges"].append({"id": "e2", "from": "step.a", "to": "var.gone", "data": {}})
        # When its problems are named
        found = graph_api_v2.problems_of(graph)
        # Then the duplicate is named once and the missing end once
        self.assertEqual(found, [{"problem": "duplicate_step", "step": "step.a"},
                                 {"problem": "missing_step", "connection": "e2", "step": "var.gone", "end": "to"}])

    @mark.req("REQ-API-027")
    def test_a_context_graph_names_the_kind_only(self):
        """Example: a context graph with a transform step -> {"kind": "transform"} without trust marks."""
        # Given a context graph
        graph = {"kind": "context", "nodes": [{"id": "c.a", "data": {"type": "transform", "toolbox_id": "tool.a"}}, {"id": "c.b", "data": None}], "edges": []}
        # When its steps are described
        steps = graph_api_v2.steps_of(graph, toolbox=None)
        # Then only the kind is given, unknown where none is stored
        self.assertEqual(steps, {"c.a": {"kind": "transform"}, "c.b": {"kind": "unknown"}})


if __name__ == "__main__":
    unittest.main()
