"""Chat agent N-2.2, the hand-over to the sound server (A-132, TD-11 option B): TC-CHA-036 (REQ-CHA-031, REQ-CHA-032, REQ-CHA-034).
The real SoundServer and SoundHandler of speak.py on a free localhost port with real TCP clients; only the speaker is a fake sink (TR-VOICE-004): it records
every chunk it is asked to play and honours `cancelled` the way Speaker.speak_chunks does. The engine itself is the hand check TC-CHA-035 (TR-VOICE-002).
This is a characterization of today's server: it is expected green from the start; a red result is a finding about the server (queue or cancel), not about this file.
Run with: python tests/test_sound_server_handover.py"""
import json
import os
import queue
import socket
import sys
import threading
import time
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests", "helpers"))

from markers import mark                                                   # noqa: E402
from constants import SPEECH_REQ, TIME_REQ, STREAM_REQ, STREAM_END_REQ     # noqa: E402
from speak import SoundHandler, SoundServer, Speaker                       # noqa: E402

PLAY = 0.3          # seconds one chunk "plays" in the sink
WAIT = 5            # seconds a test waits for something that must happen


class FakeSink(Speaker):
    """the fake speaker: takes the chunks like Speaker.speak_chunks (a feeder drains the stream while the previous chunk plays), records the start of every
    chunk, plays none, and plays no further chunk once `cancelled` is set (TR-VOICE-004). The engine (Kokoro, the effect, the upload) is not touched."""
    def __init__(self):                                      # no engine: Speaker.__init__ is not called
        self.starts = []                                     # [(text, time of the start)], in the order of the plays
        self.started = threading.Event()                     # the first chunk has started
        self._lock = threading.Lock()

    def speak_chunks(self, chunks, cancelled=None):
        cancelled = cancelled or threading.Event()
        waiting = queue.Queue()
        finished = object()

        def feed():
            for chunk in chunks:
                waiting.put(chunk)
            waiting.put(finished)
        threading.Thread(target=feed, daemon=True).start()
        play_end = 0
        item = waiting.get()
        while item is not finished:
            cancelled.wait(max(0, play_end - time.time()))   # the previous chunk is played first
            if cancelled.is_set():
                break
            with self._lock:
                self.starts.append((item, time.time()))
            self.started.set()
            play_end = time.time() + PLAY
            item = waiting.get()
        return PLAY

    @property
    def texts(self):
        with self._lock:
            return [text for text, _ in self.starts]

    def start_of(self, text):
        with self._lock:
            return next(t for name, t in self.starts if name == text)


def line(sentence=None, end=False):
    """one line of the stream protocol of SpeechStreamer: a sentence, or the end marker"""
    body = {STREAM_END_REQ: True} if end else {SPEECH_REQ: sentence, TIME_REQ: "t", STREAM_REQ: True}
    return (json.dumps(body) + "\n").encode("utf-8")


def until(condition, seconds=WAIT):
    end = time.time() + seconds
    while time.time() < end:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


class HandoverTest(unittest.TestCase):
    def setUp(self):
        self.sink = FakeSink()
        SoundServer.allow_reuse_address = True
        self.server = SoundServer(("127.0.0.1", 0), SoundHandler)       # port 0: a free one, never the port of a running MIA
        self.server.speaker = self.sink
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.sockets = []
        self.addCleanup(lambda: [s.close() for s in self.sockets])

    def connect(self):
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=WAIT)
        self.sockets.append(sock)
        return sock

    def play_stream(self, sentences, gap=0.0, during=None):
        """a client in a thread of its own: sends the sentences with `gap` s between them and the end marker, then waits for the reply of the server;
        `during` is called once after the second sentence (the moment another client arrives)"""
        sock = self.connect()

        def run():
            for number, sentence in enumerate(sentences):
                sock.sendall(line(sentence))
                if number == 1 and during:
                    during()
                time.sleep(gap)
            sock.sendall(line(end=True))
            try:
                sock.recv(4096)               # the reply "Stream played!"
            except OSError:
                pass
            sock.close()                      # as SpeechStreamer.wait does: the server's handler ends only when the client has closed (its watcher holds the reader)
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        return thread

    def assert_no_overlap(self, texts):
        """each chunk starts after the previous one has played (its start plus PLAY); a small tolerance for the clock"""
        times = [self.sink.start_of(text) for text in texts]
        for earlier, later in zip(times, times[1:]):
            self.assertGreaterEqual(later - earlier, PLAY - 0.02)

    @mark.req("REQ-CHA-031", "REQ-CHA-034")
    def test_the_sentences_arrive_in_order_and_a_second_request_waits_behind_the_first(self):
        """TC-CHA-036 (REQ-CHA-031, REQ-CHA-034): the sentences of one request reach the sink in order; a second request that arrives during the first is played after it.
        Example: client 1 sends "One.", "Two.", "Three."; client 2 connects after "Two." and sends "Four."; the sink plays One, Two, Three, Four."""
        # Given the real server with a fake sink (setUp), client 1 sending slowly, client 2 ready
        second_client = []

        def client_two():
            second_client.append(self.play_stream(["Four."]))
        # When client 1 sends the three sentences and the end marker slowly, and client 2 connects during that and sends "Four." and the end marker
        first = self.play_stream(["One.", "Two.", "Three."], gap=0.1, during=client_two)
        # Then the sink got One., Two., Three. and only then Four., never two at once
        self.assertTrue(until(lambda: len(self.sink.texts) >= 4, 10), "the sink got %r" % (self.sink.texts,))
        first.join(WAIT)
        self.assertEqual(self.sink.texts, ["One.", "Two.", "Three.", "Four."])
        self.assert_no_overlap(["One.", "Two.", "Three.", "Four."])

    @mark.req("REQ-CHA-032")
    def test_a_client_that_closes_its_connection_cancels_the_rest(self):
        """TC-CHA-036 (REQ-CHA-032): a client that closes its connection cancels the rest of its request, and the server serves the next one within 2 s.
        Example: client 1 sends "One.", waits until it plays, sends "Two.", "Three." and closes; the sink got One. and not Two. or Three.; "Five." of client 3 is played within 2 s."""
        # Given the real server with a fake sink, client 1 connected and a client 3 waiting behind it
        sock = self.connect()
        sock.sendall(line("One."))
        self.assertTrue(self.sink.started.wait(WAIT), "the sink never got One.")
        third = self.play_stream(["Five."])
        # When client 1 sends two more sentences while One. plays and closes its connection (the chat was stopped)
        sock.sendall(line("Two.") + line("Three."))
        sock.close()
        closed_at = time.time()
        # Then the sink got One. and not Two. or Three., and the next request is played within 2 s of the close
        self.assertTrue(until(lambda: "Five." in self.sink.texts, 2), "the sink got %r" % (self.sink.texts,))
        self.assertLess(self.sink.start_of("Five.") - closed_at, 2)
        self.assertEqual(self.sink.texts, ["One.", "Five."])
        third.join(WAIT)


if __name__ == "__main__":
    unittest.main()
