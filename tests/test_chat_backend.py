"""
Tests for the chat backend: chat log, mood line, chat service (events, queue, stop, errors), REST API, socket events.
Run with the MIA virtualenv: python tests/test_chat_backend.py
"""
import importlib
import json
import os
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

MOODS = os.path.join(REPO, "moods.json")


def wait_for(condition, timeout=5.0):
    end = time.time() + timeout
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.01)
    return False


class LogTest(unittest.TestCase):
    def setUp(self):
        self.chat_log = importlib.import_module("MIA.chat_log")
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "sub", "chat_log.jsonl")
        self.log = self.chat_log.ChatLog(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_append_and_history_in_order(self):
        for i in range(5):
            self.log.append("user" if i % 2 == 0 else "assistant", "m%d" % i)
        messages, older = self.log.history(limit=50)
        self.assertEqual([m["text"] for m in messages], ["m0", "m1", "m2", "m3", "m4"])
        self.assertFalse(older)
        self.assertEqual(len(self.log), 5)

    def test_ids_increase_and_page_through_history(self):
        records = [self.log.append("user", "m%d" % i) for i in range(7)]
        ids = [r["id"] for r in records]
        self.assertEqual(ids, sorted(ids))
        self.assertEqual(len(set(ids)), 7)
        page, older = self.log.history(limit=3)
        self.assertEqual([m["text"] for m in page], ["m4", "m5", "m6"])
        self.assertTrue(older)
        page, older = self.log.history(before=page[0]["id"], limit=3)
        self.assertEqual([m["text"] for m in page], ["m1", "m2", "m3"])
        page, older = self.log.history(before=page[0]["id"], limit=3)
        self.assertEqual([m["text"] for m in page], ["m0"])
        self.assertFalse(older)

    def test_record_fields_and_validation(self):
        record = self.log.append("assistant", "Hi", emotion="happy", auto=True, model="x")
        for key in ("id", "role", "text", "markdown", "emotion", "auto", "created", "status", "model"):
            self.assertIn(key, record)
        self.assertTrue(record["markdown"])
        self.assertFalse(self.log.append("user", "typed")["markdown"])
        with self.assertRaises(ValueError):
            self.log.append("robot", "x")
        with self.assertRaises(ValueError):
            self.log.append("user", "x", status="weird")

    def test_survives_restart_and_broken_lines(self):
        self.log.append("user", "one")
        with open(self.path, "a", encoding="utf-8") as fp:
            fp.write('{"half written\n')
        again = self.chat_log.ChatLog(self.path)
        again.append("user", "two")
        self.assertEqual([m["text"] for m in again.history()[0]], ["one", "two"])
        self.assertGreater(again.new_id(), self.log.last()["id"])

    def test_oldest_are_dropped_over_the_limit(self):
        small = self.chat_log.ChatLog(os.path.join(self.tmp.name, "small.jsonl"), max_messages=10)
        for i in range(25):
            small.append("user", "m%d" % i)
        texts = [m["text"] for m in small.history(limit=200)[0]]
        self.assertEqual(texts[-1], "m24")
        self.assertLessEqual(len(texts), 20)
        self.assertEqual(len(small), len(texts))

    def test_clear_empties_the_log(self):
        self.log.append("user", "x")
        self.log.clear()
        self.assertEqual(self.log.history()[0], [])
        self.assertEqual(len(self.log), 0)


class MoodTest(unittest.TestCase):
    def setUp(self):
        self.moods = importlib.import_module("MIA.moods")
        self.now = [1000.0]
        self.mood = self.moods.MoodTracker(MOODS, hold_minutes=10, clock=lambda: self.now[0])

    def test_starts_ready(self):
        status = self.mood.status()
        self.assertEqual(status["text"], "Ready when you are.")
        self.assertIsNone(status["emotion"])
        self.assertIsNone(status["activity"])

    def test_emotion_gives_first_person_text_and_emoji(self):
        self.assertTrue(self.mood.set_emotion("sad"))
        status = self.mood.status()
        self.assertEqual(status["emotion"], "sad")
        self.assertIn(status["text"], ["A bit down today.", "Feeling a little blue."])
        self.assertTrue(status["emoji"])

    def test_keyword_case_does_not_matter_and_unknown_is_neutral(self):
        self.mood.set_emotion("MIA")
        self.assertEqual(self.mood.status()["emotion"], "mia")
        self.assertIn(self.mood.status()["text"], ["Hello again!", "Nice to see you!"])
        self.mood.set_emotion("flabbergasted")
        self.assertEqual(self.mood.status()["emotion"], "neutral")

    def test_same_emotion_again_keeps_the_line(self):
        self.mood.set_emotion("happy")
        text = self.mood.status()["text"]
        self.assertFalse(self.mood.set_emotion("happy"))
        self.assertEqual(self.mood.status()["text"], text)

    def test_never_the_same_text_twice_in_a_row(self):
        previous = None
        for _ in range(30):
            self.mood.set_emotion("happy")
            self.mood.set_emotion("sad")
            self.mood.set_emotion("happy")
            text = self.mood.status()["text"]
            self.assertNotEqual(text, previous)
            previous = text

    def test_activity_overrides_and_returns(self):
        self.mood.set_emotion("happy")
        text = self.mood.status()["text"]
        self.mood.set_activity("thinking")
        self.assertEqual(self.mood.status()["text"], "Thinking ...")
        self.assertEqual(self.mood.status()["activity"], "thinking")
        self.mood.set_activity("speaking")      # no text of its own: the mood text stays
        self.assertEqual(self.mood.status()["text"], text)
        self.assertEqual(self.mood.status()["activity"], "speaking")
        self.mood.set_activity(None)
        self.assertEqual(self.mood.status()["text"], text)

    def test_mood_returns_to_ready_after_the_hold_time(self):
        self.mood.set_emotion("angry")
        self.now[0] += 9 * 60
        self.assertEqual(self.mood.status()["emotion"], "angry")
        self.now[0] += 2 * 60
        self.assertEqual(self.mood.status()["text"], "Ready when you are.")

    def test_file_changes_are_picked_up_and_broken_edits_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "moods.json")
            with open(path, "w", encoding="utf-8") as fp:
                json.dump({"emotions": {"happy": {"emoji": "A", "texts": ["first"]}}}, fp)
            mood = self.moods.MoodTracker(path)
            mood.set_emotion("happy")
            self.assertEqual(mood.status()["text"], "first")
            with open(path, "w", encoding="utf-8") as fp:
                json.dump({"emotions": {"happy": {"emoji": "B", "texts": ["second"]}}}, fp)
            os.utime(path, (time.time() + 5, time.time() + 5))
            mood.set_emotion("sad")
            mood.set_emotion("happy")
            self.assertEqual(mood.status()["text"], "second")
            with open(path, "w", encoding="utf-8") as fp:
                fp.write("{ this is not json")
            os.utime(path, (time.time() + 10, time.time() + 10))
            mood.set_emotion("sad")
            mood.set_emotion("happy")
            self.assertEqual(mood.status()["text"], "second")

    def test_missing_file_still_gives_a_ready_line(self):
        mood = self.moods.MoodTracker("/nonexistent/moods.json")
        self.assertEqual(mood.status()["text"], "Ready when you are.")


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.chat_log = importlib.import_module("MIA.chat_log")
        self.service_module = importlib.import_module("MIA.chat_service")
        self.moods = importlib.import_module("MIA.moods")
        self.tmp = tempfile.TemporaryDirectory()
        self.log = self.chat_log.ChatLog(os.path.join(self.tmp.name, "log.jsonl"))
        self.events = []
        self.gate = threading.Event()
        self.gate.set()
        self.mode = {"error": None, "words": ["Hel", "Hello", "Hello wor", "Hello world"], "emotions": ["happy"]}
        self.service = self.make()

    def tearDown(self):
        self.gate.set()
        self.tmp.cleanup()

    def make(self, **options):
        def exchange(text, on_delta, on_emotion, should_stop):
            self.gate.wait(5)
            if self.mode.get("hook"):
                self.mode["hook"]()
            if self.mode["error"]:
                raise ConnectionError(self.mode["error"])
            for emotion in self.mode["emotions"]:
                on_emotion(emotion)
            for words in self.mode["words"]:
                if should_stop():
                    break
                on_delta(words)
                time.sleep(0.001)
            return words if not should_stop() else words

        defaults = dict(model_info=lambda: ("test-model", "full"), clock=time.monotonic)
        defaults.update(options)
        return self.service_module.ChatService(lambda event, payload: self.events.append((event, payload)), self.log,
                                               self.moods.MoodTracker(MOODS), exchange, **defaults)

    def idle(self):
        return wait_for(lambda: not self.service.status()["busy"])

    def names(self):
        return [e for e, _ in self.events]

    def test_send_streams_and_logs_the_answer(self):
        ack = self.service.send("Hi MIA", client_id="c1")
        self.assertTrue(ack["ok"])
        self.assertEqual(ack["message"]["text"], "Hi MIA")
        self.assertTrue(self.idle())
        names = self.names()
        self.assertEqual(names[0], "chat_message")
        for event in ("chat_start", "chat_delta", "chat_done", "chat_status"):
            self.assertIn(event, names)
        self.assertLess(names.index("chat_start"), names.index("chat_done"))
        done = [p for e, p in self.events if e == "chat_done"][0]
        self.assertEqual((done["text"], done["emotion"], done["status"]), ("Hello world", "happy", "done"))
        messages = self.log.history()[0]
        self.assertEqual([(m["role"], m["text"]) for m in messages], [("user", "Hi MIA"), ("assistant", "Hello world")])
        self.assertEqual(messages[1]["emotion"], "happy")
        self.assertEqual(messages[1]["model"], "test-model")
        self.assertEqual(messages[1]["id"], done["id"])

    def test_pipeline_steps_reach_the_page_and_the_log_when_the_skill_shows_them(self):
        steps = [{"kind": "run_start", "payload": {"show": True}}, {"kind": "start", "node": "a"}, {"kind": "done", "node": "a"}, {"kind": "run_end", "payload": {}}]
        self.mode["hook"] = lambda: [self.service.pipeline_event(e) for e in steps]
        self.service.send("research this")
        self.assertTrue(self.idle())
        sent = [p for e, p in self.events if e == "chat_pipeline"]
        self.assertEqual([p["event"]["kind"] for p in sent], ["run_start", "start", "done", "run_end"])
        done = [p for e, p in self.events if e == "chat_done"][0]
        self.assertEqual({p["id"] for p in sent}, {done["id"]})
        self.assertEqual(self.log.history()[0][-1]["pipeline"], steps)
        # events after the answer belong to nobody
        self.service.pipeline_event({"kind": "start"})
        self.assertEqual(len([e for e, _ in self.events if e == "chat_pipeline"]), 4)

    def test_pipeline_steps_stay_hidden_without_a_status_block(self):
        steps = [{"kind": "run_start", "payload": {"show": False}}, {"kind": "start", "node": "a"}]
        self.mode["hook"] = lambda: [self.service.pipeline_event(e) for e in steps]
        self.service.send("just chat")
        self.assertTrue(self.idle())
        self.assertNotIn("chat_pipeline", self.names())
        self.assertNotIn("pipeline", self.log.history()[0][-1])

    def test_deltas_are_cumulative_and_throttled(self):
        self.mode["words"] = ["w%d" % i for i in range(200)]
        self.service.send("go")
        self.assertTrue(self.idle())
        deltas = [p["text"] for e, p in self.events if e == "chat_delta"]
        self.assertLess(len(deltas), 100)
        self.assertEqual(deltas[0], "w0")
        self.assertEqual([p["text"] for e, p in self.events if e == "chat_done"], ["w199"])

    def test_mood_follows_the_answer(self):
        self.service.send("Hi")
        self.assertTrue(self.idle())
        statuses = [p for e, p in self.events if e == "chat_status"]
        activities = [s["activity"] for s in statuses]
        self.assertIn("thinking", activities)
        self.assertIn("speaking", activities)
        self.assertEqual(statuses[-1]["activity"], "idle")
        self.assertEqual(statuses[-1]["mood"]["emotion"], "happy")
        self.assertFalse(statuses[-1]["busy"])

    def test_validation(self):
        self.assertFalse(self.service.send("   ")["ok"])
        self.assertFalse(self.service.send(None)["ok"])
        self.assertFalse(self.service.send("x" * 8001)["ok"])
        self.assertEqual(self.log.history()[0], [])
        self.assertTrue(self.service.send("a\x00b\x07c")["ok"])
        self.assertEqual(self.log.history()[0][0]["text"], "abc")

    def test_one_message_may_wait_then_busy(self):
        self.gate.clear()
        first = self.service.send("one")
        self.assertTrue(wait_for(lambda: self.service.status()["queue"] == 0))              # the worker has taken the first message (until then the queue is not empty and "two" would be refused)
        second = self.service.send("two")
        third = self.service.send("three")
        self.assertTrue(first["ok"] and not first["queued"])
        self.assertTrue(second["ok"] and second["queued"])
        self.assertFalse(third["ok"])
        self.assertIn("busy", third["error"])
        self.assertEqual(self.service.status()["queue"], 1)
        self.gate.set()
        self.assertTrue(self.idle())
        roles = [m["role"] for m in self.log.history()[0]]
        self.assertEqual(roles, ["user", "user", "assistant", "assistant"])

    def test_stop_keeps_the_text_received(self):
        self.mode["words"] = ["a", "ab", "abc", "abcd"]
        gate = self.gate
        original = self.service._run_exchange

        def slow(text, on_delta, on_emotion, should_stop):
            on_emotion("happy")
            on_delta("partial")
            gate.clear()
            gate.wait(5)
            return "partial"

        self.service._run_exchange = slow
        self.service.send("long one")
        self.assertTrue(wait_for(lambda: any(e == "chat_delta" for e, _ in self.events)))
        self.assertTrue(self.service.stop())
        gate.set()
        self.assertTrue(self.idle())
        done = [p for e, p in self.events if e == "chat_done"][0]
        self.assertEqual((done["text"], done["status"]), ("partial", "stopped"))
        self.assertEqual(self.log.history()[0][-1]["status"], "stopped")
        self.service._run_exchange = original
        self.assertFalse(self.service.stop())

    def test_model_error_becomes_a_note_and_offline_mood(self):
        self.mode["error"] = "no route to ollama"
        self.service.send("Hi")
        self.assertTrue(self.idle())
        self.assertIn("chat_error", self.names())
        error = [p for e, p in self.events if e == "chat_error"][0]
        self.assertIn("no route to ollama", error["message"])
        last = self.log.history()[0][-1]
        self.assertEqual(last["status"], "error")
        status = self.service.status()
        self.assertEqual(status["activity"], "offline")
        self.assertEqual(status["mood"]["text"], "Can't reach my brain right now.")
        # the next successful answer ends the offline state
        self.mode["error"] = None
        self.service.send("again")
        self.assertTrue(self.idle())
        self.assertEqual(self.service.status()["activity"], "idle")

    def test_commands_are_system_notes_not_chat(self):
        seen = []
        service = self.make(run_command=lambda command: seen.append(command) or "Switched.")
        ack = service.send("/Light!")
        self.assertTrue(ack["ok"] and ack["command"])
        self.assertTrue(wait_for(lambda: not service.status()["busy"]))
        self.assertEqual(seen, ["/light!"])
        messages = self.log.history()[0]
        self.assertEqual([(m["role"], m["text"]) for m in messages], [("system", "Switched.")])
        self.assertNotIn("chat_start", self.names())

    def test_dream_command_shows_the_dreaming_activity(self):
        activities = []
        service = self.make(run_command=lambda command: activities.append(service.status()["activity"]))
        service.send("/dream!")
        self.assertTrue(wait_for(lambda: not service.status()["busy"]))
        self.assertEqual(activities, ["dreaming"])
        self.assertEqual(service.status()["activity"], "idle")

    def test_rate_limit_per_sender(self):
        service = self.make(rate_limit=(3, 60), queue_size=10)
        self.gate.clear()
        results = [service.send("m%d" % i, sender="a")["ok"] for i in range(5)]
        self.assertEqual(results, [True, True, True, False, False])
        self.assertTrue(service.send("other", sender="b")["ok"])
        self.gate.set()

    def test_automatic_message_is_logged_with_marker(self):
        record = self.service.post_assistant("It is noon.", emotion="surprised", auto=True)
        self.assertTrue(record["auto"])
        self.assertEqual(self.log.last()["text"], "It is noon.")
        self.assertIn("chat_message", self.names())
        self.assertEqual(self.service.status()["mood"]["emotion"], "surprised")

    def test_commands_are_listed_once(self):
        listed = {c["command"] for c in self.service_module.COMMANDS}
        self.assertEqual(listed, {"/light!", "/full!", "/dream!", "/time!", "/lookup ", "/search ", "/goodnight!", "/break!"})
        self.assertTrue(all(c["confirm"] for c in self.service_module.COMMANDS if c["command"] in ("/break!", "/goodnight!")))


class ExchangeStopTest(unittest.TestCase):
    """Communicator.exchange(should_stop=...) with a fake model stream"""

    def test_stop_closes_the_stream_and_keeps_the_text(self):
        communicator = importlib.import_module("MIA.communicator")
        comm = communicator.Communicator.__new__(communicator.Communicator)
        comm._history = []
        comm.MSG_KEY, comm.CONTENT_KEY, comm.ROLE_KEY = "message", "content", "role"
        comm._max_conversations = 100
        comm.dump_history = lambda: None
        closed = []

        class Stream:
            def __init__(self):
                self.chunks = iter(["happy\n", "Hello ", "wor", "ld"])

            def __iter__(self):
                return self

            def __next__(self):
                return {"message": {"content": next(self.chunks)}}

            def close(self):
                closed.append(True)

        comm.chat = lambda msg, stream=True: Stream()
        counter = [0]

        def should_stop():
            counter[0] += 1
            return counter[0] > 3

        answer, filtered, penalty = comm.exchange("hi", should_stop=should_stop)
        self.assertEqual(closed, [True])
        self.assertIsNone(penalty)
        self.assertTrue(answer.startswith("happy"))
        self.assertIn("Hello", filtered)
        self.assertEqual(comm._history[-1]["content"], answer)


class WebAppChat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("MIA_TEST", "1")
        cls.wa = importlib.import_module("MIA.web_app")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.wa.chat_log.path = os.path.join(cls.tmp.name, "log.jsonl")
        cls.wa.chat_log.clear()
        cls.http = cls.wa.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.wa.chat_log.clear()
        self.answers = []
        service = self.wa.chat_service

        def fake(text, on_delta, on_emotion, should_stop):
            on_emotion("smug")
            on_delta("Fine.")
            self.answers.append(text)
            return "Fine."

        self._exchange = service._run_exchange
        service._run_exchange = fake
        service.rate_limit = None
        service._rate_count = 0

    def tearDown(self):
        self.wa.chat_service._run_exchange = self._exchange

    def test_two_clients_see_the_same_conversation(self):
        wa = self.wa
        a = wa.socketio.test_client(wa.app)
        b = wa.socketio.test_client(wa.app)
        a.get_received()
        b.get_received()
        ack = a.emit("chat_send", {"id": "c1", "text": "Hello MIA"}, callback=True)
        self.assertTrue(ack["ok"])
        self.assertTrue(wait_for(lambda: not wa.chat_service.status()["busy"]))
        time.sleep(0.2)
        for client in (a, b):
            names = [m["name"] for m in client.get_received()]
            for event in ("chat_message", "chat_start", "chat_done", "chat_status"):
                self.assertIn(event, names)
        self.assertEqual(self.answers, ["Hello MIA"])

    def test_new_page_gets_the_status_on_connect(self):
        client = self.wa.socketio.test_client(self.wa.app)
        received = client.get_received()
        status = [m["args"][0] for m in received if m["name"] == "chat_status"]
        self.assertTrue(status)
        self.assertIn("mood", status[0])

    def test_old_message_event_is_gone(self):
        client = self.wa.socketio.test_client(self.wa.app)
        client.get_received()
        client.emit("message", "old page", callback=True)
        time.sleep(0.3)
        self.assertEqual(self.answers, [])
        self.assertEqual(self.wa.chat_log.history()[0], [])
        self.assertFalse(hasattr(self.wa, "send_answer"))
        self.assertNotIn("answer", [m["name"] for m in client.get_received()])

    def test_history_status_and_commands_api(self):
        client = self.wa.socketio.test_client(self.wa.app)
        client.emit("chat_send", {"text": "one"}, callback=True)
        self.assertTrue(wait_for(lambda: not self.wa.chat_service.status()["busy"]))
        history = self.http.get("/api/chat/history?limit=10").get_json()
        self.assertEqual([m["role"] for m in history["messages"]], ["user", "assistant"])
        self.assertFalse(history["older"])
        self.assertEqual(self.http.get("/api/chat/history?limit=abc").status_code, 400)
        status = self.http.get("/api/chat/status").get_json()
        self.assertEqual(set(status), {"busy", "activity", "model", "profile", "queue", "mood"})
        commands = self.http.get("/api/chat/commands").get_json()["commands"]
        self.assertIn("/break!", [c["command"] for c in commands])

    def test_clear_needs_the_token(self):
        self.wa.chat_log.append("user", "secret")
        token = self.wa.app.config["EDITOR_TOKEN_INFO"][0]
        body = {"scope": "log"}
        if token:
            self.assertEqual(self.http.post("/api/chat/clear", json=body).status_code, 401)
        self.assertEqual(self.http.post("/api/chat/clear", json=body, headers={"X-MIA-Token": token or ""}).status_code, 200)
        self.assertEqual(self.wa.chat_log.history()[0], [])
        bad = self.http.post("/api/chat/clear", json={"scope": "all"}, headers={"X-MIA-Token": token or ""})
        self.assertEqual(bad.status_code, 400)
        foreign = self.http.post("/api/chat/clear", json=body, headers={"X-MIA-Token": token or "", "Origin": "http://evil.example"})
        self.assertEqual(foreign.status_code, 403)


if __name__ == "__main__":
    unittest.main()
