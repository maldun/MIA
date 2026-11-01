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
        """TC-CLV-014: without a session the history is 401 and the socket is refused; the page itself is open and asks for the login.

        Example: no cookie -> GET /api/chat/history 401 {"error": "unauthenticated"}, socket not connected, GET / 200.
        """
        # Given: a client without a session
        # When / Then: the history and the socket are refused, the page is served
        self.assertEqual(self.http.get("/api/chat/history").status_code, 401)
        self.assertEqual(self.http.get("/api/chat/history").get_json(), {"error": "unauthenticated"})
        refused = w.socketio.test_client(w.app, flask_test_client=self.http)
        self.assertFalse(refused.is_connected())
        self.assertEqual(self.http.get("/").status_code, 200)                    # the page itself is open, it asks for the login

    @mark.req("REQ-CLV-014")
    def test_login_sets_an_http_only_same_site_cookie_and_a_wrong_password_is_401(self):
        """TC-CLV-014: a wrong password is 401; the right one sets the session cookie, HttpOnly and SameSite=Strict, and opens the history.

        Example: anna / wrong -> 401; anna / pw-anna -> Set-Cookie mia_session=...; HttpOnly; SameSite=Strict, history {"messages": [], "older": false}.
        """
        # Given / When: a wrong and then the right password
        self.assertEqual(login(self.http, "anna", "wrong").status_code, 401)
        ok = login(self.http, "anna", "pw-anna")
        # Then: the wrong one is 401, the right one sets the cookie and opens the history
        cookie = ok.headers["Set-Cookie"]
        self.assertIn("mia_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)
        self.assertEqual(self.http.get("/api/chat/history").get_json(), {"messages": [], "older": False})

    @mark.req("REQ-CLV-014")
    def test_the_sixth_wrong_login_in_a_minute_is_throttled_even_with_the_right_password(self):
        """TC-CLV-014: five wrong logins in a minute, then even the right password is refused as throttled.

        Example: ben / wrong five times -> 401 each; ben / pw-ben -> 429.
        """
        # Given: five wrong logins within a minute
        for _ in range(5):
            self.assertEqual(login(self.http, "ben", "wrong").status_code, 401)
        # When / Then: the right password is throttled
        self.assertEqual(login(self.http, "ben", "pw-ben").status_code, 429)

    @mark.req("REQ-CLV-001", "REQ-CLV-002")
    def test_a_message_has_its_sender_and_a_position_and_the_other_user_sees_the_answer_stream(self):
        """TC-CLV-001, TC-CLV-002: the acknowledgement names the sender and the place; the other user sees the message with its sender and the answer stream.

        Example: anna sends "hello MIA" -> ack position 1, sender anna; ben gets chat_message (anna), then chat_start ... chat_done "Hello anna. ..."
        """
        # Given: the pages of anna and ben
        anna_http, anna = self.connect("anna")
        ben_http, ben = self.connect("ben")
        # When: anna sends a message
        ack = anna.emit("chat_send", {"id": "c1", "text": "hello MIA"}, callback=True)
        # Then: the ack has her name and place 1, ben sees her message, then the answer streams
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
        """TC-CLV-002: three quick messages of two users wait at places 1, 2, 3; a third of one user is refused (two per user).

        Example: anna "one", ben "two", anna "three" -> positions [1, 2, 3]; anna "four" -> not ok, "queue is full".
        """
        # Given: the pages of anna and ben
        _, anna = self.connect("anna")
        _, ben = self.connect("ben")
        # When: three messages are sent quickly, then a third of anna
        positions = [anna.emit("chat_send", {"id": "a1", "text": "one"}, callback=True)["position"],
                     ben.emit("chat_send", {"id": "b1", "text": "two"}, callback=True)["position"],
                     anna.emit("chat_send", {"id": "a2", "text": "three"}, callback=True)["position"]]
        # Then: places 1, 2, 3, and the fourth is refused
        self.assertEqual(positions, [1, 2, 3])
        refused = anna.emit("chat_send", {"id": "a3", "text": "four"}, callback=True)       # two per user (REQ-BE-003)
        self.assertFalse(refused["ok"])
        self.assertIn("queue is full", refused["error"])
        time.sleep(1.5)

    @mark.req("REQ-CLV-002")
    def test_stop_with_nothing_running_says_so(self):
        """TC-CLV-002: a stop while nothing runs answers that nothing was stopped.

        Example: chat_stop with an empty queue -> {"stopped": false}.
        """
        # Given: a page and nothing running
        # When / Then: a stop says nothing was stopped
        _, anna = self.connect("anna")
        self.assertEqual(anna.emit("chat_stop", callback=True), {"stopped": False})

    @mark.req("REQ-CLV-014")
    def test_the_event_names_are_the_ones_of_the_page(self):
        """The page listens to these and to no other chat event (tests/js/multiuser.test.mjs checks the page side).

        Example: anna sends "hi" -> she receives chat_message, chat_start, chat_delta, chat_done and expression.
        """
        # Given: anna's page
        _, anna = self.connect("anna")
        # When: she sends a message and the answer comes
        anna.emit("chat_send", {"id": "x", "text": "hi"}, callback=True)
        time.sleep(1.0)
        # Then: the events are the ones the page listens to
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
        """TC-CLV-014: every REST call of the views needs a session.

        Example: GET /api/whoami, /api/score, /api/items, /api/trust, /api/persona and POST /api/vote without a cookie -> 401 each.
        """
        # Given: a client without a session
        # When / Then: each call is 401
        for method, path in (("get", "/api/whoami"), ("get", "/api/score"), ("get", "/api/items?kind=tasks"), ("post", "/api/vote"), ("get", "/api/trust"), ("get", "/api/persona")):
            self.assertEqual(getattr(w.app.test_client(), method)(path).status_code, 401, path)

    @mark.req("REQ-CLV-022")
    def test_logout_ends_the_session_clears_the_cookie_and_leaves_other_sessions(self):
        """TC-CLV-022: the logout ends this session and clears its cookie; another session of the same account stays.

        Example: anna logs out -> 200 {"loggedOut": true}, Set-Cookie mia_session=; whoami 401, logout again 401; her other session whoami -> anna.
        """
        # Given: a second session of anna
        other = w.app.test_client()
        login(other, "anna", "pw-anna")
        # When: the first one logs out
        reply = self.anna.post("/api/logout")
        # Then: it ends, its cookie is cleared, the other session stays
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"loggedOut": True}))
        self.assertIn("mia_session=;", reply.headers.get("Set-Cookie", ""))
        self.assertEqual(self.anna.get("/api/whoami").status_code, 401)
        self.assertEqual(self.anna.post("/api/logout").status_code, 401)
        self.assertEqual(other.get("/api/whoami").get_json(), {"user": "anna"})

    @mark.req("REQ-CLV-022")
    def test_logout_with_a_connected_page_ends_the_session_and_closes_its_socket(self):
        """F8: the logout of a session whose page is connected is 200, not 500 (the events of the ended session are no longer asked for), and
        the socket of that page is closed.

        Example: anna's page connected, POST /api/logout -> 200 {"loggedOut": true}, the socket is no longer connected.
        """
        # Given: anna's page is connected with her session
        page = w.socketio.test_client(w.app, flask_test_client=self.anna)
        self.assertTrue(page.is_connected())
        # When: she logs out
        reply = self.anna.post("/api/logout")
        # Then: the logout succeeds and her page's socket is closed; ben's page stays
        self.assertEqual((reply.status_code, reply.get_json()), (200, {"loggedOut": True}))
        self.assertFalse(page.is_connected())
        self.assertTrue(self.ben_socket.is_connected())

    @mark.req("REQ-CLV-014")
    def test_whoami_and_the_own_password(self):
        """TC-CLV-014: whoami names the account; a wrong old or a short new password is refused; a good change makes the new password work.

        Example: old "nope" -> 401 bad_credentials; new "short" -> 422 weak_password; pw-anna -> long-enough-1 -> {"changed": true}, login with it 200.
        """
        # Given / When / Then: whoami names anna
        self.assertEqual(self.anna.get("/api/whoami").get_json(), {"user": "anna"})
        # When: a wrong old, a short new and a good new password are sent
        wrong = self.anna.post("/api/change_password", json={"old": "nope", "new": "long-enough-1"})
        # Then: refused, refused, changed, and the new password works
        self.assertEqual((wrong.status_code, wrong.get_json()["error"]), (401, "bad_credentials"))
        weak = self.anna.post("/api/change_password", json={"old": "pw-anna", "new": "short"})
        self.assertEqual((weak.status_code, weak.get_json()["error"]), (422, "weak_password"))
        self.assertEqual(self.anna.post("/api/change_password", json={"old": "pw-anna", "new": "long-enough-1"}).get_json(), {"changed": True})
        self.assertEqual(login(w.app.test_client(), "anna", "long-enough-1").status_code, 200)

    @mark.req("REQ-CLV-005", "REQ-CLV-008", "REQ-CLV-010", "REQ-CLV-013")
    def test_regenerate_vote_account_speak_and_the_variant_on_every_third_answer(self):
        """TC-CLV-005, -008, -010, -013: regenerate, vote, score, the account of an answer, speak again, and the variant of every third answer.

        Example: regenerate "nope" 404, the answer -> position 1 and a second answer; vote +1 -> overall 1, category mood 422; account 2 steps; speak again 2 sentences; variants [None, None, "summer"].
        """
        # Given: one answer
        sock = self.answer("one")
        first = [m for m in self.anna.get("/api/chat/history").get_json()["messages"] if m["role"] == "assistant"][-1]
        # When / Then: regenerate an unknown id, then the answer: 404, then a second answer
        self.assertEqual(self.anna.post("/api/regenerate", json={"message_id": "nope"}).status_code, 404)
        self.assertEqual(self.anna.post("/api/regenerate", json={"message_id": first["id"]}).get_json()["position"], 1)
        time.sleep(1.0)
        answers = [m["text"] for m in self.anna.get("/api/chat/history").get_json()["messages"] if m["role"] == "assistant"]
        self.assertEqual(len(answers), 2)
        # When / Then: a vote, a wrong category, the score with its weekly series, the account and speak again
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
        # When / Then: the third answer has the variant summer, the first two none
        self.answer("two")
        variants = [r["args"][0]["name"] for r in self.ben_socket.get_received() if r["name"] == "variant"]
        self.assertEqual(variants, [None, None, "summer"])                                 # answers 1 and 2 (regenerate) have none, the third has one

    @mark.req("REQ-CHA-018")
    def test_the_counters_are_the_mock_s_and_a_reset_is_heard_by_the_others(self):
        """The real routes of chat_ops_api would answer from the page's own storage: the mock must answer on their endpoints (IF-101 v5).

        Example: GET /api/counters -> greet, idle, no, talk, yes with net 0; reset "no" -> 200 and ben hears {"name": "no", "author": "anna"}; "dance" -> 404.
        """
        # Given / When: the counters of the mock
        counters = self.anna.get("/api/counters").get_json()
        # Then: the five behaviours at their defaults
        self.assertEqual(sorted(counters), ["greet", "idle", "no", "talk", "yes"])
        self.assertEqual(counters["no"], {"net": 0, "votes": 0, "chance": 1.0, "reset_at": None})
        # When / Then: a reset is heard by ben, an unknown name is 404, no session is 401
        self.ben_socket.get_received()
        self.assertEqual(self.anna.post("/api/reset_counter", json={"name": "no"}).status_code, 200)
        self.assertEqual(self.anna.post("/api/reset_counter", json={"name": "dance"}).status_code, 404)
        heard = [r["args"][0] for r in self.ben_socket.get_received() if r["name"] == "counters_changed"]
        self.assertEqual(heard, [{"name": "no", "author": "anna"}])
        self.assertEqual(w.app.test_client().get("/api/counters").status_code, 401)

    @mark.req("REQ-CLV-011", "REQ-CLV-009", "REQ-CLV-012")
    def test_records_trust_and_persona_and_the_others_hear_of_the_change(self):
        """TC-CLV-009, -011, -012: records, trust and persona are shared, and the other user hears of each change.

        Example: anna adds a task, ben sees and edits it (author ben); memory without source 422 source; trust 0.2 seen by ben, 2 refused 422; persona "MIA is calm." seen by ben; ben got item_changed, trust_changed, persona_changed.
        """
        # Given: ben's page, nothing received yet
        self.ben_socket.get_received()
        # When / Then: a task is added, seen and edited by ben; a memory needs a source; the task is deleted
        task = self.anna.post("/api/items", json={"kind": "tasks", "id": None, "text": "water the plants"}).get_json()
        self.assertEqual(self.ben.get("/api/items?kind=tasks").get_json()[0]["text"], "water the plants")
        self.assertEqual(self.ben.post("/api/items", json={"kind": "tasks", "id": task["id"], "text": "water the herbs"}).get_json()["author"], "ben")
        refused = self.anna.post("/api/items", json={"kind": "memory", "id": None, "text": "likes tea"})
        self.assertEqual((refused.status_code, refused.get_json()["rule"]), (422, "source"))
        self.assertEqual(self.anna.delete("/api/items?kind=tasks&id=" + task["id"]).get_json(), {"deleted": True})
        self.assertEqual(self.anna.get("/api/items?kind=tasks").get_json(), [])
        # When / Then: a trust value is kept, 2 is refused; the persona is shared
        self.anna.post("/api/trust", json={"source": "example.org", "value": 0.2})
        self.assertEqual(self.ben.get("/api/trust").get_json()["example.org"], 0.2)
        self.assertEqual(self.anna.post("/api/trust", json={"source": "example.org", "value": 2}).status_code, 422)
        self.anna.post("/api/persona", json={"doc": {"text": "MIA is calm."}})
        self.assertEqual(self.ben.get("/api/persona").get_json()["text"], "MIA is calm.")
        # Then: ben heard of every change
        got = {r["name"] for r in self.ben_socket.get_received()}
        self.assertTrue({"item_changed", "trust_changed", "persona_changed"} <= got, got)


if __name__ == "__main__":
    unittest.main()
