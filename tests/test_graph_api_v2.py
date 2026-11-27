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


def sent(graph):
    return {"description": graph["description"], "nodes": graph["nodes"], "edges": graph["edges"]}


def small(graph_id):
    return {"id": graph_id, "context_graph_id": "ctx", "testbench_id": "tb", "description": "small",
            "nodes": [{"id": "var.in", "data": {"type": "data", "value": "x"}}, {"id": "step.a", "data": {"type": "transform", "toolbox_id": "tool.a"}}],
            "edges": [{"id": "e1", "from": "var.in", "to": "step.a", "data": {}}]}


class Stored(unittest.TestCase):
    """g.one (var.in -> step.a) stored once by anna, and anna logged in on the provider"""

    def setUp(self):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root, True)
        self.accounts_store = Storage(FileBackend(os.path.join(root, "accounts")))
        accounts.create(self.accounts_store, "anna", "pw-anna-x", "test")
        self.backend = FileBackend(os.path.join(root, "graphs"))
        graph_model.GraphModel(Storage(self.backend), author="anna").save_graph(small("g.one"))
        self.web = graph_api_v2.create_app(self.backend, self.accounts_store, "files", (ORIGIN,)).test_client()
        self.web.post("/api/login", json={"user": "anna", "password": "pw-anna-x"}, headers={"Origin": ORIGIN})

    def save(self, payload, graph_id="g.one"):
        answer = self.web.put("/api/v2/graphs/" + graph_id, json=payload, headers={"Origin": ORIGIN})
        return answer.status_code, answer.get_json()

    def stored_versions(self):
        return len(Storage(self.backend).history("graphs", "g.one"))

    def records(self):
        return Storage(self.backend).ids("graph_changes")


class Reading(Stored):
    """the read routes of T-03 beyond the contract cases: bad versions, unknown graphs, duplicate steps, context graphs"""

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



class Saving(Stored):
    """the save route of T-04: a new version with its derived record, nothing written for an unchanged graph or a refusal"""

    @mark.req("REQ-API-032", "REQ-API-037")
    def test_a_changed_step_is_a_new_version_with_a_derived_record(self):
        """Example: step.a tool.a -> tool.b at version 1 -> version 2 by anna; record g.one/2 derived from 1 with one change_step."""
        # Given g.one at version 1, its step.a changed to tool.b
        graph = small("g.one")
        graph["nodes"][1]["data"]["toolbox_id"] = "tool.b"
        # When anna saves it on version 1
        status, answer = self.save({"graph": sent(graph), "expected_version": 1})
        # Then version 2 is written by anna
        self.assertEqual((status, answer), (200, {"version": 2, "changed": True, "logged": True, "entries": 1}))
        self.assertEqual(Storage(self.backend).get("graphs", "g.one")["author"], "anna")
        # And its record of changes is derived from version 1
        record = Storage(self.backend).get("graph_changes", "g.one/2")
        self.assertEqual((record["author"], record["version"]), ("anna", 1))
        doc = record["doc"]
        self.assertEqual((doc["graph"], doc["version"], doc["from_version"], doc["kind"]), ("g.one", 2, 1, "derived"))
        self.assertEqual(doc["entries"], [{"n": 1, "op": "change_step", "target": "step.a", "before": {"type": "transform", "toolbox_id": "tool.a"},
                                           "after": {"type": "transform", "toolbox_id": "tool.b"}, "reason": None}])

    @mark.req("REQ-API-033")
    def test_an_unchanged_graph_writes_nothing(self):
        """Example: g.one sent as stored, its steps in another order -> version 1, changed false, logged null; no record."""
        # Given g.one as stored, its steps sent in the other order
        graph = small("g.one")
        graph["nodes"].reverse()
        # When anna saves it
        status, answer = self.save({"graph": sent(graph)})
        # Then nothing is written
        self.assertEqual((status, answer), (200, {"version": 1, "changed": False, "logged": None, "entries": 0}))
        self.assertEqual((self.stored_versions(), self.records()), (1, []))

    @mark.req("REQ-API-032")
    def test_a_new_description_is_a_version_without_entries(self):
        """Example: only the description changed -> version 2, entries 0; the header keeps context_graph_id ctx."""
        # Given g.one with a new description
        graph = small("g.one")
        graph["description"] = "another text"
        # When anna saves it
        status, answer = self.save({"graph": sent(graph)})
        # Then it is version 2 with no entries, and the stored header is kept
        self.assertEqual((status, answer), (200, {"version": 2, "changed": True, "logged": True, "entries": 0}))
        stored = graph_model.GraphModel(Storage(self.backend)).read_graph("g.one")
        self.assertEqual((stored["description"], stored["context_graph_id"], stored["testbench_id"]), ("another text", "ctx", "tb"))

    @mark.req("REQ-API-037")
    def test_entries_follow_the_order_of_the_record(self):
        """Example: e1 rewired, var.in removed with its connection, var.new added -> remove_step, add_step, add_connection; no separate remove_connection."""
        # Given g.one before, and after: var.in gone (and e1 with it), var.new added and connected by e2
        before = small("g.one")
        after = {**before, "nodes": [before["nodes"][1], {"id": "var.new", "data": {"type": "data"}}],
                 "edges": [{"id": "e2", "from": "var.new", "to": "step.a", "data": {}}]}
        # When the entries are derived
        entries = graph_api_v2.derive(before, after)
        # Then the step removal carries its connection, then the addition, then the new connection
        self.assertEqual([(e["op"], e["target"]) for e in entries], [("remove_step", "var.in"), ("add_step", "var.new"), ("add_connection", "e2")])
        self.assertEqual(entries[0]["connections"], [{"id": "e1", "from": "var.in", "to": "step.a", "data": {}}])

    @mark.req("REQ-API-034")
    def test_a_stale_version_is_a_conflict(self):
        """Example: expected_version 7 at version 1 -> 409 conflict, current 1; nothing written."""
        # Given a changed g.one
        graph = small("g.one")
        graph["nodes"][1]["data"]["toolbox_id"] = "tool.b"
        # When it is saved with a version that is not the current one
        status, answer = self.save({"graph": sent(graph), "expected_version": 7})
        # Then it is a conflict naming the current version
        self.assertEqual((status, answer), (409, {"error": "conflict", "current": 1}))
        self.assertEqual(self.stored_versions(), 1)

    @mark.req("REQ-API-035")
    def test_a_broken_rule_is_refused_with_the_report(self):
        """Example: a connection step.a -> var.in closes a cycle -> 422 rules_broken whose last item is cycle; a step that is no object too."""
        # Given a graph with a cycle, and a graph whose step is a text
        cyclic = small("g.one")
        cyclic["edges"].append({"id": "e9", "from": "step.a", "to": "var.in", "data": {}})
        odd = {"nodes": ["x"], "edges": []}
        # When both are saved
        answers = [self.save({"graph": g}) for g in (sent(cyclic), odd)]
        # Then both are refused with the rule report, and nothing is written
        self.assertEqual([(s, a["error"]) for s, a in answers], [(422, "rules_broken")] * 2)
        self.assertEqual(answers[0][1]["rules"][-1]["rule"], "cycle")
        self.assertEqual((self.stored_versions(), self.records()), (1, []))

    @mark.req("REQ-API-036")
    def test_a_record_check_refusal_names_rule_and_detail(self):
        """Example: step.a with the extra field colour -> 422 refused, rule schema_break, detail colour; nothing written."""
        # Given step.a with a field the record check does not know
        graph = small("g.one")
        graph["nodes"][1]["data"]["colour"] = "red"
        # When it is saved
        status, answer = self.save({"graph": sent(graph)})
        # Then the record check refuses it
        self.assertEqual((status, answer), (422, {"error": "refused", "rule": "schema_break", "detail": "colour"}))
        self.assertEqual((self.stored_versions(), self.records()), (1, []))

    @mark.req("REQ-API-048", "REQ-API-049")
    def test_a_malformed_body_or_unknown_graph_is_refused(self):
        """Example: nodes a text, no graph, a body that is a list -> 422 invalid detail graph; g.none -> 404 not_found."""
        # Given three malformed bodies and an unknown graph
        bodies = [{"graph": {"nodes": "x", "edges": []}}, {"nodes": [], "edges": []}, ["x"]]
        # When each is saved
        answers = [self.save(b) for b in bodies] + [self.save({"graph": sent(small("g.none"))}, "g.none")]
        # Then the malformed ones name the graph and the unknown one is not found
        self.assertEqual(answers, [(422, {"error": "invalid", "detail": "graph"})] * 3 + [(404, {"error": "not_found"})])
        self.assertEqual(self.stored_versions(), 1)

    @mark.req("REQ-API-048")
    def test_a_connection_id_of_the_wrong_form_is_invalid_on_save_and_check(self):
        """Example (V-5): a connection without id, a connection id that is an object -> save and check both 422 invalid detail graph;
        still one version, no record. (A step that is no object stays a rule report, see test_a_broken_rule_is_refused_with_the_report.)"""
        # Given two graphs whose connection ids have the wrong form
        def broken(change):
            graph = small("g.one")
            change(graph)
            return {"graph": sent(graph)}
        bodies = [broken(lambda g: g["edges"][0].pop("id")), broken(lambda g: g["edges"][0].update(id={"x": 1}))]
        # When each is saved and checked
        saved = [self.save(b) for b in bodies]
        checked = [self.web.post("/api/v2/graphs/g.one/check", json=b, headers={"Origin": ORIGIN}) for b in bodies]
        # Then every one is refused as invalid and nothing is written
        self.assertEqual(saved, [(422, {"error": "invalid", "detail": "graph"})] * 2)
        self.assertEqual([(a.status_code, a.get_json()) for a in checked], [(422, {"error": "invalid", "detail": "graph"})] * 2)
        self.assertEqual((self.stored_versions(), self.records()), (1, []))



class CheckRestoreArrange(Stored):
    """the check, restore and arrangement routes of T-05 beyond the contract cases"""

    def post(self, path, payload):
        answer = self.web.post("/api/v2/graphs/g.one" + path, json=payload, headers={"Origin": ORIGIN})
        return answer.status_code, answer.get_json()

    def arrange(self, payload):
        answer = self.web.put("/api/v2/graphs/g.one/arrangement", json=payload, headers={"Origin": ORIGIN})
        return answer.status_code, answer.get_json()

    def tool_b(self):
        graph = small("g.one")
        graph["nodes"][1]["data"]["toolbox_id"] = "tool.b"
        self.assertEqual(self.save({"graph": sent(graph)})[0], 200)

    @mark.req("REQ-API-031", "REQ-API-048")
    def test_check_answers_the_report_and_stores_nothing(self):
        """Example: a cycle step.a -> var.in -> rules ending in cycle; a malformed body 422 invalid graph; still one version."""
        # Given g.one with a cycle in the working copy
        cyclic = small("g.one")
        cyclic["edges"].append({"id": "e9", "from": "step.a", "to": "var.in", "data": {}})
        # When it and a malformed body are checked
        report, bad = self.post("/check", {"graph": sent(cyclic)}), self.post("/check", {"graph": {"nodes": []}})
        # Then the report ends in the cycle, the malformed body is refused, nothing is stored
        self.assertEqual((report[0], report[1]["rules"][-1]["rule"]), (200, "cycle"))
        self.assertEqual(bad, (422, {"error": "invalid", "detail": "graph"}))
        self.assertEqual((self.stored_versions(), self.records()), (1, []))

    @mark.req("REQ-API-041")
    def test_a_restore_is_a_new_version_with_one_restore_entry(self):
        """Example: version 1 restored at 2 with reason " back " -> version 3 with tool.a; record g.one/3 restore from 2, reason trimmed."""
        # Given g.one at version 2 (step.a uses tool.b)
        self.tool_b()
        # When version 1 is restored with a reason
        status, answer = self.post("/restore", {"version": 1, "reason": " back "})
        # Then version 3 has the content of version 1
        self.assertEqual((status, answer), (200, {"version": 3, "restored": 1, "changed": True}))
        stored = graph_model.GraphModel(Storage(self.backend)).read_graph("g.one")
        self.assertEqual(stored["nodes"][1]["data"]["toolbox_id"], "tool.a")
        # And its record names the restore, from version 2
        doc = Storage(self.backend).get("graph_changes", "g.one/3")["doc"]
        self.assertEqual((doc["kind"], doc["from_version"], doc["entries"]),
                         ("restore", 2, [{"n": 1, "op": "restore", "target": 1, "before": None, "after": None, "reason": "back"}]))

    @mark.req("REQ-API-041", "REQ-API-049")
    def test_a_restore_of_the_current_content_or_a_missing_version(self):
        """Example: restoring version 1 at version 1 -> changed false, nothing written; versions 0, 9, "1" and none -> 404 not_found version."""
        # Given g.one at version 1
        # When its own version and versions that are not stored are restored
        same = self.post("/restore", {"version": 1})
        missing = [self.post("/restore", body) for body in ({"version": 0}, {"version": 9}, {"version": "1"}, {})]
        # Then the first changes nothing and the others are not found
        self.assertEqual(same, (200, {"version": 1, "restored": 1, "changed": False}))
        self.assertEqual(missing, [(404, {"error": "not_found", "detail": "version"})] * 4)
        self.assertEqual((self.stored_versions(), self.records()), (1, []))

    @mark.req("REQ-API-044", "REQ-API-048")
    def test_the_arrangement_is_kept_rounded_and_replaced(self):
        """Example: var.in 10.4, -3 and step.a 2.6, 0 -> saved 2, version 1; a second save with only step.a replaces the record (version 2)."""
        # Given g.one never arranged
        # When the owner saves two places, then one place
        first, second = self.arrange({"positions": {"var.in": {"x": 10.4, "y": -3}, "step.a": {"x": 2.6, "y": 0}}}), self.arrange({"positions": {"step.a": {"x": 1, "y": 1}}})
        # Then both are saved, the second as the whole new arrangement
        self.assertEqual((first, second), ((200, {"version": 1, "saved": 2}), (200, {"version": 2, "saved": 1})))
        read = self.web.get("/api/v2/graphs/g.one/arrangement").get_json()
        self.assertEqual((read["positions"], read["version"], read["author"]), ({"step.a": {"x": 1, "y": 1}}, 2, "anna"))

    @mark.req("REQ-API-048")
    def test_a_malformed_arrangement_is_refused(self):
        """Example: positions a list -> detail positions; var.in with y true, x infinite, or a text -> detail var.in; nothing stored."""
        # Given malformed arrangement bodies
        bodies = [{"positions": []}, {}, {"positions": {"var.in": {"x": 1, "y": True}}}, {"positions": {"var.in": {"x": float("inf"), "y": 0}}},
                  {"positions": {"var.in": "far"}}]
        # When each is saved
        answers = [self.arrange(b) for b in bodies[:3] + bodies[4:]]
        # Then each names what is wrong, and no arrangement is stored
        self.assertEqual(answers, [(422, {"error": "invalid", "detail": d}) for d in ("positions", "positions", "var.in", "var.in")])
        self.assertEqual(self.web.get("/api/v2/graphs/g.one/arrangement").get_json(), {"positions": None})
        # And an infinite number is refused by the place check itself (JSON cannot carry it)
        self.assertFalse(graph_api_v2.a_place({"x": float("inf"), "y": 0}))



class RecordFails:
    """the backend, except that a write to graph_changes raises, as a lost connection does"""

    def __init__(self, backend):
        self.backend = backend

    def append(self, table, record_id, entry):
        if table == "graph_changes":
            raise OSError("down")
        return self.backend.append(table, record_id, entry)

    def __getattr__(self, name):
        return getattr(self.backend, name)


class RecordOfChanges(Stored):
    """the record of changes of T-06: editor entries, written once, a lost record, the changes route"""

    def changes(self):
        return self.web.get("/api/v2/graphs/g.one/changes").get_json()

    def with_note(self):
        graph = small("g.one")
        graph["nodes"].append({"id": "var.note", "data": {"type": "data", "value": 1}})
        return graph

    @mark.req("REQ-API-038")
    def test_matching_editor_entries_are_kept_as_editor(self):
        """Example: add_step var.note with reason " a note " -> version 2, record editor, entry n 1, reason trimmed, extra keys dropped."""
        # Given g.one plus var.note, and the editor's entry for it
        entry = {"op": "add_step", "target": "var.note", "before": None, "after": {"type": "data", "value": 1}, "reason": " a note ", "extra": 1}
        # When anna saves with that entry
        status, answer = self.save({"graph": sent(self.with_note()), "changes": [entry]})
        # Then the entry is kept as the editor's
        self.assertEqual((status, answer), (200, {"version": 2, "changed": True, "logged": True, "entries": 1}))
        doc = Storage(self.backend).get("graph_changes", "g.one/2")["doc"]
        self.assertEqual((doc["kind"], doc["entries"]), ("editor", [{"n": 1, "op": "add_step", "target": "var.note", "before": None,
                                                                    "after": {"type": "data", "value": 1}, "reason": "a note"}]))

    @mark.req("REQ-API-051")
    def test_entries_that_do_not_give_the_graph_are_refused(self):
        """Example: an entry with another value, a restore entry, an unknown step removed, a text instead of a list -> 422 changes_do_not_match."""
        # Given g.one plus var.note and entry lists that do not give it
        wrong = [[{"op": "add_step", "target": "var.note", "after": {"type": "data", "value": 2}}],
                 [{"op": "restore", "target": 1}], [{"op": "remove_step", "target": "var.gone"}], "add var.note", [None]]
        # When anna saves with each
        answers = [self.save({"graph": sent(self.with_note()), "changes": c}) for c in wrong]
        # Then each is refused and nothing is written
        self.assertEqual(answers, [(422, {"error": "changes_do_not_match"})] * 5)
        self.assertEqual((self.stored_versions(), self.records()), (1, []))

    @mark.req("REQ-API-038", "REQ-API-051")
    def test_an_entry_whose_before_is_not_the_stored_value_is_refused(self):
        """Example (V-4): change_step step.a with before tool.x and the right after tool.b -> 422 changes_do_not_match, still one version;
        the same entry with before tool.a -> version 2."""
        # Given g.one with step.a on tool.b, and an entry whose before is false
        graph = small("g.one")
        graph["nodes"][1]["data"]["toolbox_id"] = "tool.b"
        entry = lambda tool: {"op": "change_step", "target": "step.a", "before": {"type": "transform", "toolbox_id": tool},      # noqa: E731
                              "after": {"type": "transform", "toolbox_id": "tool.b"}}
        # When anna saves with the false before, then with the true one
        wrong = self.save({"graph": sent(graph), "changes": [entry("tool.x")]})
        versions_after_wrong = self.stored_versions()
        right = self.save({"graph": sent(graph), "changes": [entry("tool.a")]})
        # Then the false one is refused and writes nothing; the true one is kept
        self.assertEqual((wrong, versions_after_wrong), ((422, {"error": "changes_do_not_match"}), 1))
        self.assertEqual(right[0], 200)

    @mark.req("REQ-API-039")
    def test_a_record_that_exists_is_not_written_again(self):
        """Example: a record g.one/2 already there -> the save of version 2 keeps it, logged false."""
        # Given a record g.one/2 written before the version (as after a move)
        Storage(self.backend).put("graph_changes", "g.one/2", {"graph": "g.one", "version": 2, "from_version": 1, "kind": "editor", "entries": []}, "anna")
        # When anna saves version 2
        status, answer = self.save({"graph": sent(self.with_note())})
        # Then the version is kept, the record not written again
        self.assertEqual((status, answer), (200, {"version": 2, "changed": True, "logged": False, "entries": 1}))
        self.assertEqual(len(Storage(self.backend).history("graph_changes", "g.one/2")), 1)

    @mark.req("REQ-API-040", "REQ-API-042")
    def test_a_lost_record_keeps_the_version(self):
        """Example: graph_changes failing -> version 2 with logged false; the changes route lists 1 and 2 before_the_record."""
        # Given the provider on a backend whose record writes fail
        self.web = graph_api_v2.create_app(RecordFails(self.backend), self.accounts_store, "files", (ORIGIN,)).test_client()
        self.web.post("/api/login", json={"user": "anna", "password": "pw-anna-x"}, headers={"Origin": ORIGIN})
        # When anna saves a changed graph
        status, answer = self.save({"graph": sent(self.with_note())})
        # Then the version is kept without its record
        self.assertEqual((status, answer), (200, {"version": 2, "changed": True, "logged": False, "entries": 1}))
        self.assertEqual([(i["version"], i["kind"], i["entries"]) for i in self.changes()], [(1, "before_the_record", []), (2, "before_the_record", [])])

    @mark.req("REQ-API-042")
    def test_the_changes_route_lists_every_version(self):
        """Example: a save and a restore -> before_the_record 1, derived 2 from 1, restore 3 from 2; authors and times of the versions."""
        # Given g.one saved once more and then restored to version 1
        self.save({"graph": sent(self.with_note())})
        self.web.post("/api/v2/graphs/g.one/restore", json={"version": 1}, headers={"Origin": ORIGIN})
        # When the changes are asked for
        items = self.changes()
        # Then each version has its item, oldest first, with the version's author and time
        self.assertEqual([(i["version"], i["kind"], i.get("from_version")) for i in items], [(1, "before_the_record", None), (2, "derived", 1), (3, "restore", 2)])
        times = [v["time"] for v in Storage(self.backend).history("graphs", "g.one")]
        self.assertEqual([(i["author"], i["time"]) for i in items], [("anna", t) for t in times])
        self.assertNotIn("from_version", items[0])
        self.assertEqual(self.web.get("/api/v2/graphs/g.none/changes").status_code, 404)


if __name__ == "__main__":
    unittest.main()
