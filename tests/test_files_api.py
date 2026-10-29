"""TC-WFM-037 and TC-WFM-033 on the wire (IF-101 v8): `files` lists the files volume, `file` sends one as an attachment byte for byte, a bad name is 422 invalid_file_name, an unknown one 404 not_found;
`pause` and `resume` reach the chat service. Needs flask: bash tools/run_in_image.sh tests/test_files_api.py"""
import os
import shutil
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from flask import Flask, g                                  # noqa: E402
from chat_log import ChatLog                                # noqa: E402
from chat_ops_api import create_chat_ops_blueprint          # noqa: E402
from chat_service import ChatService                        # noqa: E402
from file_store import FileStore                            # noqa: E402
from files_api import create_files_blueprint                # noqa: E402
from moods import MoodTracker                               # noqa: E402


class FilesApiTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.store = FileStore(os.path.join(self.dir, "files"))
        chat = ChatService(lambda e, p: None, ChatLog(os.path.join(self.dir, "log.jsonl")), MoodTracker(os.path.join(ROOT, "moods.json")), lambda *a: "x", spawn=lambda t: t())
        self.chat = chat
        app = Flask(__name__)

        @app.before_request
        def who():
            g.account = "anna"

        app.register_blueprint(create_files_blueprint(self.store))
        app.register_blueprint(create_chat_ops_blueprint(chat))
        self.client = app.test_client()

    def test_the_list_and_the_download_are_byte_for_byte(self):
        self.store.put("review-2026.md", "# Report\nümlaut\n", task="review", message_id="m7")
        listed = self.client.get("/api/files").get_json()
        self.assertEqual([(f["name"], f["task"], f["message_id"]) for f in listed], [("review-2026.md", "review", "m7")])
        got = self.client.get("/api/files/review-2026.md")
        self.assertEqual(got.status_code, 200)
        self.assertEqual(got.data, "# Report\nümlaut\n".encode("utf-8"))
        self.assertIn("attachment", got.headers["Content-Disposition"])
        self.assertIn("review-2026.md", got.headers["Content-Disposition"])

    def test_a_bad_name_is_422_and_an_unknown_name_404(self):
        bad = self.client.get("/api/files/..x.md")
        self.assertEqual((bad.status_code, bad.get_json()["error"]), (422, "invalid_file_name"))
        missing = self.client.get("/api/files/nothing.md")
        self.assertEqual((missing.status_code, missing.get_json()["error"]), (404, "not_found"))

    def test_there_is_no_route_to_delete_a_file(self):
        self.store.put("a.md", "x")
        self.assertEqual(self.client.delete("/api/files/a.md").status_code, 405)
        self.assertEqual(len(self.store.list()), 1)

    def test_pause_and_resume_reach_the_chat_service(self):
        self.assertEqual(self.client.post("/api/pause").get_json(), {"paused": False})          # nothing runs
        self.chat.pause = lambda: True
        self.assertEqual(self.client.post("/api/pause").get_json(), {"paused": True})
        called = []
        self.chat.resume = lambda: called.append(1) or True
        self.assertEqual(self.client.post("/api/resume").get_json(), {"paused": False})
        self.assertEqual(called, [1])


if __name__ == "__main__":
    unittest.main()
