"""
A stop ends the voice of an answer (owner check A3, D-154; REQ-VPB-002, REQ-FE-012): the speech process (speak.py) publishes no further
line of a stream whose client went away, and the client (speech_stream.py) goes away when the chat is stopped while the answer is spoken.
The speech process runs for real on a free port of the loopback, with a speaker that renders no sound and records what it publishes.
Needs the app's packages: bash tools/run_in_image.sh tests/test_speech_stop.py
"""
import importlib
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "helpers"))

_LINK_DIR = tempfile.mkdtemp()
os.symlink(REPO, os.path.join(_LINK_DIR, "MIA"))
sys.path.insert(0, _LINK_DIR)

from markers import mark  # noqa: E402

speak = importlib.import_module("MIA.speak")
speech_stream = importlib.import_module("MIA.speech_stream")
C = importlib.import_module("MIA.constants")

LINE_SECONDS = 0.3            # the play length of every rendered sentence


class RecordingSpeaker(speak.Speaker):
    """renders a sentence into a text file and 'publishes' it by recording the sentence (the real one uploads the wav by POST /upload)"""

    def __init__(self):            # no TTS model
        self._sentence_pause = 0
        self.published = []
        self.first_published = threading.Event()

    def render_voice(self, msg, output_file):
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(msg)
        return LINE_SECONDS

    def play_voice(self, wav_file):
        with open(wav_file, encoding="utf-8") as rendered:
            self.published.append(rendered.read())
        self.first_published.set()


class SpeechStop(unittest.TestCase):
    def setUp(self):
        self.speaker = RecordingSpeaker()
        self.server = speak.SoundServer(("127.0.0.1", 0), speak.SoundHandler)
        self.server.speaker = self.speaker
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.port = self.server.server_address[1]

    def stream(self, sentences):
        """a client that sends the sentences of an answer and its end marker, as SpeechStreamer.finish does"""
        client = socket.create_connection(("127.0.0.1", self.port))
        lines = [{C.SPEECH_REQ: s, C.TIME_REQ: "t", C.STREAM_REQ: True} for s in sentences] + [{C.STREAM_END_REQ: True, C.TIME_REQ: "t"}]
        client.sendall("".join(json.dumps(line) + "\n" for line in lines).encode("utf-8"))
        return client

    @mark.req("REQ-VPB-002", "REQ-FE-012")
    def test_a_client_that_goes_away_gets_no_further_line_published(self):
        """A3: the speech process stops a stream whose client closed the connection: the sentences still waiting or being rendered are not published.

        Example: four sentences sent, the client closes after "One." is published -> published == ["One."], also 1 s later.
        """
        # Given: an answer of four sentences in the speech process, the first one published
        client = self.stream(["One.", "Two.", "Three.", "Four."])
        self.assertTrue(self.speaker.first_published.wait(5))
        # When: the client goes away (the chat was stopped)
        client.close()
        time.sleep(4 * LINE_SECONDS + 0.5)
        # Then: nothing after the first sentence was published
        self.assertEqual(self.speaker.published, ["One."])

    @mark.req("REQ-VPB-002", "REQ-FE-012")
    def test_a_client_that_goes_away_while_the_answer_is_written_gets_no_further_line_published(self):
        """A3: a stop while the model still writes (SpeechStreamer.abort before the end marker) also ends the stream.

        Example: four sentences sent without the end marker, the client closes after "One." -> published == ["One."].
        """
        # Given: four sentences of an answer that is still being written (no end marker), the first one published
        client = socket.create_connection(("127.0.0.1", self.port))
        client.sendall("".join(json.dumps({C.SPEECH_REQ: s, C.TIME_REQ: "t", C.STREAM_REQ: True}) + "\n"
                               for s in ["One.", "Two.", "Three.", "Four."]).encode("utf-8"))
        self.assertTrue(self.speaker.first_published.wait(5))
        # When: the client goes away
        client.close()
        time.sleep(4 * LINE_SECONDS + 0.5)
        # Then: nothing after the first sentence was published
        self.assertEqual(self.speaker.published, ["One."])

    @mark.req("REQ-VPB-002", "REQ-FE-012")
    def test_an_answer_that_is_not_stopped_is_published_whole(self):
        """The stop check does not cut a normal answer: every sentence is published and the client gets its reply.

        Example: three sentences, nobody stops -> published == ["One.", "Two.", "Three."], the reply names SOUND.
        """
        # Given: a streamer of the chat with an answer of three sentences
        streamer = speech_stream.SpeechStreamer("127.0.0.1", self.port)
        streamer.finish("One. Two. Three.")
        # When: it waits for the voice without a stop
        streamer.wait(should_stop=lambda: False)
        # Then: all three sentences were published
        self.assertEqual(self.speaker.published, ["One.", "Two.", "Three."])

    @mark.req("REQ-VPB-002", "REQ-FE-012")
    def test_a_stop_while_the_answer_is_spoken_ends_the_stream_at_once(self):
        """A3: SpeechStreamer.wait(should_stop) gives up the stream when the chat is stopped, so the speech process publishes nothing more.

        Example: four sentences, the stop comes after "One." -> wait returns in under 1 s, published == ["One."].
        """
        # Given: a streamer of the chat with an answer of four sentences, the first one published
        streamer = speech_stream.SpeechStreamer("127.0.0.1", self.port)
        streamer.finish("One. Two. Three. Four.")
        self.assertTrue(self.speaker.first_published.wait(5))
        # When: the chat is stopped while the answer is spoken
        started = time.monotonic()
        streamer.wait(should_stop=lambda: True)
        waited = time.monotonic() - started
        time.sleep(4 * LINE_SECONDS + 0.5)
        # Then: the wait ended at once and no further sentence was published
        self.assertLess(waited, 1)
        self.assertEqual(self.speaker.published, ["One."])


if __name__ == "__main__":
    unittest.main()
