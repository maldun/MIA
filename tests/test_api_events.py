"""
N-2.1 T-03, the events of IF-101 on the real Backend (component tests):
 TC-API-001  REQ-API-001  an answer of the scripted model reaches every connected page as ordered sentences, then chat_done
 TC-API-002  REQ-API-002  a change of shared data by one user reaches a second device within 5 s with its author
Needs flask: run with the image:  bash tools/run_in_image.sh tests/test_api_events.py
"""
import importlib
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))
sys.path.insert(0, os.path.join(HERE, "helpers", "mocks"))

import checkout_copy  # noqa: E402  (MIA from a temporary copy: nothing is written into the checkout, D-169)
_PACKAGE_DIR = checkout_copy.use()

from flask import Flask                                            # noqa: E402
from flask_socketio import SocketIO                                # noqa: E402

import accounts                                                    # noqa: E402
import accounts_api as A                                           # noqa: E402
from items_api import create_items_blueprint                       # noqa: E402
from trust_persona_api import create_trust_persona_blueprint       # noqa: E402
from if_102_storage import StorageMock                             # noqa: E402
from markers import mark                                           # noqa: E402

SENTENCES = ["Hello Anna.", "How are you?", "The sun is out."]


def wait_for(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


def payloads(received, name):
    return [m["args"][0] for m in received if m["name"] == name]


class AnswerReachesEveryPage(unittest.TestCase):
    """REQ-API-001 on the real web_app.py (the default config, accounts off): a scripted model says three sentences, two pages listen."""

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.wa = importlib.import_module("MIA.web_app")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.wa.chat_log.path = os.path.join(cls.tmp.name, "log.jsonl")
        cls.wa.chat_log.clear()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        service = self.wa.chat_service

        def scripted(text, on_delta, on_emotion, should_stop):
            shown = ""
            for sentence in SENTENCES:
                shown = (shown + " " + sentence).strip()
                on_delta(shown)
            return shown

        self._exchange = service._run_exchange
        service._run_exchange = scripted

    def tearDown(self):
        self.wa.chat_service._run_exchange = self._exchange

    def page(self):
        client = self.wa.socketio.test_client(self.wa.app)
        client.get_received()
        return client

    def answer_seen_by(self, client):
        """the events of the answer one page received, after the answer is done"""
        self.assertTrue(wait_for(lambda: not self.wa.chat_service.status()["busy"]))
        time.sleep(0.2)
        return client.get_received()

    @mark.req("REQ-API-001")
    def test_the_answer_reaches_every_page_as_ordered_sentences(self):
        """TC-API-001: the scripted answer of three sentences reaches both pages as growing deltas in the order of the sentences, then chat_done.

        Example: send "hi" -> each page sees "Hello Anna." before "How are you?" before "The sun is out.", and chat_done with the whole text.
        """
        # Given
        first, second = self.page(), self.page()
        # When
        ack = first.emit("chat_send", {"id": "c1", "text": "hi"}, callback=True)
        # Then
        self.assertTrue(ack["ok"])
        for client in (first, second):
            received = self.answer_seen_by(client)
            order = [m["name"] for m in received if m["name"] in ("chat_message", "chat_start", "chat_done")]
            self.assertEqual(order[0], "chat_message")
            self.assertLess(order.index("chat_start"), order.index("chat_done"))
            deltas = [p["text"] for p in payloads(received, "chat_delta")]
            self.assertEqual(deltas[-1], " ".join(SENTENCES))
            self.assertTrue(all(later.startswith(earlier) for earlier, later in zip(deltas, deltas[1:])))
            positions = [deltas[-1].index(sentence) for sentence in SENTENCES]
            self.assertEqual(positions, sorted(positions))
            done = payloads(received, "chat_done")[0]
            self.assertEqual((done["text"], done["status"]), (deltas[-1], "done"))

    def test_web_app_writes_into_its_own_data_folder_not_the_checkout(self):
        """R-6 of the N-2.1 re-verification (D-167): the imported web_app keeps its data (token, library, presets, workflows) in a temporary folder.

        Example: data/ of the imported web_app is a real folder under the temporary directory, not a link into the checkout.
        """
        # Given: the web_app this test imported
        data = os.path.realpath(os.path.join(self.wa.FPATH, "data"))
        # Then: its data folder lies outside the checkout
        self.assertFalse(data.startswith(os.path.realpath(REPO) + os.sep), data)


class ChangesReachEveryDevice(unittest.TestCase):
    """REQ-API-002 on the real guard, routes and Socket.IO broadcast of the Backend, with the storage mock (IF-102) and two accounts."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app)
        store = StorageMock()
        accounts.create(store, "anna", "pw-anna-1", "setup")
        accounts.create(store, "ben", "pw-ben-123", "setup")
        self.service, self.sockets = A.install(self.app, self.socketio, store, allowed_origins=lambda: [])

        @self.socketio.on("connect")
        def connect(_auth=None):
            A.guard_connect(self.sockets)

        self.app.register_blueprint(create_items_blueprint(store, self.socketio.emit))
        self.app.register_blueprint(create_trust_persona_blueprint(os.path.join(self.tmp.name, "trust.json"), os.path.join(self.tmp.name, "persona.json"),
                                                                   self.socketio.emit))

    def tearDown(self):
        self.tmp.cleanup()

    def device(self, user, password):
        """a logged-in browser: its HTTP client (with the session cookie) and its socket"""
        web = self.app.test_client()
        self.assertEqual(web.post("/api/login", json={"user": user, "password": password}).status_code, 200)
        sock = self.socketio.test_client(self.app, flask_test_client=web)
        self.assertTrue(sock.is_connected())
        sock.get_received()
        return web, sock

    def seen_within_5_s(self, sock, name):
        """the payloads of the event `name` that reached the socket within 5 s"""
        found = []
        wait_for(lambda: found.extend(payloads(sock.get_received(), name)) or found)
        return found

    @mark.req("REQ-API-002")
    def test_a_saved_and_a_deleted_item_reach_the_other_device_with_the_author(self):
        """TC-API-002: anna saves and deletes a memo; ben's device gets both changes with anna as the author within 5 s.

        Example: anna saves "buy tea" and deletes it -> ben sees item_changed (deleted False) and item_changed (deleted True), author anna.
        """
        # Given
        anna_web, _ = self.device("anna", "pw-anna-1")
        _, ben_sock = self.device("ben", "pw-ben-123")
        # When
        saved = anna_web.post("/api/items", json={"kind": "memos", "text": "buy tea"}).get_json()
        anna_web.delete("/api/items?kind=memos&id=" + saved["id"])
        # Then
        changes = self.seen_within_5_s(ben_sock, "item_changed")
        self.assertEqual([(c["kind"], c["id"], c["author"], c["deleted"]) for c in changes], [("memos", saved["id"], "anna", False), ("memos", saved["id"], "anna", True)])

    @mark.req("REQ-API-002")
    def test_a_trust_change_reaches_the_other_device_with_the_author(self):
        """TC-API-002: ben sets the trust of a source; anna's device gets trust_changed with ben as the author within 5 s.

        Example: ben sets preprint to 0.2 -> anna sees trust_changed {source preprint, new 0.2, author ben}.
        """
        # Given
        ben_web, _ = self.device("ben", "pw-ben-123")
        _, anna_sock = self.device("anna", "pw-anna-1")
        # When
        answer = ben_web.post("/api/trust", json={"source": "preprint", "value": 0.2})
        # Then
        self.assertEqual(answer.status_code, 200)
        changes = self.seen_within_5_s(anna_sock, "trust_changed")
        self.assertEqual([(c["source"], c["new"], c["author"]) for c in changes], [("preprint", 0.2, "ben")])

    @mark.req("REQ-API-002")
    def test_a_persona_change_reaches_the_other_device_with_the_author(self):
        """TC-API-002: anna saves the persona; ben's device gets persona_changed with anna as the author within 5 s.

        Example: anna saves "calm and curious" -> ben sees persona_changed {author anna}.
        """
        # Given
        anna_web, _ = self.device("anna", "pw-anna-1")
        _, ben_sock = self.device("ben", "pw-ben-123")
        # When
        answer = anna_web.post("/api/persona", json={"doc": {"text": "calm and curious"}})
        # Then
        self.assertEqual(answer.status_code, 200)
        self.assertEqual(self.seen_within_5_s(ben_sock, "persona_changed"), [{"author": "anna"}])

    @mark.req("REQ-API-002")
    def test_the_device_that_made_the_change_gets_it_too(self):
        """TC-API-002: the change reaches every connected device, also the one of the author.

        Example: anna saves a task from her browser -> her own socket sees item_changed with author anna.
        """
        # Given
        anna_web, anna_sock = self.device("anna", "pw-anna-1")
        # When
        anna_web.post("/api/items", json={"kind": "tasks", "text": "water the plants"})
        # Then
        changes = self.seen_within_5_s(anna_sock, "item_changed")
        self.assertEqual([(c["kind"], c["author"]) for c in changes], [("tasks", "anna")])

if __name__ == "__main__":
    unittest.main()
