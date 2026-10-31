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
        """TC-WFM-037: a stored file is listed with its task and message, and downloaded as an attachment byte for byte.

        Example: review-2026.md "# Report\\nümlaut\\n" of task review, message m7 -> listed once; GET /api/files/review-2026.md -> 200, same bytes, attachment.
        """
        # Given: one file in the files volume
        self.store.put("review-2026.md", "# Report\nümlaut\n", task="review", message_id="m7")
        # When: the list is asked and the file downloaded
        listed = self.client.get("/api/files").get_json()
        got = self.client.get("/api/files/review-2026.md")
        # Then: one entry with its task and message, and the same bytes as an attachment
        self.assertEqual([(f["name"], f["task"], f["message_id"]) for f in listed], [("review-2026.md", "review", "m7")])
        self.assertEqual(got.status_code, 200)
        self.assertEqual(got.data, "# Report\nümlaut\n".encode("utf-8"))
        self.assertIn("attachment", got.headers["Content-Disposition"])
        self.assertIn("review-2026.md", got.headers["Content-Disposition"])

    def test_a_bad_name_is_422_and_an_unknown_name_404(self):
        """TC-WFM-037: a name that could leave the volume is refused, a name that is not in it is not found.

        Example: GET /api/files/..x.md -> 422 invalid_file_name; GET /api/files/nothing.md -> 404 not_found.
        """
        # Given: an empty files volume
        # When: a bad and an unknown name are asked for
        bad = self.client.get("/api/files/..x.md")
        missing = self.client.get("/api/files/nothing.md")
        # Then: 422 and 404 with their codes
        self.assertEqual((bad.status_code, bad.get_json()["error"]), (422, "invalid_file_name"))
        self.assertEqual((missing.status_code, missing.get_json()["error"]), (404, "not_found"))

    def test_there_is_no_route_to_delete_a_file(self):
        """TC-WFM-037 (IF-101 v8): the files are deleted in the volume, never through the page.

        Example: DELETE /api/files/a.md -> 405, the file is still listed.
        """
        # Given: one file
        self.store.put("a.md", "x")
        # When / Then: a delete is not allowed and the file stays
        self.assertEqual(self.client.delete("/api/files/a.md").status_code, 405)
        self.assertEqual(len(self.store.list()), 1)

    def test_pause_and_resume_reach_the_chat_service(self):
        """TC-WFM-033: pause and resume are passed to the chat service and answer whether the task is paused.

        Example: nothing runs -> pause {"paused": false}; a task runs -> {"paused": true}; resume -> {"paused": false}, the service called once.
        """
        # Given / When / Then: with nothing running, pause says so
        self.assertEqual(self.client.post("/api/pause").get_json(), {"paused": False})          # nothing runs
        # Given: a chat service with a task that can be paused and resumed
        self.chat.pause = lambda: True
        self.assertEqual(self.client.post("/api/pause").get_json(), {"paused": True})
        called = []
        self.chat.resume = lambda: called.append(1) or True
        # When / Then: pause and resume reach it
        self.assertEqual(self.client.post("/api/resume").get_json(), {"paused": False})
        self.assertEqual(called, [1])


if __name__ == "__main__":
    unittest.main()
