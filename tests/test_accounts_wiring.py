"""
N-2.1, Verify finding V-1: the production wiring of web_app.py with accounts_enabled: true (component tests, no model server: a scripted answer).
 TC-API-007  REQ-API-007  no session, no route and no socket; the message rate limit counts per account, not per connection
 TC-API-009  REQ-API-009  a chat message carries its account as sender and is in the change record
 TC-API-014  REQ-API-014  the routes of IF-104 are registered and answer under the session
web_app is imported from a folder of links to the checkout with its own configuration and data folder, so the checkout is not changed.
Needs flask: run with the image:  bash tools/run_in_image.sh tests/test_accounts_wiring.py
"""

import json
import os
import shutil
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark  # noqa: E402

OWN_FILES = ("setup_cfg.json", "setup_cfg.local.json", "data")       # made fresh for the test, never the checkout's
GRAPH = {"nodes": [{"id": "claim", "kind": "data"}, {"id": "check", "kind": "process"}, {"id": "verdict", "kind": "data"}],
         "edges": [{"from": "claim", "to": "check"}, {"from": "check", "to": "verdict"}]}
RATE = 10                 # messages per 60 s and account (chat_rate_per_minute)


def package_with_accounts(folder):
    """a folder MIA/ whose files are links to the checkout, with its own configuration (the example with accounts on) and an empty data folder:
    web_app reads setup_cfg.json and writes data/ next to its own file, so nothing of the checkout is changed"""
    package = os.path.join(folder, "MIA")
    os.makedirs(os.path.join(package, "data"))
    for name in os.listdir(REPO):
        if name not in OWN_FILES:
            os.symlink(os.path.join(REPO, name), os.path.join(package, name))
    with open(os.path.join(REPO, "setup_cfg.example.json"), encoding="utf-8") as fp:
        cfg = json.load(fp)
    cfg.update({"accounts_enabled": True, "chat_rate_per_minute": RATE})
    with open(os.path.join(package, "setup_cfg.json"), "w", encoding="utf-8") as fp:
        json.dump(cfg, fp)
    return package


def wait_for(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


class ProductionWiring(unittest.TestCase):
    """the real web_app.py with accounts_enabled: true, a scripted model instead of the model server"""

    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.mkdtemp()
        cls.addClassCleanup(shutil.rmtree, cls.folder, True)
        cls.package = package_with_accounts(cls.folder)
        sys.path.insert(0, cls.folder)
        os.environ.setdefault("MIA_TEST", "1")
        from MIA import accounts, web_app
        cls.wa = web_app
        accounts.create(web_app._account_store, "anna", "pw-anna-1", "setup")
        accounts.create(web_app._account_store, "ben", "pw-ben-123", "setup")
        web_app.chat_service._run_exchange = lambda text, on_delta, on_emotion, should_stop: (on_delta("Fine."), "Fine.")[1]

    def setUp(self):
        self.wa.chat_service._hits.clear()                 # every test starts with an empty rate window

    def login(self, user, password):
        """a browser of `user` with its session cookie"""
        web = self.wa.app.test_client()
        self.assertEqual(web.post("/api/login", json={"user": user, "password": password}).status_code, 200)
        return web

    def socket(self, web):
        return self.wa.socketio.test_client(self.wa.app, flask_test_client=web)

    def send(self, sock, text):
        """chat_send over the socket; returns the ack after the answer is done"""
        ack = sock.emit("chat_send", {"id": "c-" + text, "text": text}, callback=True)
        wait_for(lambda: not self.wa.chat_service.status().get("busy"))
        return ack

    def changes(self):
        path = os.path.join(self.package, "data", "changes.jsonl")
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as fp:
            return [json.loads(line) for line in fp]

    @mark.req("REQ-API-014")
    def test_the_graph_routes_answer_under_the_session(self):
        """TC-API-014: without a session /api/workflows is refused; with anna's session a saved workflow is version 1 by anna.

        Example: GET /api/workflows without cookie -> 401; anna PUT /api/workflows/w {doc} -> 200 {"version": 1}, GET -> author anna.
        """
        # Given: a browser without a session and anna's browser
        stranger = self.wa.app.test_client()
        anna = self.login("anna", "pw-anna-1")
        # When: both use the routes of IF-104
        refused = stranger.get("/api/workflows")
        saved = anna.put("/api/workflows/w", json={"doc": GRAPH})
        read = anna.get("/api/workflows/w")
        # Then: the stranger gets 401, anna's save is version 1 with her as author
        self.assertEqual(refused.status_code, 401)
        self.assertEqual((saved.status_code, saved.get_json()), (200, {"version": 1}))
        self.assertEqual((read.get_json()["author"], read.get_json()["doc"]), ("anna", GRAPH))

    @mark.req("REQ-API-007")
    def test_a_socket_without_session_is_refused(self):
        """TC-API-007: the socket handshake needs the session cookie.

        Example: connect without cookie -> not connected; connect with anna's cookie -> connected.
        """
        # Given: a browser without a session and anna's browser
        stranger = self.wa.app.test_client()
        anna = self.login("anna", "pw-anna-1")
        # When: both open the socket
        refused, accepted = self.socket(stranger), self.socket(anna)
        # Then: only anna's is connected
        self.assertEqual((refused.is_connected(), accepted.is_connected()), (False, True))

    @mark.req("REQ-API-009")
    def test_a_chat_message_carries_its_account(self):
        """TC-API-009: the message of chat_send names the account of the socket as its sender.

        Example: anna sends "hello" -> ack ok, message.sender anna.
        """
        # Given: anna's socket
        sock = self.socket(self.login("anna", "pw-anna-1"))
        # When: she sends a message
        ack = self.send(sock, "hello")
        # Then: the message is hers
        self.assertEqual((ack["ok"], ack["message"]["sender"]), (True, "anna"))

    @mark.req("REQ-API-009")
    def test_a_chat_message_is_in_the_change_record(self):
        """TC-API-009: chat_send writes one line of the change record with the account and no text.

        Example: ben sends "note" -> a new line {account: ben, action: chat_send, target: ""}.
        """
        # Given: ben's socket and the change record so far
        sock = self.socket(self.login("ben", "pw-ben-123"))
        before = len(self.changes())
        # When: he sends a message
        self.send(sock, "note")
        # Then: one new line names him and the action, without the text
        new = [(row["account"], row["action"], row["target"]) for row in self.changes()[before:]]
        self.assertEqual(new, [("ben", "chat_send", "")])

    @mark.req("REQ-API-007")
    def test_the_rate_limit_counts_per_account_not_per_connection(self):
        """TC-API-007: the messages of all of anna's connections count together; another account has its own limit.

        Example: anna sends 10 over two sockets -> all ok; her 11th over a third socket -> refused; ben's first -> ok.
        """
        # Given: three sockets of anna and one of ben
        first, second, third = (self.socket(self.login("anna", "pw-anna-1")) for _ in range(3))
        ben = self.socket(self.login("ben", "pw-ben-123"))
        # When: anna sends RATE messages over two sockets, then one more over the third, then ben sends one
        acks = [self.send(first if i % 2 else second, "m%d" % i) for i in range(RATE)]
        eleventh = self.send(third, "one more")
        bens = self.send(ben, "mine")
        # Then: the first RATE pass, the next one of anna is refused, ben's passes
        self.assertEqual([ack["ok"] for ack in acks], [True] * RATE)
        self.assertEqual(eleventh["ok"], False)
        self.assertEqual(bens["ok"], True)

if __name__ == "__main__":
    unittest.main()
