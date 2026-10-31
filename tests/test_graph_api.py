"""
N-2.1 T-04, the routes of IF-104 (graph_api.py) on the real guard and the real workflow library, with the file backend of the Storage layer:
 TC-API-014  REQ-API-014, REQ-API-016  each of the six operations works on its route; an invalid graph is refused with the rule named
Needs flask: run with the image:  bash tools/run_in_image.sh tests/test_graph_api.py
"""

import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from flask import Flask                                  # noqa: E402

import accounts                                          # noqa: E402
import accounts_api as A                                 # noqa: E402
from graph_api import create_graph_blueprint             # noqa: E402
from storage import Storage                              # noqa: E402
from storage_files import FileBackend                    # noqa: E402
from workflow_library import WorkflowLibrary             # noqa: E402
from markers import mark                                 # noqa: E402

GRAPH = {"nodes": [{"id": "claim", "kind": "data"}, {"id": "check", "kind": "process"}, {"id": "verdict", "kind": "data"}],
         "edges": [{"from": "claim", "to": "check"}, {"from": "check", "to": "verdict"}]}
CYCLE = {"nodes": [{"id": "a", "kind": "process"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}]}
ADJACENT = {"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}


def edited(note):
    doc = {"nodes": [dict(n) for n in GRAPH["nodes"]], "edges": list(GRAPH["edges"])}
    doc["nodes"][1]["note"] = note
    return doc


class NoSockets:
    def disconnect(self, sid):
        pass


class GraphRoutes(unittest.TestCase):
    """the routes of IF-104 on the real guard of the Backend and the real workflow library (IF-203) on the Storage layer with the file backend"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        store = Storage(FileBackend(os.path.join(self.tmp.name, "db")))
        accounts.create(store, "anna", "pw-anna-1", "setup")
        accounts.create(store, "ben", "pw-ben-123", "setup")
        self.app = Flask(__name__)
        A.install(self.app, NoSockets(), store, allowed_origins=lambda: [])
        self.app.register_blueprint(create_graph_blueprint(WorkflowLibrary(store)))
        self.anna = self.browser("anna", "pw-anna-1")

    def tearDown(self):
        self.tmp.cleanup()

    def browser(self, user, password):
        """a logged-in browser: a test client that carries the session cookie"""
        web = self.app.test_client()
        self.assertEqual(web.post("/api/login", json={"user": user, "password": password}).status_code, 200)
        return web

    def put(self, web, path, doc, expected=None):
        body = {"doc": doc} if expected is None else {"doc": doc, "expected_version": expected}
        return web.put(path, json=body)

    @mark.req("REQ-API-014", "REQ-API-016")
    def test_save_read_and_list(self):
        """TC-API-014: a saved workflow is version 1 by the session's account, read back with the five fields, and listed.

        Example: anna PUTs the lookup graph -> {"version": 1}; GET gives id lookup, version 1, author anna, the same doc.
        """
        # Given
        path = "/api/workflows/lookup"
        # When
        answer = self.put(self.anna, path, GRAPH)
        # Then
        self.assertEqual((answer.status_code, answer.get_json()), (200, {"version": 1}))
        read = self.anna.get(path).get_json()
        self.assertEqual(set(read), {"id", "version", "author", "time", "doc"})
        self.assertEqual((read["id"], read["version"], read["author"], read["doc"]), ("lookup", 1, "anna", GRAPH))
        self.assertEqual(self.anna.get("/api/workflows").get_json(), ["lookup"])

    @mark.req("REQ-API-014", "REQ-API-016")
    def test_history_diff_restore_and_an_older_version(self):
        """TC-API-014: two authors make versions 1 and 2, the diff names the changed node, restore makes version 3 equal to version 1.

        Example: anna saves, ben edits the node check, anna restores 1 -> history (1 anna, 2 ben, 3 anna).
        """
        # Given
        ben = self.browser("ben", "pw-ben-123")
        self.put(self.anna, "/api/workflows/lookup", GRAPH)
        self.put(ben, "/api/workflows/lookup", edited("tighter"))
        # When
        diff = self.anna.get("/api/workflows/lookup/diff?a=1&b=2").get_json()
        restored = self.anna.post("/api/workflows/lookup/restore", json={"version": 1}).get_json()
        # Then
        self.assertEqual(diff, {"nodes_added": [], "nodes_removed": [], "nodes_changed": ["check"], "edges_added": [], "edges_removed": []})
        self.assertEqual(restored, {"version": 3})
        self.assertEqual(self.anna.get("/api/workflows/lookup").get_json()["doc"], GRAPH)
        self.assertEqual(self.anna.get("/api/workflows/lookup?version=2").get_json()["doc"], edited("tighter"))
        history = self.anna.get("/api/workflows/lookup/history").get_json()
        self.assertEqual([(h["version"], h["author"]) for h in history], [(1, "anna"), (2, "ben"), (3, "anna")])
        self.assertEqual(set(history[0]), {"version", "author", "time"})

    @mark.req("REQ-API-014", "REQ-API-016")
    def test_an_invalid_graph_is_refused_with_the_rule(self):
        """TC-API-014: a cycle and two adjacent data nodes are 422 invalid with the rule; no id appears.

        Example: PUT a->b->a -> 422 {"error": "invalid", "rule": "cycle"}.
        """
        # Given
        self.assertEqual(self.anna.get("/api/workflows").get_json(), [])
        # When
        cycle = self.put(self.anna, "/api/workflows/bad", CYCLE)
        adjacent = self.put(self.anna, "/api/context_graphs/bad", ADJACENT)
        # Then
        self.assertEqual((cycle.status_code, cycle.get_json()["error"], cycle.get_json()["rule"]), (422, "invalid", "cycle"))
        self.assertEqual((adjacent.status_code, adjacent.get_json()["rule"]), (422, "adjacent_data_nodes"))
        self.assertEqual(self.anna.get("/api/workflows").get_json(), [])
        self.assertEqual(self.anna.get("/api/context_graphs").get_json(), [])

    @mark.req("REQ-API-016")
    def test_unknown_kind_id_and_version_are_404(self):
        """TC-API-014: an unknown kind is 404 unknown_kind; an unknown id or version is 404 not_found.

        Example: GET /api/nonsense -> 404 {"error": "unknown_kind"}.
        """
        # Given
        self.put(self.anna, "/api/workflows/lookup", GRAPH)
        # When
        kind = self.anna.get("/api/nonsense")
        record = self.anna.get("/api/workflows/none")
        version = self.anna.get("/api/workflows/lookup?version=7")
        diff = self.anna.get("/api/workflows/lookup/diff?a=1&b=9")
        # Then
        self.assertEqual((kind.status_code, kind.get_json()), (404, {"error": "unknown_kind"}))
        self.assertEqual((record.status_code, record.get_json()), (404, {"error": "not_found"}))
        self.assertEqual((version.status_code, version.get_json()), (404, {"error": "not_found"}))
        self.assertEqual((diff.status_code, diff.get_json()), (404, {"error": "not_found"}))

    @mark.req("REQ-API-016")
    def test_a_stale_expected_version_is_409_with_the_current_version(self):
        """TC-API-014: saving with expected_version 1 when the record is at version 2 is 409 conflict with the current version; nothing changes.

        Example: versions 1 and 2, PUT with expected_version 1 -> 409 {"error": "conflict", "detail": {"current": 2}}.
        """
        # Given
        self.put(self.anna, "/api/workflows/w", GRAPH)
        self.put(self.anna, "/api/workflows/w", edited("b"))
        # When
        answer = self.put(self.anna, "/api/workflows/w", edited("c"), expected=1)
        # Then
        self.assertEqual((answer.status_code, answer.get_json()), (409, {"error": "conflict", "detail": {"current": 2}}))
        self.assertEqual(len(self.anna.get("/api/workflows/w/history").get_json()), 2)

    @mark.req("REQ-API-014", "REQ-API-007")
    def test_no_session_is_401_and_changes_nothing(self):
        """TC-API-014: without the session cookie every route is 401 unauthenticated and nothing is saved.

        Example: PUT /api/workflows/w without a login -> 401 {"error": "unauthenticated"}.
        """
        # Given
        stranger = self.app.test_client()
        # When
        answers = [stranger.get("/api/workflows"), stranger.put("/api/workflows/w", json={"doc": GRAPH}), stranger.get("/api/workflows/w/history"),
                   stranger.post("/api/workflows/w/restore", json={"version": 1})]
        # Then
        self.assertEqual([(a.status_code, a.get_json()) for a in answers], [(401, {"error": "unauthenticated"})] * 4)
        self.assertEqual(self.anna.get("/api/workflows").get_json(), [])

    @mark.req("REQ-API-016")
    def test_the_id_in_the_path_is_url_encoded(self):
        """TC-API-014: an id with a space travels URL-encoded in the path and comes back as it was.

        Example: PUT /api/workflows/my%20flow -> the list is ["my flow"].
        """
        # Given
        path = "/api/workflows/my%20flow"
        # When
        answer = self.put(self.anna, path, GRAPH)
        # Then
        self.assertEqual(answer.get_json(), {"version": 1})
        self.assertEqual(self.anna.get("/api/workflows").get_json(), ["my flow"])
        self.assertEqual(self.anna.get(path).get_json()["id"], "my flow")

    @mark.req("REQ-API-016")
    def test_an_id_the_routes_cannot_take_is_404_not_found_in_json(self):
        """TC-API-014 (D-149, V-7): an id with an encoded slash cannot be addressed; every route answers JSON 404 not_found and nothing is saved.

        Example: GET /api/workflows/a%2Fb -> 404 {"error": "not_found"} (was Flask's HTML 404).
        """
        # Given
        path = "/api/workflows/a%2Fb"
        # When
        answers = [self.anna.get(path), self.put(self.anna, path, GRAPH), self.anna.get(path + "/history"), self.anna.get(path + "/diff?a=1&b=2"),
                   self.anna.post(path + "/restore", json={"version": 1})]
        # Then
        self.assertEqual([(a.status_code, a.get_json()) for a in answers], [(404, {"error": "not_found"})] * 5)
        self.assertEqual(self.anna.get("/api/workflows").get_json(), [])

if __name__ == "__main__":
    unittest.main()
