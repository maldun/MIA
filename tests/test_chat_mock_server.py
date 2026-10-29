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


class RestViews(unittest.TestCase):
    """The REST routes of IF-101 v1 that the views of the page call (templates/static/chat/api.js)."""

    def setUp(self):
        server.api.__init__(accounts=dict(server.ACCOUNTS), answers=[])
        server.sids.clear()
        server.tokens.clear()
        server.turn["n"] = 0
        self.anna = w.app.test_client()
        login(self.anna, "anna", "pw-anna")
        self.ben = w.app.test_client()
        login(self.ben, "ben", "pw-ben")
        self.ben_socket = w.socketio.test_client(w.app, flask_test_client=self.ben)

    def answer(self, text="hi"):
        sock = w.socketio.test_client(w.app, flask_test_client=self.anna)
        sock.emit("chat_send", {"id": "c" + text, "text": text}, callback=True)
        time.sleep(1.0)
        return sock

    @mark.req("REQ-CLV-014")
    def test_no_session_no_rest_call(self):
        for method, path in (("get", "/api/whoami"), ("get", "/api/score"), ("get", "/api/items?kind=tasks"), ("post", "/api/vote"), ("get", "/api/trust"), ("get", "/api/persona")):
            self.assertEqual(getattr(w.app.test_client(), method)(path).status_code, 401, path)

    @mark.req("REQ-CLV-022")
    def test_logout_ends_the_session_clears_the_cookie_and_leaves_other_sessions(self):
        other = w.app.test_client()
        login(other, "anna", "pw-anna")
        reply = self.anna.post("/api/logout")
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"loggedOut": True}))
        self.assertIn("mia_session=;", reply.headers.get("Set-Cookie", ""))
        self.assertEqual(self.anna.get("/api/whoami").status_code, 401)
        self.assertEqual(self.anna.post("/api/logout").status_code, 401)
        self.assertEqual(other.get("/api/whoami").get_json(), {"user": "anna"})

    @mark.req("REQ-CLV-014")
    def test_whoami_and_the_own_password(self):
        self.assertEqual(self.anna.get("/api/whoami").get_json(), {"user": "anna"})
        wrong = self.anna.post("/api/change_password", json={"old": "nope", "new": "long-enough-1"})
        self.assertEqual((wrong.status_code, wrong.get_json()["error"]), (401, "bad_credentials"))
        weak = self.anna.post("/api/change_password", json={"old": "pw-anna", "new": "short"})
        self.assertEqual((weak.status_code, weak.get_json()["error"]), (422, "weak_password"))
        self.assertEqual(self.anna.post("/api/change_password", json={"old": "pw-anna", "new": "long-enough-1"}).get_json(), {"changed": True})
        self.assertEqual(login(w.app.test_client(), "anna", "long-enough-1").status_code, 200)

    @mark.req("REQ-CLV-005", "REQ-CLV-008", "REQ-CLV-010", "REQ-CLV-013")
    def test_regenerate_vote_account_speak_and_the_variant_on_every_third_answer(self):
        sock = self.answer("one")
        first = [m for m in self.anna.get("/api/chat/history").get_json()["messages"] if m["role"] == "assistant"][-1]
        self.assertEqual(self.anna.post("/api/regenerate", json={"message_id": "nope"}).status_code, 404)
        self.assertEqual(self.anna.post("/api/regenerate", json={"message_id": first["id"]}).get_json()["position"], 1)
        time.sleep(1.0)
        answers = [m["text"] for m in self.anna.get("/api/chat/history").get_json()["messages"] if m["role"] == "assistant"]
        self.assertEqual(len(answers), 2)
        vote = self.anna.post("/api/vote", json={"subject": first["id"], "category": "answer_quality", "value": 1}).get_json()
        self.assertEqual(vote["score"]["overall"], 1)
        self.assertEqual(self.anna.post("/api/vote", json={"subject": first["id"], "category": "mood", "value": 1}).status_code, 422)
        self.assertEqual(self.anna.get("/api/score").get_json()["categories"]["answer_quality"], 1)
        series = self.anna.get("/api/score").get_json()["series"]                           # IF-101 v4: the sums per ISO week
        self.assertEqual([w["overall"] for w in series], [1])
        self.assertRegex(series[0]["week"], r"^\d{4}-W\d{2}$")
        self.assertEqual(len(self.anna.get("/api/account?message_id=" + first["id"]).get_json()), 2)
        sock.get_received()
        self.assertEqual(self.anna.post("/api/speak_again", json={"message_id": first["id"]}).get_json()["sentences"], 2)
        self.answer("two")
        variants = [r["args"][0]["name"] for r in self.ben_socket.get_received() if r["name"] == "variant"]
        self.assertEqual(variants, [None, None, "summer"])                                 # answers 1 and 2 (regenerate) have none, the third has one

    @mark.req("REQ-CHA-018")
    def test_the_counters_are_the_mock_s_and_a_reset_is_heard_by_the_others(self):
        """The real routes of chat_ops_api would answer from the page's own storage: the mock must answer on their endpoints (IF-101 v5)."""
        counters = self.anna.get("/api/counters").get_json()
        self.assertEqual(sorted(counters), ["greet", "idle", "no", "talk", "yes"])
        self.assertEqual(counters["no"], {"net": 0, "votes": 0, "chance": 1.0, "reset_at": None})
        self.ben_socket.get_received()
        self.assertEqual(self.anna.post("/api/reset_counter", json={"name": "no"}).status_code, 200)
        self.assertEqual(self.anna.post("/api/reset_counter", json={"name": "dance"}).status_code, 404)
        heard = [r["args"][0] for r in self.ben_socket.get_received() if r["name"] == "counters_changed"]
        self.assertEqual(heard, [{"name": "no", "author": "anna"}])
        self.assertEqual(w.app.test_client().get("/api/counters").status_code, 401)

    @mark.req("REQ-CLV-011", "REQ-CLV-009", "REQ-CLV-012")
    def test_records_trust_and_persona_and_the_others_hear_of_the_change(self):
        self.ben_socket.get_received()
        task = self.anna.post("/api/items", json={"kind": "tasks", "id": None, "text": "water the plants"}).get_json()
        self.assertEqual(self.ben.get("/api/items?kind=tasks").get_json()[0]["text"], "water the plants")
        self.assertEqual(self.ben.post("/api/items", json={"kind": "tasks", "id": task["id"], "text": "water the herbs"}).get_json()["author"], "ben")
        refused = self.anna.post("/api/items", json={"kind": "memory", "id": None, "text": "likes tea"})
        self.assertEqual((refused.status_code, refused.get_json()["rule"]), (422, "source"))
        self.assertEqual(self.anna.delete("/api/items?kind=tasks&id=" + task["id"]).get_json(), {"deleted": True})
        self.assertEqual(self.anna.get("/api/items?kind=tasks").get_json(), [])
        self.anna.post("/api/trust", json={"source": "example.org", "value": 0.2})
        self.assertEqual(self.ben.get("/api/trust").get_json()["example.org"], 0.2)
        self.assertEqual(self.anna.post("/api/trust", json={"source": "example.org", "value": 2}).status_code, 422)
        self.anna.post("/api/persona", json={"doc": {"text": "MIA is calm."}})
        self.assertEqual(self.ben.get("/api/persona").get_json()["text"], "MIA is calm.")
        got = {r["name"] for r in self.ben_socket.get_received()}
        self.assertTrue({"item_changed", "trust_changed", "persona_changed"} <= got, got)


class ReviewOnTheMock(unittest.TestCase):
    """so that the status card, pause and the Files tab can be seen by hand without a model: the scripted review of the IF-101 mock runs on the mock server (TC-WFM-031, -033, -036, -037)"""

    def setUp(self):
        server.api.__init__(accounts=dict(server.ACCOUNTS), answers=[])
        server.sids.clear()
        server.tokens.clear()
        server.turn["n"] = 0
        self.client = w.app.test_client()
        login(self.client, "anna", "pw-anna")
        self.sock = w.socketio.test_client(w.app, flask_test_client=self.client)
        self.sock.get_received()

    def test_a_review_shows_a_card_asks_and_gives_the_result_as_the_newest_message_with_a_file(self):
        ack = self.sock.emit("chat_send", {"id": "c1", "text": "/review do canary releases help?"}, callback=True)
        self.assertTrue(ack["ok"])
        first = self.sock.get_received()
        cards = [r["args"][0] for r in first if r["name"] == "task_status"]
        self.assertEqual((cards[-1]["task"], cards[-1]["done"]), ("review", False))
        self.assertIn("on_list", cards[-1]["counts"])                          # the mock server adds demo figures so that the card has something to show
        self.assertIn("Shall I go on?", [r["args"][0]["text"] for r in first if r["name"] == "chat_message"])
        reply = self.sock.emit("chat_send", {"id": "c2", "text": "no"}, callback=True)
        self.assertEqual((reply["ok"], reply["position"]), (True, 0))
        second = self.sock.get_received()
        order = names(second)
        self.assertGreater(order.index("chat_start"), max(i for i, n in enumerate(order) if n == "chat_message"))
        self.assertTrue([r["args"][0] for r in second if r["name"] == "task_status"][-1]["done"])
        done = [r["args"][0] for r in second if r["name"] == "chat_done"][0]
        self.assertEqual((done["text"], done["files"]), ("the report", ["review-contract.md"]))
        self.assertEqual([f["name"] for f in self.client.get("/api/files").get_json()], ["review-contract.md"])
        got = self.client.get("/api/files/review-contract.md")
        self.assertEqual((got.status_code, got.data), (200, b"# the report\n"))
        self.assertIn("attachment", got.headers["Content-Disposition"])

    def test_pause_and_resume_reach_the_running_review_and_a_bad_file_name_is_refused(self):
        self.assertEqual(self.client.post("/api/pause").get_json(), {"paused": False})            # nothing runs
        self.sock.emit("chat_send", {"id": "c1", "text": "/review do canary releases help?"}, callback=True)
        self.sock.get_received()
        self.assertEqual(self.client.post("/api/pause").get_json(), {"paused": True})
        self.assertTrue([r["args"][0] for r in self.sock.get_received() if r["name"] == "task_status"][-1]["paused"])
        self.assertEqual(self.client.post("/api/resume").get_json(), {"paused": False})
        self.assertEqual(self.client.get("/api/files/..x.md").status_code, 422)
        self.assertEqual(self.client.get("/api/files/none.md").status_code, 404)
        self.assertEqual(w.app.test_client().get("/api/files").status_code, 401)

    def test_stop_ends_a_waiting_review_with_the_result_as_it_stands(self):
        self.sock.emit("chat_send", {"id": "c1", "text": "/review do canary releases help?"}, callback=True)
        self.sock.get_received()
        self.assertEqual(self.sock.emit("chat_stop", callback=True), {"stopped": True})
        done = [r["args"][0] for r in self.sock.get_received() if r["name"] == "chat_done"]
        self.assertEqual([d["status"] for d in done], ["stopped"])


if __name__ == "__main__":
    unittest.main()
