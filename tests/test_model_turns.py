"""
TC-RUN-009 (REQ-RUN-009) and TC-RUN-010 (REQ-RUN-010): the model server takes one call at a time (pipeline_model.ModelTurns); a chat call that waits gets
the next turn before the next call of a background run, which yields between its calls; a streamed answer holds its turn until it is read or stopped.
The Ollama client is a fake that records the order of the calls and whether two ever overlapped.
Run with: python tests/test_model_turns.py
"""

import os
import sys
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, "helpers"))

from markers import mark                                       # noqa: E402
from pipeline_model import ModelTurns, OllamaModel, TurnClient  # noqa: E402


class FakeClient:
    """records every call (its tag) in order; `hold[tag]` is an Event the call waits for before it ends; counts how many calls run at once"""

    def __init__(self):
        self.order, self.hold, self.started = [], {}, {}
        self.running = self.most = 0
        self._lock = threading.Lock()

    def _enter(self, tag):
        with self._lock:
            self.running += 1
            self.most = max(self.most, self.running)
            self.order.append(tag)
        self.started.setdefault(tag, threading.Event()).set()
        if tag in self.hold:
            self.hold[tag].wait(5)
        with self._lock:
            self.running -= 1

    def chat(self, model=None, messages=None, stream=False, **kwargs):
        tag = messages[-1]["content"]
        if stream:
            return self._stream(tag)
        self._enter(tag)
        return {"message": {"content": "ok " + tag}}

    def _stream(self, tag):
        self._enter(tag)
        for word in ("a", "b", "c"):
            yield {"message": {"content": word}}

    def list(self):
        return {"models": []}


def ask(client, tag, **kwargs):
    return client.chat(model="m", messages=[{"role": "user", "content": tag}], **kwargs)


def background(turns, fake, tags):
    model = OllamaModel(TurnClient(fake, turns, "background"), lambda profile: None, lambda: ("m", None))
    for tag in tags:
        model.chat([{"role": "user", "content": tag}])


def wait_until(condition, seconds=5):
    deadline = time.monotonic() + seconds
    while not condition():
        if time.monotonic() > deadline:
            raise AssertionError("condition not reached")
        time.sleep(0.005)


class ModelTurnsTests(unittest.TestCase):

    @mark.req("REQ-RUN-010")
    def test_two_simultaneous_messages_are_answered_one_after_the_other(self):
        """TC-RUN-010: two simultaneous messages are answered one after the other.

        Example: first, second -> order ["first", "second"], most 1
        """
        # Given: turns, fake = ModelTurns(), FakeClient()
        turns, fake = ModelTurns(), FakeClient()
        fake.hold["first"] = threading.Event()
        chat = TurnClient(fake, turns, "chat")
        one = threading.Thread(target=ask, args=(chat, "first"))
        one.start()
        wait_until(lambda: "first" in fake.started)
        two = threading.Thread(target=ask, args=(chat, "second"))
        two.start()
        wait_until(lambda: turns.waiting()["chat"] == 1)
        fake.hold["first"].set()
        one.join(5)
        two.join(5)
        self.assertEqual(fake.order, ["first", "second"])
        self.assertEqual(fake.most, 1)

    @mark.req("REQ-RUN-009")
    def test_a_waiting_chat_message_gets_the_next_turn(self):
        """TC-RUN-009: a waiting chat message gets the next turn.

        Example: b1, b2, b3 + chat -> order ["b1", "chat", "b2", "b3"], most 1
        """
        # Given: turns, fake = ModelTurns(), FakeClient()
        turns, fake = ModelTurns(), FakeClient()
        fake.hold["b1"] = threading.Event()
        run = threading.Thread(target=background, args=(turns, fake, ["b1", "b2", "b3"]))
        run.start()
        wait_until(lambda: "b1" in fake.started)
        chat = threading.Thread(target=ask, args=(TurnClient(fake, turns, "chat"), "chat"))
        chat.start()
        wait_until(lambda: turns.waiting()["chat"] == 1)
        fake.hold["b1"].set()
        run.join(5)
        chat.join(5)
        self.assertEqual(fake.order, ["b1", "chat", "b2", "b3"])
        self.assertEqual(fake.most, 1)

    @mark.req("REQ-RUN-010")
    def test_one_model_call_at_a_time_across_chat_and_background(self):
        """TC-RUN-010: one model call at a time across chat and background.

        Example: 2 background runs, 5 chat calls -> 15 total calls, most 1
        """
        # Given: turns, fake = ModelTurns(), FakeClient()
        turns, fake = ModelTurns(), FakeClient()
        chat = TurnClient(fake, turns, "chat")
        threads = [threading.Thread(target=background, args=(turns, fake, ["b%d-%d" % (i, j) for j in range(5)])) for i in range(2)]
        threads += [threading.Thread(target=ask, args=(chat, "c%d" % i)) for i in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(5)
        self.assertEqual(len(fake.order), 15)
        self.assertEqual(fake.most, 1)

    @mark.req("REQ-RUN-010")
    def test_a_streamed_answer_holds_its_turn_until_it_is_read(self):
        """TC-RUN-010: a streamed answer holds its turn until it is read.

        Example: streamed + b1 -> order ["streamed", "b1"], first "a", rest ["b", "c"]
        """
        # Given: turns, fake = ModelTurns(), FakeClient()
        turns, fake = ModelTurns(), FakeClient()
        stream = ask(TurnClient(fake, turns, "chat"), "streamed", stream=True)
        first = next(stream)
        other = threading.Thread(target=background, args=(turns, fake, ["b1"]))
        other.start()
        wait_until(lambda: turns.waiting()["background"] == 1)
        self.assertEqual(fake.order, ["streamed"])
        rest = [chunk["message"]["content"] for chunk in stream]
        other.join(5)
        self.assertEqual((first["message"]["content"], rest), ("a", ["b", "c"]))
        self.assertEqual(fake.order, ["streamed", "b1"])

    @mark.req("REQ-RUN-010")
    def test_a_stopped_stream_gives_back_its_turn(self):
        """TC-RUN-010: a stopped stream gives back its turn.

        Example: stopped stream + b1 -> order ["stopped", "b1"]
        """
        # Given: turns, fake = ModelTurns(), FakeClient()
        turns, fake = ModelTurns(), FakeClient()
        stream = ask(TurnClient(fake, turns, "chat"), "stopped", stream=True)
        next(stream)
        stream.close()
        other = threading.Thread(target=background, args=(turns, fake, ["b1"]))
        other.start()
        other.join(5)
        self.assertEqual(fake.order, ["stopped", "b1"])

    @mark.req("REQ-RUN-010")
    def test_the_holder_may_call_again_without_waiting_for_itself(self):
        """TC-RUN-010: the holder may call again without waiting for itself.

        Example: answer + repair -> order ["answer", "repair"], list []
        """
        # Given: turns, fake = ModelTurns(), FakeClient()
        turns, fake = ModelTurns(), FakeClient()
        chat = TurnClient(fake, turns, "chat")
        stream = ask(chat, "answer", stream=True)
        next(stream)
        repaired = ask(chat, "repair")
        list(stream)
        self.assertEqual(repaired["message"]["content"], "ok repair")
        self.assertEqual(fake.order, ["answer", "repair"])
        self.assertEqual(chat.list(), {"models": []})


if __name__ == "__main__":
    unittest.main()
