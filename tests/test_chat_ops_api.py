"""The routes of the operations on answers (IF-101 v1 over IF-201): vote, score, regenerate, speak_again, account; the errors keep their codes and statuses.
Needs flask: bash tools/run_in_image.sh tests/test_chat_ops_api.py"""
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
from moods import MoodTracker                               # noqa: E402
from storage import Storage                                 # noqa: E402
from storage_files import FileBackend                       # noqa: E402


class OpsApiTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.dir, True)
        self.events = []
        log = ChatLog(os.path.join(self.dir, "log.jsonl"))
        self.chat = ChatService(lambda e, p: self.events.append((e, p)), log, MoodTracker(os.path.join(ROOT, "moods.json")),
                                lambda text, on_delta, on_emotion, stop: "One. Two.", queue_size=5, spawn=lambda t: t(),
                                votes=Storage(FileBackend(os.path.join(self.dir, "db"))))
        app = Flask(__name__)

        @app.before_request
        def who():
            g.account = "anna"                               # what the guard of accounts_api does

        app.register_blueprint(create_chat_ops_blueprint(self.chat))
        self.client = app.test_client()
        self.chat.send("hi", author="anna")
        self.answer = log.last("assistant")["id"]

    def test_vote_and_score(self):
        got = self.client.post("/api/vote", json={"subject": self.answer, "category": "answer_quality", "value": 1})
        self.assertEqual((got.status_code, got.get_json()["stored"]), (200, True))
        score = self.client.get("/api/score").get_json()
        self.assertEqual((score["overall"], score["votes"], len(score["series"])), (1, 1, 1))

    def test_errors_keep_code_rule_and_status(self):
        bad = self.client.post("/api/vote", json={"subject": "x", "category": "mood", "value": 1})
        self.assertEqual((bad.status_code, bad.get_json()), (422, {"error": "invalid_vote", "rule": "category"}))
        missing = self.client.post("/api/vote", json={"subject": "nope", "category": "answer_quality", "value": 1})
        self.assertEqual((missing.status_code, missing.get_json()), (404, {"error": "not_found"}))
        self.assertEqual(self.client.post("/api/vote", json={}).status_code, 422)             # a body without fields is invalid, not a crash

    def test_answer_operations(self):
        self.assertEqual(self.client.post("/api/speak_again", json={"id": self.answer}).get_json(), {"sentences": 2})
        self.assertTrue(self.client.get("/api/account/" + self.answer).get_json()[0]["plain"])
        self.assertEqual(self.client.get("/api/account/nope").status_code, 404)
        self.assertEqual(self.client.post("/api/regenerate", json={"id": self.answer}).get_json()["position"], 1)
        self.assertEqual(self.client.post("/api/regenerate", json={"id": "nope"}).status_code, 404)


if __name__ == "__main__":
    unittest.main()
