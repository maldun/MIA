"""The mock server of the chat page (ui/tools/chat_mock_server.py): the page's login, sender names and queue positions against the IF-101 mock.
TC-CLV-001 (two users), TC-CLV-002 (positions), TC-CLV-014 (login). Run with the MIA virtualenv: python tests/test_chat_mock_server.py"""
import importlib.util
import os
import sys
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))
os.environ.update({"ANSWER_DELAY": "0.3", "EVENT_GAP": "0", "MIA_TEST": "1"})

from markers import mark  # noqa: E402

spec = importlib.util.spec_from_file_location("chat_mock_server", os.path.join(REPO, "ui", "tools", "chat_mock_server.py"))
server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(server)
w = server.w


def login(client, user, password):
    return client.post("/api/login", json={"user": user, "password": password})


def names(received):
    return [r["name"] for r in received]


class MockServer(unittest.TestCase):
    def setUp(self):
        server.api.__init__(accounts=dict(server.ACCOUNTS), answers=[])      # a fresh mock for every test
        server.sids.clear()
        server.tokens.clear()
        server.turn["n"] = 0
        self.http = w.app.test_client()

    def connect(self, user):
        client = w.app.test_client()
        self.assertEqual(login(client, user, "pw-" + user).status_code, 200)
        sock = w.socketio.test_client(w.app, flask_test_client=client)
        self.assertTrue(sock.is_connected())
        return client, sock

    @mark.req("REQ-CLV-014")
    def test_no_session_no_history_and_no_socket(self):
        self.assertEqual(self.http.get("/api/chat/history").status_code, 401)
        self.assertEqual(self.http.get("/api/chat/history").get_json(), {"error": "unauthenticated"})
        refused = w.socketio.test_client(w.app, flask_test_client=self.http)
        self.assertFalse(refused.is_connected())
        self.assertEqual(self.http.get("/").status_code, 200)                    # the page itself is open, it asks for the login

    @mark.req("REQ-CLV-014")
    def test_login_sets_an_http_only_same_site_cookie_and_a_wrong_password_is_401(self):
        self.assertEqual(login(self.http, "anna", "wrong").status_code, 401)
        ok = login(self.http, "anna", "pw-anna")
        cookie = ok.headers["Set-Cookie"]
        self.assertIn("mia_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertEqual(self.http.get("/api/chat/history").get_json(), {"messages": [], "older": False})

    @mark.req("REQ-CLV-014")
    def test_the_sixth_wrong_login_in_a_minute_is_throttled_even_with_the_right_password(self):
        for _ in range(5):
            self.assertEqual(login(self.http, "ben", "wrong").status_code, 401)
        self.assertEqual(login(self.http, "ben", "pw-ben").status_code, 429)

    @mark.req("REQ-CLV-001", "REQ-CLV-002")
    def test_a_message_has_its_sender_and_a_position_and_the_other_user_sees_the_answer_stream(self):
        anna_http, anna = self.connect("anna")
        ben_http, ben = self.connect("ben")
        ack = anna.emit("chat_send", {"id": "c1", "text": "hello MIA"}, callback=True)
        self.assertTrue(ack["ok"])
        self.assertEqual((ack["position"], ack["message"]["sender"], ack["message"]["text"]), (1, "anna", "hello MIA"))
        seen = [r for r in ben.get_received() if r["name"] == "chat_message"]
        self.assertEqual((seen[0]["args"][0]["sender"], seen[0]["args"][0]["text"]), ("anna", "hello MIA"))   # ben sees who wrote it
        time.sleep(1.0)
        events = ben.get_received()
        order = [n for n in names(events) if n in ("chat_start", "chat_delta", "chat_done")]
        self.assertEqual(order[0], "chat_start")
        self.assertEqual(order[-1], "chat_done")
        done = [r["args"][0] for r in events if r["name"] == "chat_done"][0]
        self.assertTrue(done["text"].startswith("Hello anna."))
        history = ben_http.get("/api/chat/history").get_json()["messages"]
        self.assertEqual([(m["role"], m["sender"]) for m in history], [("user", "anna"), ("assistant", "MIA")])

    @mark.req("REQ-CLV-002")
    def test_three_quick_messages_wait_at_positions_1_2_3_and_a_fourth_is_refused_per_user(self):
        _, anna = self.connect("anna")
        _, ben = self.connect("ben")
        positions = [anna.emit("chat_send", {"id": "a1", "text": "one"}, callback=True)["position"],
                     ben.emit("chat_send", {"id": "b1", "text": "two"}, callback=True)["position"],
                     anna.emit("chat_send", {"id": "a2", "text": "three"}, callback=True)["position"]]
        self.assertEqual(positions, [1, 2, 3])
        refused = anna.emit("chat_send", {"id": "a3", "text": "four"}, callback=True)       # two per user (REQ-BE-003)
        self.assertFalse(refused["ok"])
        self.assertIn("queue is full", refused["error"])
        time.sleep(1.5)

    @mark.req("REQ-CLV-002")
    def test_stop_with_nothing_running_says_so(self):
        _, anna = self.connect("anna")
        self.assertEqual(anna.emit("chat_stop", callback=True), {"stopped": False})

    @mark.req("REQ-CLV-014")
    def test_the_event_names_are_the_ones_of_the_page(self):
        """The page listens to these and to no other chat event (tests/js/multiuser.test.mjs checks the page side)."""
        _, anna = self.connect("anna")
        anna.emit("chat_send", {"id": "x", "text": "hi"}, callback=True)
        time.sleep(1.0)
        got = set(names(anna.get_received()))
        self.assertTrue({"chat_message", "chat_start", "chat_delta", "chat_done", "expression"} <= got, got)


if __name__ == "__main__":
    unittest.main()
