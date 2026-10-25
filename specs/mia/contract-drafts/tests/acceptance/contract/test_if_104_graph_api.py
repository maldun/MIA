"""IF-104 workflow and graph API for the Graph app: the contract suite runs against the mock (stage 1) and the real provider
(stage 2, skipped until N-2 is integrated). Protected after the Plan gate. Run with: python tests/acceptance/contract/test_if_104_graph_api.py"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "helpers"))

from contract import contract, each_provider  # noqa: E402
from markers import mark                      # noqa: E402  (from tests/helpers, shared with the other acceptance tests)
from errors import ApiError                   # noqa: E402

IF = "IF-104"
GRAPH = {"nodes": [{"id": "claim", "kind": "data"}, {"id": "check", "kind": "process"}, {"id": "verdict", "kind": "data"}],
         "edges": [{"from": "claim", "to": "check"}, {"from": "check", "to": "verdict"}]}


def edited(note):
    doc = {"nodes": [dict(n) for n in GRAPH["nodes"]], "edges": list(GRAPH["edges"])}
    doc["nodes"][1]["note"] = note
    return doc


def error_of(call):
    try:
        call()
    except ApiError as err:
        return err
    raise AssertionError("no ApiError raised")


@contract
class GraphApiContract(unittest.TestCase):
    @mark.req("IF-104", "REQ-BE-076")
    @each_provider(IF)
    def test_save_edit_diff_and_restore(self, api):
        """TC-IF-104-01 golden 1: version 1, an edit as version 2, the diff names the changed node, restore gives version 3 equal to version 1."""
        s = api.login("anna", "pw-anna")
        self.assertEqual(api.save(s, "workflows", "lookup", GRAPH), {"version": 1})
        self.assertEqual(api.save(s, "workflows", "lookup", edited("tighter")), {"version": 2})
        self.assertEqual(api.diff(s, "workflows", "lookup", 1, 2)["nodes_changed"], ["check"])
        self.assertEqual(api.restore(s, "workflows", "lookup", 1), {"version": 3})
        self.assertEqual(api.read(s, "workflows", "lookup")["doc"], GRAPH)
        self.assertEqual(api.read(s, "workflows", "lookup", version=2)["doc"], edited("tighter"))
        self.assertEqual([h["version"] for h in api.history(s, "workflows", "lookup")], [1, 2, 3])
        self.assertEqual(api.list_ids(s, "workflows"), ["lookup"])

    @mark.req("IF-104", "REQ-GA-007")
    @each_provider(IF)
    def test_the_author_is_the_session_account(self, api):
        """TC-IF-104-02: the graph app has no login of its own; the version records the account of the backend session."""
        anna, ben = api.login("anna", "pw-anna"), api.login("ben", "pw-ben")
        api.save(anna, "context_graphs", "chat", GRAPH)
        api.save(ben, "context_graphs", "chat", edited("x"))
        self.assertEqual([h["author"] for h in api.history(anna, "context_graphs", "chat")], ["anna", "ben"])

    @mark.req("IF-104", "REQ-GA-007")
    @each_provider(IF)
    def test_no_session_no_access(self, api):
        """TC-IF-104-03 golden 3: wrong credentials and a made-up token are 401 and change nothing."""
        self.assertEqual(error_of(lambda: api.login("anna", "wrong")).status, 401)
        for call in (lambda: api.list_ids("made-up", "workflows"), lambda: api.save("made-up", "workflows", "w", GRAPH),
                     lambda: api.read("made-up", "workflows", "w")):
            err = error_of(call)
            self.assertEqual((err.status, err.code), (401, "unauthenticated"))
        s = api.login("anna", "pw-anna")
        self.assertEqual(api.list_ids(s, "workflows"), [])

    @mark.req("IF-104", "REQ-BE-076", "REQ-GA-003")
    @each_provider(IF)
    def test_an_invalid_graph_is_refused_with_the_rule(self, api):
        """TC-IF-104-04 golden 2: a cycle is 422 with the rule; no id and no version appear."""
        s = api.login("anna", "pw-anna")
        cyc = {"nodes": [{"id": "a", "kind": "process"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}, {"from": "b", "to": "a"}]}
        err = error_of(lambda: api.save(s, "workflows", "bad", cyc))
        self.assertEqual((err.status, err.code, err.rule), (422, "invalid", "cycle"))
        adj = {"nodes": [{"id": "a", "kind": "data"}, {"id": "b", "kind": "data"}], "edges": [{"from": "a", "to": "b"}]}
        self.assertEqual(error_of(lambda: api.save(s, "workflows", "bad", adj)).rule, "adjacent_data_nodes")
        session = {"nodes": [{"id": "debate", "kind": "process", "session": True}], "edges": []}
        self.assertEqual(error_of(lambda: api.save(s, "workflows", "bad", session)).rule, "session_stopping_criterion")
        self.assertEqual(api.list_ids(s, "workflows"), [])

    @mark.req("IF-104")
    @each_provider(IF)
    def test_not_found_and_conflict(self, api):
        """TC-IF-104-05 golden 3: unknown id and kind are 404; a stale expected_version is 409 with the current version."""
        s = api.login("anna", "pw-anna")
        self.assertEqual(error_of(lambda: api.read(s, "workflows", "none")).status, 404)
        self.assertEqual(error_of(lambda: api.list_ids(s, "nonsense")).status, 404)
        api.save(s, "workflows", "w", GRAPH)
        api.save(s, "workflows", "w", edited("b"))
        err = error_of(lambda: api.save(s, "workflows", "w", edited("c"), expected_version=1))
        self.assertEqual((err.status, err.code, err.detail), (409, "conflict", {"current": 2}))


if __name__ == "__main__":
    unittest.main()
