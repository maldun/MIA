"""
Acceptance tests of G-V4.VIEW Track A (N-2.1 API and accounts, N-4.2 operation): TC-API-018 to 025 and TC-OPR-011 of
specs/mia/goals/G-V4.VIEW/test-spec.md, under TR-VIEW-001, 003, 006, 007, 014, 018, 021.
TC-API-018 to 020 run MIA's real web_app from a copy of the checkout (tests/checkout_copy.py) with its own configuration, as production reads it
(TR-VIEW-007); TC-API-021 to 025 run the real provider graph_api_v2.create_app(backend, accounts_store, store, allowed_origins) (REQ-API-030)
over the Flask test client. Until Track A builds it, every case fails by assertion or names the missing module (red).
Run with: /home/maldun/prog/Python/venvs/mia312/bin/python tests/acceptance/test_view_backend.py
"""
import copy
import json
import os
import re
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TESTS = os.path.dirname(HERE)
REPO = os.path.dirname(TESTS)
sys.path[:0] = [REPO, os.path.join(TESTS, "helpers"), TESTS]

from markers import mark          # noqa: E402
import core_stores                # noqa: E402
import graph_view_data as data    # noqa: E402

ORIGIN = "http://localhost"
FOREIGN = "https://evil.example"


def tearDownModule():
    core_stores.stop_database()


# --- the real provider over HTTP ------------------------------------------------------------------------------------------------------

class Provider:
    """graph_api_v2.create_app on `backend`, accounts anna (first, the owner) and ben (TR-VIEW-003); one test client per login"""

    def __init__(self, test, backend, store="files"):
        try:
            import graph_api_v2
        except ImportError as err:
            test.fail("the real provider graph_api_v2.create_app (N-2.1, Track A of G-V4.VIEW) is not built yet: %s" % err)
        import accounts
        from storage import Storage
        self.backend = backend
        self.accounts_store = Storage(core_stores.fresh_backend("files", test))
        for name in ("anna", "ben"):
            accounts.create(self.accounts_store, name, "pw-" + name, "view-tests")
        self.app = graph_api_v2.create_app(backend, self.accounts_store, store, allowed_origins=(ORIGIN,))

    def login(self, user):
        client = self.app.test_client()
        answer = client.post("/api/login", json={"user": user, "password": "pw-" + user}, headers={"Origin": ORIGIN})
        assert answer.status_code == 200, (user, answer.status_code)
        return client


def call(client, method, path, body=None, origin=ORIGIN):
    """(status, JSON body) of one request"""
    answer = client.open(path, method=method, json=body, headers={"Origin": origin} if origin else {})
    return answer.status_code, answer.get_json(silent=True)


def body_of(graph):
    return {"description": graph.get("description"), "nodes": copy.deepcopy(graph["nodes"]), "edges": copy.deepcopy(graph["edges"])}


def graph_versions(backend, graph_id):
    return len(backend.versions("graphs", graph_id))


def change_records(backend):
    return {i: len(backend.versions("graph_changes", i)) for i in backend.ids("graph_changes")}


def append_raw_version(backend, graph, author):
    """one more version of `graph`, written around the checks as raw records: a member gets a new version only when its content changed"""
    gid = graph["id"]
    members = []
    for table, items in (("graph_nodes", graph["nodes"]), ("graph_edges", graph["edges"])):
        refs = []
        for item in items:
            rid = "%s/%s" % (gid, item["id"])
            doc = {"id": rid, "data": item["data"]} if table == "graph_nodes" else \
                {"id": rid, "from": "%s/%s" % (gid, item["from"]), "to": "%s/%s" % (gid, item["to"]), "data": item["data"]}
            old = backend.versions(table, rid)
            if not old or old[-1]["doc"] != doc:
                backend.append(table, rid, {"id": rid, "version": len(old) + 1, "author": author, "time": "2026-11-22T12:00:00Z", "doc": doc})
            refs.append({"id": rid, "version": len(backend.versions(table, rid))})
        members.append(refs)
    head = backend.versions("graphs", gid)
    backend.append("graphs", gid, {"id": gid, "version": len(head) + 1, "author": author, "time": "2026-11-22T12:00:00Z",
                                   "doc": {"id": gid, "data": {"kind": "workflow", "context_graph_id": graph["context_graph_id"], "testbench_id": graph["testbench_id"],
                                                               "description": graph["description"], "nodes": members[0], "edges": members[1]}}})
    return len(head) + 1


def with_colour(graph):
    """step.write with the extra field `colour`: every graph rule kept, refused by the record check (schema_break, D-444)"""
    g = copy.deepcopy(graph)
    g["nodes"][1]["data"]["colour"] = "red"
    return g


class GraphChangesFail:
    """the backend, except that every write to `graph_changes` raises (TR-VIEW-006); `fired` counts the raised writes"""

    def __init__(self, backend):
        self.backend, self.fired = backend, 0

    def append(self, table, record_id, entry):
        if table == "graph_changes":
            self.fired += 1
            raise OSError("graph_changes write fails (TC-API-023)")
        return self.backend.append(table, record_id, entry)

    def __getattr__(self, name):
        return getattr(self.backend, name)


# --- MIA's web application from a copy of the checkout --------------------------------------------------------------------------------

def checkout_with(settings, drop=("store",)):
    """a copy of the checkout (tests/checkout_copy.py) whose configuration has `settings` over the example and none of the keys in `drop`
    unless `settings` names them; returns the folder holding MIA/"""
    import checkout_copy
    folder = checkout_copy.make(settings)
    path = os.path.join(folder, "MIA", "setup_cfg.json")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    for key in drop:
        if key not in settings:
            cfg.pop(key, None)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f)
    return folder


def data_folder(folder):
    """the folder of the file store MIA uses today: `accounts_dir` of the configuration, default data/db (web_app.py)"""
    with open(os.path.join(folder, "MIA", "setup_cfg.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    return os.path.join(folder, "MIA", cfg.get("accounts_dir", "data/db"))


class WebAppProbe:
    """imports MIA.web_app of `folder` in a separate process (so module state of other tests cannot leak in) and runs `script` there;
    the script sees `wa` (the web_app module) and prints one JSON line"""

    @staticmethod
    def run(folder, script, env=None):
        prelude = ("import json, os, sys\nsys.path[:0] = [%r, %r]\nos.environ.setdefault('MIA_TEST', '1')\nfrom MIA import web_app as wa\nfrom MIA import accounts\n"
                   % (folder, os.path.join(folder, "MIA")))
        environment = {k: v for k, v in os.environ.items() if k != "MIA_DATABASE_URL"}      # only what the check gives (TR-VIEW-007)
        environment.update(env or {})
        done = subprocess.run([sys.executable, "-c", prelude + script], cwd=folder, env=environment, capture_output=True, text=True, timeout=180)
        return done


LOGIN_AND_ASK = """
accounts.create(wa._account_store, "anna", "pw-anna-1", "setup")
web = wa.app.test_client()
login = web.post("/api/login", json={"user": "anna", "password": "pw-anna-1"})
out = {"login": login.status_code}
for path in PATHS:
    answer = web.get(path)
    out[path] = [answer.status_code, answer.get_json(silent=True)]
print(json.dumps(out))
"""


class StoreSetting(unittest.TestCase):

    @mark.req("REQ-API-019")
    def test_TC_API_018_without_a_store_setting_the_data_folder_is_read(self):
        """TC-API-018: with no store setting the v2 routes read the graphs written to the data folder MIA uses today.
        Example: cp2.multi written with four versions into data/db -> listed at version 4; the store route says files."""
        # Given a configuration with no store setting, cp2.multi stored into the data folder through CORE's GraphModel
        folder = checkout_with({"accounts_enabled": True})
        from storage_files import FileBackend
        os.makedirs(data_folder(folder), exist_ok=True)
        data.seed(FileBackend(data_folder(folder)), ids={"cp2.multi"})
        # When anna lists the graphs, reads cp2.multi and asks for the store through IF-104 v2
        done = WebAppProbe.run(folder, "PATHS = ['/api/v2/graphs', '/api/v2/graphs/cp2.multi', '/api/v2/store']\n" + LOGIN_AND_ASK)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        out = json.loads(done.stdout.strip().splitlines()[-1])
        # Then the list holds cp2.multi at version 4 and the read gives version 4
        status, listed = out["/api/v2/graphs"]
        self.assertEqual(status, 200, listed)
        self.assertEqual([(g["id"], g["version"]) for g in listed if g["id"] == "cp2.multi"], [("cp2.multi", 4)])
        self.assertEqual(out["/api/v2/graphs/cp2.multi"][1]["version"], 4)
        # And the store route answers files
        self.assertEqual(out["/api/v2/store"][1]["store"], "files")

    @mark.req("REQ-API-020")
    def test_TC_API_019_an_unknown_store_setting_stops_the_start(self):
        """TC-API-019: a store setting that is neither files nor database stops the start and names `store` and the value.
        Example: store: postgress -> the start fails with a message naming store and postgress."""
        for value, shown in (("postgress", ("postgress",)), ("", ('""', "''", "empty")), (5, ("5",))):
            with self.subTest(value=value):
                # Given a configuration whose store setting is the wrong value
                folder = checkout_with({"accounts_enabled": True, "store": value})
                # When the web application is started (imported)
                done = WebAppProbe.run(folder, "print('started')")
                # Then the start is refused
                self.assertNotEqual(done.returncode, 0, "the start was not refused for store=%r" % (value,))
                # And the message names the setting and its value
                message = done.stderr
                self.assertIn("store", message)
                self.assertTrue(any(s in message for s in shown), message[-500:])

    @mark.req("REQ-API-030")
    def test_TC_API_020_the_v2_routes_live_in_the_web_application(self):
        """TC-API-020: MIA's web application serves IF-104 v2 under its own session, beside the v1 routes.
        Example: anna logs in once; /api/v2/me -> anna, owner; /api/v2/graphs lists cp2.multi; /api/workflows answers 200."""
        # Given MIA's web application with accounts on and a files store holding cp2.multi
        folder = checkout_with({"accounts_enabled": True, "store": "files"})
        from storage_files import FileBackend
        os.makedirs(data_folder(folder), exist_ok=True)
        data.seed(FileBackend(data_folder(folder)), ids={"cp2.multi"})
        # When anna logs in through /api/login and calls v2 and v1 routes with that one session
        done = WebAppProbe.run(folder, "PATHS = ['/api/v2/me', '/api/v2/graphs', '/api/workflows']\n" + LOGIN_AND_ASK)
        self.assertEqual(done.returncode, 0, done.stderr[-2000:])
        out = json.loads(done.stdout.strip().splitlines()[-1])
        # Then me answers anna as owner and the list holds cp2.multi
        self.assertEqual(out["login"], 200)
        self.assertEqual(out["/api/v2/me"], [200, {"user": "anna", "owner": True}])
        self.assertEqual(out["/api/v2/graphs"][0], 200, out["/api/v2/graphs"])
        self.assertIn("cp2.multi", [g["id"] for g in out["/api/v2/graphs"][1]])
        # And the v1 route answers as before
        self.assertEqual(out["/api/workflows"][0], 200)


class Writes(unittest.TestCase):

    def seeded(self, kind="files"):
        backend = core_stores.fresh_backend(kind, self)      # skips with the reason where PostgreSQL cannot run (TR-VIEW-001)
        data.seed(backend, ids={"cp2.multi"})
        return backend

    @mark.req("REQ-API-036")
    def test_TC_API_021_a_refused_record_check_writes_nothing(self):
        """TC-API-021: a save or restore the store's record check refuses is 422 refused naming the rule and detail; nothing is written (D-444).
        Example: step.write with the extra field colour -> 422 refused, schema_break, colour; still the same versions."""
        for kind in ("files", "postgres"):
            with self.subTest(store=kind):
                # Given cp2.multi at version 4, plus a raw version 5 with the extra field and a normal version 6 on top (for the restore)
                backend = self.seeded(kind)
                api = Provider(self, backend, "files" if kind == "files" else "database")
                anna = api.login("anna")
                status, saved = call(anna, "PUT", "/api/v2/graphs/cp2.multi", {"graph": body_of(with_colour(data.graph("cp2.multi")))})
                # Then the save is refused by the record check
                self.assertEqual((status, saved.get("error"), saved.get("rule"), saved.get("detail")), (422, "refused", "schema_break", "colour"), saved)
                self.assertEqual(graph_versions(backend, "cp2.multi"), 4)
                # When a version 5 with that content exists (written around the checks), a clean version 6 is kept, and 5 is restored
                self.assertEqual(append_raw_version(backend, with_colour(data.graph("cp2.multi")), "anna"), 5)
                clean = data.graph("cp2.multi")
                clean["nodes"][1]["data"]["toolbox_id"] = "t9"
                self.assertEqual(call(anna, "PUT", "/api/v2/graphs/cp2.multi", {"graph": body_of(clean)})[0], 200)
                before = change_records(backend)
                status, restored = call(anna, "POST", "/api/v2/graphs/cp2.multi/restore", {"version": 5})
                # Then the restore is refused the same way
                self.assertEqual((status, restored.get("error"), restored.get("rule"), restored.get("detail")), (422, "refused", "schema_break", "colour"), restored)
                # And no version and no record of changes was written
                self.assertEqual(graph_versions(backend, "cp2.multi"), 6)
                self.assertEqual(change_records(backend), before)

    @mark.req("REQ-API-039")
    def test_TC_API_022_a_record_of_changes_is_written_once(self):
        """TC-API-022: the record of changes of a version is written only when no record with its ID exists.
        Example: a record cp2.multi/5 already there (as after a move) -> the save of version 5 leaves it with one version and its entries."""
        # Given cp2.multi at 4 and a record cp2.multi/5 already in graph_changes (written around the checks)
        backend = self.seeded()
        first = {"graph": "cp2.multi", "version": 5, "from_version": 4, "kind": "editor",
                 "entries": [{"n": 1, "op": "change_step", "target": "step.write", "before": {"toolbox_id": "t4"}, "after": {"toolbox_id": "t7"}, "reason": "first"}]}
        backend.append("graph_changes", "cp2.multi/5", {"id": "cp2.multi/5", "version": 1, "author": "anna", "time": "2026-11-22T12:00:00Z", "doc": first})
        api = Provider(self, backend)
        anna = api.login("anna")
        changed = data.graph("cp2.multi")
        changed["nodes"][1]["data"]["toolbox_id"] = "t9"
        # When the owner saves version 5, which would write the record cp2.multi/5 again
        status, saved = call(anna, "PUT", "/api/v2/graphs/cp2.multi", {"graph": body_of(changed), "expected_version": 4})
        self.assertEqual((status, saved.get("version")), (200, 5), saved)
        # Then no second write was made: the record keeps one version
        kept = backend.versions("graph_changes", "cp2.multi/5")
        self.assertEqual(len(kept), 1)
        # And its entries are those of the first write
        self.assertEqual(kept[0]["doc"], first)

    @mark.req("REQ-API-040", "REQ-API-042")
    def test_TC_API_023_a_version_without_its_record(self):
        """TC-API-023: when the record cannot be written, the version is kept, logged is false, and the changes route lists it before_the_record.
        Example: graph_changes failing -> version 5, changed true, logged false; the fifth item of the changes route is before_the_record."""
        # Given cp2.multi at 4 on a backend whose graph_changes writes fail (TR-VIEW-006)
        failing = GraphChangesFail(self.seeded())
        api = Provider(self, failing)
        anna = api.login("anna")
        changed = data.graph("cp2.multi")
        changed["nodes"][1]["data"]["toolbox_id"] = "t9"
        # When the owner saves a changed graph
        status, saved = call(anna, "PUT", "/api/v2/graphs/cp2.multi", {"graph": body_of(changed)})
        # Then version 5 is kept with logged false, and the fault fired
        self.assertEqual(status, 200, saved)
        self.assertEqual((saved["version"], saved["changed"], saved["logged"]), (5, True, False))
        self.assertGreaterEqual(failing.fired, 1)
        self.assertEqual(graph_versions(failing.backend, "cp2.multi"), 5)
        # And the changes route lists five items, the last one version 5 made before the record
        status, items = call(anna, "GET", "/api/v2/graphs/cp2.multi/changes")
        self.assertEqual(status, 200, items)
        self.assertEqual([(i["version"], i["kind"]) for i in items][-1], (5, "before_the_record"))
        self.assertEqual(len(items), 5)

    @mark.req("REQ-API-047")
    def test_TC_API_024_a_foreign_origin_changes_nothing(self):
        """TC-API-024: every writing route of IF-104 v2 refuses a foreign Origin with 403 bad_origin, also without a session; nothing changes.
        Example: a save with Origin https://evil.example -> 403 bad_origin, still 4 versions."""
        # Given the real provider on files, allowed origin http://localhost, cp2.multi at 4, anna logged in
        backend = self.seeded()
        api = Provider(self, backend)
        anna = api.login("anna")
        graph = body_of(data.graph("cp2.multi"))
        calls = [("POST", "/api/v2/graphs/cp2.multi/check", {"graph": graph}), ("PUT", "/api/v2/graphs/cp2.multi", {"graph": graph}),
                 ("POST", "/api/v2/graphs/cp2.multi/restore", {"version": 1}), ("PUT", "/api/v2/graphs/cp2.multi/arrangement", {"positions": {"var.in": {"x": 1, "y": 1}}})]
        # When anna sends each with a foreign origin, and a save comes with that origin and no session
        answers = [call(anna, m, p, b, origin=FOREIGN) for m, p, b in calls]
        answers.append(call(api.app.test_client(), "PUT", "/api/v2/graphs/cp2.multi", {"graph": graph}, origin=FOREIGN))
        # Then each is 403 bad_origin (the origin is checked before the session)
        self.assertEqual([(s, (b or {}).get("error")) for s, b in answers], [(403, "bad_origin")] * 5)
        # And nothing changed
        self.assertEqual(graph_versions(backend, "cp2.multi"), 4)
        self.assertEqual(backend.ids("arrangements"), [])
        self.assertEqual(change_records(backend), {})

    @mark.req("REQ-API-031", "REQ-API-035", "HR-008")
    def test_TC_API_025_one_rule_report_on_check_save_and_restore(self):
        """TC-API-025: the check route, a refused save and a refused restore give the same items as IF-301 v4 rule_report (TR-VIEW-014: needs RULES).
        Example: cp2.multi plus a second e1 (as e3) and e9 var.out -> step.write -> duplicate_connection, then cycle; 0 differences."""
        try:
            import graph_rule_set
        except ImportError:
            self.fail("IF-301 v4 (graph_rule_set of G-V4.GRAPHAPI.RULES) is not merged into this branch yet (TR-VIEW-014)")
        # Given cp2.multi at 4; a working copy with a duplicate connection and a cycle; a raw version 5 with the same faults and a clean version 6
        backend = self.seeded()
        api = Provider(self, backend)
        anna = api.login("anna")
        broken = data.graph("cp2.multi")
        broken["edges"] += [{"id": "e3", "from": "var.in", "to": "step.write", "data": {}}, {"id": "e9", "from": "var.out", "to": "step.write", "data": {}}]
        expected = graph_rule_set.rule_report({"kind": "workflow", "nodes": broken["nodes"], "edges": broken["edges"]})
        self.assertEqual([i["rule"] for i in expected], ["duplicate_connection", "cycle"])
        # When the copy is checked and saved
        status, checked = call(anna, "POST", "/api/v2/graphs/cp2.multi/check", {"graph": body_of(broken)})
        self.assertEqual(status, 200, checked)
        status, saved = call(anna, "PUT", "/api/v2/graphs/cp2.multi", {"graph": body_of(broken)})
        self.assertEqual((status, saved.get("error")), (422, "rules_broken"), saved)
        # And a stored version 5 with the same faults is restored on top of a clean version 6
        self.assertEqual(append_raw_version(backend, broken, "anna"), 5)
        clean = data.graph("cp2.multi")
        clean["nodes"][1]["data"]["toolbox_id"] = "t9"
        self.assertEqual(call(anna, "PUT", "/api/v2/graphs/cp2.multi", {"graph": body_of(clean)})[0], 200)
        status, restored = call(anna, "POST", "/api/v2/graphs/cp2.multi/restore", {"version": 5})
        self.assertEqual((status, restored.get("error")), (422, "rules_broken"), restored)
        # Then all three give the items of rule_report, in the same order (0 differences)
        self.assertEqual(checked["rules"], expected)
        self.assertEqual(saved["rules"], expected)
        self.assertEqual(restored["rules"], expected)
        # And nothing was written by the refusals
        self.assertEqual(graph_versions(backend, "cp2.multi"), 6)


class ReleaseImage(unittest.TestCase):

    @mark.req("REQ-OPR-011")
    def test_TC_OPR_011_the_image_installs_the_database_driver(self):
        """TC-OPR-011: the stage of deploy/Containerfile that makes the release image installs requirements-db.txt after copying it in.
        Example: `COPY requirements-db.txt ...` then `RUN pip install ... -r requirements-db.txt` in the last stage."""
        # Given deploy/Containerfile and requirements-db.txt as committed
        with open(os.path.join(REPO, "deploy", "Containerfile"), encoding="utf-8") as f:
            text = f.read()
        self.assertTrue(os.path.exists(os.path.join(REPO, "requirements-db.txt")))
        # When the stage that makes the release image (the last FROM) is read
        stage = re.split(r"(?im)^FROM\s", text)[-1]
        lines = [l.strip() for l in re.sub(r"\\\n", " ", stage).splitlines()]
        copied = [i for i, l in enumerate(lines) if re.match(r"(?i)(COPY|ADD)\s", l) and ("requirements-db.txt" in l or re.search(r"\s\.\s+\S+$|\s\.\s*$", l))]
        installed = [i for i, l in enumerate(lines) if re.match(r"(?i)RUN\s", l) and re.search(r"pip3?\s+install\b.*-r\s+\S*requirements-db\.txt", l)]
        # Then it installs requirements-db.txt with pip, after the file is copied in
        self.assertTrue(installed, "no `pip install -r requirements-db.txt` in the release stage")
        self.assertTrue(copied and min(copied) < installed[0], "requirements-db.txt is not copied in before it is installed")


if __name__ == "__main__":
    unittest.main()
