"""The records of tasks, memos and memory over the Storage layer (IF-101 v1 items, IF-102 tables): the routes of templates/static/chat/api.js,
the event item_changed, text byte for byte (FR-28), shared by all users (CON-6). Needs flask: bash tools/run_in_image.sh tests/test_items_api.py"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask, g                                  # noqa: E402
from items_api import create_items_blueprint                # noqa: E402
from storage import Storage                                 # noqa: E402
from storage_files import FileBackend                       # noqa: E402

TEXT = "  water the plants\n\tfirst the ficus — «ß» é  \n"          # blanks, tab, newline and non-ASCII must come back unchanged


class ItemsApiTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.events = []
        self.now = [1000.0]
        self.account = ["anna"]
        app = Flask(__name__)

        @app.before_request
        def who():
            g.account = self.account[0]                       # what the guard of accounts_api does

        self.storage = Storage(FileBackend(os.path.join(self.dir, "db")))
        app.register_blueprint(create_items_blueprint(self.storage, lambda e, p: self.events.append((e, p)), clock=lambda: self.now[0]))
        self.client = app.test_client()

    def save(self, kind, text, id=None, source=None):
        return self.client.post("/api/items", json={"kind": kind, "id": id, "text": text, "source": source})

    def test_a_new_record_comes_back_byte_for_byte_and_is_listed(self):
        got = self.save("tasks", TEXT)
        self.assertEqual(got.status_code, 200)
        record = got.get_json()
        self.assertEqual((record["text"], record["author"]), (TEXT, "anna"))
        self.assertEqual(self.client.get("/api/items?kind=tasks").get_json(), [record])
        self.assertEqual(self.client.get("/api/items?kind=memos").get_json(), [])

    def test_everybody_sees_and_changes_everything_and_the_creation_stays(self):
        first = self.save("memos", "one").get_json()
        self.now[0] += 60
        self.account[0] = "ben"
        changed = self.save("memos", "two", id=first["id"]).get_json()
        self.assertEqual((changed["id"], changed["text"], changed["author"], changed["created"]), (first["id"], "two", "ben", first["created"]))
        self.assertEqual(len(self.client.get("/api/items?kind=memos").get_json()), 1)

    def test_the_list_is_oldest_first(self):
        ids = []
        for text in ("a", "b", "c"):
            ids.append(self.save("tasks", text).get_json()["id"])
            self.now[0] += 0.001
        self.assertEqual([r["id"] for r in self.client.get("/api/items?kind=tasks").get_json()], ids)

    def test_memory_needs_a_source(self):
        bad = self.save("memory", "likes tea")
        self.assertEqual((bad.status_code, bad.get_json()), (422, {"error": "invalid_item", "rule": "source"}))
        ok = self.save("memory", "likes tea", source="chat").get_json()
        self.assertEqual(ok["source"], "chat")
        self.assertEqual(len(self.client.get("/api/items?kind=memory").get_json()), 1)

    def test_refusals_store_nothing(self):
        self.assertEqual(self.save("tasks", "  \n").get_json(), {"error": "empty_text"})
        self.assertEqual(self.save("tasks", "x", id="nope").status_code, 404)
        self.assertEqual(self.save("votes", "x").status_code, 404)                          # only tasks, memos and memory are items
        self.assertEqual(self.client.get("/api/items?kind=history").status_code, 404)
        self.assertEqual(self.client.delete("/api/items?kind=tasks&id=nope").status_code, 404)
        self.assertEqual(self.client.get("/api/items?kind=tasks").get_json(), [])
        self.assertEqual(self.events, [])

    def test_delete_and_the_event_for_the_others(self):
        record = self.save("tasks", "x").get_json()
        self.assertEqual(self.events[-1], ("item_changed", {"kind": "tasks", "id": record["id"], "author": "anna", "deleted": False}))
        self.account[0] = "ben"
        self.assertEqual(self.client.delete("/api/items?kind=tasks&id=" + record["id"]).get_json(), {"deleted": True})
        self.assertEqual(self.events[-1], ("item_changed", {"kind": "tasks", "id": record["id"], "author": "ben", "deleted": True}))
        self.assertEqual(self.client.get("/api/items?kind=tasks").get_json(), [])


if __name__ == "__main__":
    unittest.main()
